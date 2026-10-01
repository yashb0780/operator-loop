"""Shared settings: file locations, LangSmith names, and the model we use.

Loading this module also reads your .env file, so API keys are available
to the Anthropic and LangSmith libraries.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# The project folder (one level above this file).
ROOT = Path(__file__).resolve().parent.parent

# Read keys from .env into the environment. Real environment variables win.
load_dotenv(ROOT / ".env")

# The Claude model the agent uses.
MODEL = "claude-sonnet-5-5"

# Names of things we create in LangSmith.
DATASET_NAME = "operator-loop-handoffs"
PROMPT_NAME = "operator-loop-playbook"
QUEUE_NAME = "operator-loop-review"

# Local files and folders.
DATA_FILE = ROOT / "data" / "handoffs.json"
PLAYBOOK_FILE = ROOT / "playbook" / "playbook.md"
VERSIONS_DIR = ROOT / "playbook" / "versions"
CHANGELOG_FILE = ROOT / "CHANGELOG.md"
RESULTS_DIR = ROOT / "results"
LATEST_RESULTS_FILE = RESULTS_DIR / "latest.json"
HISTORY_FILE = RESULTS_DIR / "history.jsonl"
JUDGMENTS_FILE = ROOT / "reviews" / "judgments.jsonl"
PROPOSALS_DIR = ROOT / "proposals"

# Who gets credited in the CHANGELOG when a rule is approved.
OPERATOR_NAME = os.getenv("OPERATOR_NAME") or "operator"


def require_keys() -> None:
    """Stop with a friendly message if an API key is missing from .env."""
    missing = [k for k in ("ANTHROPIC_API_KEY", "LANGSMITH_API_KEY") if not os.getenv(k)]
    if missing:
        sys.exit(f"Missing {', '.join(missing)}. Copy .env.example to .env and fill it in.")
