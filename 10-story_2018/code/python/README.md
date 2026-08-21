# 2018 ten-story Python workflow

`run_pipeline.py` is the active entry for all ten raw-data-complete loading
cases. Raw files under `data/raw/` are read only. Results are written under
the workspace-level `results/2018/<case>/` directory.

```powershell
python run_pipeline.py --list-cases
python run_pipeline.py --case 20
python run_pipeline.py --all-loading
python plot_from_csv.py --case 20
python run_pipeline.py --case 20 --then-plot
python validate_against_matlab.py --case 20
```

The calculation stage writes CSV files directly for floor/table acceleration,
story shear, story displacement/drift, absolute and accumulated displacement,
joint rotation and, where JB04/JB05/JB06 exist, rebar strain. `plot_from_csv.py`
reads only CSV files; raw data, Excel and NPZ files are not plotting inputs. Use
it by itself after changing figure format, axes, colours or font sizes.
`--then-plot` is only an explicit convenience for a full raw-to-figure rerun.
All plotting entries share `common/python/publication_style.py`; the default
`paper` mode writes matching 600 dpi PNG and vector PDF files.

Peak selection and figure appearance are kept in the shared
`common/config/plot_config.json`. The 2018
rule selects the four highest local positive-drift peaks in 10--30 s, applies no
minimum time separation, and labels the selected samples A--D chronologically.
The contribution is `abs(joint rotation / story drift) * 100`. Each plot run
writes the exact samples to `csv/selected_peaks.csv` and source hashes to
`plot_metadata.json`. Optional manual times can be added per case and floor in
`manual_peak_times_s`.

```json
"manual_peak_times_s": {
  "20190109-2(JMAKobe100%)": {"4F": [13.00, 14.00, 16.00, 18.00]}
}
```

Case 20 deterministic outputs match the archived MATLAB workbooks. Its old
accumulated-displacement sheets used a stale `residual_disp_7.mat` that differs
from the current MATLAB algorithm from the first loading case. The Python
workflow therefore rebuilds the residual chain from raw data and records the
historical state mismatch in `validation_against_matlab.json`.

The older `run_case20.py` modules remain temporarily for provenance of earlier
Python results, but they are not the formal workflow.
