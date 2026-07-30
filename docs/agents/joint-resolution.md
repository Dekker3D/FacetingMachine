# Joint resolution and build order

## Status

This is a design note, not the current implementation plan. The quill variable cleanup deliberately leaves the existing quill joint wiring and geometry unchanged.

## Why joints need a separate resolution stage

A joint is the compatibility layer between two endpoints. Some joints can be defined entirely from known measurements, such as the replacement quill fitting an off-the-shelf quill holder. Other joints need information from both endpoints to determine valid dimensions, shared axes, limits, and placements.

This creates a dependency problem if endpoint geometry is constructed immediately in each endpoint's constructor:

- The joint may need both endpoint specifications before it can resolve dimensions.
- Each endpoint should depend only on a generic joint-side interface, not on a concrete joint implementation.
- Building either endpoint before resolving the joint makes later changes difficult and risks stale cached geometry.

## Intended architecture

Use three distinct stages:

1. **Endpoint specification**
   - Select off-the-shelf parts and user-controlled design parameters.
   - Expose only the dimensional constraints relevant to a joint.
   - Do not construct CadQuery geometry yet.

2. **Joint resolution**
   - Give the concrete joint both endpoint specifications.
   - Calculate shared axes, allowable ranges, clearances, final interface dimensions, and transforms.
   - Reject incompatible endpoint combinations explicitly.
   - Produce a resolved generic interface for each endpoint.

3. **Geometry construction**
   - Construct each endpoint from its specification and its resolved joint-side interface.
   - Keep built geometry immutable and eagerly cached after resolution.

Conceptually:

```text
endpoint A specification --\
                            > concrete joint resolver -> resolved A/B interfaces
endpoint B specification --/                              |
                                                           v
                                                  build endpoint geometry
```

## Why not lazy-build mutable parts

Moving all geometry into a lazy `_build()` called from `get_object()` or `get_assembly()` would postpone construction, but it would also introduce mutable build state and cache-invalidation questions. A setting changed after the first build could leave `_object`, `_assembly`, exports, and the BOM inconsistent.

Separating specification, resolution, and construction solves the ordering problem while allowing the final parts to remain eagerly built and immutable.

## Off-the-shelf endpoints

A modeled endpoint is not required when the mating component is off-the-shelf. A lightweight endpoint specification containing the manufacturer's or measured interface dimensions is sufficient. The concrete joint can resolve against that specification without constructing the off-the-shelf holder.

For the current quill holder, fixed measured nub and shoulder dimensions may therefore remain inputs to the concrete holder-compatible joint. This special case should still produce the same generic resolved interface used by other joint implementations.

## Deferred decisions

Before implementing this architecture, decide:

- The minimal protocol exposed by endpoint specifications.
- The minimal generic interface returned to each endpoint.
- Whether a resolved joint is one object containing two views or two immutable side-specific objects.
- Which component owns fasteners and contributes them to the BOM.
- How joint validation reports incompatible dimension ranges.

Until those decisions are made, avoid further coupling the quill and holder classes to each other's concrete implementations.
