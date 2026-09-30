"""Build a course from what someone says they want to learn. Each framework calls main().

    python -m impl.strands.run "I'd like to deeply understand Terraform"
    python -m impl.adk.run "I'd like to deeply understand Terraform" --answer "I've never used it"

The intake may ask a few questions first. Pass --answer to reply, or leave it off and it
builds with what it has. Every stage is saved under --runs as it passes, so running the
same command again after a crash picks up where it stopped.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Callable

from . import course_dir, stages
from .flow import Flow, open_problems, start
from .model import LearnerProfile
from .web import HttpWeb


def _caused_by(e: BaseException | None, kind: type[Exception]) -> bool:
    """Strands raises a hook's exception wrapped in its own EventLoopException."""
    while e is not None:
        if isinstance(e, kind):
            return True
        e = e.__cause__ or e.__context__
    return False


def load_spend(meter, path: Path) -> None:
    """Earlier sessions of this run count against the same cap, so a resume isn't a fresh budget.

    Each role is [calls, tokens in, tokens out, dollars]. Files from before dollars were
    saved have 3 numbers, and their tokens are priced at the run's main model.
    """
    if path.exists():
        from .budget import Usage, price_for
        p = price_for(meter.model)
        for role, row in json.loads(path.read_text()).items():
            calls, tokens_in, tokens_out = row[:3]
            usd = row[3] if len(row) > 3 else (tokens_in * p[0] + tokens_out * p[1]) / 1_000_000
            meter.by_role[role] = Usage(calls, tokens_in, tokens_out, usd)


def save_spend(meter, path: Path) -> None:
    path.write_text(json.dumps({r: [u.calls, u.input_tokens, u.output_tokens, round(u.usd, 6)]
                                for r, u in meter.by_role.items()}, indent=1))


def main(framework: str, model: str, make_brain: Callable, meter, run_pipeline: Callable[[Flow], object],
         budget_error: type[Exception], argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("message", help="what you want to learn, in your own words")
    ap.add_argument("--answer", help="your reply if the intake asks questions")
    ap.add_argument("--out", type=Path, default=Path(f"out/{framework}"))
    ap.add_argument("--runs", type=Path, default=Path(f"runs/{framework}"))
    ap.add_argument("--no-review", action="store_true", help="skip the model reviewer, keep the mechanical checks")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    for noisy in ("strands", "botocore", "httpx", "mcp", "google_adk", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    log = logging.getLogger("learning")
    args.runs.mkdir(parents=True, exist_ok=True)
    spend = args.runs / "spend.json"
    load_spend(meter, spend)
    # written as it's counted, so a run that's killed still leaves what it spent
    meter.persist = lambda: save_spend(meter, spend)
    brain = make_brain(meter)
    started = time.monotonic()

    try:
        saved = args.runs / "profile.json"
        if saved.exists():
            profile = LearnerProfile.model_validate_json(saved.read_text())
            log.info("resuming %s from %s", profile.subject, args.runs)
        else:
            profile = stages.intake(brain, args.message)
            if profile.questions:
                print("\nThe intake asks:")
                for q in profile.questions:
                    print(f"  - {q}")
                answer = args.answer or "No preference, go ahead with what you have."
                print(f"\nReplying: {answer}\n")
                profile = stages.intake(brain, f"{args.message}\n\nYou asked:\n"
                                        + "\n".join(f"- {q}" for q in profile.questions)
                                        + f"\n\nThey answered: {answer}\n\nDon't ask again.")
            if not profile.subject_is_clear:
                print("The subject still isn't clear enough to research:", profile.questions)
                return 1
            saved.write_text(profile.model_dump_json(indent=1))
        print(profile.brief(), "\n")

        flow = start(brain, HttpWeb(), profile, args.runs, reviewer=not args.no_review)
        run_pipeline(flow)
        course = flow.course()
    except Exception as e:
        if not _caused_by(e, budget_error):
            raise
        print(f"\nStopped by the budget cap: {e}", file=sys.stderr)
        return 2
    finally:
        save_spend(meter, spend)
        t = meter.total
        print(f"\n{framework}, every session of this run: {t.calls} model calls, {t.input_tokens} tokens in, "
              f"{t.output_tokens} out, ${meter.spent_usd:.2f} estimated. This session {time.monotonic() - started:.0f}s")
        for role, u in sorted(meter.by_role.items()):
            print(f"  {role:18} {u.calls:4} calls {u.input_tokens:9} in {u.output_tokens:8} out")

    root = course_dir.write(course, args.out)
    problems = open_problems(flow.board)
    kb = course.knowledge
    print(f"\n{course.curriculum.title}: {len(course.curriculum.units)} units, {len(course.lessons)} lessons, "
          f"{len(kb.claims)} claims from {len(kb.sources)} sources ({len(kb.dropped)} dropped)")
    if problems:
        print(f"{len(problems)} problems left after retries:")
        for p in problems:
            print(f"  {p.stage.value} {p.lesson_id or ''} {p.check}: {p.detail[:200]}")
    print(f"\nwrote {root}. Start with: cd {root} && python3 learn.py next")
    return 0 if not problems else 1
