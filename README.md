# asset_manager

A physical object used in robotics research appears in several systems at once. A
simulator needs its model file, a perception pipeline needs the labels a detector may
assign to it, and a planner or policy may need its category, mass, or other task
metadata. When each system keeps its own description, the descriptions drift apart: a
renamed file breaks one consumer, and a detector label that one system understands is
unknown to the next.

asset_manager keeps one description of each object and answers the questions those
systems share. It indexes a directory of assets, checks the fields it interprets,
resolves simulator model paths, and maps detector labels to canonical asset names.

The scope is intentionally narrow. asset_manager is not an asset collection, a scene
builder, a simulator loader, or a perception system. It defines the metadata format
and the registry that those packages share.

## Asset directories

An asset is a directory containing a `meta.yaml` file and the files it refers to,
such as a MuJoCo model. The model file remains authoritative for geometry, inertia,
and contacts. `meta.yaml` adds what the model format does not express uniformly: a
canonical name, categories, the labels perception may use, and the location of each
simulator's model.

```yaml
name: cup
category: [kitchenware, container, fragile]
mass: 0.15
dimensions: [0.08, 0.08, 0.12]
mujoco:
  xml_path: mujoco_cup.xml
perception:
  aliases: ["mug", "red cup", "coffee cup"]
policy:
  grasping:
    preferred_grasp_type: top_down
```

The exact format is specified in [the schema](docs/schema.md).

## The registry

`AssetManager` walks a base directory and indexes every directory that contains a
`meta.yaml`. Indexing is where problems are reported. A malformed interpreted field, a
missing model file, a duplicate name, or a label that would name two assets raises an
error that identifies the file. A registry that was constructed successfully can
therefore answer queries without further checks.

Queries return copies. Changing the metadata returned by `get()` does not change the
registry, so one registry can be shared safely among several consumers.

## Sections and their owners

The registry interprets a small set of fields: `name`, `category`, the simulator
sections `mujoco` and `isaac`, and `perception.aliases`. Every other field or section,
such as `policy`, `safety`, or `rendering`, belongs to the consumer that reads it. The
registry stores and returns those sections unchanged and does not check their
contents. A new consumer can therefore add its own section without changing this
package, but it is responsible for validating that section itself.

## Perception labels

A detector reports labels such as "mug" or "soda can", while the rest of the system
refers to objects by canonical names. `resolve_alias` maps a label to the asset whose
canonical name or `perception.aliases` list contains it, ignoring case.

Each label must identify at most one asset. The registry refuses, while indexing, an
alias listed by two assets and an alias equal to another asset's name. Resolution is
then a single lookup whose answer does not depend on the order in which directories
were visited. The reasons for a single flat alias list rather than one list per
detector are recorded in [a decision record](docs/decisions/0001-flat-perception-aliases.md).

## Using the registry

From a clone, [uv](https://docs.astral.sh/uv/) installs the package and its
development tools:

```sh
git clone https://github.com/personalrobotics/asset_manager
cd asset_manager
uv sync
```

The following example indexes the sample objects in `data/objects`, queries them by
category, resolves two detector labels, and finds a MuJoCo model:

```python
from pathlib import Path

from asset_manager import AssetManager

registry = AssetManager("data/objects")
print(registry.list())
print(registry.by_category("kitchenware"))
print(registry.resolve_alias("Red Cup"), registry.resolve_alias("dish"))
print(Path(registry.get_path("cup", "mujoco")).relative_to(Path.cwd()))
```

Run it with `uv run python` from the repository root. It prints:

```text
['bottle', 'bowl', 'box', 'cup', 'fork', 'knife', 'plate']
['bottle', 'bowl', 'cup', 'plate']
cup plate
data/objects/cup/mujoco_cup.xml
```

CI runs this example from the built wheel and compares its output with the text above.
The sample objects are part of the repository, not the installed package. Their
physical and task metadata is illustrative rather than measured. A fuller tour is in
`demos/full_capabilities.py`.

## Current capabilities

| Capability | Status | Details |
| --- | --- | --- |
| Index asset directories and validate interpreted fields | Implemented | [Schema](docs/schema.md) |
| MuJoCo model paths, checked while indexing | Implemented; used by mj_environment with prl_assets | [Schema](docs/schema.md#simulator-sections) |
| Isaac model paths | Path lookup and existence check only; no Isaac consumer exists yet | [Schema](docs/schema.md#simulator-sections) |
| Perception label resolution | Implemented; used by mj_manipulator's `SimPerceptionService` | [Schema](docs/schema.md#perception) |
| Category queries | Implemented | [Schema](docs/schema.md#interpreted-fields) |
| Consumer sections such as `policy` or `safety` | Stored and returned unchanged; not interpreted | [Schema](docs/schema.md#consumer-sections) |
| ROS, Gazebo, or URDF model paths | Not supported | |

## Related packages

| Package | Owns |
| --- | --- |
| asset_manager | The `meta.yaml` format, indexing, validation, and label resolution |
| [prl_assets](https://github.com/personalrobotics/prl_assets) | The reusable objects used by the lab's robots |
| [mj_environment](https://github.com/personalrobotics/mj_environment) | Building MuJoCo scenes from indexed assets |
| [mj_manipulator](https://github.com/personalrobotics/mj_manipulator) | Perception services that resolve detector labels |

## Documentation

| Task | Document |
| --- | --- |
| Write or check a `meta.yaml` precisely | [Schema](docs/schema.md) |
| Add an asset or publish a package of assets | [Authoring assets](docs/authoring.md) |
| Change the documentation | [Documentation guide](docs/documentation.md) |

## License

MIT. See [LICENSE](LICENSE).
