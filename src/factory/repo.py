"""The git steps the handlers take on the checkout: branches, pulls, commits, pushes.

Every step that may fail for a reason outside the factory (a rewritten branch, a conflict, a
remote that refuses) returns False instead of raising; the caller decides whether that is a
stall. Steps that fail only when the factory itself is wrong raise.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from factory import watch


def ok(root: Path, *args: str) -> bool:
    """Run `git <args>`; True when it exits 0."""
    result = subprocess.run(["git", *args], cwd=root, check=False, capture_output=True)
    return result.returncode == 0


def current_branch(root: Path) -> str:
    return watch.git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()


def head(root: Path) -> str:
    return watch.git(root, "rev-parse", "HEAD").strip()


def has_local(root: Path, branch: str) -> bool:
    return ok(root, "rev-parse", "--verify", "-q", f"refs/heads/{branch}")


def has_remote(root: Path, branch: str) -> bool:
    return ok(root, "rev-parse", "--verify", "-q", f"refs/remotes/origin/{branch}")


def exists(root: Path, branch: str) -> bool:
    return has_local(root, branch) or has_remote(root, branch)


def show(root: Path, branch: str, path: str) -> str | None:
    """The file at the tip of `branch` (local first, then `origin/`), None when absent."""
    for ref in (f"refs/heads/{branch}", f"refs/remotes/origin/{branch}"):
        if ok(root, "rev-parse", "--verify", "-q", ref):
            return show_ref(root, ref, path)
    return None


def show_ref(root: Path, ref: str, path: str) -> str | None:
    """The file at `ref`, None when the ref or the file is absent."""
    try:
        return watch.git(root, "show", f"{ref}:{path}")
    except subprocess.CalledProcessError:
        return None


def checkout(root: Path, branch: str) -> bool:
    """Switch to `branch`, tracking `origin/<branch>` when it exists only there, and bring it up
    to date with a fast-forward pull. False when the pull cannot fast-forward."""
    if current_branch(root) != branch:
        if has_local(root, branch):
            watch.git(root, "checkout", "-q", branch)
        else:
            watch.git(root, "checkout", "-q", "-b", branch, "--track", f"origin/{branch}")
    if not has_remote(root, branch):
        return True
    return ok(root, "pull", "-q", "--ff-only", "origin", branch)


def merge_main(root: Path, message: str) -> bool:
    """Merge `origin/main` into the current branch; on a conflict abort and return False."""
    ok(root, "fetch", "-q", "origin", "main")
    if ok(root, "merge", "-q", "--no-edit", "-m", message, "origin/main"):
        return True
    ok(root, "merge", "--abort")
    return False


def commit_all(root: Path, subject: str) -> None:
    watch.git(root, "add", "-A")
    watch.git(root, "commit", "-q", "-m", subject)


def push(root: Path, branch: str) -> None:
    watch.git(root, "push", "-q", "-u", "origin", branch)


def delete(root: Path, branch: str) -> None:
    """Delete `branch` locally and on `origin`; a branch already gone is fine."""
    if has_local(root, branch) and current_branch(root) != branch:
        watch.git(root, "branch", "-q", "-D", branch)
    ok(root, "fetch", "-q", "--prune", "origin")
    if has_remote(root, branch):
        watch.git(root, "push", "-q", "origin", "--delete", branch)
