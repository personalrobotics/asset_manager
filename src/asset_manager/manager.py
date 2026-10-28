# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Siddhartha Srinivasa

import copy
import os
from typing import Any, Dict, List, Optional

import yaml

# Simulator section -> key holding its model file, relative to the asset directory.
SIMULATOR_PATH_KEYS = {
    "mujoco": "xml_path",
    "isaac": "usd_path",
}


class AssetManager:
    """Minimal, simulator-agnostic Asset Manager."""

    def __init__(self, base_dir: str, verbose: bool = False, validate_files: bool = True):
        self.base_dir = os.path.abspath(base_dir)
        self.verbose = verbose
        self.validate_files = validate_files
        if not os.path.isdir(self.base_dir):
            raise FileNotFoundError(f"Asset base directory not found: {self.base_dir}")
        self.assets: Dict[str, Dict[str, Any]] = {}
        self._asset_dirs: Dict[str, str] = {}
        self._meta_paths: Dict[str, str] = {}
        self._labels: Dict[str, str] = {}
        self._index()

    def _index(self) -> None:
        for root, _, files in os.walk(self.base_dir):
            if "meta.yaml" in files:
                meta_path = os.path.join(root, "meta.yaml")
                data = self._load_yaml(meta_path)
                name = data.get("name") or os.path.basename(root)
                data["name"] = name

                if name in self.assets:
                    raise ValueError(f"Duplicate asset name {name!r} in {self._meta_paths[name]} and {meta_path}")
                self._asset_dirs[name] = root
                self._meta_paths[name] = meta_path

                for sim_key, path_key in SIMULATOR_PATH_KEYS.items():
                    if path_key in data.get(sim_key, {}):
                        rel = data[sim_key][path_key]
                        full = self._model_path(meta_path, root, f"{sim_key}.{path_key}", rel)
                        if self.validate_files and not os.path.isfile(full):
                            raise FileNotFoundError(f"{sim_key} file missing for {name}: {full}")
                self.assets[name] = data
        self._index_labels()
        if self.verbose:
            print(f"[AssetManager] Indexed {len(self.assets)} assets from {self.base_dir}")

    @staticmethod
    def _model_path(meta_path: str, root: str, field: str, rel: Any) -> str:
        """Join a declared model path to its asset directory, refusing one that leaves it."""
        if not isinstance(rel, str) or not rel:
            raise ValueError(f"{meta_path}: {field} must be a non-empty string")
        full = os.path.join(root, rel)
        real_root = os.path.realpath(root)
        if os.path.isabs(rel) or os.path.commonpath([real_root, os.path.realpath(full)]) != real_root:
            raise ValueError(f"{meta_path}: {field} must stay inside the asset directory, got {rel!r}")
        return full

    def _index_labels(self) -> None:
        """Map every case-folded canonical name and alias to exactly one asset."""
        labels = [(name, name) for name in self.assets]
        for name, meta in self.assets.items():
            labels += [(alias, name) for alias in meta.get("perception", {}).get("aliases", [])]
        for label, name in labels:
            owner = self._labels.setdefault(label.casefold(), name)
            if owner != name:
                raise ValueError(
                    f"Label {label!r} is ambiguous: it names both {owner!r} ({self._meta_paths[owner]}) "
                    f"and {name!r} ({self._meta_paths[name]})"
                )

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ValueError(f"{path}: expected a mapping at the top level, got {type(data).__name__}")
        self._validate(path, data)
        return data

    @staticmethod
    def _validate(path: str, data: Dict[str, Any]) -> None:
        """Check the fields the registry interprets. Other sections belong to their consumers."""

        def is_str_list(value: Any) -> bool:
            return isinstance(value, list) and all(isinstance(v, str) for v in value)

        non_string = [key for key in data if not isinstance(key, str)]
        if non_string:
            raise ValueError(f"{path}: field names must be strings, got {non_string!r}")
        if "name" in data and not isinstance(data["name"], str):
            raise ValueError(f"{path}: name must be a string")
        if "category" in data and not is_str_list(data["category"]):
            raise ValueError(f"{path}: category must be a list of strings")
        for section in [*SIMULATOR_PATH_KEYS, "perception"]:
            if section in data and not isinstance(data[section], dict):
                raise ValueError(f"{path}: {section} must be a mapping")
        if "aliases" in data.get("perception", {}) and not is_str_list(data["perception"]["aliases"]):
            raise ValueError(f"{path}: perception.aliases must be a list of strings")

    def get(self, name: str) -> Dict[str, Any]:
        if name not in self.assets:
            raise KeyError(name)
        return copy.deepcopy(self.assets[name])

    def list(self) -> List[str]:
        return sorted(self.assets.keys())

    def by_category(self, category: str) -> List[str]:
        return sorted(n for n, m in self.assets.items() if category in m.get("category", []))

    def get_path(self, name: str, simulator: str) -> Optional[str]:
        if simulator not in SIMULATOR_PATH_KEYS:
            raise ValueError(f"Unknown simulator {simulator!r}; expected one of {sorted(SIMULATOR_PATH_KEYS)}")
        if name not in self.assets:
            return None
        rel = self.assets[name].get(simulator, {}).get(SIMULATOR_PATH_KEYS[simulator])
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
        """Top-level metadata sections that hold a mapping, across all assets."""
        return sorted({key for meta in self.assets.values() for key, val in meta.items() if isinstance(val, dict)})

    def resolve_alias(self, alias: str) -> Optional[str]:
        """Resolve a perception label to the canonical asset name.

        A label matches an asset's canonical name or any entry of its flat
        ``perception.aliases`` list, ignoring case. Indexing refuses any label that
        would name two assets, so the result never depends on traversal order.

        Args:
            alias: The label to resolve (e.g., "soda can", "can")

        Returns:
            The canonical asset name if found, None otherwise.
        """
        if not isinstance(alias, str):
            raise TypeError(f"alias must be a string, got {type(alias).__name__}")
        return self._labels.get(alias.casefold())
