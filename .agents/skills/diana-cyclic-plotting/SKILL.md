---
name: diana-cyclic-plotting
description: "Process DIANA cyclic-loading CSV exports and compare any selected variant condition against the origin baseline, including four-node joint deformation angle. Use for this project's DIANA beam/column strain, story-shear, and specified joint-node displacement data; do not use for unrelated DIANA export schemas."
---

# Diana Cyclic Plotting

Use this skill for the DIANA data workflow in this repository. Raw exports stay
under `diana/data/raw/` and are never edited. Plotting reads only the standardized
files under `diana/data/processed/`.

## Reusable condition workflow

- `origin` is the sole baseline condition. Each requested variant is compared only with `origin`; do not alter the skill when another variant is added.
- Keep raw exports in `diana/data/raw/<folder>/` unchanged. Write reproducible outputs under `diana/data/processed/<condition_code>/`.
- On each new variant, inspect every CSV header and all Load-step rows. Infer the unique `NX` export as story shear, the unique `EZZ` export as column longitudinal strain, and the `TDtX`/`TDtZ` pair as joint displacement data.
- For multiple `EXX` exports, infer beam versus joint-stirrup use only when the headers or the established baseline mapping make it unambiguous. If it remains ambiguous, stop and ask the user for the mapping; never guess.
- Derive a short English condition code and display label from the folder name. Use title case in legends (for example, `changed_column_longitudinal_rebar` → `Changed Column Rebar`). Ask only when the translation would be materially ambiguous.
- Exclude case IDs 1–10. Derive story drift as `load factor * 0.005 rad`, convert story shear from N to kN, and normalize steel strain by 0.002.
- Verify every populated response column over every Load-step. Retain the first only when all populated alternatives are exactly identical; otherwise request an explicit mapping.

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
  raw exports. Use the selected variant's node exports; when they are absent, request their location rather than substituting another condition.

When plotting joint deformation angle, exclude load steps 1--10 and verify its
remaining load-step range matches `cyclic_response.csv`. Write two figures to
the same `results/diana/<comparison-name>/` directory used by the cyclic-response figures: joint angle versus analysis step, and
joint angle (solid) versus story drift (dashed). Both figures overlay the
`origin` and the selected variant condition, use radian units, and export SVG
and 600 dpi PNG.

Run `diana/code/python/prepare_cyclic_comparison_data.py --dry-run` before any
processing change. Run it without `--dry-run` to produce standardized `cyclic_response.csv` files. It does not generate figures.

## Curve-source registry

Every non-dry processing run must refresh `results/diana/cyclic_axial_force_comparison/curve-source-registry.csv`. It is a filterable CSV and records, for both conditions, each plotted response's raw CSV, selected response column, node and element identifiers, duplicate-column verification, case-ID filter, output CSV, and unit/normalization or derived-value rules. Do not hand-edit it or reuse a stale mapping.

## Plotting requirements

When the user asks for figures, compare `origin` with the selected variant condition. Generate story shear versus story drift, beam longitudinal-strain ratio versus analysis step, column longitudinal-strain ratio versus analysis step, per-condition beam-versus-column strain figures, and joint-stirrup strain when its mapping is available.

Keep the two compared conditions on identical axes, exclude the first ten axial-load cases, and export SVG plus 600 dpi PNG to one shared `results/diana/<variant_code>_comparison/` directory. This directory is the complete result package for one variant: do not split it by figure type, and do not encode the condition name in individual figure stems. Pass that exact directory to both plotting commands. Use the existing sequence: `01`–`06` for cyclic-response figures, `07_joint_deformation_angle_by_step`, and `08_joint_deformation_angle_vs_story_drift`. Include a `curve-source-registry.csv` containing only `origin` and the selected variant. Use integer strain-ratio ticks and yield reference lines at -1 and +1. Use upright subscripts in $\epsilon_{\mathrm{s}}/\epsilon_{\mathrm{y}}$ and label the x-axis `Analysis step`.

Read [the source and output schema](references/data_contract.md) before selecting mappings, deriving outputs, or plotting.
