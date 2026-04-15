from __future__ import annotations

import os
import random
import re
import string
from pathlib import Path

import yaml

DEFAULT_VAULT_PATH = Path("data")


# ── Low-level file I/O (private helpers) ─────────────────────────────────────


def _generate_id(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w]+", "_", text)
    return text.strip("_")[:40]


def _new_filepath(description: str, vault: Path) -> Path:
    vault.mkdir(parents=True, exist_ok=True)
    return vault / f"{_generate_id()}_{_slugify(description)}.yaml"
