"""Keeping a course away from the learner's real AWS account.

`learn check` runs an exercise's tests against a mock provider, but lessons also tell the
learner to run Terraform and the AWS CLI themselves, and those use whatever credentials the
machine has. So a lesson's files are read for every way they could reach a real account,
before any of them runs, here or on the learner's machine. Each rule closes one way in:

- every `provider "aws"` block has literal fake keys, skips the account lookups, and sends
  any endpoint it names to this machine. Keys in the block win over environment variables,
  profiles, SSO and an instance role, so the learner's own credentials never load
- a configuration that uses AWS has that block at its root, so Terraform doesn't fill in a
  default one that finds the learner's credentials
- state stays on the machine: no other backend, no cloud block, no remote state
- nothing runs commands or fetches from the network: no provisioners, no `http` or
  `external` data, and modules only from local folders
- the tests use `mock_provider "aws"` and configure no provider of their own
- an `aws` command in the lesson goes to a local endpoint, and exercise code doesn't use an
  AWS SDK, for now
- no `.tf.json` or override files, which could undo any of the above

The files are read with a small HCL reader, not run. A file it can't follow counts as a
problem, so nothing it doesn't understand gets through.
"""

from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from .model import CourseFile, Lesson

# what the lesson prompt tells the teacher to write
FAKE_KEYS = 'access_key = "test" and secret_key = "test"'
SKIPS = ("skip_credentials_validation", "skip_requesting_account_id", "skip_metadata_api_check")
# each of these makes the provider load credentials from somewhere other than its own keys
OTHER_CREDENTIALS = ("profile", "shared_credentials_files", "shared_config_files")
OTHER_CREDENTIAL_BLOCKS = ("assume_role", "assume_role_with_web_identity")
# the shape of a real AWS access key id
REAL_KEY = re.compile(r"\b(?:AKIA|ASIA|AIDA|AROA)[A-Z0-9]{16}\b")
# the top-level blocks whose first label names a resource type
TYPED = ("resource", "data", "ephemeral", "action", "list")
HASHICORP_AWS = ("hashicorp/aws", "registry.terraform.io/hashicorp/aws")
# every key the endpoints block takes, from `terraform providers schema` on hashicorp/aws 6.68.0
ENDPOINT_KEYS = frozenset("""
    accessanalyzer account accountaccess acm acmpca agentregistry amg amp amplify apigateway
    apigatewayv2 appautoscaling appconfig appfabric appflow appintegrations
    appintegrationsservice applicationautoscaling applicationinsights applicationsignals appmesh
    appregistry apprunner appstream appsync arcregionswitch arczonalshift athena auditmanager
    autoscaling autoscalingplans backup batch bcmdataexports beanstalk bedrock bedrockagent
    bedrockagentcore bedrockruntime billing budgets ce chatbot chime chimesdkmediapipelines
    chimesdkvoice cleanrooms cloud9 cloudcontrol cloudcontrolapi cloudformation cloudfront
    cloudfrontkeyvaluestore cloudhsm cloudhsmv2 cloudsearch cloudtrail cloudwatch
    cloudwatchevents cloudwatchevidently cloudwatchlog cloudwatchlogs
    cloudwatchobservabilityaccessmanager cloudwatchomni cloudwatchrum codeartifact codebuild
    codecatalyst codecommit codeconnections codedeploy codeguruprofiler codegurureviewer
    codepipeline codestarconnections codestarnotifications cognitoidentity
    cognitoidentityprovider cognitoidp comprehend computeoptimizer config configservice connect
    connectcases controltower costandusagereportservice costexplorer costoptimizationhub cur
    customerprofiles databasemigration databasemigrationservice databrew dataexchange
    datapipeline datasync datazone dax deploy detective devicefarm devopsagent devopsguru
    directconnect directoryservice directoryservicedata dlm dms docdb docdbelastic drs ds dsql
    dynamodb ec2 ecr ecrpublic ecs efs eks elasticache elasticbeanstalk elasticloadbalancing
    elasticloadbalancingv2 elasticsearch elasticsearchservice elastictranscoder elb elbv2 emr
    emrcontainers emrserverless es eventbridge eventbridgev2 events evidently evs finspace
    firehose fis fms fsx gamelift glacier globalaccelerator glue gluedatabrew grafana greengrass
    groundstation guardduty healthlake iam identitystore imagebuilder inspector inspector2
    inspectorv2 interconnect internetmonitor invoicing iot ivs ivschat kafka kafkaconnect kendra
    keyspaces kinesis kinesisanalytics kinesisanalyticsv2 kinesisvideo kms lakeformation lambda
    lambdacore lambdamicrovms lambdaweb launchwizard lex lexmodelbuilding
    lexmodelbuildingservice lexmodels lexmodelsv2 lexv2models licensemanager lightsail location
    locationservice logs m2 macie2 mailmanager managedgrafana mediaconnect mediaconvert
    medialive mediapackage mediapackagev2 mediapackagevod mediastore memorydb mgn mpa mq msk
    mwaa mwaaserverless neptune neptunegraph networkfirewall networkflowmonitor networkmanager
    networkmonitor networksecuritymanager notifications notificationscontacts oam
    observabilityadmin odb opensearch opensearchingestion opensearchserverless opensearchservice
    organizations osis outposts paymentcryptography pcaconnectorad pcs pinpoint
    pinpointsmsvoicev2 pipes polly pricing prometheus prometheusservice qbusiness qldb
    quicksight ram rbin rds rdsdata rdsdataservice recyclebin redshift redshiftdata
    redshiftdataapiservice redshiftserverless rekognition resiliencehub resiliencehubv2
    resourceexplorer2 resourcegroups resourcegroupstagging resourcegroupstaggingapi
    rolesanywhere route53 route53domains route53profiles route53recoverycontrolconfig
    route53recoveryreadiness route53resolver rum s3 s3api s3control s3files s3outposts s3tables
    s3vectors sagemaker savingsplans scheduler schemas secretsmanager securityhub securitylake
    serverlessapplicationrepository serverlessapprepo serverlessrepo servicecatalog
    servicecatalogappregistry servicediscovery servicequotas ses sesv2 sfn shield signer sns sqs
    ssm ssmcontacts ssmincidents ssmquicksetup ssmsap sso ssoadmin stepfunctions storagegateway
    sts swf synthetics taxsettings timestreaminfluxdb timestreamquery timestreamwrite transcribe
    transcribeservice transfer uxc verifiedpermissions vpclattice waf wafregional wafv2
    wellarchitected workmail workspaces workspacesweb xray
""".split())
# the endpoints key each kind of AWS resource calls, where its name doesn't say. Otherwise
# aws_<key>_... calls <key>. A type that calls no API (aws_iam_policy_document, aws_region)
# isn't held to an endpoint
SERVICE_OF = [(re.compile(f"aws_(?:{types})"), service) for types, service in [
    (r"(?:elb|lb)_hosted_zone_id|(?:elb|cloudtrail|redshift|billing)_service_account|"
     r"cloudfront_log_delivery_canonical_user_id|iam_policy_document|region|partition|arn|default_tags", None),  # these call no API
    (r"instances?|vpcs?|vpc_.*|subnets?|security_groups?|security_group_.*|internet_gateway|"
     r"egress_only_internet_gateway|nat_gateways?|route|route_tables?|route_table_association|"
     r"main_route_table_association|eips?|eip_association|key_pair|amis?|ami_.*|ebs_.*|network_.*|"
     r"launch_template|placement_group|default_(?:vpc|subnet|security_group|route_table|network_acl)|"
     r"flow_log|spot_.*|ec2_.*|volume_attachment|customer_gateway|vpn_.*|availability_zones?", "ec2"),
    (r"s3_.*", "s3"), (r"iam_(?!policy_document$).*", "iam"), (r"caller_identity", "sts"),
    (r"lambda_.*", "lambda"), (r"dynamodb_.*", "dynamodb"), (r"sqs_.*", "sqs"), (r"sns_.*", "sns"),
    (r"kms_.*", "kms"), (r"cloudwatch_log_.*", "logs"), (r"cloudwatch_(?:metric_alarm|composite_alarm|dashboard)", "cloudwatch"),
    (r"elb|elb_.*|lb_cookie_stickiness_policy|lb_ssl_negotiation_policy|app_cookie_stickiness_policy|"
     r"load_balancer_.*|proxy_protocol_policy", "elb"),
    (r"lb|alb|lb_.*|alb_.*", "elbv2"), (r"cloudwatch_event_.*", "events"), (r"api_gateway_.*", "apigateway"),
    (r"kinesis_firehose_.*", "firehose"), (r"kinesis_video_.*", "kinesisvideo"),
    (r"kinesis_analytics_.*", "kinesisanalytics"), (r"cloudwatch_query_definition", "logs"),
    (r"route53_resolver_.*", "route53resolver"), (r"launch_configuration", "autoscaling"),
    (r"cognito_user_pools?|cognito_user_pool_.*|cognito_user|cognito_user_group|cognito_user_in_group|"
     r"cognito_identity_provider|cognito_resource_server|cognito_risk_configuration", "cognitoidp"),
    (r"cognito_identity_pool.*", "cognitoidentity"), (r"regions", "ec2"), (r"canonical_user_id", "s3"), (r"db_.*|rds_.*", "rds"), (r"autoscaling_.*", "autoscaling"),
    (r"ecr_.*", "ecr"), (r"ecs_.*", "ecs"), (r"route53_.*", "route53"), (r"secretsmanager_.*", "secretsmanager"),
    (r"ssm_.*", "ssm"),
]]


class Unreadable(ValueError):
    pass


# -- reading HCL ------------------------------------------------------------------------
#
# Enough of HCL's native syntax to find blocks and attributes: comments, strings with
# ${...} inside, heredocs, and expressions that span lines inside brackets.

Token = tuple[str, str]


@dataclass
class Block:
    type: str
    labels: list[str]
    attrs: dict[str, list[Token]] = field(default_factory=dict)
    blocks: list[Block] = field(default_factory=list)

    def label(self, i: int = 0) -> str:
        return self.labels[i] if len(self.labels) > i else ""

    def children(self, type_: str) -> list[Block]:
        return [b for b in self.blocks if b.type == type_]

    def walk(self):
        yield self
        for b in self.blocks:
            yield from b.walk()


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")
_HEREDOC = re.compile(r"<<-?([A-Za-z_][A-Za-z0-9_]*)[ \t]*\n")


def _string_end(text: str, i: int) -> int:
    """Where the quoted string that starts at i ends, past its closing quote."""
    j = i + 1
    while j < len(text):
        c = text[j]
        if c == "\\":
            j += 2
        elif c == '"':
            return j + 1
        elif c == "\n":
            raise Unreadable("a string runs past the end of its line")
        elif text.startswith(("$${", "%%{"), j):
            j += 3
        elif text.startswith(("${", "%{"), j):
            j = _template_end(text, j + 2)
        else:
            j += 1
    raise Unreadable("a string never ends")


def _template_end(text: str, j: int) -> int:
    depth = 1
    while j < len(text):
        c = text[j]
        if c == '"':
            j = _string_end(text, j)
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    raise Unreadable("a ${...} never closes")


def tokens(text: str) -> list[Token]:
    out: list[Token] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r":
            i += 1
        elif c == "\n":
            out.append(("nl", c))
            i += 1
        elif c == "#" or text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end < 0 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise Unreadable("a /* comment never ends")
            if "\n" in text[i:end]:
                out.append(("nl", "\n"))
            i = end + 2
        elif c == '"':
            end = _string_end(text, i)
            out.append(("string", text[i:end]))
            i = end
        elif m := _HEREDOC.match(text, i):
            close = re.compile(rf"^[ \t]*{re.escape(m.group(1))}[ \t]*$", re.M).search(text, m.end())
            if close is None:
                raise Unreadable(f"the <<{m.group(1)} heredoc never ends")
            out.append(("heredoc", text[i:close.end()]))
            i = close.end()
        elif m := _IDENT.match(text, i):
            out.append(("ident", m.group(0)))
            i = m.end()
        elif c in "{}[]()=":
            out.append(("punct", c))
            i += 1
        else:
            out.append(("other", c))
            i += 1
    return out


def _unquote(s: str) -> str:
    return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")


def _body(toks: list[Token], i: int, closed: bool) -> tuple[dict, list[Block], int]:
    attrs: dict[str, list[Token]] = {}
    blocks: list[Block] = []
    while i < len(toks):
        kind, text = toks[i]
        if kind == "nl":
            i += 1
            continue
        if closed and toks[i] == ("punct", "}"):
            return attrs, blocks, i + 1
        if kind != "ident":
            raise Unreadable(f"expected a name, found {text!r}")
        if i + 1 < len(toks) and toks[i + 1] == ("punct", "="):
            # an attribute runs to the end of its line, or past it inside brackets
            j, depth = i + 2, 0
            while j < len(toks):
                k, t = toks[j]
                if k == "punct" and t in "{[(":
                    depth += 1
                elif k == "punct" and t in "}])":
                    if depth == 0:
                        break  # the block it's in closes on the same line
                    depth -= 1
                elif k == "nl" and depth == 0:
                    break
                j += 1
            attrs[text] = [t for t in toks[i + 2:j] if t[0] != "nl"]
            i = j
            continue
        j, labels = i + 1, []
        while j < len(toks) and toks[j][0] in ("string", "ident"):
            labels.append(_unquote(toks[j][1]) if toks[j][0] == "string" else toks[j][1])
            j += 1
        if j >= len(toks) or toks[j] != ("punct", "{"):
            raise Unreadable(f"`{text}` is followed by neither = nor a block")
        inner_attrs, inner_blocks, i = _body(toks, j + 1, closed=True)
        blocks.append(Block(text, labels, inner_attrs, inner_blocks))
    if closed:
        raise Unreadable("a block never closes")
    return attrs, blocks, i


def read(text: str) -> list[Block]:
    """The top-level blocks of an HCL file. Raises Unreadable for what it can't follow."""
    attrs, blocks, _ = _body(tokens(text), 0, closed=False)
    if attrs:
        raise Unreadable(f"`{next(iter(attrs))} =` outside any block")
    return blocks


def literal(expr: list[Token] | None) -> str | None:
    """The value of an expression that is one plain string, else None."""
    if expr and len(expr) == 1 and expr[0][0] == "string" and "${" not in expr[0][1] and "%{" not in expr[0][1]:
        return _unquote(expr[0][1])
    return None


def is_true(expr: list[Token] | None) -> bool:
    return expr == [("ident", "true")]


def local_url(url: str) -> bool:
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and (host in ("localhost", "127.0.0.1", "::1")
                                                  or host.endswith(".localhost"))


# -- Terraform ----------------------------------------------------------------------------

FORBIDDEN_FILE = re.compile(r"(^|/)([^/]*\.tf\.json|[^/]*\.tftest\.json|override\.tf|[^/]*_override\.tf)$")


def _is_tf(path: str) -> bool:
    return path.endswith(".tf")


def _is_test(path: str) -> bool:
    return path.endswith(".tftest.hcl")


def _local_source(expr: list[Token] | None, folder: str = "") -> bool:
    """A module source that's a folder inside the exercise, relative to the file that names it."""
    source = literal(expr)
    if source is None or not source.startswith(("./", "../")):
        return False
    inside = posixpath.normpath(posixpath.join(folder or ".", source))
    return inside != ".." and not inside.startswith("../")


def service_of(resource_type: str) -> str | None:
    for pattern, svc in SERVICE_OF:
        if pattern.fullmatch(resource_type):
            return svc
    first = resource_type.removeprefix("aws_").split("_")[0]
    return first if first in ENDPOINT_KEYS else None


def _provider_ref(toks: list[Token]) -> tuple[str, str] | None:
    """aws.west, read as the tokens aws . west, gives ("aws", "west"). aws gives ("aws", "")."""
    if len(toks) == 1 and toks[0][0] == "ident":
        return toks[0][1], ""
    if len(toks) == 3 and toks[0][0] == "ident" and toks[1] == ("other", ".") and toks[2][0] == "ident":
        return toks[0][1], toks[2][1]
    return None


def _module_aliases(blocks: list[tuple[str, str, Block]]) -> dict[str, str]:
    """The folder of each module handed providers = { aws = aws.west }, and the alias it gets."""
    out = {}
    for path, _, b in blocks:
        toks, source = b.attrs.get("providers", []), literal(b.attrs.get("source"))
        if b.type != "module" or source is None:
            continue
        for i in range(len(toks) - 2):
            if toks[i] == ("ident", "aws") and toks[i + 1] == ("punct", "="):
                ref = _provider_ref(toks[i + 2:i + 5]) if toks[i + 3:i + 4] == [("other", ".")] else \
                    _provider_ref(toks[i + 2:i + 3])
                if ref:
                    out[posixpath.normpath(posixpath.join(posixpath.dirname(path) or ".", source))] = ref[1]
    return out


def _provider_problems(where: str, p: Block, services: set[str]) -> list[str]:
    name = f'{where}: the provider "aws" block' + (f' with alias {literal(p.attrs.get("alias"))!r}'
                                                     if "alias" in p.attrs else "")
    out = []
    keys = [literal(p.attrs.get(k)) for k in ("access_key", "secret_key")]
    if None in keys:
        out.append(f"{name} has no fake keys of its own, so Terraform would load the learner's own AWS "
                   f"credentials. Give it {FAKE_KEYS}")
    elif REAL_KEY.search(keys[0]):
        out.append(f"{name} has what looks like a real access key. Use {FAKE_KEYS}")
    missing = [s for s in SKIPS if not is_true(p.attrs.get(s))]
    if missing:
        out.append(f"{name} needs {', '.join(f'{s} = true' for s in missing)}, or the provider calls real "
                   "AWS to check the keys and look up the account")
    other = [a for a in OTHER_CREDENTIALS + OTHER_CREDENTIAL_BLOCKS if a in p.attrs] + \
        [b.type for b in p.blocks if b.type in OTHER_CREDENTIAL_BLOCKS]
    if other:
        out.append(f"{name} sets {', '.join(other)}, which loads credentials from somewhere other than its own "
                   "fake keys. Remove it")
    if "endpoints" in p.attrs:
        out.append(f"{name} sets endpoints = {{...}} as a map. Write it as an endpoints block")
    named = set()
    for endpoints in p.children("endpoints"):
        for service, expr in endpoints.attrs.items():
            named.add(service)
            url = literal(expr)
            if url is None or not local_url(url):
                out.append(f"{name} sends {service} to {url or 'an address worked out at run time'}. Every "
                           "endpoint has to be on this machine, like http://localhost:4566")
    for service in sorted(services - named):
        out.append(f'{name} has no endpoint for {service}, which the configuration uses, so those calls would go '
                   f'to real AWS. Add {service} = "http://localhost:4566" to its endpoints block')
    return out


def _source_of(expr: list[Token] | None) -> str | None:
    """The source in a required_providers entry, { source = "hashicorp/aws", ... }."""
    toks = expr or []
    for i in range(len(toks) - 2):
        if toks[i] == ("ident", "source") and toks[i + 1] == ("punct", "="):
            return literal(toks[i + 2:i + 3])
    return HASHICORP_AWS[0]  # with no source, Terraform uses hashicorp/aws


def config_problems(files: list[CourseFile], checks: list[CourseFile], which: str) -> list[str]:
    """What in one set of files (the starter or the solution) and the checks could reach a
    real AWS account, when the learner runs Terraform or when `learn check` does."""
    out: list[str] = []
    tf: dict[str, tuple[str, list[Block]]] = {}    # path: (how a problem names it, its blocks)
    tests: dict[str, tuple[str, list[Block]]] = {}
    named = {id(f): f"{f.path} ({which})" for f in files} | {id(f): f.path for f in checks}
    for f in files + checks:
        if FORBIDDEN_FILE.search(f.path):
            out.append(f"{named[id(f)]}: .tf.json and override files can change the provider without it "
                       "showing in the .tf files. Write plain .tf files")
            continue
        if not (_is_tf(f.path) or _is_test(f.path)):
            continue
        try:
            (tests if _is_test(f.path) else tf)[f.path] = (named[id(f)], read(f.content))
        except Unreadable as e:
            out.append(f"{named[id(f)]} couldn't be read to check it stays away from real AWS: {e}")

    blocks = [(path, where, b) for path, (where, bs) in tf.items() for b in bs]
    nested = [(path, where, x) for path, where, b in blocks for x in b.walk()]  # a check block can hold data
    uses_aws = any(b.type == "provider" and b.label() == "aws" or
                   b.type in TYPED and b.label().startswith("aws_") for _, _, b in nested)
    root = [b for path, _, b in blocks if "/" not in path]
    services: dict[str, set[str]] = {}  # by the provider alias the resources use
    handed = _module_aliases(blocks)
    for path, where, b in nested:
        if b.type not in TYPED or not b.label().startswith("aws_"):
            continue
        ref = _provider_ref(b.attrs.get("provider", []))
        if "provider" in b.attrs and (ref is None or ref[0] != "aws"):
            out.append(f"{where}: {b.label()} uses a provider other than aws or aws.<alias>, which these "
                       "checks don't follow. Use the aws provider block")
        folder = posixpath.dirname(path) or "."
        inherited = next((a for f, a in handed.items() if folder == f or folder.startswith(f + "/")), "")
        if svc := service_of(b.label()):
            services.setdefault(ref[1] if ref else inherited, set()).add(svc)
    if uses_aws and not any(b.type == "provider" and b.label() == "aws" and "alias" not in b.attrs for b in root):
        out.append(f"the {which}'s configuration uses AWS with no provider \"aws\" block in the exercise's top "
                   "folder, so Terraform would make a default one that finds the learner's own credentials. "
                   "Add the provider block from the instructions")

    for path, where, b in blocks:
        if b.type == "provider" and b.label() == "aws":
            out += _provider_problems(where, b, services.get(literal(b.attrs.get("alias")) or "", set()))
        if b.type == "module" and not _local_source(b.attrs.get("source"), posixpath.dirname(path)):
            out.append(f"{where}: module {b.label()!r} comes from {literal(b.attrs.get('source')) or 'somewhere'} "
                       "instead of a folder in the exercise, so its code isn't checked here. Use a local "
                       "path like ./modules/name")
        if b.type == "terraform":
            for required in b.children("required_providers"):
                source = _source_of(required.attrs.get("aws"))
                if "aws" in required.attrs and (source or "").casefold() not in HASHICORP_AWS:
                    out.append(f"{where} maps the aws provider to {source or 'a source worked out at run time'}, "
                               "which isn't hashicorp/aws, so its code isn't what these checks know. Use hashicorp/aws")
                for name, expr in required.attrs.items():
                    named_source = any(t == ("ident", "source") for t in expr)
                    if name != "aws" and named_source and (_source_of(expr) or "").casefold() in HASHICORP_AWS:
                        out.append(f"{where} names hashicorp/aws {name!r}. Call it aws, so the checks for its "
                                   "provider block apply")
            for backend in b.children("backend"):
                if backend.label() != "local":
                    out.append(f'{where} keeps state in a backend "{backend.label()}", which talks to a real '
                               "service with the learner's credentials. Leave state local and teach the backend "
                               "in the explanation")
            if b.children("cloud"):
                out.append(f"{where} has a cloud block, which sends state to HCP Terraform. Leave state local")

    for _, where, b in nested:
        if b.type == "provider" and b.label() == "awscc" or b.type in TYPED and b.label().startswith("awscc_"):
            out.append(f"{where} uses the awscc provider, which these checks don't cover yet. Use hashicorp/aws")
        if b.type == "data" and b.label() == "terraform_remote_state" and literal(b.attrs.get("backend")) != "local":
            out.append(f"{where} reads remote state from another backend. Only backend = \"local\" stays on "
                       "the machine")
        if b.type == "data" and b.label() in ("http", "external", "aws_ip_ranges"):
            out.append(f'{where} has a data "{b.label()}" source, which reaches the network or runs a '
                       "program. Remove it")
        if b.type == "provisioner":
            out.append(f"{where} has a provisioner, which runs commands on the learner's machine. Remove it")

    for where, bs in tests.values():
        mocks = [b for b in bs if b.type == "mock_provider" and b.label() == "aws"]
        if uses_aws and not any("alias" not in m.attrs for m in mocks):
            out.append(f'{where} has no mock_provider "aws" {{}} without an alias, so the tests would use the '
                       "real provider")
        if any(b.type == "provider" for b in bs):
            out.append(f"{where} configures a real provider. Tests use mock_provider only")
        for run in (b for b in bs if b.type == "run"):
            if "providers" in run.attrs:
                out.append(f"{where}: run {run.label()!r} sets providers, which can swap the mock for a real "
                           "provider. Leave it out")
            for module in run.children("module"):
                if not _local_source(module.attrs.get("source")):
                    out.append(f"{where}: run {run.label()!r} loads a module from outside the exercise. Use a "
                               "local path")
    return out


# -- the lesson's own words, and exercise code ------------------------------------------

_FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.S)
_SPAN = re.compile(r"`([^`\n]+)`")
# a command starts a line, or follows ; & && || | ( ) $( or a backtick
_SEPARATOR = re.compile(r";|&&?|\|\|?|\$\(|[()`]")
# the AWS CLI, however it's named: aws, aws2, /usr/local/bin/aws, python -m awscli
_COMMAND = re.compile(r"\s*(?:[$%>]\s+)?(?:sudo\s+)?((?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*)"
                      r"(?:[\w.~/-]*/)?(?:aws[0-9]*|python[0-9.]*\s+-m\s+awscli)\s+(?!=)(?=\S)(.*)$")
# the endpoint comes first, right after the CLI's name or just before it, so nothing later in
# the line (a comment, another call) can stand in for it
_ENDPOINT = re.compile(r"--endpoint-url(?:=|\s+)[\"']?([^\s\"']+)")
_ENV_ENDPOINT = re.compile(r"AWS_ENDPOINT_URL=[\"']?([^\s\"']+)")
SDK_CODE = (".py", ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts")
_SDK = re.compile(r"^\s*(?:import|from)\s+(?:boto3|botocore|aiobotocore)\b|@aws-sdk/|[\"']aws-sdk[\"']", re.M)


def _no_call(args: list[str]) -> bool:
    """aws --version, aws configure (but not configure sso), and help at the end: no API call."""
    if args == ["--version"] or args[:1] == ["configure"] and not (args[1:2] and args[1].startswith("sso")):
        return True
    return args[-1:] == ["help"] and not any(a.startswith("-") for a in args)


def _commands(code: str) -> list[tuple[str, bool]]:
    """The aws commands in a piece of code, each with whether it starts by naming a local endpoint."""
    joined = re.sub(r"\\\n", " ", code)
    found = []
    for line in joined.splitlines():
        for segment in _SEPARATOR.split(line):
            m = _COMMAND.match(segment)
            if not m or _no_call(m.group(2).split()):
                continue
            prefix = m.group(1).split()
            env = _ENV_ENDPOINT.fullmatch(prefix[-1]) if prefix else None
            own = _ENDPOINT.match(m.group(2))
            local = bool(env and local_url(env.group(1)) or own and local_url(own.group(1)))
            found.append((m.group(1) + "aws " + m.group(2), local))
    return found


def aws_commands(text: str) -> list[tuple[str, bool]]:
    code = _FENCE.findall(text)
    spans = _SPAN.findall(_FENCE.sub("", text))
    return [c for piece in code + spans for c in _commands(piece)]


def command_problems(commands: list[tuple[str, bool]], where: str) -> list[str]:
    out = []
    for c, safe in commands:
        if not safe:
            short = " ".join(c.split())[:80]
            out.append(f"{where} has `{short}`, which uses the learner's own AWS account. Start it "
                       "`aws --endpoint-url http://localhost:4566` so it goes to the emulator")
    return out


def uses_aws(lesson: Lesson) -> bool:
    """Does this lesson touch AWS at all: a provider, a resource, or an aws command."""
    if lesson.exercise:
        for f in lesson.exercise.starter + lesson.exercise.solution:
            if _is_tf(f.path) and re.search(r'provider\s+"aws"|^\s*(?:resource|data)\s+"aws_', f.content, re.M):
                return True
    texts = [lesson.explanation, lesson.worked_example]
    if lesson.exercise:
        texts += [lesson.exercise.task, *lesson.exercise.hints]
    return any(aws_commands(t) for t in texts)


def problems(lesson: Lesson) -> list[str]:
    """Every way this lesson could reach a real AWS account. Empty means none was found."""
    out = command_problems(aws_commands(lesson.explanation), "the explanation")
    out += command_problems(aws_commands(lesson.worked_example), "the worked example")
    ex = lesson.exercise
    if ex is not None:
        out += command_problems(aws_commands(ex.task), "the task")
        for i, h in enumerate(ex.hints, 1):
            out += command_problems(aws_commands(h), f"hint {i}")
        out += config_problems(ex.starter, ex.checks, "starter")
        out += config_problems(ex.solution, ex.checks, "solution")
        for f in ex.starter + ex.solution + ex.checks:
            name = PurePosixPath(f.path).name
            if (name.endswith(SDK_CODE) or name in ("package.json", "requirements.txt")) and _SDK.search(f.content):
                out.append(f"{f.path} uses an AWS SDK, which finds the learner's own credentials. Exercises "
                           "don't use one yet")
            elif name.endswith(".md"):
                out += command_problems(aws_commands(f.content), f.path)
            elif not (_is_tf(f.path) or _is_test(f.path)):
                out += command_problems(_commands(f.content), f.path)  # a script is all code
    return list(dict.fromkeys(out))
