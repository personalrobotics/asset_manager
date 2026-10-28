# Authoring assets

This guide describes how to add an object and how to distribute a collection of
objects. The format itself is specified in [the schema](schema.md).

## Adding an object

Create a directory named after the object, containing the simulator model and a
`meta.yaml`:

```
objects/
└── cup/
    ├── meta.yaml
    └── mujoco_cup.xml
```

Start `meta.yaml` with the fields the registry interprets:

```yaml
name: cup
category: [kitchenware, container]
mujoco:
  xml_path: mujoco_cup.xml
perception:
  aliases: ["mug", "coffee cup"]
```

Choose aliases from the labels your detectors actually produce. A label may identify
only one object in a registry. If two objects could reasonably be called "bin", give
each a more specific alias rather than sharing one.

Add any sections your consumers need, such as `policy` or `safety`. The registry
stores them unchanged. The consumer that reads a section owns its format and its
validation.

## Checking an object

Construct a registry over the collection with the default settings:

```sh
uv run python -c "from asset_manager import AssetManager; AssetManager('objects').summary()"
```

Construction fails with a message naming the file if an interpreted field is malformed,
a model file is missing, or a label is ambiguous. A successful summary lists every
object with its categories and model paths.

Then load each model in the simulator that will use it, and check that any
`dimensions` you declare agree with the model's geometry. The registry does not
inspect model files.

## Distributing a collection

A collection of objects is an ordinary Python package that ships its object
directories as package data and exposes their location.
[prl_assets](https://github.com/personalrobotics/prl_assets) is the reference:

```python
from asset_manager import AssetManager
from prl_assets import OBJECTS_DIR

registry = AssetManager(OBJECTS_DIR)
```

Locate the directory relative to the package's own `__init__.py`, and check that it is
present in the built wheel, not only in a source checkout.
