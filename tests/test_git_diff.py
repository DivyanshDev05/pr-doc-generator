import pytest

from git_diff import _safe_check, FORBIDDEN_VERBS


class TestSafeCheck:
    """Test git command safety checking."""

    def test_blocks_commit(self):
        """git commit should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "commit", "-m", "fix bug"])

    def test_blocks_push(self):
        """git push should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "push", "origin", "main"])

    def test_blocks_pull(self):
        """git pull should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "pull", "origin", "main"])

    def test_blocks_merge(self):
        """git merge should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "merge", "feature-branch"])

    def test_blocks_rebase(self):
        """git rebase should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "rebase", "main"])

    def test_blocks_reset(self):
        """git reset should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "reset", "--hard", "HEAD~1"])

    def test_blocks_checkout(self):
        """git checkout should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "checkout", "main"])

    def test_blocks_switch(self):
        """git switch should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "switch", "main"])

    def test_blocks_stash(self):
        """git stash should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "stash"])

    def test_blocks_rm(self):
        """git rm should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "rm", "file.txt"])

    def test_blocks_clean(self):
        """git clean should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "clean", "-fd"])

    def test_blocks_cherry_pick(self):
        """git cherry-pick should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "cherry-pick", "abc123"])

    def test_blocks_revert(self):
        """git revert should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "revert", "abc123"])

    def test_blocks_bisect(self):
        """git bisect should be blocked."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "bisect", "start"])

    def test_allows_diff(self):
        """git diff should be allowed."""
        result = _safe_check(["git", "diff", "main...branch"])
        assert result is None

    def test_allows_diff_with_options(self):
        """git diff with options should be allowed."""
        result = _safe_check(["git", "diff", "--stat", "main"])
        assert result is None

    def test_allows_log(self):
        """git log should be allowed."""
        result = _safe_check(["git", "log", "--oneline", "-10"])
        assert result is None

    def test_allows_fetch(self):
        """git fetch should be allowed (read-only)."""
        result = _safe_check(["git", "fetch", "origin"])
        assert result is None

    def test_allows_show(self):
        """git show should be allowed."""
        result = _safe_check(["git", "show", "abc123"])
        assert result is None

    def test_allows_rev_parse(self):
        """git rev-parse should be allowed."""
        result = _safe_check(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        assert result is None

    def test_allows_status(self):
        """git status should be allowed."""
        result = _safe_check(["git", "status"])
        assert result is None

    def test_case_insensitive(self):
        """Safety check should be case insensitive."""
        with pytest.raises(PermissionError):
            _safe_check(["git", "COMMIT", "-m", "msg"])
        
        with pytest.raises(PermissionError):
            _safe_check(["git", "PUSH", "origin", "main"])

    def test_ignores_flags(self):
        """Flags (starting with -) should be ignored in check."""
        result = _safe_check(["git", "diff", "--stat", "-w", "main"])
        assert result is None

        result = _safe_check(["git", "log", "--oneline", "-n", "10"])
        assert result is None


class TestForbiddenVerbs:
    """Test FORBIDDEN_VERBS set completeness."""

    def test_contains_dangerous_verbs(self):
        """Should contain all dangerous git verbs."""
        dangerous = {
            "commit", "push", "pull", "merge", "rebase", "reset",
            "checkout", "switch", "stash", "cherry-pick", "revert",
            "rm", "clean", "apply", "am", "bisect"
        }
        assert FORBIDDEN_VERBS == dangerous
