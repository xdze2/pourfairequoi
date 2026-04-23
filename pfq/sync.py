"""Git sync helpers for pfq vaults.

A vault is a git-managed directory. Sync = pull on open, commit+push on close.
All functions return a SyncResult — never raise.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class SyncResult:
    ok: bool
    message: str  # short, suitable for a toast or modal line


def _run(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run a git command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def is_git_repo(vault_path: Path) -> bool:
    code, _, _ = _run(["git", "rev-parse", "--git-dir"], vault_path)
    return code == 0


def has_remote(vault_path: Path) -> bool:
    code, out, _ = _run(["git", "remote"], vault_path)
    return code == 0 and bool(out.strip())


def has_uncommitted_changes(vault_path: Path) -> bool:
    code, out, _ = _run(["git", "status", "--porcelain"], vault_path)
    return code == 0 and bool(out.strip())


def pull(vault_path: Path) -> SyncResult:
    """Pull from remote. Detects merge conflicts."""
    code, out, err = _run(["git", "pull", "--no-rebase"], vault_path)
    if code == 0:
        if "Already up to date" in out:
            return SyncResult(ok=True, message="Already up to date")
        return SyncResult(ok=True, message="Pulled latest changes")
    # conflict?
    if "CONFLICT" in out or "CONFLICT" in err or "merge conflict" in err.lower():
        return SyncResult(ok=False, message="Merge conflict — fix in your editor before next sync")
    return SyncResult(ok=False, message=err or out or "Pull failed")


def commit_and_push(vault_path: Path) -> SyncResult:
    """Stage all changes, commit with a timestamped message, and push."""
    if not has_uncommitted_changes(vault_path):
        # Still push in case a previous commit wasn't pushed
        code, _, err = _run(["git", "push"], vault_path)
        if code == 0:
            return SyncResult(ok=True, message="Nothing to commit — pushed")
        return SyncResult(ok=False, message=err or "Push failed")

    # Stage
    code, _, err = _run(["git", "add", "-A"], vault_path)
    if code != 0:
        return SyncResult(ok=False, message=err or "git add failed")

    # Commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"pfq: session {timestamp}"
    code, _, err = _run(["git", "commit", "-m", msg], vault_path)
    if code != 0:
        return SyncResult(ok=False, message=err or "git commit failed")

    # Push
    code, _, err = _run(["git", "push"], vault_path)
    if code != 0:
        return SyncResult(ok=False, message=err or "Push failed — committed locally")

    return SyncResult(ok=True, message=f"Synced: {msg}")


def sync(vault_path: Path) -> SyncResult:
    """Full sync: pull then commit+push. Returns the first failure or final success."""
    pull_result = pull(vault_path)
    if not pull_result.ok:
        return pull_result
    return commit_and_push(vault_path)
