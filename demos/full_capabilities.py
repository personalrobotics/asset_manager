# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Siddhartha Srinivasa

"""
full_capabilities_demo.py

Comprehensive demonstration of the AssetManager capabilities:
- Recursive discovery and indexing
- Summaries and module introspection
- Category and path queries
- Alias resolution (perception integration)
- Simulator-specific path resolution (MuJoCo, Isaac)
- YAML export of a subset
"""

import os
from pathlib import Path

import yaml

from asset_manager.manager import AssetManager


def main():
    # ----------------------------------------------------------------------
    # 1️⃣ Initialize AssetManager
    # ----------------------------------------------------------------------
    # The sample objects live in the repository, next to this demo.
    base_dir = Path(__file__).resolve().parent.parent / "data" / "objects"
    am = AssetManager(str(base_dir), verbose=True)

    print("\n========== SUMMARY ==========")
    am.summary()

    print("\n========== MODULES ==========")
    print(am.modules())

    # ----------------------------------------------------------------------
    # 2️⃣ Query all assets and categories
    # ----------------------------------------------------------------------
    print("\n========== ASSET LIST ==========")
    all_assets = am.list()
    print(all_assets)

    print("\n========== KITCHENWARE ==========")
    print(am.by_category("kitchenware"))

    # ----------------------------------------------------------------------
    # 3️⃣ Simulator-specific path resolution
    # ----------------------------------------------------------------------
    print("\n========== SIMULATOR PATHS ==========")
    for name in am.list():
        mj_path = am.get_path(name, "mujoco")
        isaac_path = am.get_path(name, "isaac")
        print(f"{name:10s} | MuJoCo: {mj_path or '-':40s} | Isaac: {isaac_path or '-'}")

    # ----------------------------------------------------------------------
    # 4️⃣ Perception alias resolution
    # ----------------------------------------------------------------------
    print("\n========== ALIAS RESOLUTION ==========")
    aliases = ["cup", "red cup", "mug", "knife", "unknown"]
    for alias in aliases:
        resolved = am.resolve_alias(alias)
        print(f"Perception alias '{alias}' → {resolved}")

    # ----------------------------------------------------------------------
    # 5️⃣ Simulate perception detections
    # ----------------------------------------------------------------------
    print("\n========== PERCEPTION SIMULATION ==========")
    perception_output = [
        {"label": "cup", "confidence": 0.91},
        {"label": "mug", "confidence": 0.87},
        {"label": "plate", "confidence": 0.94},
    ]
    resolved_objects = []
    for det in perception_output:
        canonical = am.resolve_alias(det["label"])
        resolved_objects.append(
            {
                "label": det["label"],
                "canonical_name": canonical,
                "confidence": det["confidence"],
            }
        )

    print(yaml.dump(resolved_objects, sort_keys=False, default_flow_style=False))

    # ----------------------------------------------------------------------
    # 6️⃣ Validate paths
    # ----------------------------------------------------------------------
    print("\n========== VALIDATION ==========")
    for name in am.list():
        for backend in ["mujoco", "isaac"]:
            path = am.get_path(name, backend)
            exists = os.path.exists(path) if path else False
            print(
                f"{backend.capitalize():6s} path for {name:8s}: {path or '-':40s} {'[OK]' if exists else '[MISSING]'}"
            )

    # ----------------------------------------------------------------------
    # 7️⃣ Export subset to YAML
    # ----------------------------------------------------------------------
    print("\n========== EXPORT SUBSET ==========")
    subset = {n: am.get(n) for n in am.by_category("kitchenware")}
    print(yaml.dump(subset, sort_keys=False))
    print(f"Subset contains {len(subset)} assets: {list(subset.keys())}")

    # ----------------------------------------------------------------------
    # 8️⃣ Summary footer
    # ----------------------------------------------------------------------
    print("\n========== DONE ==========")
    print("All AssetManager features successfully demonstrated.")


if __name__ == "__main__":
    main()
