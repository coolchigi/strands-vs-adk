"""Build a course on Strands. See learning/cli.py for the options."""

import sys

from learning.cli import main

from .brain import MODEL_ID, StrandsBrain
from .pipeline import run
from .telemetry import BudgetExceeded, Meter

if __name__ == "__main__":
    sys.exit(main("strands", MODEL_ID, StrandsBrain, Meter.from_env(MODEL_ID), run, BudgetExceeded))
