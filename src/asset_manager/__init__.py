"""Asset Manager - A unified, simulator-agnostic registry for robotics assets."""

from pathlib import Path

from asset_manager.manager import AssetManager

__all__ = ["AssetManager", "get_objects_path"]
__version__ = "0.1.0"

# Package directory (where this __init__.py lives)
_PACKAGE_DIR = Path(__file__).parent


def get_objects_path() -> Path:
    """Get the path to the default objects directory.

    Returns:
        Path to data/objects/ containing object assets (cup, plate, etc.)

    Example:
        >>> from asset_manager import AssetManager, get_objects_path
        >>> manager = AssetManager(base_dir=str(get_objects_path()))
    """
    return _PACKAGE_DIR.parent.parent / "data" / "objects"

