# Documentation guide

asset_manager follows the conventions of
[ssrobot's documentation guide](https://github.com/personalrobotics/ssrobot/blob/main/docs/documentation.md)
for writing voice, figures, and the distinction between implemented and planned
behavior. This file records how those conventions apply to this repository.

## Conceptual order

The README explains the model before the interface, in this order:

1. Several systems need one description of each physical object.
2. An asset is a directory whose `meta.yaml` complements, rather than replaces, its
   model files.
3. The registry checks the fields it interprets while indexing, so queries on a
   constructed registry need no further checks.
4. The registry interprets a few fields; every other section belongs to its consumer.
5. Perception labels resolve to exactly one asset.

These ideas are followed by one runnable example, the current capabilities, related
packages, and links to further detail.

## Document ownership

Each explanation has one canonical owner. Other documents summarize only what their
readers need and link to the owner.

| Document | Owns |
| --- | --- |
| `README.md` | The conceptual argument, the runnable example, current capabilities, related packages, and routing |
| `docs/schema.md` | The normative `meta.yaml` format, validation rules, and query behavior |
| `docs/authoring.md` | The workflow for adding, checking, and distributing assets |
| `docs/decisions/` | The reasons for durable design choices |
| `docs/documentation.md` | This guide |

## Examples

The README contains one complete example. It must run from the installed wheel, from
the repository root, and print exactly the output shown beneath it. CI extracts the
first `python` block and the following `text` block from the `Using the registry`
section and compares them. If that heading changes, update the extraction in
`.github/workflows/ci.yml` in the same commit.

## Verification

A documentation change is complete when

- the README example passes in CI from the installed wheel,
- every relative link and anchor resolves, and
- `uv run ruff format --check .` passes, which also formats Python code blocks in
  Markdown.

There are no figures yet. Add one only when it answers a question that prose would
make difficult to hold in mind, following ssrobot's figure conventions.
