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
           worked_example: str = "An example.", hints: list[str] | None = None) -> Lesson:
    files = [CourseFile(path="main.tf", content=main)] + [CourseFile(path=p, content=c) for p, c in (extra or {}).items()]
    return Lesson(id="u1-l1", title="t", recall="", explanation="Text [c:aaaaaaaaaaaa].", worked_example=worked_example,
                  exercise=Exercise(task="t", starter=files, solution=files,
                                    checks=[CourseFile(path="tests/vpc.tftest.hcl", content=test)], hints=hints or ["h"]),
                  quiz=[QuizItem(stem="q", options=["a", "b", "c"], answer=0, explanation="e", objective="o")])


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
])
def test_each_way_into_a_real_account_is_found(main, extra, found):
    problems = safety.problems(lesson(main, extra))
    assert any(found in p for p in problems), problems


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
    ("aws_regions", "ec2"), ("aws_elb_service_account", None), ("aws_lb_hosted_zone_id", None),
    ("aws_cloudfront_log_delivery_canonical_user_id", None), ("aws_canonical_user_id", "s3"),
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
