---
name: diana-cyclic-plotting
description: "Process DIANA cyclic-loading CSV exports and prepare original-versus-reduced-axial-force comparison plots, including four-node joint deformation angle. Use for this project's DIANA beam/column strain, story-shear, and specified joint-node displacement data; do not use for unrelated DIANA export schemas."
---

# Diana Cyclic Plotting

Use this skill for the DIANA data workflow in this repository. Raw exports stay
under `diana/data/raw/` and are never edited. Plotting reads only the standardized
files under `diana/data/processed/`.

## Current data contract

- Conditions: `origin` and `50pct_axial_force`.
- Each condition has one story-shear CSV plus beam and column longitudinal-strain
  CSV exports.
- Omit case IDs 1--10 because they apply axial force.
- For all later records, derive story drift as
  `load factor * 0.005 rad`. This follows 1.3125 mm per 0.1 load-factor increment
  and a 2625 mm story height.
- For every exported CSV, identify all populated response columns and verify them
  over every Load-step before selecting a response. If they are exactly
  identical, treat them as duplicate instrumentation and retain the first column.
  Stop and request an explicit mapping if any values differ. Normalize beam and
  column strain by 0.002.
- Convert DIANA story shear from N to kN.
## Four-node joint deformation angle

For the joint displacement exports named `TDtX_nodes_620_623_636_639.csv` and
`TDtZ_nodes_620_623_636_639.csv`, use the layout 623 upper-left, 620 upper-right,
639 lower-left, and 636 lower-right. The diagonals are 623--636 and 620--639.

- Use `a = b = 350 mm` unless the user explicitly supplies other dimensions.
- At each load step, calculate the requested diagonal instrument reading as
  `sqrt((ux_b - ux_a)^2 + (uz_b - uz_a)^2)`.
- Calculate joint deformation angle as
  `sqrt(a^2 + b^2) / (2*a*b) * (reading_623_636 - reading_620_639)` in rad.
- Also retain deformed diagonal lengths and signed length changes as diagnostic
  values; a positive length change is extension and a negative value is
  shortening.
- Write the derived table to
  `diana/data/processed/<condition>/joint_deformation_angle.csv`; never modify
  raw exports. The `50pct_axial_force` node exports currently reside under its
  processed directory and may be read from there when no raw copy is present.

When plotting joint deformation angle, exclude load steps 1--10 and verify its
remaining load-step range matches `cyclic_response.csv`. Write two figures to
`results/diana/joint_deformation_angle/`: joint angle versus analysis step, and
joint angle (solid) versus story drift (dashed). Both figures overlay the
`origin` and `50pct_axial_force` conditions, use radian units, and export SVG
and 600 dpi PNG.

Run `diana/code/python/prepare_cyclic_comparison_data.py --dry-run` before any
processing change. Run it without `--dry-run` to produce the two standardized
`cyclic_response.csv` files. It does not generate figures.

## Curve-source registry

Every non-dry processing run must refresh `results/diana/cyclic_axial_force_comparison/curve-source-registry.csv`. It is a filterable CSV and records, for both conditions, each plotted response's raw CSV, selected response column, node and element identifiers, duplicate-column verification, case-ID filter, output CSV, and unit/normalization or derived-value rules. Do not hand-edit it or reuse a stale mapping.

## Plotting requirements

When the user asks for figures, make one overlaid original-versus-reduced-axial-force
comparison for each of the following:

1. story shear (kN) versus story drift (rad);
2. beam longitudinal strain divided by 0.002 versus case ID;
3. column longitudinal strain divided by 0.002 versus case ID.
4. beam and column strain ratios in separate figures for each condition;

Keep the two conditions on identical axes within each figure. Do not include the
first ten axial-load cases. Write figures only to `results/diana/<comparison-name>/`
as SVG (PPT) and 600 dpi PNG (paper), leaving inputs untouched.

For every strain figure, use integer y-axis ticks at an interval of 1 and show
the yield reference lines at -1 and +1, rather than emphasizing the zero line.
Use upright subscripts in $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$, label the x-axis
only `Analysis step`, and use only lettered panel labels.

Read [the source and output schema](references/data_contract.md) before changing
input mapping, derived values, or plotting semantics.
