"""
git_diff.py — Git diff engine
Runs git commands only after getting user confirmation.
Never commits, pushes, pulls, or modifies any file.
"""

import re
import subprocess
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# Commands that are NEVER allowed regardless of user input
FORBIDDEN_VERBS = {
    "commit", "push", "pull", "merge", "rebase", "reset",
    "checkout", "switch", "stash", "cherry-pick", "revert",
    "rm", "clean", "apply", "am", "bisect",
}


def _safe_check(command_parts: list):
    """Raise if a forbidden git verb is in the command."""
    verbs = {p.lower() for p in command_parts if not p.startswith("-")}
    bad = verbs & FORBIDDEN_VERBS
    if bad:
        raise PermissionError(
            f"Command contains forbidden git verb(s): {bad}. "
            "This tool never commits, pushes, pulls, or modifies files."
        )


class GitDiffEngine:
    def __init__(self, project_root: str, confirm_callback: Callable[[str], bool]):
        self.root = project_root
        self.confirm = confirm_callback  # user must approve each command

    def _run(self, args: list, env: dict = None, input_text: str = None) -> subprocess.CompletedProcess:
        """Run a git command after safety check and user confirmation."""
        _safe_check(args)
        display = "git " + " ".join(args)
        if not self.confirm(display):
            raise InterruptedError(f"User declined to run: {display}")
        result = subprocess.run(
            ["git"] + args,
            cwd=self.root,
            capture_output=True,
            text=True,
            input=input_text,
            env=env,
        )
        return result

    def current_branch(self) -> Optional[str]:
        """Return the name of the currently checked-out branch."""
        result = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
        if result.returncode == 0:
            return result.stdout.strip()
        return None

    def get_diff(
        self,
        base_branch: str,
        current_branch: str,
        password: str = None,
    ) -> Dict:
        """
        Return diff stats and full diff text between base and current branch.
        Uses local git only — no network calls, no auth required for local repos.
        For remote branches it uses fetch (read-only).
        """

        # First try a straight local diff — works if branches are already fetched
        diff_result = self._try_local_diff(base_branch, current_branch)
        if diff_result:
            return diff_result

        # If branches are not available locally, offer to fetch (read-only)
        print(f"\n  ℹ  Base branch '{base_branch}' not found locally. Need to fetch it.")
        fetch_result = self._fetch_branch(base_branch, password=password)
        if not fetch_result:
            return {"diff": None, "needs_password": True}

        diff_result = self._try_local_diff(f"origin/{base_branch}", current_branch)
        if diff_result:
            return diff_result

        return {"diff": None, "stats": "No diff found", "changed_files": []}

    def _try_local_diff(self, base: str, head: str) -> Optional[Dict]:
        """Attempt a diff between two local refs."""

        # Check if base ref exists
        check = subprocess.run(
            ["git", "rev-parse", "--verify", base],
            cwd=self.root, capture_output=True, text=True
        )
        if check.returncode != 0:
            return None  # ref not available locally

        # Get stat summary
        stat_result = self._run(["diff", "--stat", f"{base}...{head}"])
        stats = stat_result.stdout.strip() if stat_result.returncode == 0 else "unknown"

        # Get full diff (exclude binary files, limit size)
        diff_result = self._run([
            "diff",
            "--diff-filter=ACMRT",   # Added, Copied, Modified, Renamed, Type-changed
            "--no-color",
            "-U5",                   # 5 lines of context
            f"{base}...{head}",
        ])

        if diff_result.returncode != 0:
            return None

        raw_diff = diff_result.stdout

        # Get list of changed files
        files_result = self._run([
            "diff", "--name-only", f"{base}...{head}"
        ])
        changed_files = []
        if files_result.returncode == 0:
            changed_files = [f for f in files_result.stdout.strip().splitlines() if f]

        # Trim diff if very large (>150KB) to stay within Claude context
        MAX_DIFF_CHARS = 150_000
        trimmed = False
        if len(raw_diff) > MAX_DIFF_CHARS:
            raw_diff = raw_diff[:MAX_DIFF_CHARS]
            trimmed = True

        return {
            "diff": raw_diff,
            "stats": stats + (" [TRIMMED — diff too large, showing first 150KB]" if trimmed else ""),
            "changed_files": changed_files,
            "needs_password": False,
        }

    def _fetch_branch(self, branch: str, password: str = None) -> bool:
        """Fetch a remote branch (read-only). Returns True on success."""
        try:
            result = self._run(["fetch", "origin", branch])
            if result.returncode == 0:
                return True
            if "Authentication failed" in result.stderr or "could not read Username" in result.stderr:
                return False  # caller will ask for password
            print(f"  ⚠  Fetch warning: {result.stderr.strip()}")
            return result.returncode == 0
        except InterruptedError:
            return False
