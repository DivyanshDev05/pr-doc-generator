import os
import tempfile
from pathlib import Path

import pytest

from config import load_config, config_exists, DEFAULT_CONFIG, get_config_path


class TestDefaultConfig:
    """Test default configuration values."""

    def test_default_provider_is_groq(self):
        """Default provider should be groq (free)."""
        config = load_config()
        assert config["provider"] == "groq"

    def test_default_base_branch_is_main(self):
        """Default base branch should be main."""
        config = load_config()
        assert config["base_branch"] == "main"

    def test_default_output_dir(self):
        """Default output dir should be ./pr-docs."""
        config = load_config()
        assert config["output_dir"] == "./pr-docs"

    def test_model_is_none_by_default(self):
        """Model should be None by default (uses provider default)."""
        config = load_config()
        assert config["model"] is None

    def test_template_is_none_by_default(self):
        """Template should be None by default (uses bundled template)."""
        config = load_config()
        assert config["template"] is None


class TestConfigLoading:
    """Test configuration loading from files."""

    def test_load_config_with_no_file_returns_defaults(self):
        """When no config file exists, should return defaults."""
        config = load_config("/nonexistent/project")
        assert config["provider"] == "groq"
        assert config["base_branch"] == "main"

    def test_config_exists_returns_false_for_nonexistent(self):
        """config_exists should return False for nonexistent path."""
        assert config_exists("/nonexistent/project") is False


class TestConfigFilePriority:
    """Test config file priority: project > home > defaults."""

    def test_project_config_overrides_home(self, tmp_path):
        """Project config should take priority over home config."""
        home_config = Path.home() / ".pr-doc-gen.yaml"
        home_config.write_text("provider: openai\n")

        project_config = tmp_path / ".pr-doc-gen.yaml"
        project_config.write_text("provider: anthropic\n")

        try:
            config = load_config(str(tmp_path))
            assert config["provider"] == "anthropic"
        finally:
            home_config.unlink(missing_ok=True)

    def test_home_config_is_used_when_no_project_config(self, tmp_path):
        """Home config should be used when no project config exists."""
        home_config = Path.home() / ".pr-doc-gen.yaml"
        home_config.write_text("provider: gemini\nbase_branch: develop\n")

        try:
            config = load_config(str(tmp_path))
            assert config["provider"] == "gemini"
            assert config["base_branch"] == "develop"
        finally:
            home_config.unlink(missing_ok=True)

    def test_partial_config_merges_with_defaults(self, tmp_path):
        """Partial config should merge with defaults."""
        config_file = tmp_path / ".pr-doc-gen.yaml"
        config_file.write_text("provider: openai\n")

        config = load_config(str(tmp_path))
        assert config["provider"] == "openai"
        assert config["base_branch"] == "main"


class TestGetConfigPath:
    """Test config path detection."""

    def test_returns_none_when_no_config(self):
        """Should return None when no config file exists."""
        path = get_config_path("/nonexistent/project")
        assert path is None

    def test_finds_project_config(self, tmp_path):
        """Should find config in project root."""
        config_file = tmp_path / ".pr-doc-gen.yaml"
        config_file.write_text("provider: groq\n")

        path = get_config_path(str(tmp_path))
        assert path == config_file

    def test_finds_home_config(self, tmp_path, monkeypatch):
        """Should find config in home directory."""
        home_config = Path.home() / ".pr-doc-gen.yaml"
        home_config.write_text("provider: groq\n")

        monkeypatch.chdir(tmp_path)
        try:
            path = get_config_path()
            assert path == home_config
        finally:
            home_config.unlink(missing_ok=True)
