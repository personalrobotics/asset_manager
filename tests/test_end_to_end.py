# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Siddhartha Srinivasa

"""End-to-end check of the registry over the repository's sample objects.

The test indexes ``data/objects`` with default settings, exercises every public query,
compiles each sample MJCF file with MuJoCo, and checks that it agrees with the ``dimensions`` declared in its
``meta.yaml``. It writes ``artifacts/registry_summary.json``, a sorted, deterministic
record of every asset's categories, aliases, and resolved MuJoCo path relative to the
repository root. Set ``ASSET_MANAGER_ARTIFACTS`` to write it elsewhere.

Reproduce with ``uv run pytest tests/ -v`` and inspect the JSON. Running it twice
produces byte-identical output.
"""

import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import pytest

from asset_manager import AssetManager

REPO_ROOT = Path(__file__).resolve().parent.parent
OBJECTS_DIR = REPO_ROOT / "data" / "objects"
ARTIFACT_DIR = Path(os.environ.get("ASSET_MANAGER_ARTIFACTS", REPO_ROOT / "artifacts"))


@pytest.fixture(scope="module")
def registry():
    return AssetManager(str(OBJECTS_DIR))


def _geom_extents(xml_path):
    """Full x, y, z extents of the single box or cylinder geom in a sample MJCF file."""
    geoms = ET.parse(xml_path).getroot().findall(".//geom")
    assert len(geoms) == 1, f"{xml_path}: expected one geom"
    geom = geoms[0]
    size = [float(v) for v in geom.get("size").split()]
    if geom.get("type") == "box":
        return [2 * s for s in size]
    if geom.get("type") == "cylinder":
        radius, half_height = size
        return [2 * radius, 2 * radius, 2 * half_height]
    raise AssertionError(f"{xml_path}: unexpected geom type {geom.get('type')}")


def test_sample_registry(registry):
    names = registry.list()
    assert names == ["bottle", "bowl", "box", "cup", "fork", "knife", "plate"]

    # Detector labels resolve case-insensitively through the flat alias list, and a
    # canonical name resolves to itself.
    assert registry.resolve_alias("mug") == "cup"
    assert registry.resolve_alias("Red Cup") == "cup"
    assert registry.resolve_alias("dish") == "plate"
    assert registry.resolve_alias("knife") == "knife"
    assert registry.resolve_alias("spatula") is None

    assert registry.by_category("kitchenware") == ["bottle", "bowl", "cup", "plate"]
    assert registry.by_category("kitchen") == []

    summary = {}
    for name in names:
        meta = registry.get(name)
        xml_path = registry.get_path(name, "mujoco")
        assert xml_path is not None and os.path.isfile(xml_path)
        mujoco.MjModel.from_xml_path(xml_path)
        assert _geom_extents(xml_path) == pytest.approx(meta["dimensions"]), name
        summary[name] = {
            "category": meta.get("category", []),
            "aliases": meta.get("perception", {}).get("aliases", []),
            "mujoco": Path(xml_path).relative_to(REPO_ROOT).as_posix(),
        }

    # get() hands out an independent copy; changing it leaves the registry intact.
    meta = registry.get("cup")
    meta["mujoco"]["xml_path"] = "elsewhere.xml"
    meta["perception"]["aliases"].append("bucket")
    assert registry.get_path("cup", "mujoco").endswith("mujoco_cup.xml")
    assert "bucket" not in registry.get("cup")["perception"]["aliases"]

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACT_DIR / "registry_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
