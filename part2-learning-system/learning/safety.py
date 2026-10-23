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


def _local_source(expr: list[Token] | None) -> bool:
    source = literal(expr)
    return source is not None and source.startswith(("./", "../"))


def _provider_problems(where: str, p: Block) -> list[str]:
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
    for endpoints in p.children("endpoints"):
        for service, expr in endpoints.attrs.items():
            url = literal(expr)
            if url is None or not local_url(url):
                out.append(f"{name} sends {service} to {url or 'an address worked out at run time'}. Every "
                           "endpoint has to be on this machine, like http://localhost:4566")
    return out


def config_problems(files: list[CourseFile], checks: list[CourseFile], which: str) -> list[str]:
    """What in one set of files (the starter or the solution) and the checks could reach a
    real AWS account, when the learner runs Terraform or when `learn check` does."""
    out: list[str] = []
    tf: dict[str, list[Block]] = {}
    tests: dict[str, list[Block]] = {}
    named = {id(f): f"{f.path} ({which})" for f in files} | {id(f): f.path for f in checks}
    for f in files + checks:
        if FORBIDDEN_FILE.search(f.path):
            out.append(f"{named[id(f)]}: .tf.json and override files can change the provider without it "
                       "showing in the .tf files. Write plain .tf files")
            continue
        if not (_is_tf(f.path) or _is_test(f.path)):
            continue
        try:
            (tests if _is_test(f.path) else tf)[named[id(f)]] = read(f.content)
        except Unreadable as e:
            out.append(f"{named[id(f)]} couldn't be read to check it stays away from real AWS: {e}")

    blocks = [(where, b) for where, bs in tf.items() for b in bs]
    nested = [(where, x) for where, b in blocks for x in b.walk()]  # a check block can hold a data source
    uses_aws = any(b.type == "provider" and b.label() == "aws" or
                   b.type in TYPED and b.label().startswith("aws_") for _, b in nested)
    root = [(where, b) for where, b in blocks if "/" not in where.split(" ")[0]]
    if uses_aws and not any(b.type == "provider" and b.label() == "aws" and "alias" not in b.attrs for _, b in root):
        out.append(f"the {which}'s configuration uses AWS with no provider \"aws\" block in the exercise's top "
                   "folder, so Terraform would make a default one that finds the learner's own credentials. "
                   "Add the provider block from the instructions")

    for where, b in blocks:
        if b.type == "provider" and b.label() == "aws":
            out += _provider_problems(where, b)
        if b.type == "module" and not _local_source(b.attrs.get("source")):
            out.append(f"{where}: module {b.label()!r} comes from {literal(b.attrs.get('source')) or 'somewhere'} "
                       "instead of a folder in the exercise, so its code isn't checked here. Use a local "
                       "path like ./modules/name")
        if b.type == "terraform":
            for backend in b.children("backend"):
                if backend.label() != "local":
                    out.append(f'{where} keeps state in a backend "{backend.label()}", which talks to a real '
                               "service with the learner's credentials. Leave state local and teach the backend "
                               "in the explanation")
            if b.children("cloud"):
                out.append(f"{where} has a cloud block, which sends state to HCP Terraform. Leave state local")

    for where, b in nested:
        if b.type == "provider" and b.label() == "awscc" or b.type in TYPED and b.label().startswith("awscc_"):
            out.append(f"{where} uses the awscc provider, which these checks don't cover yet. Use hashicorp/aws")
        if b.type == "data" and b.label() == "terraform_remote_state" and literal(b.attrs.get("backend")) != "local":
            out.append(f"{where} reads remote state from another backend. Only backend = \"local\" stays on "
                       "the machine")
        if b.type == "data" and b.label() in ("http", "external"):
            out.append(f'{where} has a data "{b.label()}" source, which reaches the network or runs a '
                       "program. Remove it")
        if b.type == "provisioner":
            out.append(f"{where} has a provisioner, which runs commands on the learner's machine. Remove it")

    for where, bs in tests.items():
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
# an aws command where a command starts: a line, or after ; && || | $( or a $ prompt
_COMMAND = re.compile(r"(?:^|[;&|(`])\s*(?:[$%>]\s+)?(?:sudo\s+)?((?:[A-Z_]+=\S+\s+)*)aws\s+(?!=)(?=\S)(.*)$")
_ENDPOINT = re.compile(r"--endpoint-url(?:=|\s+)[\"']?([^\s\"']+)")
_ENV_ENDPOINT = re.compile(r"AWS_ENDPOINT_URL=[\"']?([^\s\"']+)")
SDK_CODE = (".py", ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts")
_SDK = re.compile(r"^\s*(?:import|from)\s+(?:boto3|botocore|aiobotocore)\b|@aws-sdk/|[\"']aws-sdk[\"']", re.M)


def _commands(code: str) -> list[str]:
    """The aws commands in a piece of code, each with its continuation lines joined on."""
    joined = re.sub(r"\\\n", " ", code)
    found = []
    for line in joined.splitlines():
        if m := _COMMAND.search(line):
            found.append(m.group(1) + "aws " + m.group(2))
    return found


def aws_commands(text: str) -> list[str]:
    code = _FENCE.findall(text)
    spans = _SPAN.findall(_FENCE.sub("", text))
    return [c for piece in code + spans for c in _commands(piece)]


def command_problems(commands: list[str], where: str) -> list[str]:
    out = []
    for c in commands:
        endpoint = _ENDPOINT.search(c) or _ENV_ENDPOINT.search(c)
        if not (endpoint and local_url(endpoint.group(1))):
            short = " ".join(c.split())[:80]
            out.append(f"{where} has `{short}`, which uses the learner's own AWS account. Add "
                       "--endpoint-url http://localhost:4566 so it goes to the emulator")
    return out


def uses_aws(lesson: Lesson) -> bool:
    """Does this lesson touch AWS at all: a provider, a resource, or an aws command."""
    if lesson.exercise:
        for f in lesson.exercise.starter + lesson.exercise.solution:
            if _is_tf(f.path) and re.search(r'provider\s+"aws"|^\s*(?:resource|data)\s+"aws_', f.content, re.M):
                return True
    return bool(aws_commands(lesson.explanation + "\n" + lesson.worked_example))


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
