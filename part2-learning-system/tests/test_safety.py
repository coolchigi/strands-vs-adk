"""Nothing in a lesson reaches a real AWS account: the files are read before anything runs."""

from __future__ import annotations

import os
import re

import pytest

from learning import checks, course_dir, exercises, learn_cli, prompts, safety
from learning.model import CourseFile, Exercise, Lesson, QuizItem

# the block the lesson prompt tells the teacher to write, so the two can't drift apart
PROVIDER = re.search(r'^( +)provider "aws" \{\n.*?^\1\}', prompts.LESSON, re.S | re.M).group(0)
PROVIDER = "\n".join(line[8:] for line in PROVIDER.splitlines()) + "\n"
VPC = 'resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"\n}\n'
# a second, aliased provider for another region, with only EC2 on the emulator
WEST = PROVIDER.replace("provider \"aws\" {\n", "provider \"aws\" {\n  alias = \"west\"\n").replace(
    '"us-east-1"', '"us-west-2"').replace('    s3  = "http://localhost:4566"\n', "")
TEST = '''mock_provider "aws" {}

run "vpc" {
  command = apply
  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "aws_vpc.main should use 10.0.0.0/16"
  }
}
'''


def lesson(main: str = PROVIDER + VPC, extra: dict | None = None, test: str = TEST,
           worked_example: str = "An example.", hints: list[str] | None = None, recall: str = "",
           quiz_explanation: str = "e", checks: dict | None = None) -> Lesson:
    files = [CourseFile(path="main.tf", content=main)] + [CourseFile(path=p, content=c) for p, c in (extra or {}).items()]
    tests = [CourseFile(path="tests/vpc.tftest.hcl", content=test)] + [CourseFile(path=p, content=c)
                                                                        for p, c in (checks or {}).items()]
    return Lesson(id="u1-l1", title="t", recall=recall, explanation="Text [c:aaaaaaaaaaaa].", worked_example=worked_example,
                  exercise=Exercise(task="t", starter=files, solution=files, checks=tests, hints=hints or ["h"]),
                  quiz=[QuizItem(stem="q", options=["a", "b", "c"], answer=0, explanation=quiz_explanation, objective="o")])


def test_the_block_the_prompt_gives_is_safe():
    assert 'access_key                  = "test"' in PROVIDER
    assert safety.problems(lesson()) == []


@pytest.mark.parametrize("main, extra, found", [
    (VPC, {}, "no provider \"aws\" block in the exercise's top folder"),
    ('provider "aws" {\n  region = "us-east-1"\n}\n' + VPC, {}, "no fake keys"),
    (PROVIDER.replace('"test"\n  secret', 'var.key\n  secret', 1) + VPC, {}, "no fake keys"),
    (PROVIDER.replace('access_key                  = "test"', 'access_key = "AKIAIOSFODNN7EXAMPLE"') + VPC, {}, "real access key"),
    (PROVIDER.replace("skip_requesting_account_id  = true", "") + VPC, {}, "skip_requesting_account_id = true"),
    (PROVIDER.replace('region ', 'profile = "default"\n  region ') + VPC, {}, "sets profile"),
    (PROVIDER.replace('ec2 = "http://localhost:4566"', 'ec2 = "https://ec2.us-east-1.amazonaws.com"') + VPC, {}, "sends ec2 to"),
    # resolves to 127.0.0.1 only because a public DNS record says so today
    (PROVIDER.replace('s3  = "http://localhost:4566"', 's3 = "http://s3.localhost.localstack.cloud:4566"') + VPC, {}, "sends s3 to"),
    (PROVIDER + VPC + 'provider "aws" {\n  alias  = "west"\n  region = "us-west-2"\n}\n', {}, "alias 'west' has no fake keys"),
    (PROVIDER + VPC, {"backend.tf": 'terraform {\n  backend "s3" {\n    bucket = "b"\n  }\n}\n'}, 'backend "s3"'),
    (PROVIDER + VPC, {"backend.tf": 'terraform {\n  cloud {\n    organization = "o"\n  }\n}\n'}, "cloud block"),
    (PROVIDER + VPC + 'data "terraform_remote_state" "net" {\n  backend = "s3"\n}\n', {}, "remote state"),
    (PROVIDER + VPC + 'check "up" {\n  data "http" "site" {\n    url = "https://example.com"\n  }\n}\n', {}, 'data "http"'),
    (PROVIDER + 'resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"\n  provisioner "local-exec" {\n'
     '    command = "aws s3 ls"\n  }\n}\n', {}, "provisioner"),
    (PROVIDER + 'module "vpc" {\n  source = "terraform-aws-modules/vpc/aws"\n}\n', {}, "comes from terraform-aws-modules"),
    (PROVIDER + VPC, {"main.tf.json": "{}"}, ".tf.json and override files"),
    (PROVIDER + VPC, {"provider_override.tf": 'provider "aws" {}\n'}, ".tf.json and override files"),
    (PROVIDER + VPC, {"modules/net/main.tf": 'provider "aws" {\n  region = "us-east-1"\n}\n'}, "modules/net/main.tf"),
    (PROVIDER + 'resource "awscc_s3_bucket" "b" {}\n', {}, "awscc"),
    (PROVIDER + 'resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"\n', {}, "isn't HCL these checks can read"),
    # found by the falsifier on 6ac6784
    (re.sub(r"  endpoints \{.*?\n  \}\n", "", PROVIDER, flags=re.S) + VPC, {}, "no endpoint for ec2"),
    (PROVIDER.replace('    ec2 = "http://localhost:4566"\n', "") + 'resource "aws_instance" "web" {}\n', {},
     "no endpoint for ec2"),
    (re.sub(r"  endpoints \{.*?\n  \}\n", '  endpoints = { ec2 = "https://ec2.amazonaws.com" }\n', PROVIDER, flags=re.S) + VPC,
     {}, "as a map"),
    (PROVIDER + VPC, {"versions.tf": 'terraform {\n  required_providers {\n    aws = {\n      source = "example-corp/aws"\n'
                                     '    }\n  }\n}\n'}, "maps the aws provider to example-corp/aws"),
    (PROVIDER + 'module "x" {\n  source = "../../../other/mod"\n}\n', {}, "comes from ../../../other/mod"),
    (VPC, {"a b/providers.tf": PROVIDER}, "no provider \"aws\" block in the exercise's top folder"),
    # and on fc41b89
    (PROVIDER + 'resource "aws_eks_cluster" "k" {}\n', {}, "no endpoint for eks"),
    (PROVIDER + WEST.replace('    ec2 = "http://localhost:4566"\n', '    s3 = "http://localhost:4566"\n') +
     'resource "aws_instance" "w" {\n  provider = aws.west\n}\n', {}, "alias 'west' has no endpoint for ec2"),
    # and on 26f0137
    (PROVIDER + 'provider "awsx" {}\nresource "aws_vpc" "x" {\n  provider = awsx\n}\n',
     {"versions.tf": 'terraform {\n  required_providers {\n    awsx = { source = "example-corp/aws" }\n  }\n}\n'},
     "uses a provider other than aws"),
    (PROVIDER + VPC, {"versions.tf": 'terraform {\n  required_providers {\n    awsx = { source = "hashicorp/aws" }\n'
                                     '  }\n}\n'}, "names hashicorp/aws 'awsx'"),
    (PROVIDER + WEST.replace('    ec2 = "http://localhost:4566"\n', '    s3 = "http://localhost:4566"\n') +
     'module "net" {\n  source = "./modules/net"\n  providers = {\n    aws = aws.west\n  }\n}\n',
     {"modules/net/main.tf": 'resource "aws_instance" "w" {}\n'}, "alias 'west' has no endpoint for ec2"),
    (PROVIDER + 'data "aws_ip_ranges" "r" {\n  services = ["s3"]\n}\n', {}, 'data "aws_ip_ranges"'),
    # and on 8dabd23
    (PROVIDER + 'module "m" {\n  source = "./modules/m"\n  providers = {\n    aws = awsx\n  }\n}\n',
     {"modules/m/main.tf": VPC}, "handed a provider other than aws"),
    (PROVIDER + VPC + 'provider "thing" {}\n',
     {"versions.tf": 'terraform {\n  required_providers {\n    thing = { source = "example-corp/thing" }\n  }\n}\n'},
     "fetches the example-corp/thing provider"),
    (PROVIDER + VPC + 'provider "kubernetes" {}\n', {}, 'configures a provider "kubernetes"'),
    # and after the proof builds on 7fddf12: a type the table didn't know was skipped
    (PROVIDER + 'resource "aws_elastic_beanstalk_application" "a" {\n  name = "demo"\n}\n', {},
     "no endpoint for elasticbeanstalk"),
    (PROVIDER + 'resource "aws_newservice_widget" "w" {}\n', {}, "can't tell which endpoint aws_newservice_widget calls"),
    (PROVIDER + 'check "c" {\n  data "aws_madeup_thing" "t" {}\n}\n', {}, "can't tell which endpoint aws_madeup_thing calls"),
    # and by the falsifier on that fix
    (PROVIDER + 'resource "aws_s3_account_public_access_block" "a" {}\n', {}, "no endpoint for s3control"),
    (PROVIDER + 'resource "aws_s3_access_point" "a" {}\n', {}, "no endpoint for s3control"),
    (PROVIDER + 'resource "aws_chime_voice_connector" "v" {}\n', {}, "no endpoint for chimesdkvoice"),
    (PROVIDER + 'import {\n  to = aws_iam_role.app\n  id = "app-role"\n}\n', {}, "no endpoint for iam"),
    (PROVIDER + 'removed {\n  from = aws_sqs_queue.q\n}\n', {}, "no endpoint for sqs"),
    ('import {\n  to = aws_iam_role.app\n  id = "app-role"\n}\n', {}, "no provider \"aws\" block in the exercise's top folder"),
    (PROVIDER + 'import {\n  to = awscc_s3_bucket.b\n  id = "b"\n}\n', {}, "awscc"),
    (PROVIDER + VPC, {"roles.tfquery.hcl": 'list "aws_iam_role" "all" {\n  provider = aws\n}\n'}, "query file"),
    # and on the second fix
    (PROVIDER + 'import {\n  to = resource.aws_iam_role.app\n  id = "app-role"\n}\n', {}, "no endpoint for iam"),
    ('import {\n  to = resource.aws_iam_role.app\n  id = "app-role"\n}\n', {}, "no provider \"aws\" block in the exercise's top folder"),
    (PROVIDER + 'import {\n  to = resource.awscc_s3_bucket.b\n  id = "b"\n}\n', {}, "awscc"),
    (PROVIDER.replace('    s3  = "http://localhost:4566"\n', '    s3  = "http://localhost:4566"\n    sqs = "http://localhost:4566"\n')
     + WEST + 'removed {\n  from = module.acct.aws_sqs_queue.q\n}\n', {}, "alias 'west' has no endpoint for sqs"),
    (PROVIDER + VPC + 'resource "google_storage_bucket" "b" {}\n', {}, "comes from the google provider"),
    (PROVIDER + VPC + 'import {\n  to = google_storage_bucket.b\n  id = "b"\n}\n', {}, "comes from the google provider"),
    # and on 64d97bd: local 2.9.1 runs programs, and a module's folder can be spelled two ways
    (PROVIDER + VPC + 'data "local_command" "who" {\n  command   = "aws"\n  arguments = ["sts", "get-caller-identity"]\n}\n',
     {}, 'data "local_command"'),
    (PROVIDER + VPC + 'ephemeral "local_command" "ls" {\n  command = "aws"\n}\n', {}, 'ephemeral "local_command"'),
    (PROVIDER + VPC + 'ephemeral "http" "h" {\n  url = "https://example.com"\n}\n', {}, 'ephemeral "http"'),
    (PROVIDER + VPC + 'data "tls_certificate" "c" {\n  url = "https://example.com"\n}\n', {}, 'data "tls_certificate"'),
    ('provider "kubernetes" {\n  exec {\n    api_version = "client.authentication.k8s.io/v1beta1"\n'
     '    command     = "aws"\n    args        = ["eks", "get-token"]\n  }\n}\n', {}, "has an exec block"),
    (PROVIDER + 'module "acct" {\n  source = "./modules/acct"\n}\n', {"Modules/acct/main.tf": VPC},
     "names modules/acct, but its files are in Modules/acct"),
])
def test_each_way_into_a_real_account_is_found(main, extra, found):
    problems = safety.problems(lesson(main, extra))
    assert any(found in p for p in problems), problems


WEST_IAM = WEST.replace('    ec2 = "http://localhost:4566"\n', '    ec2 = "http://localhost:4566"\n    iam = "http://localhost:4566"\n')


@pytest.mark.parametrize("main, extra", [
    # an import goes through the provider of the resource block it fills in
    (PROVIDER + WEST_IAM + 'resource "aws_iam_role" "app" {\n  provider = aws.west\n}\n'
     'import {\n  to = aws_iam_role.app\n  id = "app-role"\n}\n', {}),
    (PROVIDER + WEST_IAM + 'module "acct" {\n  source = "./modules/acct"\n  providers = {\n    aws = aws.west\n  }\n}\n'
     'import {\n  to = module.acct.aws_iam_role.app\n  id = "app-role"\n}\n',
     {"modules/acct/main.tf": 'resource "aws_iam_role" "app" {}\n'}),
    # a removed block that only forgets calls nothing
    (PROVIDER + VPC + 'removed {\n  from = aws_sqs_queue.q\n  lifecycle {\n    destroy = false\n  }\n}\n', {}),
    (PROVIDER + VPC + 'resource "terraform_data" "t" {}\nresource "random_pet" "p" {}\n', {}),
])
def test_what_terraform_sends_through_the_right_provider_is_cleared(main, extra):
    assert safety.problems(lesson(main, extra)) == []


NET = PROVIDER + 'module "net" {\n  source = "./modules/net"\n}\n'
CD_NET = "Run it there:\n\n```bash\ncd modules/net\nterraform apply\n```\n"


@pytest.mark.parametrize("built, found", [
    # Terraform skips a file whose name starts with a dot, so the provider block in it doesn't count
    (lesson(VPC, {".provider.tf": PROVIDER}), "Terraform skips .provider.tf"),
    # two paths that are one file on disk: the second overwrites the provider block
    (lesson(PROVIDER + VPC, {"./main.tf": VPC}), "isn't a plain path"),
    (lesson(PROVIDER + VPC, {"Main.tf": VPC}), "are the same file on disk"),
    (lesson(PROVIDER + VPC, {"../../outside.tf": VPC}), "isn't a plain path"),
    (lesson(PROVIDER + VPC, {"/tmp/outside.tf": VPC}), "isn't a plain path"),
    # Terraform run in a module folder has no provider block there
    (lesson(NET, {"modules/net/main.tf": VPC}, worked_example=CD_NET), "moves into modules/net"),
    (lesson(NET, {"modules/net/main.tf": VPC}, hints=["`terraform -chdir=modules/net plan`"]), "moves into modules/net"),
    (lesson(NET, {"modules/net/main.tf": VPC, "run.sh": "cd ./modules/net && terraform plan\n"}), "moves into modules/net"),
    # found by the falsifier on 64d97bd. A Mac reads é typed 2 ways as 1 name, and a folder's case either way
    (lesson(VPC, {"configuración.tf": PROVIDER, "configuración.tf": "# the provider is in the notes\n"}),
     "are the same file on disk"),
    (lesson(NET, {"modules/net/main.tf": VPC, "Modules/net/outputs.tf": ""}), "the folder Modules/net is also written modules/net"),
    # Terraform reads this as the backend it was last set up with
    (lesson(PROVIDER + VPC, {".Terraform/terraform.TFSTATE": '{"version": 3, "backend": {"type": "s3"}}'}),
     "a file Terraform writes for itself"),
    (lesson(PROVIDER + VPC, {"a" * 300 + ".tf": VPC}), "longer than 255 bytes"),
    # Windows writes C:main.tf over main.tf, and main.tf. too
    (lesson(PROVIDER + VPC, {"C:main.tf": VPC}), "isn't a plain path"),
    (lesson(PROVIDER + VPC, {"main.tf.": VPC}), "isn't a plain path"),
    (lesson(PROVIDER + VPC, {"CON.tf": VPC}), "isn't a plain path"),
    # a folder with AWS and no provider that the exercise doesn't call, where a learner might run Terraform
    (lesson(PROVIDER + VPC, {"examples/main.tf": VPC}), "examples has AWS resources and no provider block"),
    (lesson(PROVIDER + VPC, checks={"tests/setup/main.tf": 'resource "aws_s3_bucket" "b" {}\n'}),
     "tests/setup has AWS resources and no provider block"),
    # the ways of saying it the folder rule missed
    (lesson(NET, {"modules/net/main.tf": VPC}, worked_example="Change into modules/net and run `terraform plan`."),
     "moves into modules/net"),
    (lesson(NET, {"modules/net/main.tf": VPC}, worked_example="From inside modules/net, run terraform plan."),
     "moves into modules/net"),
    (lesson(NET, {"modules/net/main.tf": VPC}, worked_example="~~~bash\ncd modules/net\nterraform plan\n~~~\n"),
     "moves into modules/net"),
    (lesson(NET, {"modules/net/main.tf": VPC}, worked_example="```bash\ncd modules\ncd net\nterraform plan\n```\n"),
     "moves into net"),
    (lesson(NET, {"modules/net/main.tf": VPC}, worked_example="```powershell\nSet-Location -Path modules\\net\n```\n"),
     "moves into modules/net"),
    (lesson(NET, {"modules/net/main.tf": VPC}, worked_example="```bash\nbash -c \"cd modules/net && terraform plan\"\n```\n"),
     "moves into modules/net"),
    (lesson(NET, {"modules/net/main.tf": VPC}, worked_example="```bash\ncd Modules/Net\n```\n"), "moves into Modules/Net"),
    (lesson(NET, {"modules/net/main.tf": VPC}, worked_example="```bash\nD=modules/net\ncd \"$D\"\n```\n"),
     "a folder worked out as it runs"),
    (lesson(NET, {"modules/net/main.tf": VPC}, recall="Last time you ran `cd modules/net && terraform plan`."),
     "the recall moves into modules/net"),
    (lesson(NET, {"modules/net/main.tf": VPC}, quiz_explanation="Run `cd modules/net` first."),
     "quiz question 1 moves into modules/net"),
    # and the folders it didn't count as having no provider block
    (lesson(NET, {"modules/net/main.tf": '# the provider "aws" block is in the top folder\n' + VPC}, worked_example=CD_NET),
     "moves into modules/net"),
    (lesson(NET, {"modules/net/main.tf": WEST + VPC}, worked_example=CD_NET), "moves into modules/net"),
    (lesson(NET, {"modules/net/main.tf": 'module "inner" {\n  source = "./inner"\n}\n', "modules/net/inner/main.tf": VPC},
            worked_example=CD_NET), "moves into modules/net"),
])
def test_files_and_folders_terraform_would_see_differently_are_found(built, found):
    problems = safety.problems(built)
    assert any(found in p for p in problems), problems


def test_a_folder_with_a_provider_block_only_in_the_solution_has_none_in_the_starter():
    built = lesson(NET, {"modules/net/main.tf": VPC}, worked_example=CD_NET)
    solution = [f.model_copy(update={"content": PROVIDER + VPC}) if f.path == "modules/net/main.tf" else f
                for f in built.exercise.solution]
    problems = safety.problems(built.model_copy(update={"exercise": built.exercise.model_copy(update={"solution": solution})}))
    assert any("moves into modules/net" in p for p in problems), problems


def test_moving_into_the_exercise_folder_or_a_folder_without_aws_is_fine():
    text = "```bash\ncd exercise\nterraform apply\ncd modules/names\ncd modules/region\n```\n"
    assert safety.problems(lesson(NET, {"modules/net/main.tf": VPC, "modules/names/main.tf": 'resource "random_pet" "p" {}\n',
                                        "modules/region/main.tf": 'variable "aws_region" {}\nresource "random_pet" "p" {}\n'},
                                  worked_example=text)) == []


@pytest.mark.parametrize("built", [
    # a test's setup module runs with the mock provider
    lesson(PROVIDER + VPC, checks={"tests/setup/main.tf": 'resource "aws_s3_bucket" "b" {}\n'},
           test=TEST.replace('run "vpc" {', 'run "setup" {\n  module {\n    source = "./tests/setup"\n  }\n}\n\nrun "vpc" {')),
    lesson(PROVIDER + VPC + 'data "tls_certificate" "c" {\n  content = "-----BEGIN CERTIFICATE-----"\n}\n'),
    lesson(PROVIDER + VPC, {"console.tf": "", "auxiliary/notes.md": "Notes."}),
])
def test_what_looks_close_to_those_but_isnt_is_cleared(built):
    assert safety.problems(built) == []


def test_a_module_the_solution_calls_is_a_module_in_the_starter_too():
    built = lesson(NET, {"modules/net/main.tf": VPC})
    starter = [f.model_copy(update={"content": PROVIDER}) if f.path == "main.tf" else f for f in built.exercise.starter]
    assert safety.problems(built.model_copy(update={"exercise": built.exercise.model_copy(update={"starter": starter})})) == []


def test_the_lesson_writer_drops_state_files_however_they_are_spelled():
    files = [CourseFile(path=p, content="{}") for p in ("main.tf", ".Terraform/terraform.TFSTATE", "TERRAFORM.tfState")]
    assert [f.path for f in exercises.authored(files)] == ["main.tf"]


def test_each_provider_needs_only_the_endpoints_its_own_resources_use():
    main = (PROVIDER.replace('    ec2 = "http://localhost:4566"\n', "") + WEST + 'resource "aws_s3_bucket" "b" {}\n'
            'resource "aws_instance" "w" {\n  provider = aws.west\n}\n')
    required = 'terraform {\n  required_providers {\n    aws = { source = "HashiCorp/aws" }\n  }\n}\n'
    assert safety.problems(lesson(main, {"versions.tf": required})) == []


def test_a_module_given_an_alias_is_held_to_that_providers_endpoints():
    main = (PROVIDER.replace('    ec2 = "http://localhost:4566"\n', "") + WEST +
            'module "net" {\n  source = "./modules/net"\n  providers = {\n    aws = aws.west\n  }\n}\n')
    assert safety.problems(lesson(main, {"modules/net/main.tf": 'resource "aws_instance" "w" {}\n'})) == []


@pytest.mark.parametrize("resource_type, service", [
    ("aws_kinesis_firehose_delivery_stream", "firehose"), ("aws_kinesis_video_stream", "kinesisvideo"),
    ("aws_kinesis_stream", "kinesis"), ("aws_cloudwatch_query_definition", "logs"),
    ("aws_route53_resolver_endpoint", "route53resolver"), ("aws_route53_record", "route53"),
    ("aws_launch_configuration", "autoscaling"), ("aws_cognito_user_pool", "cognitoidp"),
    ("aws_regions", "ec2"), ("aws_canonical_user_id", "s3"),
    ("aws_elastic_beanstalk_application", "elasticbeanstalk"), ("aws_dx_connection", "directconnect"),
    ("aws_directory_service_directory", "ds"), ("aws_mskconnect_connector", "kafkaconnect"),
    ("aws_service_discovery_service", "servicediscovery"), ("aws_media_packagev2_channel_group", "mediapackagev2"),
    ("aws_verifiedaccess_instance", "ec2"), ("aws_internet_gateway_attachment", "ec2"), ("aws_lbs", "elbv2"),
    ("aws_cognito_managed_user_pool_client", "cognitoidp"),
    ("aws_cognito_identity_openid_token_for_developer_identity", "cognitoidentity"),
    ("aws_pricingplanmanager_subscription", "pricingplanmanager"), ("aws_newservice_widget", None),
    ("aws_s3_access_point", "s3control"), ("aws_s3_account_public_access_block", "s3control"), ("aws_s3_bucket", "s3"),
    ("aws_chime_voice_connector_logging", "chimesdkvoice"),
])
def test_each_resource_type_is_held_to_the_endpoint_it_calls(resource_type, service):
    assert safety.service_of(resource_type) == service


def test_an_aws_lesson_may_use_the_providers_that_stay_on_the_machine():
    required = ('terraform {\n  required_providers {\n    aws    = { source = "hashicorp/aws" }\n'
                '    random = { source = "hashicorp/random" }\n    local  = { source = "hashicorp/local" }\n  }\n}\n')
    main = PROVIDER + VPC + 'resource "random_pet" "p" {}\nresource "local_file" "f" {\n  filename = "x"\n  content = "y"\n}\n'
    assert safety.problems(lesson(main, {"versions.tf": required})) == []


def test_what_calls_no_api_needs_no_endpoint():
    main = (PROVIDER.replace('    ec2 = "http://localhost:4566"\n', "") + 'data "aws_iam_policy_document" "p" {}\n'
            'data "aws_region" "here" {}\nresource "aws_s3_bucket" "b" {}\n'
            'data "aws_elb_service_account" "e" {}\ndata "aws_lb_hosted_zone_id" "z" {}\n'
            'data "aws_cloudfront_log_delivery_canonical_user_id" "c" {}\ndata "aws_service_principal" "p" {\n'
            '  service_name = "s3"\n}\ndata "aws_elastic_beanstalk_hosted_zone" "h" {}\n'
            'data "aws_eks_cluster_auth" "k" {\n  name = "x"\n}\n'
            'module "net" {\n  source = "./modules/net"\n}\n')
    required = 'terraform {\n  required_providers {\n    aws = { source = "hashicorp/aws", version = "~> 6.0" }\n  }\n}\n'
    assert safety.problems(lesson(main, {"versions.tf": required,
                                         "modules/net/main.tf": 'resource "aws_s3_bucket" "logs" {}\n'})) == []


@pytest.mark.parametrize("test, found", [
    (TEST.replace('mock_provider "aws" {}', ""), 'no mock_provider "aws"'),
    (TEST.replace('mock_provider "aws" {}', 'mock_provider "aws" {\n  alias = "fake"\n}'), 'no mock_provider "aws"'),
    (TEST + 'provider "aws" {\n  region = "us-east-1"\n}\n', "configures a real provider"),
    (TEST.replace("command = apply", "command = apply\n  providers = {\n    aws = aws\n  }"), "sets providers"),
])
def test_tests_only_ever_use_the_mock(test, found):
    problems = safety.problems(lesson(test=test))
    assert any(found in p for p in problems), problems


def test_a_tests_problem_is_said_once_not_for_starter_and_solution_each():
    problems = safety.problems(lesson(test=TEST + 'provider "aws" {}\n'))
    assert len([p for p in problems if "configures a real provider" in p]) == 1


@pytest.mark.parametrize("text, safe", [
    ("Check it:\n\n```bash\naws s3 ls\n```\n", False),
    ("Run `aws ec2 describe-vpcs` to see them.", False),
    ("```bash\n$ aws ec2 describe-instances \\\n    --instance-ids i-123\n```\n", False),
    ("```bash\naws --endpoint-url http://localhost:4566 s3 ls\n```\n", True),
    ("```bash\naws --endpoint-url=http://localhost:4566 ec2 describe-vpcs\n```\n", True),
    # the flag only: AWS_ENDPOINT_URL_S3 or AWS_IGNORE_CONFIGURED_ENDPOINT_URLS can override the variable
    ("```bash\nAWS_ENDPOINT_URL=http://localhost:4566 aws s3 ls\n```\n", False),
    ("```bash\naws --endpoint-url https://s3.amazonaws.com s3 ls\n```\n", False),
    # HCL and prose that mention aws without running it
    ("```hcl\nterraform {\n  required_providers {\n    aws = {\n      source = \"hashicorp/aws\"\n    }\n  }\n}\n"
     "# configure the aws provider\nresource \"aws_vpc\" \"main\" {}\n```\n", True),
    ("The aws provider reads `aws_vpc` blocks.", True),
    # found by the falsifier on 6ac6784: a second command, and the CLI under other names
    ("`aws --endpoint-url http://localhost:4566 s3 ls; aws s3 rm s3://real --recursive`", False),
    ("```bash\naws --endpoint-url http://localhost:4566 s3 ls && aws iam create-user --user-name x\n```\n", False),
    ("`/usr/local/bin/aws s3 ls`", False),
    ("`aws2 s3 ls`", False),
    ("```bash\npython3 -m awscli s3 ls\n```\n", False),
    ("`aws configure`, then `aws --version` to check it's installed.", True),
    # and on fc41b89
    ("`aws --endpoint-url http://localhost:4566 s3 ls & aws s3 rm s3://real --recursive`", False),
    ("`aws ec2 help`", True),
    ("```bash\naws --endpoint-url http://localhost:4566 s3 cp ./f s3://bucket-$(date +%s)/\n```\n", True),
    # and on 26f0137: the endpoint has to come first, so nothing later can stand in for it
    ("```bash\naws s3 cp ./f s3://bucket-$(date +%s)/ --endpoint-url http://localhost:4566\n```\n", False),
    ("```bash\naws s3 rm s3://real --recursive  # add --endpoint-url http://localhost:4566 for LocalStack\n```\n", False),
    ("```bash\naws --endpoint-url http://localhost:4566 s3 cp f s3://b/$(aws sts get-caller-identity) "
     "--endpoint-url http://localhost:4566\n```\n", False),
    ("`aws --endpoint-url http://localhost:4566 iam create-user --user-name help`", True),
    ("`aws iam create-user --user-name help`", False),
    ("`aws iam create-user help`", True),
    ("`aws configure sso`", False),
    # and on 8dabd23: one endpoint, as a whole word, and the CLI however it's started
    ("`aws --endpoint-url http://localhost:4566 --endpoint-url https://s3.amazonaws.com s3 ls`", False),
    ("```bash\naws --endpoint-url \"http://localhost:4566\"@s3.amazonaws.com s3 ls\n```\n", False),
    ("```bash\naws --endpoint-url \"http://localhost:4566\" s3 ls\n```\n", True),
    ("```bash\nls | xargs aws s3 rm --recursive\n```\n", False),
    ("```bash\neval \"aws s3 ls\"\n```\n", False),
    ("```bash\nbash -c \"aws s3 ls\"\n```\n", False),
    ("```bash\nenv aws s3 ls\n```\n", False),
    ("```bash\ntimeout 30 aws s3 ls\n```\n", False),
    ("```powershell\nPS C:\\> aws s3 ls\n```\n", False),
    ("`aws login`", False),
    ("The `aws s3` commands copy files.", True),
    ("```bash\naws --version 2>&1\n```\n", True),
    ("```text\nInitializing provider plugins...\n- Finding hashicorp/aws versions matching \"~> 6.0\"...\n```\n", True),
    ("```bash\naws --endpoint-url http://localhost:4566 s3 cp ./f s3://b/$(aws s3 ls | head -1)\n```\n", False),
])
def test_an_aws_command_has_to_go_to_the_emulator(text, safe):
    problems = safety.problems(lesson(worked_example=text))
    assert (problems == []) is safe, problems


def test_a_hint_and_a_script_are_read_for_aws_commands_too():
    assert safety.problems(lesson(hints=["Try `aws s3 ls`."]))
    assert safety.problems(lesson(extra={"check.sh": "#!/bin/sh\nset -e\naws sts get-caller-identity\n"}))
    # and the recall and the quiz, found by the falsifier on 64d97bd
    assert any("the recall has `aws s3 ls`" in p for p in safety.problems(lesson(recall="You ran `aws s3 ls`.")))
    assert any("quiz question 1 has `aws s3 ls`" in p for p in safety.problems(lesson(quiz_explanation="`aws s3 ls` lists them.")))


def test_a_course_with_aws_only_in_a_hint_still_says_what_is_simulated():
    l = lesson(main="# nothing yet\n", hints=["Run `aws --endpoint-url http://localhost:4566 s3 ls`."])
    assert safety.uses_aws(l)


@pytest.mark.parametrize("path, content, safe", [
    ("Makefile", "sync:\n\t@aws s3 sync . s3://real\n", False),
    ("package.json", '{"scripts": {"deploy": "aws s3 sync . s3://real"}}', False),
    ("run.py", 'import subprocess\nsubprocess.run(["aws", "s3", "ls"])\n', False),
    ("run.py", 'import subprocess\nsubprocess.run(["aws", "--endpoint-url", "http://localhost:4566", "s3", "ls"])\n', True),
    ("Makefile", "sync:\n\taws --endpoint-url http://localhost:4566 s3 sync . s3://b\n", True),
])
def test_commands_in_exercise_files_are_read_too(path, content, safe):
    problems = safety.problems(lesson(extra={path: content}))
    assert (problems == []) is safe, problems


def test_exercise_code_doesnt_use_an_aws_sdk():
    l = lesson(extra={"app.py": "import boto3\n\nboto3.client('s3').list_buckets()\n"})
    assert any("AWS SDK" in p for p in safety.problems(l))


@pytest.mark.parametrize("text, said", [
    ('mock_provider "aws" {}\n\nrun "valid"\n  command = plan\n}\n', "line 3: `run` needs a { on the same line"),
    ('locals {\n  a = 1\n', "the block opened on line 1 never closes"),
    ('locals {\n  a = "no end\n}\n', "line 2: a string runs past the end of its line"),
])
def test_what_the_reader_cant_follow_says_which_line(text, said):
    # from the 24 October ADK build: the teacher wrote a run block with no {
    with pytest.raises(safety.Unreadable, match=re.escape(said)):
        safety.read(text)


def test_the_reader_follows_what_real_configurations_have():
    text = '''
/* a block comment with a } in it */
locals {
  tags = {
    Name = "web-${var.env}"   # an object over several lines
    Path = "a}b"
  }
  doc  = <<-EOT
    a heredoc with "quotes" and a } brace
    EOT
  pick = { for k, v in var.m : k => "${v["name"]}" if v != null }
}
check "health" {
  assert {
    condition     = length(var.m) >= 0
    error_message = "never"
  }
}
mock_provider "aws" {}
'''
    blocks = safety.read(text)
    assert [b.type for b in blocks] == ["locals", "check", "mock_provider"]
    assert set(blocks[0].attrs) == {"tags", "doc", "pick"}
    assert blocks[1].children("assert")[0].attrs["error_message"] == [("string", '"never"')]


def test_a_lesson_that_could_reach_aws_is_never_run(monkeypatch):
    calls = []
    monkeypatch.setattr(exercises, "verify", lambda ex: calls.append(ex) or [])
    monkeypatch.setattr(exercises, "stale_pins", lambda files: [])
    found = checks.lesson(lesson(main=VPC), [], set(), needs_exercise=True)
    assert calls == [] and any(p.check == "could_reach_aws" for p in found)
    checks.lesson(lesson(), [], set(), needs_exercise=True)
    assert len(calls) == 1  # the safe one runs


def test_a_lesson_that_could_still_reach_aws_is_held_back(tmp_path):
    from test_learner import course
    c = course()
    unsafe = c.lessons[0].model_copy(update={"worked_example": "```bash\naws s3 ls\n```\n"})
    root = course_dir.write(c.model_copy(update={"lessons": [unsafe]}), tmp_path / "course")
    readme = (root / "README.md").read_text()
    assert not list((root / "units").glob("*/u1-l1-*"))
    assert "(held back, see Known problems)" in readme
    assert "u1-l1 was held back by the check that keeps lessons away from your AWS account: the worked example has `aws s3 ls`" in readme
    assert "u1-l1" not in (root / ".learn" / "lessons.json").read_text()


def test_a_course_that_uses_aws_says_what_is_simulated_on_its_first_page(tmp_path):
    from test_learner import course
    readme = (course_dir.write(course(), tmp_path / "course") / "README.md").read_text()
    assert readme.index("**About AWS.**") < readme.index("## Who this is for")


def test_learn_check_runs_the_tests_without_the_learners_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIAIOSFODNN7EXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY")
    monkeypatch.setenv("AWS_PROFILE", "work")
    (tmp_path / "test_env.py").write_text(f'''import os, unittest
class T(unittest.TestCase):
    def test_env(self):
        self.assertFalse({{k for k in os.environ if k.startswith("AWS_") and k not in
                          ("AWS_EC2_METADATA_DISABLED", "AWS_SHARED_CREDENTIALS_FILE", "AWS_CONFIG_FILE")}})
        self.assertEqual(os.environ["AWS_SHARED_CREDENTIALS_FILE"], os.devnull)
        self.assertNotEqual(os.path.expanduser("~"), {os.path.expanduser("~")!r})
        print(os.environ.get("NOT_THERE", "{os.environ["AWS_SECRET_ACCESS_KEY"]}"))
''')
    outcome, output = learn_cli.run_exercise(tmp_path, "python")
    assert outcome == "passed", output
    assert "wJalrXUtnFEMI" not in output


@pytest.mark.parametrize("first, builds_on_it", [(lesson(), True), (lesson(main=VPC), False)])
def test_the_next_lesson_builds_only_on_files_that_are_safe_to_ship(tmp_path, monkeypatch, first, builds_on_it):
    from learning import flow as flows, stages
    from learning.model import Curriculum, KnowledgeBase, LearnerProfile, LessonSpec, Spec, Unit
    from learning.web import FakeWeb
    profile = LearnerProfile(subject="Terraform", goal="g", subject_is_clear=True)
    f = flows.start(None, FakeWeb(), profile, tmp_path)
    f.board.knowledge = KnowledgeBase(profile=profile, spec=Spec(kind="derived_from_docs", title="Terraform"))
    f.board.curriculum = Curriculum(title="t", units=[Unit(id="u1", title="One", lessons=[
        LessonSpec(id="u1-l1", title="First"), LessonSpec(id="u1-l2", title="Second")])])
    f.checkpoint.save("lessons/u1-l1", first)
    given = []
    monkeypatch.setattr(stages, "teach_lesson", lambda brain, kb, spec, previous, *a, **k:
                        given.append(previous) or stages.LessonResult(lesson=first.model_copy(update={"id": spec.id})))
    f.teaching()
    assert given == [first.exercise.solution if builds_on_it else []]
