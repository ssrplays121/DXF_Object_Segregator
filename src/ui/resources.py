"""UI resources manager."""

from typing import Dict, Optional
from pathlib import Path


class ResourceManager:
    """Manager for UI resources (icons, images, etc.)."""

    def __init__(self):
        """Initialize the resource manager."""
        self.resources_dir = Path(__file__).parent.parent.parent / "resources"
        self.icons_cache: Dict[str, str] = {}

    def get_icon_path(self, icon_name: str) -> Optional[str]:
        """
        Get the path to an icon.

        Args:
            icon_name: Name of the icon (without extension).

        Returns:
            Path to the icon file, or None if not found.
        """
        if icon_name in self.icons_cache:
            return self.icons_cache[icon_name]

        icon_path = self.resources_dir / "icons" / f"{icon_name}.png"
        if icon_path.exists():
            self.icons_cache[icon_name] = str(icon_path)
            return str(icon_path)

        return None

    def get_config_path(self, config_name: str) -> Optional[str]:
        """
        Get the path to a configuration file.

        Args:
            config_name: Name of the configuration file.

        Returns:
            Path to the configuration file, or None if not found.
        """
        config_path = self.resources_dir / config_name
        if config_path.exists():
            return str(config_path)
        return None
