# config_loader.py

import os
import yaml
from typing import Any, Dict


class ConfigLoader:
    """
    Central loader for YAML configs in config/ directory.

    Example:
        loader = ConfigLoader()
        nats_cfg = loader.get("nats.yaml")
        loader.save("new_config.yaml", {"a": 1, "b": 2})
    """

    def __init__(self, config_dir: str = "config"):
        self.config_dir = os.path.abspath(config_dir)

    def _file_path(self, filename: str) -> str:
        """Build absolute path to a config file."""
        return os.path.join(self.config_dir, filename)

    def _load_file(self, filename: str) -> Dict[str, Any]:
        """
        Private: check file existence and load YAML as dict.
        Raises:
            FileNotFoundError: if the file does not exist
            ValueError: if file is empty or contains invalid YAML
        """
        path = self._file_path(filename)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}") from e

        if not data:
            raise ValueError(f"Config file is empty or invalid: {path}")

        return data

    def get(self, filename: str) -> Dict[str, Any]:
        """
        Public method: load YAML and return dict.
        Raises exceptions if file missing or data invalid.
        """
        return self._load_file(filename)

    def save(self, filename: str, data: Dict[str, Any]) -> str:
        """
        Save a dictionary as a YAML config file inside the config directory.

        Args:
            filename: Target YAML filename 
            data: Dict to write into the YAML file.

        Returns:
            Absolute path to the generated file.

        Raises:
            ValueError: If data is not a dict.
            OSError: If file cannot be written.
        """
        if not isinstance(data, dict):
            raise ValueError("Config data must be a dictionary")

        path = self._file_path(filename)

        # Ensure directory exists
        os.makedirs(self.config_dir, exist_ok=True)

        try:
            with open(path, "w") as f:
                yaml.safe_dump(data, f, sort_keys=False)
        except Exception as e:
            raise OSError(f"Failed to write YAML file: {path}: {e}") from e

        return path
