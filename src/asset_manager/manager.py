
import os
import yaml
from typing import Dict, Any, List, Optional

class AssetManager:
    """Minimal, simulator-agnostic Asset Manager."""

    def __init__(self, base_dir: str, verbose: bool=False, validate_files: bool=True):
        self.base_dir = os.path.abspath(base_dir)
        self.verbose = verbose
        self.validate_files = validate_files
        if not os.path.isdir(self.base_dir):
            raise FileNotFoundError(f"Asset base directory not found: {self.base_dir}")
        self.assets: Dict[str, Dict[str, Any]] = {}
        self._asset_dirs: Dict[str, str] = {}
        self._index()

    def _index(self) -> None:
        for root, _, files in os.walk(self.base_dir):
            if "meta.yaml" in files:
                meta_path = os.path.join(root, "meta.yaml")
                data = self._load_yaml(meta_path)
                name = data.get("name") or os.path.basename(root)
                data["name"] = name

                if name in self.assets:
                    raise ValueError(f"Duplicate asset name: {name}")
                self._asset_dirs[name] = root

                for sim_key, path_key in [("mujoco", "xml_path"), ("isaac", "usd_path")]:
                    if sim_key in data and isinstance(data[sim_key], dict):
                        rel = data[sim_key].get(path_key)
                        if rel:
                            full = os.path.join(root, rel)
                            if self.validate_files and not os.path.isfile(full):
                                raise FileNotFoundError(f"{sim_key} file missing for {name}: {full}")
                self.assets[name] = data
        if self.verbose:
            print(f"[AssetManager] Indexed {len(self.assets)} assets from {self.base_dir}")

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}

    def get(self, name: str) -> Dict[str, Any]:
        if name not in self.assets:
            raise KeyError(name)
        return self.assets[name].copy()

    def list(self) -> List[str]:
        return sorted(self.assets.keys())

    def by_category(self, category: str) -> List[str]:
        return [n for n, m in self.assets.items() if category in m.get("category", [])]

    def get_path(self, name: str, simulator: str) -> Optional[str]:
        if name not in self.assets:
            return None
        sim_data = self.assets[name].get(simulator, {})
        if not isinstance(sim_data, dict):
            return None
        key = "xml_path" if simulator == "mujoco" else "usd_path"
        rel = sim_data.get(key)
        if not rel:
            return None
        return os.path.join(self._asset_dirs[name], rel)

    def summary(self) -> None:
        print(f"\n[AssetManager] Loaded {len(self.assets)} assets from {self.base_dir}")
        for name in self.list():
            meta = self.assets[name]
            cats = ", ".join(meta.get("category", []))
            mj = meta.get("mujoco", {}).get("xml_path", "-")
            isaac = meta.get("isaac", {}).get("usd_path", "-")
            print(f"  - {name:10s} | {cats:20s} | MJ: {mj:15s} | Isaac: {isaac}")
        print()

    def modules(self) -> List[str]:
        mods = set()
        for meta in self.assets.values():
            for key, val in meta.items():
                if isinstance(val, dict):
                    mods.add(key)
                if key == "perception" and isinstance(val, dict):
                    for sub in val.keys():
                        mods.add(f"perception:{sub}")
        return sorted(mods)

    def resolve_alias(self, alias: str, module: str) -> Optional[str]:
        """Resolve a perception alias to the canonical asset name.
        
        Args:
            alias: The alias string to resolve (e.g., "red cup", "mug")
            module: The perception module name (e.g., "ycb", "coco")
            
        Returns:
            The canonical asset name if found, None otherwise.
        """
        alias_lower = alias.lower()
        for name, meta in self.assets.items():
            perception = meta.get("perception", {})
            if not isinstance(perception, dict):
                continue
            module_data = perception.get(module, {})
            if not isinstance(module_data, dict):
                continue
            aliases = module_data.get("aliases", [])
            if not isinstance(aliases, list):
                continue
            for a in aliases:
                if isinstance(a, str) and a.lower() == alias_lower:
                    return name
            # Also check if the alias matches the canonical name
            if name.lower() == alias_lower:
                return name
        return None
