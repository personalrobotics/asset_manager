# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Siddhartha Srinivasa

"""Index-time rules that well-formed sample data cannot exercise.

Malformed metadata must be refused while indexing, with the file named, rather than
failing later inside a query or matching the wrong asset. Alias resolution must not
depend on directory traversal order, so any label that could name two assets is
refused when the registry is built.
"""

import pytest

from asset_manager import AssetManager


def _registry(tmp_path, assets):
    for directory, text in assets.items():
        (tmp_path / directory).mkdir()
        (tmp_path / directory / "meta.yaml").write_text(text)
    return AssetManager(str(tmp_path))


@pytest.mark.parametrize(
    "text, field",
    [
        ("- 1\n- 2\n", "mapping"),
        ("name: [a, b]\n", "name"),
        ("category: kitchenware\n", "category"),
        ("mujoco: null\n", "mujoco"),
        ("isaac: cup.usd\n", "isaac"),
        ("perception: [cup]\n", "perception"),
        ("perception:\n  aliases: cup\n", "perception.aliases"),
        ("perception:\n  aliases: [cup, 3]\n", "perception.aliases"),
        ("1: {}\npolicy: {}\n", "field names"),
        ("mujoco:\n  xml_path: 5\n", "mujoco.xml_path"),
        # A declared path is checked whatever its value, including falsy ones.
        ("mujoco:\n  xml_path: []\n", "mujoco.xml_path"),
        ("mujoco:\n  xml_path: false\n", "mujoco.xml_path"),
        ("mujoco:\n  xml_path: null\n", "mujoco.xml_path"),
        ("mujoco:\n  xml_path: 0\n", "mujoco.xml_path"),
        ("mujoco:\n  xml_path: ''\n", "mujoco.xml_path"),
        # Model paths must stay inside the asset directory.
        ("mujoco:\n  xml_path: ../outside.xml\n", "mujoco.xml_path"),
        ("mujoco:\n  xml_path: /etc/hosts\n", "mujoco.xml_path"),
    ],
)
def test_malformed_metadata_is_refused_with_its_file(tmp_path, text, field):
    with pytest.raises(ValueError) as excinfo:
        _registry(tmp_path, {"a": text})
    assert "meta.yaml" in str(excinfo.value)
    assert field in str(excinfo.value)


def test_a_model_path_may_not_escape_through_a_symlink(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "model.xml").write_text("<mujoco/>")
    (tmp_path / "objects" / "a").mkdir(parents=True)
    (tmp_path / "objects" / "a" / "link.xml").symlink_to(outside / "model.xml")
    (tmp_path / "objects" / "a" / "meta.yaml").write_text("mujoco:\n  xml_path: link.xml\n")
    with pytest.raises(ValueError, match="mujoco.xml_path") as excinfo:
        AssetManager(str(tmp_path / "objects"))
    assert "meta.yaml" in str(excinfo.value)


@pytest.mark.parametrize(
    "assets",
    [
        # Two assets claim the same alias, in different case.
        {"a": "perception:\n  aliases: [bin]\n", "b": "perception:\n  aliases: [Bin]\n"},
        # An alias names a different asset.
        {"a": "perception:\n  aliases: [cup]\n", "cup": "{}\n"},
        # Two canonical names differ only in case.
        {"a": "name: Cup\n", "b": "name: cup\n"},
        # Case-insensitive comparison covers Unicode case folding.
        {"a": "perception:\n  aliases: [Straße]\n", "b": "perception:\n  aliases: [STRASSE]\n"},
    ],
)
def test_ambiguous_labels_are_refused_at_index_time(tmp_path, assets):
    with pytest.raises(ValueError, match="ambiguous") as excinfo:
        _registry(tmp_path, assets)
    # Both declaring files are named so the conflict can be found.
    for directory in assets:
        assert str(tmp_path / directory / "meta.yaml") in str(excinfo.value)


def test_duplicate_names_are_refused_with_both_files(tmp_path):
    with pytest.raises(ValueError, match="Duplicate") as excinfo:
        _registry(tmp_path, {"a": "name: cup\n", "b": "name: cup\n"})
    for directory in ["a", "b"]:
        assert str(tmp_path / directory / "meta.yaml") in str(excinfo.value)


def test_an_asset_may_list_its_own_name_as_an_alias(tmp_path):
    registry = _registry(tmp_path, {"cup": "perception:\n  aliases: [Cup, mug]\n"})
    assert registry.resolve_alias("CUP") == "cup"
    assert registry.resolve_alias("mug") == "cup"


def test_query_inputs_are_checked(tmp_path):
    registry = _registry(tmp_path, {"cup": "{}\n"})
    with pytest.raises(TypeError):
        registry.resolve_alias(None)
    with pytest.raises(ValueError, match="ros"):
        registry.get_path("cup", "ros")
