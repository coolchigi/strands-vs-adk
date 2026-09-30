"""Build a course on ADK. See learning/cli.py for the options."""

import sys

from learning.cli import main

from .brain import MODEL, AdkBrain
from .pipeline import run
from .telemetry import BudgetExceeded, Meter

if __name__ == "__main__":
    sys.exit(main("adk", MODEL, AdkBrain, Meter.from_env(MODEL), run, BudgetExceeded))
