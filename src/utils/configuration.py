"""Configuration management."""

import json
import jsonschema
from jsonschema import validate
import os
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logging import get_logger

logger = get_logger(__name__)


def load_configuration(config_path: str = None) -> dict:
    """
    Load and validate configuration file
    Implements schema validation for algorithm modes and parameters
    """
    default_config = {
        'vertex_sharing_mode': 1,
        'intersection_mode': 1,
        'grouping_mode': 1,
        'tree_mode': 1,
        'tolerance_percent': 1.0,
        'benchmarking': {'enabled': False},
        'logging': {'level': 'INFO'},
        'ui': {'theme': 'system'}
    }

    if not config_path:
        # Try default config location
        config_path = Path.home() / '.dxf_segregator' / 'config.json'
        if not config_path.exists():
            return default_config

    try:
        with open(config_path, 'r') as f:
            user_config = json.load(f)

        # Validate against schema
        schema = {
            "type": "object",
            "properties": {
                "vertex_sharing_mode": {"type": "integer", "minimum": 1, "maximum": 3},
                "intersection_mode": {"type": "integer", "minimum": 1, "maximum": 3},
                "grouping_mode": {"type": "integer", "minimum": 1, "maximum": 3},
                "tree_mode": {"type": "integer", "minimum": 1, "maximum": 3},
                "tolerance_percent": {"type": "number", "minimum": 0.1, "maximum": 10.0},
                "benchmarking": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "min_iterations": {"type": "integer", "minimum": 1},
                        "max_iterations": {"type": "integer", "minimum": 1},
                        "output_dir": {"type": "string"}
                    }
                },
                "logging": {
                    "type": "object",
                    "properties": {
                        "level": {
                            "type": "string",
                            "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
                        },
                        "file": {"type": "string"},
                        "max_size": {"type": "integer", "minimum": 1024},
                        "backup_count": {"type": "integer", "minimum": 0}
                    }
                },
                "ui": {
                    "type": "object",
                    "properties": {
                        "theme": {
                            "type": "string",
                            "enum": ["system", "light", "dark"]
                        },
                        "window_width": {"type": "integer", "minimum": 600},
                        "window_height": {"type": "integer", "minimum": 400},
                        "recent_files": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        }

        validate(instance=user_config, schema=schema)
        logger.info(f"Configuration validated successfully: {config_path}")

        # Merge with defaults
        merged_config = default_config.copy()
        merged_config.update(user_config)
        return merged_config

    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        logger.warning("Using default configuration")
        return default_config
    except Exception as e:
        logger.error(f"Configuration loading failed: {str(e)}")
        logger.warning("Using default configuration")
        return default_config


class Config:
    """Application configuration manager (backward compatibility)."""

    def __init__(self, config_dict: Dict[str, Any] = None):
        """
        Initialize configuration.

        Args:
            config_dict: Configuration dictionary.
        """
        self.config = config_dict or {}

    @staticmethod
    def load(filepath: str) -> 'Config':
        """
        Load configuration from file.

        Args:
            filepath: Path to configuration file.

        Returns:
            Config instance.
        """
        config_dict = load_configuration(filepath)
        return Config(config_dict)

    @staticmethod
    def load_default() -> 'Config':
        """
        Load default configuration.

        Returns:
            Config instance with default values.
        """
        default_config = {
            "theme": "light",
            "grid_size": 50,
            "vertex_tolerance": 1e-6,
            "auto_save": True,
            "auto_save_interval": 300,
        }
        return Config(default_config)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value

    def save(self, filepath: str):
        """Save configuration to file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            json.dump(self.config, f, indent=2)
