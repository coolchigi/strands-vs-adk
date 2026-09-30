"""Grade a finished course folder, from either framework, with the same checks.

    python -m learning.judge out/adk
    python -m learning.judge out/strands --no-run     # skip running the exercises

Everything here is re-checked from the folder, not taken from the run's word for it: every
quote against its stored page, the curriculum's coverage of the objectives, every
exercise's solution passing and starter failing, every provider pin against the registry.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from . import checks, course_dir
from .model import Evidence


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("course", type=Path)
    ap.add_argument("--no-run", action="store_true", help="don't run the exercises (fast)")
    args = ap.parse_args(argv)

    c = course_dir.load(args.course)
    kb, cur = c.knowledge, c.curriculum
    problems = checks.course(c, run_exercises=not args.no_run)

    leaves = kb.spec.leaves()
    taught = {i for l in cur.lessons() for o in l.objectives for i in o.covers}
    exercises = [l for l in c.lessons if l.exercise]
    print(f"{cur.title}  ({kb.spec.kind}, version {kb.spec.version or 'n/a'})")
    print(f"  objectives        {len(kb.spec.objectives)}, {len(leaves)} leaves, "
          f"{len([o for o in leaves if o.id in taught or o.parent_id in taught])} taught")
    print(f"  evidence          {len(kb.claims)} claims from {len(kb.sources)} sources, "
          f"{len(kb.dropped)} dropped by the quote check")
    print(f"  curriculum        {len(cur.units)} units, {len(cur.lessons())} lessons, "
          f"{sum(1 for u in cur.units if u.project)} unit projects")
    levels = Counter(o.level.value for l in cur.lessons() for o in l.objectives)
    print(f"  objective levels  {dict(levels)}")
    print(f"  lessons           {len(c.lessons)} written, {len(exercises)} with exercises, "
          f"{sum(len(l.quiz) for l in c.lessons)} questions")
    owed = [l.id for l in cur.lessons() if any(o.evidence is Evidence.EXERCISE for o in l.objectives)]
    print(f"  exercises owed    {len(owed)}")
    print()
    if not problems:
        print("PASS")
        return 0
    print(f"FAIL  {len(problems)} problems")
    for check, n in sorted(Counter(p.check for p in problems).items()):
        print(f"  {check:28} {n}")
    print()
    for p in problems[:30]:
        print(f"  [{p.stage.value}] {p.lesson_id or ''} {p.check}: {p.detail[:300]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
