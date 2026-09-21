"""Check the install without spending a token.

Run:  python smoke_test.py

Every example here either calls a model or builds something that will. This
script goes as far as it can without credentials:

  parse      every file compiles
  imports    every import in every file resolves against what you installed
  construct  every agent, graph and app object is built for real

What it cannot tell you is whether the model answers well. That needs AWS
credentials for the Strands files and a GOOGLE_API_KEY for the ADK ones.
"""
from __future__ import annotations

import ast
import importlib
import importlib.util
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent

# Files whose module body calls a model. They are parsed and import checked, and
# not executed, because running them costs money and needs credentials.
CALLS_A_MODEL = {
    "01-hello-world/hello-world.py",
    "02-tools/hello-world.py",
    "03-agent-loop/hello-world.py",
    "03-agent-loop/main.py",
    "04-state/conversation.py",
    "04-state/main.py",
    "05-control-points/hooks.py",
}

# Files needing a package beyond the base two. Reported, not failed, when absent.
OPTIONAL = {
    "07-evaluation/evaluate_strands.py": "strands_evals",
    "07-evaluation/test_researcher.py": "pytest",
    "08-deployment/app.py": "fastapi",
}

GREEN, RED, DIM, OFF = "\033[32m", "\033[31m", "\033[2m", "\033[0m"
if not sys.stdout.isatty():
    GREEN = RED = DIM = OFF = ""


SKIP_DIRS = {".venv", "venv", "__pycache__", ".git", "build", "dist", "node_modules"}


def python_files() -> list[pathlib.Path]:
    """Every example file, and nothing from a virtualenv.

    `uv sync` and `python -m venv .venv` both put the environment inside this
    folder, so an unfiltered rglob walks into site-packages and tries to import
    a few thousand third party modules.
    """
    return sorted(
        p for p in ROOT.rglob("*.py")
        if p.name not in {"smoke_test.py", "__init__.py"}
        and not any(part in SKIP_DIRS or part.startswith(".") for part in p.relative_to(ROOT).parts)
    )


def imports_of(tree: ast.AST) -> list[tuple[str, str | None]]:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out += [(node.module, a.name) for a in node.names]
        elif isinstance(node, ast.Import):
            out += [(a.name, None) for a in node.names]
    return out


def check(path: pathlib.Path) -> tuple[bool, str]:
    rel = path.relative_to(ROOT).as_posix()
    src = path.read_text()

    try:
        tree = ast.parse(src, filename=rel)
    except SyntaxError as exc:
        return False, f"does not parse: {exc.msg} (line {exc.lineno})"

    need = OPTIONAL.get(rel)
    if need and importlib.util.find_spec(need) is None:
        return True, f"skipped, needs {need}"

    for module, name in imports_of(tree):
        if module.startswith("course_agent"):
            continue
        try:
            mod = importlib.import_module(module)
        except ImportError as exc:
            return False, f"import {module} failed: {exc}"
        if name and not hasattr(mod, name):
            return False, f"{module} has no {name}"

    if rel in CALLS_A_MODEL:
        return True, "parsed and imports resolve, not run"

    # Safe to execute: these build objects without calling a model.
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location(f"smoke_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - we want the reason, whatever it is
        return False, f"{type(exc).__name__}: {exc}"
    finally:
        sys.path.pop(0)
    return True, "constructed"


def stale_entries() -> list[str]:
    """Paths in the tables above that no longer exist.

    A renamed folder silently turns "do not run this, it calls a model" into
    "run it", which costs money and needs credentials. Catch it here instead.
    """
    return sorted(
        rel for rel in (CALLS_A_MODEL | set(OPTIONAL))
        if not (ROOT / rel).exists()
    )


def main() -> int:
    os.environ.setdefault("GOOGLE_API_KEY", "smoke-test-not-a-real-key")

    stale = stale_entries()
    if stale:
        print(f"{RED}This script is out of date. These paths no longer exist:{OFF}")
        for rel in stale:
            print(f"    {rel}")
        return 1

    files = python_files()
    failed = 0
    for path in files:
        ok, note = check(path)
        mark = f"{GREEN}ok{OFF}" if ok else f"{RED}FAIL{OFF}"
        if not ok:
            failed += 1
        print(f"  {mark:>14}  {path.relative_to(ROOT).as_posix():<40} {DIM}{note}{OFF}")

    print()
    if failed:
        print(f"{RED}{failed} of {len(files)} files failed.{OFF}")
        return 1
    print(f"{GREEN}All {len(files)} files are good.{OFF} Add credentials and run them for real.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
