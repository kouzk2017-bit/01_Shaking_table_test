# DIANA cyclic comparison data contract

## Source files

Each condition directory under `diana/data/raw/` contains:

- a beam longitudinal-strain CSV;
- a column longitudinal-strain CSV;
- a story-shear CSV.

DIANA exports a first units row after the column headers. Ignore it and retain
only rows whose `case label` starts with `Load-step`.

The first ten case IDs are the axial-force application stage. They are excluded
from cyclic-response tables and figures.

For every export, identify all populated response columns and compare them over
every Load-step before selecting a response. If they are exactly identical,
record the first as the canonical response and treat the rest as duplicate
instrumentation. If any value differs, preserve the raw file and require an explicit
mapping.

## Derived columns

| Output column | Definition | Unit |
| --- | --- | --- |
| `case_id` | DIANA case ID; parse `Load-step N` when absent | - |
| `load_factor` | DIANA load factor | - |
| `story_drift_rad` | `load_factor * 0.025` | rad |
| `story_shear_kN` | first populated shear response / 1000 | kN |
| `beam_strain_over_0p002` | first populated beam strain / 0.002 | - |
| `column_strain_over_0p002` | first populated column strain / 0.002 | - |

The 0.025 rad scale equals 65.625 mm / 2625 mm. Equivalently, each 0.1
load-factor increment represents 6.5625 mm and 0.0025 rad.

## Figure outputs

Generate five comparison figures: story shear versus story drift, beam
longitudinal strain ratio versus analysis step, column longitudinal strain ratio
versus analysis step, and separate beam-versus-column strain comparisons for the
original and reduced-axial-force conditions.
Export each as SVG for PowerPoint and 600 dpi PNG for paper layout; do not
produce PDF unless the user explicitly asks. Use y-axis ticks at 1.0 increments
for every strain figure and highlight the $-1$ and $+1$ yield-ratio lines.

## Integrity checks

- Both conditions must have the same cyclic case-ID range before overlaying.
- Fail if a required response is blank or a case ID is duplicated.
- Preserve the raw exports and treat `data/processed/` as reproducible output.
