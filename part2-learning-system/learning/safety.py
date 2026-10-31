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
- nothing runs commands or fetches from the network: no provisioners, no `http`, `external`
  or `local_command` types, no provider `exec` blocks, and modules only from local folders
- the tests use `mock_provider "aws"` and configure no provider of their own
- an `aws` command anywhere the learner reads it goes to a local endpoint, and exercise code
  doesn't use an AWS SDK, for now
- no `.tf.json` or override files, which could undo any of the above, no query files, and
  none of the state files Terraform writes for itself
- `import` and `removed` blocks count as uses of the type they name
- each exercise file has a plain path inside the exercise, no two land on the same file, a
  folder is spelled one way, and no .tf file has a name Terraform skips (a leading dot). A
  Mac ignores case and how an accent is typed, so names are compared the way it does
- a folder with AWS resources and no provider block is a module the exercise uses, and
  nothing the learner reads moves them into it, where Terraform would make a default one

The files are read with a small HCL reader, not run. A file it can't follow counts as a
problem, and so does an AWS type whose endpoint it can't name. The text is read for the ways
a lesson says to change folder: cd and the commands like it, `terraform -chdir`, and
sentences like "change into modules/net". Text worded to get around those still gets past.

The keys are what keep the account safe. The endpoints keep a lesson's calls on this
machine, with these gaps, where a call goes to AWS carrying the fake keys and AWS refuses it:
- some types also call a second service, like an EC2 lookup from an Elastic Beanstalk
  environment or a KMS read from an encrypted DynamoDB table. The table holds each type's
  own service
- a resource left in state by an earlier apply, and no longer in the files, is read through
  the provider the state names, and the files can't say which services that provider needs

And s3control calls put the account ID in front of the endpoint's host
(123456789012.localhost), which doesn't resolve on a Mac, so they fail before going anywhere.
"""

from __future__ import annotations

import posixpath
import re
import unicodedata
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
# what a configuration that uses AWS may fetch: the aws provider and the ones that stay on the
# machine. local's local_command runs a program, so it's refused with http and external
RUNS_OR_FETCHES = ("http", "external", "local_command", "aws_ip_ranges")
OFFLINE_PROVIDERS = ("aws", "random", "null", "local", "tls", "time", "archive")
# every key the endpoints block takes, from `terraform providers schema` on hashicorp/aws 6.70.0
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
    pinpointsmsvoicev2 pipes polly pricing pricingplanmanager prometheus prometheusservice qbusiness qldb
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
# the types that call no endpoint the provider block sets: they're worked out on the machine,
# or fetch a public file (aws_ip_ranges, refused on its own in config_problems)
NO_ENDPOINT = re.compile(r"aws_(?:(?:elb|lb)_hosted_zone_id|(?:elb|cloudtrail|redshift|billing)_service_account|"
                         r"cloudfront_log_delivery_canonical_user_id|elastic_beanstalk_hosted_zone|iam_policy_document|"
                         r"region|partition|arn|default_tags|service|service_principal|ip_ranges|"
                         r"eks_cluster_auth)")
# the endpoints key each kind of AWS resource calls, where its name doesn't say. Otherwise
# aws_<key>_... calls <key>, and a type that matches neither isn't cleared
SERVICE_OF = [(re.compile(f"aws_(?:{types})"), service) for types, service in [
    (r"instances?|vpcs?|vpc_.*|subnets?|security_groups?|security_group_.*|internet_gateway.*|"
     r"egress_only_internet_gateway|nat_gateways?|nat_gateway_.*|route|route_tables?|route_table_association|"
     r"main_route_table_association|eips?|eip_.*|key_pair|amis?|ami_.*|ebs_.*|network_.*|"
     r"launch_template|placement_group|default_(?:vpc|vpc_dhcp_options|subnet|security_group|route_table|network_acl)|"
     r"flow_log|spot_.*|ec2_.*|volume_attachment|customer_gateway|vpn_.*|availability_zones?|prefix_list|"
     r"snapshot_create_volume_permission|verifiedaccess_.*", "ec2"),
    (r"s3_account_.*|s3_access_.*", "s3control"),  # the provider's own names table puts these under s3control
    (r"s3_.*", "s3"), (r"iam_(?!policy_document$).*", "iam"), (r"caller_identity", "sts"),
    (r"lambda_.*", "lambda"), (r"dynamodb_.*", "dynamodb"), (r"sqs_.*", "sqs"), (r"sns_.*", "sns"),
    (r"kms_.*", "kms"), (r"cloudwatch_log_.*", "logs"), (r"cloudwatch_(?:metric_alarm|composite_alarm|dashboard)", "cloudwatch"),
    (r"elb|elb_.*|lb_cookie_stickiness_policy|lb_ssl_negotiation_policy|app_cookie_stickiness_policy|"
     r"load_balancer_.*|proxy_protocol_policy", "elb"),
    (r"lb|lbs|alb|lb_.*|alb_.*", "elbv2"), (r"cloudwatch_event_.*", "events"), (r"api_gateway_.*", "apigateway"),
    (r"kinesis_firehose_.*", "firehose"), (r"kinesis_video_.*", "kinesisvideo"),
    (r"kinesis_analytics_.*", "kinesisanalytics"), (r"cloudwatch_query_definition", "logs"),
    (r"route53_resolver_.*", "route53resolver"), (r"launch_configuration", "autoscaling"),
    (r"cognito_identity_pool.*|cognito_identity_openid_token_for_developer_identity", "cognitoidentity"),
    (r"cognito_.*", "cognitoidp"), (r"regions", "ec2"), (r"canonical_user_id", "s3"), (r"db_.*|rds_.*", "rds"), (r"autoscaling_.*", "autoscaling"),
    (r"ecr_.*", "ecr"), (r"ecs_.*", "ecs"), (r"route53_.*", "route53"), (r"secretsmanager_.*", "secretsmanager"),
    (r"ssm_.*", "ssm"), (r"directory_service_.*", "ds"), (r"dx_.*", "directconnect"),
    (r"elastic_beanstalk_.*", "elasticbeanstalk"), (r"media_convert_.*", "mediaconvert"),
    (r"media_package_.*", "mediapackage"), (r"media_packagev2_.*", "mediapackagev2"),
    (r"media_store_.*", "mediastore"), (r"mskconnect_.*", "kafkaconnect"),
    (r"service_discovery_.*", "servicediscovery"), (r"chime_voice_connector.*", "chimesdkvoice"),
]]


class Unreadable(ValueError):
    pass


# -- reading HCL ------------------------------------------------------------------------
#
# Enough of HCL's native syntax to find blocks and attributes: comments, strings with
# ${...} inside, heredocs, and expressions that span lines inside brackets.

Token = tuple[str, str]


class _Tok(tuple):
    """A (kind, text) token that also knows its line, and still compares equal to a plain pair."""
    line = 0


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

    def add(kind: str, value: str, at: int) -> None:
        t = _Tok((kind, value))
        t.line = text.count("\n", 0, at) + 1
        out.append(t)

    try:
        _scan(text, add)
    except Unreadable as e:
        raise Unreadable(f"line {e.args[1]}: {e.args[0]}" if len(e.args) > 1 else str(e)) from None
    return out


def _scan(text: str, add) -> None:
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r":
            i += 1
        elif c == "\n":
            add("nl", c, i)
            i += 1
        elif c == "#" or text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end < 0 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise Unreadable("a /* comment never ends", text.count("\n", 0, i) + 1)
            if "\n" in text[i:end]:
                add("nl", "\n", i)
            i = end + 2
        elif c == '"':
            try:
                end = _string_end(text, i)
            except Unreadable as e:
                raise Unreadable(str(e), text.count("\n", 0, i) + 1) from None
            add("string", text[i:end], i)
            i = end
        elif m := _HEREDOC.match(text, i):
            close = re.compile(rf"^[ \t]*{re.escape(m.group(1))}[ \t]*$", re.M).search(text, m.end())
            if close is None:
                raise Unreadable(f"the <<{m.group(1)} heredoc never ends", text.count("\n", 0, i) + 1)
            add("heredoc", text[i:close.end()], i)
            i = close.end()
        elif m := _IDENT.match(text, i):
            add("ident", m.group(0), i)
            i = m.end()
        elif c in "{}[]()=":
            add("punct", c, i)
            i += 1
        else:
            add("other", c, i)
            i += 1


def _unquote(s: str) -> str:
    return s[1:-1].replace('\\"', '"').replace("\\\\", "\\")


def _body(toks: list[Token], i: int, closed: bool, opened: int = 0) -> tuple[dict, list[Block], int]:
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
            raise Unreadable(f"line {toks[i].line}: {text!r} where a block or an attribute name should be")
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
            raise Unreadable(f"line {toks[i].line}: `{text}` needs a {{ on the same line to open its block, "
                             "or = and a value")
        inner_attrs, inner_blocks, i = _body(toks, j + 1, closed=True, opened=toks[j].line)
        blocks.append(Block(text, labels, inner_attrs, inner_blocks))
    if closed:
        raise Unreadable(f"the block opened on line {opened} never closes")
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
# `terraform query` runs these files' list blocks against the real provider, and they aren't read here
QUERY_FILE = re.compile(r"\.tfquery\.(hcl|json)$")
# what Windows reads as something else: C:main.tf is main.tf on drive C, main.tf. is main.tf, CON is a device
WINDOWS_NAME = re.compile(r'[<>:"|?*\x00-\x1f]|[. ]$|^(?:con|prn|aux|nul|com[0-9¹²³]|lpt[0-9¹²³])(?:\.|$)', re.I)
# Terraform writes these and reads them back. A shipped one can name a backend that isn't in the files
WORKING_FILE = re.compile(r"(^|/)(\.terraform(/|$)|terraform\.tfstate\.d/|[^/]*\.tfstate(\.backup)?$)")


def disk_key(path: str) -> str:
    """The same string for every spelling a Mac's disk reads as one name: it ignores case, and
    é typed as one character or as e and an accent."""
    return unicodedata.normalize("NFD", unicodedata.normalize("NFD", path).casefold())


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
    """The endpoints key a type calls, or None when these checks can't name it."""
    for pattern, svc in SERVICE_OF:
        if pattern.fullmatch(resource_type):
            return svc
    first = resource_type.removeprefix("aws_").split("_")[0]
    return first if first in ENDPOINT_KEYS else None


def _address(b: Block) -> tuple[list[str], str | None, str | None]:
    """The modules, type and name in the address an import or removed block names:
    `to = module.net.resource.aws_vpc.main["a"]` gives (["net"], "aws_vpc", "main")."""
    names = [v for k, v in b.attrs.get("to" if b.type == "import" else "from", []) if k == "ident"]
    modules = []
    while names[:1] == ["module"] and len(names) > 1:
        modules, names = modules + [names[1]], names[2:]
    if names[:1] == ["resource"]:  # Terraform accepts resource.aws_vpc.main for aws_vpc.main
        names = names[1:]
    return modules, (names[0] if names else None), (names[1] if len(names) > 1 else None)


def _typed(b: Block) -> str | None:
    """The resource type a block works on: its label, or the type an import or removed block names."""
    if b.type in TYPED:
        return b.label()
    return _address(b)[1] if b.type in ("import", "removed") else None


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
        if QUERY_FILE.search(f.path):
            out.append(f"{named[id(f)]}: `terraform query` runs a query file's list blocks, and these checks "
                       "don't read query files. Leave it out")
            continue
        if not (_is_tf(f.path) or _is_test(f.path)):
            continue
        try:
            (tests if _is_test(f.path) else tf)[f.path] = (named[id(f)], read(f.content))
        except Unreadable as e:
            out.append(f"{named[id(f)]} isn't HCL these checks can read, so it couldn't be cleared: {e}")

    blocks = [(path, where, b) for path, (where, bs) in tf.items() for b in bs]
    folders = {posixpath.dirname(path) for path in tf}
    nested = [(path, where, x) for path, where, b in blocks for x in b.walk()]  # a check block can hold data
    uses_aws = any(b.type == "provider" and b.label() == "aws" or
                   (_typed(b) or "").startswith("aws_") for _, _, b in nested)
    root = [b for path, _, b in blocks if "/" not in path]
    services: dict[str, set[str]] = {}  # by the provider alias the resources use
    destroyed: set[str] = set()         # by removed blocks, through whichever provider the state names
    handed = _module_aliases(blocks)
    root_resources = {(b.label(0), b.label(1)) for b in root if b.type == "resource"}
    for path, where, b in nested:
        kind = _typed(b)
        if not kind:
            continue
        maker = kind.split("_")[0]
        # terraform_data is built in. awscc, http and external have their own problems below
        if uses_aws and maker not in OFFLINE_PROVIDERS + ("terraform", "awscc", "http", "external"):
            out.append(f"{where}: {kind} comes from the {maker} provider, which these checks don't know. An AWS "
                       f"lesson uses only {', '.join(OFFLINE_PROVIDERS)}")
        if maker != "aws":
            continue
        if b.type == "import":
            modules, _, name = _address(b)
            # Terraform imports into a resource block, which is checked as its own. Only a root import
            # with no block behind it makes one, with `terraform plan -generate-config-out`
            if modules or (kind, name) in root_resources:
                continue
        if b.type == "removed":
            lifecycle = b.children("lifecycle")
            if lifecycle and lifecycle[0].attrs.get("destroy") == [("ident", "false")]:
                continue  # Terraform forgets it and calls nothing
            if svc := None if NO_ENDPOINT.fullmatch(kind) else service_of(kind):
                destroyed.add(svc)
                continue
        ref = _provider_ref(b.attrs.get("provider", []))
        if "provider" in b.attrs and (ref is None or ref[0] != "aws"):
            out.append(f"{where}: {kind} uses a provider other than aws or aws.<alias>, which these "
                       "checks don't follow. Use the aws provider block")
        folder = posixpath.dirname(path) or "."
        inherited = next((a for f, a in handed.items() if folder == f or folder.startswith(f + "/")), "")
        if NO_ENDPOINT.fullmatch(kind):
            continue
        if svc := service_of(kind):
            services.setdefault(ref[1] if ref else inherited, set()).add(svc)
        else:
            out.append(f"{where}: these checks can't tell which endpoint {kind} calls, so they can't make sure "
                       "it goes to this machine. Use resources from services they know, like ec2, s3, iam, sqs "
                       "or sns")
    # the files don't say which provider a removed resource was made with, so every aws block needs it
    for b in (b for _, _, b in blocks if b.type == "provider" and b.label() == "aws"):
        services.setdefault(literal(b.attrs.get("alias")) or "", set()).update(destroyed)
    if uses_aws and not any(b.type == "provider" and b.label() == "aws" and "alias" not in b.attrs for b in root):
        out.append(f"the {which}'s configuration uses AWS with no provider \"aws\" block in the exercise's top "
                   "folder, so Terraform would make a default one that finds the learner's own credentials. "
                   "Add the provider block from the instructions")

    for path, where, b in blocks:
        if b.type == "provider" and b.label() == "aws":
            out += _provider_problems(where, b, services.get(literal(b.attrs.get("alias")) or "", set()))
        if b.type == "module":
            toks = b.attrs.get("providers", [])
            for i in range(len(toks) - 2):
                if toks[i] == ("ident", "aws") and toks[i + 1] == ("punct", "=") and toks[i + 2] != ("ident", "aws"):
                    out.append(f"{where}: module {b.label()!r} is handed a provider other than aws or aws.<alias> "
                               "for aws. Hand it aws or one of its aliases")
        if b.type == "provider" and uses_aws and b.label() not in OFFLINE_PROVIDERS:
            out.append(f'{where} configures a provider "{b.label()}", which these checks don\'t know. An AWS lesson '
                       f"uses only {', '.join(OFFLINE_PROVIDERS)}")
        if b.type == "module" and not _local_source(b.attrs.get("source"), posixpath.dirname(path)):
            out.append(f"{where}: module {b.label()!r} comes from {literal(b.attrs.get('source')) or 'somewhere'} "
                       "instead of a folder in the exercise, so its code isn't checked here. Use a local "
                       "path like ./modules/name")
        elif b.type == "module":
            named = posixpath.normpath(posixpath.join(posixpath.dirname(path) or ".", literal(b.attrs["source"])))
            spelled = sorted(d for d in folders if disk_key(d) == disk_key(named) and d != named)
            if named not in folders and spelled:
                out.append(f"{where}: module {b.label()!r} names {named}, but its files are in {spelled[0]}. A Mac "
                           "reads them as one folder and Linux doesn't. Spell it the same way")
        if b.type == "terraform":
            for required in b.children("required_providers"):
                source = _source_of(required.attrs.get("aws"))
                if "aws" in required.attrs and (source or "").casefold() not in HASHICORP_AWS:
                    out.append(f"{where} maps the aws provider to {source or 'a source worked out at run time'}, "
                               "which isn't hashicorp/aws, so its code isn't what these checks know. Use hashicorp/aws")
                for name, expr in required.attrs.items():
                    source = (_source_of(expr) if any(t == ("ident", "source") for t in expr)
                              else f"hashicorp/{name}").casefold().removeprefix("registry.terraform.io/")
                    if name != "aws" and source == "hashicorp/aws":
                        out.append(f"{where} names hashicorp/aws {name!r}. Call it aws, so the checks for its "
                                   "provider block apply")
                    elif uses_aws and source not in {f"hashicorp/{n}" for n in OFFLINE_PROVIDERS}:
                        out.append(f"{where} fetches the {source} provider, which these checks don't know. An AWS "
                                   f"lesson uses only hashicorp {', '.join(OFFLINE_PROVIDERS)}")
            for backend in b.children("backend"):
                if backend.label() != "local":
                    out.append(f'{where} keeps state in a backend "{backend.label()}", which talks to a real '
                               "service with the learner's credentials. Leave state local and teach the backend "
                               "in the explanation")
            if b.children("cloud"):
                out.append(f"{where} has a cloud block, which sends state to HCP Terraform. Leave state local")

    for _, where, b in nested:
        if b.type == "provider" and b.label() == "awscc" or (_typed(b) or "").startswith("awscc_"):
            out.append(f"{where} uses the awscc provider, which these checks don't cover yet. Use hashicorp/aws")
        if b.type == "data" and b.label() == "terraform_remote_state" and literal(b.attrs.get("backend")) != "local":
            out.append(f"{where} reads remote state from another backend. Only backend = \"local\" stays on "
                       "the machine")
        # tls_certificate reads a certificate from content, or fetches it from a url
        if b.type in TYPED and (b.label() in RUNS_OR_FETCHES or b.label() == "tls_certificate" and "url" in b.attrs):
            out.append(f'{where} has {b.type} "{b.label()}", which reaches the network or runs a program. '
                       "Remove it")
        if b.type == "provider" and any(x.type == "exec" for x in b.walk()):
            out.append(f'{where}: the provider "{b.label()}" block has an exec block, which runs a program on the '
                       "learner's machine to get credentials. Remove it")
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

_FENCE = re.compile(r"```([^\n]*)\n(.*?)```", re.S)
_SPAN = re.compile(r"`([^`\n]+)`")
# the AWS CLI wherever a command can start: a line, a separator, a quote (bash -c "aws ..."),
# a space (xargs aws, env aws), Make's @ and - prefixes, as /path/to/aws, aws2 or awscli
_CLI = re.compile(r"(?:^|(?<=[\s;&|(`'\"=@+-]))(?:(?:/|~/|\.\.?/)[\w.~/-]*/)?(?:aws[0-9]*|awscli)(?=\s+[^\s=])"
                  r"|python[0-9.]*\s+-m\s+awscli(?=\s)")
_END = re.compile(r";|&&|(?<![<>])&|\|\|?|\$\(|[()`]")  # where the command ends
# its endpoint comes first, as one whole shell word, so nothing after it can stand in for it
_LOCAL_FIRST = re.compile(r"\s+--endpoint-url(?:=|\s+)([\"']?)([^\s\"']+)\1(?=\s|$)")
_LIST_FORM = re.compile(r"[\"']aws[0-9]*[\"']\s*,(?!\s*[\"']--endpoint-url[\"']\s*,\s*[\"']https?://(?:localhost|127\.0\.0\.1)[:/\"'])")
# fenced code a learner would run. HCL, JSON or Python fences are read as that language
SHELL_FENCES = {"", "bash", "sh", "shell", "console", "zsh", "terminal", "powershell", "ps1", "pwsh", "cmd",
                "bat", "shell-session"}
SDK_CODE = (".py", ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts")
_SDK = re.compile(r"^\s*(?:import|from)\s+(?:boto3|botocore|aiobotocore)\b|@aws-sdk/|[\"']aws-sdk[\"']", re.M)


def _no_call(args: list[str]) -> bool:
    """aws --version, aws configure (but not configure sso), help at the end, or a service with no
    operation (`aws s3` in a sentence): no API call."""
    if len(args) < 2 or args[:1] == ["configure"] and not (args[1:2] and args[1].startswith("sso")):
        return args[:1] != ["login"]
    return args[-1:] == ["help"] and not any(a.startswith("-") for a in args)


def _commands(code: str) -> list[tuple[str, bool]]:
    """The aws commands in a piece of code, each with whether it names one local endpoint first."""
    found = []
    for line in re.sub(r"\\\n", " ", code).splitlines():
        for m in _CLI.finditer(line):
            rest = line[m.end():]
            command = _END.split(rest, 1)[0]
            args = [a.strip("\"'") for a in command.split() if not re.match(r"\d*[<>]", a)]
            if _no_call(args):
                continue
            first = _LOCAL_FIRST.match(rest)
            local = bool(first and local_url(first.group(2)) and command.count("--endpoint-url") == 1)
            found.append((f"aws {' '.join(command.split())}", local))
        if _LIST_FORM.search(line):  # subprocess.run(["aws", "s3", "ls"])
            found.append((line.strip(), False))
    return found


def aws_commands(text: str) -> list[tuple[str, bool]]:
    fences = [code for tag, code in _FENCE.findall(text) if tag.strip().lower() in SHELL_FENCES]
    spans = _SPAN.findall(_FENCE.sub("", text))
    return [c for piece in fences + spans for c in _commands(piece)]


def command_problems(commands: list[tuple[str, bool]], where: str) -> list[str]:
    out = []
    for c, safe in commands:
        if not safe:
            short = " ".join(c.split())[:80]
            out.append(f"{where} has `{short}`, which uses the learner's own AWS account. Start it "
                       "`aws --endpoint-url http://localhost:4566` so it goes to the emulator")
    return out


# how lesson text moves the learner into another folder: cd and the commands like it in bash,
# PowerShell, cmd and Python, terraform -chdir and env -C, each followed by the folder
_MOVE = re.compile(r"(?:(?<![\w$-])(?:cd|pushd|chdir|sl|set-location|push-location)(?:\s+(?:-{1,2}[a-z]+|--|/d)(?=\s))*"
                   r"|(?<!\w)--?chdir|(?<![\w$-])env(?:\s+-[a-z]+)*?\s+-C)(?:\s*[=(]\s*|\s+)[\"']?([^\s\"'`;&|()]+)",
                   re.I)
# and the ways a sentence says it
_MOVE_WORDS = re.compile(r"\b(?:change|move|switch|go|navigate|step|head)\s+(?:back\s+|over\s+|down\s+)?(?:in)?to\s+"
                         r"(?:the\s+|your\s+)?(?:folder\s+|directory\s+)?[`\"']?([\w./\\~-]+)", re.I)
_RUN_IN = re.compile(r"\b(?:from\s+(?:inside\s+|within\s+|in\s+)?|inside\s+|within\s+|in\s+)(?:the\s+|your\s+)?"
                     r"[`\"']?([\w./\\~-]+)", re.I)
_TERRAFORM_RUN = re.compile(r"\bterraform\s+(?:-\S+\s+)*(?:init|plan|apply|destroy|import|refresh|console|state|test|"
                            r"output|show)\b", re.I)


def _moves(text: str) -> set[str]:
    """Every folder a piece of lesson text moves the learner into, as the text writes it."""
    found = {m.group(1) for pattern in (_MOVE, _MOVE_WORDS) for m in pattern.finditer(text)}
    for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
        if _TERRAFORM_RUN.search(sentence):  # "run terraform plan from inside modules/net"
            found |= {m.group(1) for m in _RUN_IN.finditer(sentence)}
    return found


def _path_problems(ex) -> list[str]:
    """Exercise files that wouldn't be where these checks read them: outside the exercise
    folder, written over each other, in a folder spelled two ways, a .tf file Terraform skips,
    or a file Terraform writes for itself."""
    out = []
    spellings: dict[str, set[str]] = {}
    for f in ex.starter + ex.solution + ex.checks:
        parts = f.path.split("/")
        if f.path.startswith("/") or "\\" in f.path or any(p in ("", ".", "..") or WINDOWS_NAME.search(p) for p in parts):
            out.append(f"{f.path!r} isn't a plain path inside the exercise folder, the same on Mac, Linux and "
                       "Windows, like modules/net/main.tf. Write it that way")
            continue
        if any(len(p.encode()) > 255 for p in parts):
            out.append(f"{f.path[:60]}... has a name longer than 255 bytes, which Linux doesn't allow. Shorten it")
        elif WORKING_FILE.search(disk_key(f.path)):
            out.append(f"{f.path} is a file Terraform writes for itself, and a shipped one can point it at state "
                       "kept somewhere else. Leave it out")
        elif parts[-1].startswith(".") and (_is_tf(f.path) or _is_test(f.path)):
            out.append(f"Terraform skips {f.path} because its name starts with a dot, but these checks read it. "
                       "Rename it")
        for i in range(1, len(parts)):
            spellings.setdefault(disk_key("/".join(parts[:i])), set()).add("/".join(parts[:i]))
    for names in spellings.values():
        if len(names) > 1:
            first, *rest = sorted(names)
            out.append(f"the folder {first} is also written {', '.join(rest)}. A Mac reads them as one folder and "
                       "Linux as more than one, so the lesson would work differently on each. Spell it one way")
    # the same path twice is fine: the course and these checks both keep the last one
    for which, files in (("starter", ex.starter + ex.checks), ("solution", ex.solution + ex.checks)):
        seen: dict[str, str] = {}
        for f in files:
            if (key := disk_key(f.path)) in seen and seen[key] != f.path:
                out.append(f"the {which}'s {seen[key]} and {f.path} are the same file on disk (a Mac ignores case "
                           "and how an accent is typed), so one would overwrite the other. Give them different names")
            seen[key] = f.path
    return out


def _bare_folders(files: list[CourseFile]) -> tuple[dict[str, str], set[str]]:
    """The folders where Terraform would make a default aws provider: they use AWS, in their
    own files or the modules they call, and have no provider "aws" block without an alias.
    Keyed by disk_key, with the name as written. And the keys of the folders the exercise
    runs as modules, from the top folder or the tests."""
    blocks: dict[str, list[Block]] = {}
    names: dict[str, str] = {}
    calls: dict[str, set[str]] = {}
    for f in {f.path: f for f in files}.values():  # a path written twice: the last one is on disk
        if not (_is_tf(f.path) or _is_test(f.path)):
            continue
        try:
            found = read(f.content)
        except Unreadable:
            continue  # config_problems says so
        # Terraform finds a test's run modules from the top folder, like the top folder's own modules
        folder = "" if _is_test(f.path) else posixpath.dirname(f.path)
        key = disk_key(folder)
        modules = [b for b in found if b.type == "module"] + [m for b in found if b.type == "run"
                                                               for m in b.children("module")]
        for m in modules:
            if _local_source(m.attrs.get("source"), folder):
                called = posixpath.normpath(posixpath.join(folder or ".", literal(m.attrs["source"])))
                calls.setdefault(key, set()).add(disk_key("" if called == "." else called))
        if not _is_test(f.path):
            blocks.setdefault(key, []).extend(found)
            names.setdefault(key, folder)

    def uses_aws(key: str, seen: frozenset = frozenset()) -> bool:
        return key not in seen and (
            any((_typed(x) or "").startswith("aws_") for b in blocks.get(key, []) for x in b.walk()) or
            any(uses_aws(c, seen | {key}) for c in calls.get(key, ())))

    run, todo = set(), list(calls.get("", ()))
    while todo:
        if (key := todo.pop()) not in run:
            run.add(key)
            todo += calls.get(key, ())
    bare = {key: names[key] for key, bs in blocks.items() if key and uses_aws(key) and not any(
        b.type == "provider" and b.label() == "aws" and "alias" not in b.attrs for b in bs)}
    return bare, run


def _elsewhere_problems(ex, texts: list[tuple[str, str, bool]]) -> list[str]:
    """Folders where Terraform would find the learner's own credentials, because they use AWS
    with no provider block: one the exercise doesn't use as a module, or one the lesson's text
    moves the learner into."""
    bare: dict[str, str] = {}
    run: set[str] = set()
    for files in (ex.starter + ex.checks, ex.solution + ex.checks):  # the learner goes from one to the other
        b, r = _bare_folders(files)
        bare |= b
        run |= r
    out = [f"{name} has AWS resources and no provider block, and the exercise doesn't use it as a module, so "
           "Terraform run there would make a default provider that finds the learner's own credentials. Add the "
           "provider block from the instructions, or leave the folder out" for key, name in sorted(bare.items())
           if key not in run]
    for where, text, _ in texts:
        for moved in sorted(_moves(text)):
            if re.search(r"[$%]", moved):
                if bare:
                    out.append(f"{where} moves into {moved}, a folder worked out as it runs, and the exercise has "
                               f"AWS resources with no provider block in {', '.join(sorted(bare.values()))}, where "
                               "Terraform would use the learner's own credentials. Run Terraform from the exercise "
                               "folder")
                continue
            folder = posixpath.normpath(moved.replace("\\", "/").rstrip(".,:;") or ".")
            key = disk_key(folder)
            if any(key == k or key.endswith("/" + k) or k.endswith("/" + key) for k in bare):
                out.append(f"{where} moves into {folder}, which has AWS resources and no provider block of its "
                           "own, so Terraform run there would use the learner's own credentials. Run Terraform "
                           "from the exercise folder")
    return out


def _texts(lesson: Lesson) -> list[tuple[str, str, bool]]:
    """Everything the learner reads or runs, as (where, text, is it code). A script is all
    code. In the rest, commands are in code spans and fences."""
    out = [("the title", lesson.title, False), ("the recall", lesson.recall, False),
           ("the explanation", lesson.explanation, False), ("the worked example", lesson.worked_example, False)]
    out += [(f"quiz question {i}", "\n\n".join([q.stem, *q.options, q.explanation]), False)
            for i, q in enumerate(lesson.quiz, 1)]
    if ex := lesson.exercise:
        out += [("the task", ex.task, False)] + [(f"hint {i}", h, False) for i, h in enumerate(ex.hints, 1)]
        out += [(f.path, f.content, not f.path.endswith(".md")) for f in ex.starter + ex.solution + ex.checks
                if not (_is_tf(f.path) or _is_test(f.path))]
    return out


def _aws_commands(text: str, code: bool) -> list[tuple[str, bool]]:
    return _commands(text) if code else aws_commands(text)


def uses_aws(lesson: Lesson) -> bool:
    """Does this lesson touch AWS at all: a provider, a resource, or an aws command."""
    if lesson.exercise:
        for f in lesson.exercise.starter + lesson.exercise.solution:
            if _is_tf(f.path) and re.search(r'provider\s+"aws"|^\s*(?:resource|data|ephemeral|action|list)\s+"aws_|'
                                            r'^\s*(?:to|from)\s*=.*\baws_', f.content, re.M):
                return True
    return any(_aws_commands(text, code) for _, text, code in _texts(lesson))


def problems(lesson: Lesson) -> list[str]:
    """Every way this lesson could reach a real AWS account. Empty means none was found."""
    texts = _texts(lesson)
    out = [p for where, text, code in texts for p in command_problems(_aws_commands(text, code), where)]
    ex = lesson.exercise
    if ex is not None:
        out += _path_problems(ex)
        out += config_problems(ex.starter, ex.checks, "starter")
        out += config_problems(ex.solution, ex.checks, "solution")
        for f in ex.starter + ex.solution + ex.checks:
            name = PurePosixPath(f.path).name
            if (name.endswith(SDK_CODE) or name in ("package.json", "requirements.txt")) and _SDK.search(f.content):
                out.append(f"{f.path} uses an AWS SDK, which finds the learner's own credentials. Exercises "
                           "don't use one yet")
        out += _elsewhere_problems(ex, texts)
    return list(dict.fromkeys(out))
