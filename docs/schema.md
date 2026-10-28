# Schema

This document specifies the `meta.yaml` format and the checks `AssetManager` applies
while indexing. It is the canonical description of the format. Other documents link
here rather than restating it.

## Discovery

`AssetManager(base_dir)` walks `base_dir` recursively. Every directory that contains a
file named `meta.yaml` is one asset, and paths in that file are relative to that
directory. An empty `meta.yaml` describes an asset with no metadata beyond its name.

The top level of `meta.yaml` must be a mapping. Indexing raises `ValueError` naming
the file when it is not.

## Interpreted fields

The registry interprets these fields and checks their types while indexing. A
violation raises `ValueError` naming the file and the field.

| Field | Type | Meaning |
| --- | --- | --- |
| `name` | string | The canonical asset name. If absent or empty, the directory name is used. |
| `category` | list of strings | Categories used by `by_category`. Matching is exact. |
| `mujoco` | mapping | MuJoCo section. See [simulator sections](#simulator-sections). |
| `isaac` | mapping | Isaac section. See [simulator sections](#simulator-sections). |
| `perception` | mapping | Perception section. See [perception](#perception). |

Canonical names must be unique. A second asset with the same name raises `ValueError`
naming both files.

## Simulator sections

Each supported simulator has one key that holds the path of its model file:

| Simulator | Section | Path key |
| --- | --- | --- |
| MuJoCo | `mujoco` | `xml_path` |
| Isaac | `isaac` | `usd_path` |

A path must be a string, relative to the asset directory, and must resolve, after
following symbolic links, to a location inside that directory. Indexing raises
`ValueError` naming the file otherwise.

When `validate_files` is true, which is the default, indexing raises
`FileNotFoundError` if a declared model file does not exist. `get_path(name,
simulator)` returns the absolute path of the model file, or `None` when the asset is
unknown or declares no model for that simulator. It raises `ValueError` for a
simulator not listed above.

Other keys in a simulator section, such as `scale` or `friction`, are stored but not
interpreted by the registry.

## Perception

`perception.aliases` is a list of strings: the labels a perception system may report
for this asset. `resolve_alias(label)` returns the asset whose canonical name or
alias list contains `label`, ignoring case, and `None` otherwise. It raises
`TypeError` when `label` is not a string.

Labels are compared after Unicode case folding, so "Straße" and "STRASSE" are the same
label. Each label must identify at most one asset. Indexing raises `ValueError`, naming
both declaring files, when

- two assets list the same alias,
- an alias equals another asset's canonical name, or
- two canonical names differ only in case.

An asset may list its own name as an alias. Other keys under `perception` are stored
but not interpreted.

## Consumer sections

Every other top-level field belongs to the consumer that reads it, for example
`policy`, `safety`, `learning`, `rendering`, `mass`, or `dimensions`. The registry
stores and returns these fields unchanged and does not check them. A consumer that
depends on a section is responsible for validating it.

`modules()` lists the top-level fields whose value is a mapping, across all assets.

## Queries

| Method | Returns |
| --- | --- |
| `list()` | Canonical names, sorted |
| `get(name)` | An independent copy of the asset's metadata, including `name`. Raises `KeyError` for an unknown asset. |
| `by_category(category)` | Names of assets whose `category` list contains `category`, sorted |
| `get_path(name, simulator)` | See [simulator sections](#simulator-sections) |
| `resolve_alias(label)` | See [perception](#perception) |
| `modules()` | See [consumer sections](#consumer-sections) |
| `summary()` | Prints one line per asset |
