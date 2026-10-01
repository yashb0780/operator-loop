"""Reading the playbook and its version number."""

import re

from operator_loop.config import PLAYBOOK_FILE


def read_playbook() -> str:
    """Return the full text of the live playbook."""
    return PLAYBOOK_FILE.read_text()


def current_version(text: str | None = None) -> str:
    """Find the 'Version: vN' line in the playbook and return 'vN'."""
    text = text if text is not None else read_playbook()
    match = re.search(r"^Version:\s*(v\d+)", text, flags=re.MULTILINE)
    if not match:
        raise ValueError("The playbook is missing a 'Version: vN' line.")
    return match.group(1)
