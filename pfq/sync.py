"""Git sync helpers for pfq vaults.

A vault is a git-managed directory. Sync = pull on open, commit+push on close.
All functions return a SyncResult — never raise.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SyncResult:
    ok: bool
    message: str  # short, suitable for a toast or modal line


def _run(args: list[str], cwd: Path, timeout: int = 5) -> tuple[int, str, str]:
    """Run a git command, return (returncode, stdout, stderr).

    timeout is in seconds; prevents hanging on SSH password prompts.
    """
    try:
        # GIT_SSH_COMMAND disables password prompts — SSH will fail fast instead of hanging
        env = {"GIT_SSH_COMMAND": "ssh -o BatchMode=yes"}
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            input="",  # Prevent blocking on stdin
            timeout=timeout,
            env={**subprocess.os.environ, **env},  # Merge with existing env
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out (likely waiting for password/authentication)"


def is_git_repo(vault_path: Path) -> bool:
    """True only if vault_path itself is the root of a git repo (not a subdirectory of one)."""
    code, out, _ = _run(["git", "rev-parse", "--show-toplevel"], vault_path)
    if code != 0:
        return False
    return Path(out) == vault_path.resolve()


def has_remote(vault_path: Path) -> bool:
    code, out, _ = _run(["git", "remote"], vault_path)
    return code == 0 and bool(out.strip())


def get_remote_name(vault_path: Path) -> Optional[str]:
    """Return the first remote name, or None."""
    code, out, _ = _run(["git", "remote"], vault_path)
    if code != 0 or not out.strip():
        return None
    return out.splitlines()[0].strip()


def has_uncommitted_changes(vault_path: Path) -> bool:
    code, out, _ = _run(["git", "status", "--porcelain"], vault_path)
    return code == 0 and bool(out.strip())


def check_remote_access(vault_path: Path) -> SyncResult:
    """Check if the remote is accessible (pre-flight check).

    Uses 'git ls-remote' which is lightweight and doesn't modify anything.
    Returns success if remote is reachable, failure with advice otherwise.
    """
    code, out, err = _run(["git", "ls-remote", "--heads"], vault_path, timeout=3)
    if code == 0:
        return SyncResult(ok=True, message="Remote is accessible")
    # timeout or auth issue
    if code == 124:
        return SyncResult(ok=False, message="SSH authentication required — set up SSH keys or use HTTPS remote")
    # other errors
    return SyncResult(ok=False, message=err or out or "Cannot access remote")


def pull(vault_path: Path) -> SyncResult:
    """Pull from remote. Detects merge conflicts and auth issues."""
    code, out, err = _run(["git", "pull", "--no-rebase"], vault_path)
    if code == 0:
        if "Already up to date" in out:
            return SyncResult(ok=True, message="Already up to date")
        return SyncResult(ok=True, message="Pulled latest changes")
    # timeout or auth issue (SSH password prompt hangs)
    if code == 124:
        return SyncResult(ok=False, message="SSH authentication required — set up SSH keys or use HTTPS remote")
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
        # timeout or auth issue (SSH password prompt hangs)
        if code == 124:
            return SyncResult(ok=False, message="SSH authentication required — set up SSH keys or use HTTPS remote")
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
        # timeout or auth issue (SSH password prompt hangs)
        if code == 124:
            return SyncResult(ok=False, message="SSH authentication required — set up SSH keys or use HTTPS remote")
        return SyncResult(ok=False, message=err or "Push failed — committed locally")

    return SyncResult(ok=True, message=f"Synced: {msg}")


def sync(vault_path: Path) -> SyncResult:
    """Full sync: pull then commit+push. Returns the first failure or final success."""
    pull_result = pull(vault_path)
    if not pull_result.ok:
        return pull_result
    return commit_and_push(vault_path)
