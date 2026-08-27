# DIANA cyclic comparison data contract

## Source files

Each condition directory under `diana/data/raw/` contains:

- a beam longitudinal-strain CSV;
- a column longitudinal-strain CSV;
- a story-shear CSV.

`origin` is the fixed baseline. Process one selected variant at a time and compare it only with `origin`; additional variants do not require a skill change. Use a short English condition code and title-case display label derived from the variant folder name.

DIANA exports a first units row after the column headers. Ignore it and retain
only rows whose `case label` starts with `Load-step`.

The first ten case IDs are the axial-force application stage. They are excluded
from cyclic-response tables and figures.

For every export, identify all populated response columns and compare them over
every Load-step before selecting a response. If they are exactly identical,
record the first as the canonical response and treat the rest as duplicate
instrumentation. If any value differs, preserve the raw file and require an explicit
mapping.

## Curve-source registry

`prepare_cyclic_comparison_data.py` regenerates `results/diana/cyclic_axial_force_comparison/curve-source-registry.csv` on every non-dry processing run after validating the current raw exports. The filterable registry is the maintained record of each curve's selected response, node/element metadata, duplicate-column status, case-ID filter, output CSV, and conversion or normalization.

## Derived columns

| Output column | Definition | Unit |
| --- | --- | --- |
| `case_id` | DIANA case ID; parse `Load-step N` when absent | - |
| `load_factor` | DIANA load factor | - |
| `story_drift_rad` | `load_factor * 0.005` | rad |
| `story_shear_kN` | first populated shear response / 1000 | kN |
| `beam_strain_over_0p002` | first populated beam strain / 0.002 | - |
| `column_strain_over_0p002` | first populated column strain / 0.002 | - |

The 0.005 rad scale equals 65.625 mm / 2625 mm. Equivalently, each 0.1
load-factor increment represents 1.3125 mm and 0.0005 rad.

## Figure outputs

For `origin` and the selected variant, generate story shear versus story drift, beam longitudinal-strain ratio versus analysis step, column longitudinal-strain ratio versus analysis step, and separate beam-versus-column strain figures.
Export every figure as SVG for PowerPoint and 600 dpi PNG for paper layout to the same `results/diana/<comparison-name>/` directory, including joint-deformation-angle figures; do not create a joint-angle subfolder or produce PDF unless the user explicitly asks. Use y-axis ticks at 1.0 increments
for every strain figure and highlight the $-1$ and $+1$ yield-ratio lines.

## Comparison result package

Each `results/diana/<variant_code>_comparison/` directory is a complete, self-contained comparison package. Keep all numbered figures (01–08) and a `curve-source-registry.csv` filtered to `origin` plus that variant in this directory. Do not create a figure-type subfolder or add the variant name to individual figure filenames.

## Integrity checks

- `origin` and the selected variant must have the same cyclic case-ID range before overlaying.
- Fail if a required response is blank or a case ID is duplicated.
- Preserve the raw exports and treat `data/processed/` as reproducible output.
