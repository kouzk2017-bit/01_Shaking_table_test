# 2015 MATLAB archive

Archived on 2026-07-30 after the raw-data-to-CSV Python workflow was verified.

- Original active path: `10-story_2015/code/matlab/`
- Archived path: `legacy/matlab_archive/10-story_2015/code/matlab/`
- Status: reference and numerical-baseline material only; not an active entry point.
- Historical MATLAB workbooks, figures, runtime state and raw data remain in their
  original project locations so that Python outputs can be checked against them.
- `manifest.sha256` records every archived source file.

The active replacement is `10-story_2015/code/python/run_pipeline.py`. It reads
`data/raw/` without modifying it, writes one CSV per physical quantity, and the
plotting stage reads those CSV files directly.

