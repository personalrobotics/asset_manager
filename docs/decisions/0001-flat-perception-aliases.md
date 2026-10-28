# 0001: One flat alias list per asset

## Context

The original format nested aliases by perception system, for example
`perception.ycb.aliases` and `perception.coco.aliases`, and `resolve_alias` required
the caller to name the system. In practice the consumers did not know, or care, which
detector produced a label. mj_manipulator's `SimPerceptionService` resolves whatever
label it receives, and prl_assets declared a single list from the start. Keeping the
nested form meant every caller had to pick a module, and a label listed under another
module silently failed to resolve.

## Decision

Each asset declares one list, `perception.aliases`. `resolve_alias(label)` takes only
the label. The change was made in #2.

Because every detector vocabulary now shares one namespace per registry, a label that
could identify two assets is refused while indexing rather than resolved by
traversal order.

## Consequences

- A caller cannot restrict resolution to one detector's vocabulary. If that becomes
  necessary, it should be added as a filter over the flat list, not as a return to
  per-module lists.
- Per-detector settings, such as dataset identifiers or confidence thresholds, are no
  longer interpreted. They may be kept elsewhere under `perception` as consumer data.
- Collections written in the nested form must be converted. Their nested aliases are
  ignored, not reported.
