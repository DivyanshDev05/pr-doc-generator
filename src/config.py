"""
config.py — Configuration loader for PR Doc Generator.

Loads config from:
1. Project root: <project>/.pr-doc-gen.yaml
2. Home directory: ~/.pr-doc-gen.yaml
3. Defaults if neither found
"""

import os
from pathlib import Path
from typing import Optional

import yaml

DEFAULT_CONFIG = {
    "provider": "groq",
    "model": None,
    "base_branch": "main",
    "output_dir": "./pr-docs",
    "template": None,
}


def get_config_path(project_root: Optional[str] = None) -> Optional[Path]:
    """Find config file location with priority: project > home > None."""
    if project_root:
        project_config = Path(project_root) / ".pr-doc-gen.yaml"
        if project_config.exists():
            return project_config

    home_config = Path.home() / ".pr-doc-gen.yaml"
    if home_config.exists():
        return home_config

    return None


def load_config(project_root: Optional[str] = None) -> dict:
    """Load configuration with priority: project > home > defaults.
    
    Args:
        project_root: Path to the git project (used to find project config)
    
    Returns:
        Dictionary with configuration values
    """
    config = DEFAULT_CONFIG.copy()

    config_path = get_config_path(project_root)
    if config_path:
        try:
            with open(config_path) as f:
                user_config = yaml.safe_load(f) or {}
            
            for key, value in user_config.items():
                if key in config and value is not None:
                    config[key] = value
        except yaml.YAMLError as e:
            print(f"Warning: Invalid YAML in {config_path}: {e}")
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")

    return config


def config_exists(project_root: Optional[str] = None) -> bool:
    """Check if a config file exists."""
    return get_config_path(project_root) is not None
