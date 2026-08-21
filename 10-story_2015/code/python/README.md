# 2015 ten-story Python workflow

This is the active 2015 processing entry. Raw files under `data/raw/` are read
only. Results are written under `results/2015/<case>/` at the workspace root.

```powershell
python run_pipeline.py --list-cases
python run_pipeline.py --case 20
python run_pipeline.py --all-loading
python plot_from_csv.py --case 20
python run_pipeline.py --case 20 --then-plot
python validate_against_matlab.py --case 20
```

The calculation stage writes CSV files directly for floor acceleration, table
and foundation acceleration, story shear, story displacement/drift, absolute
and accumulated displacement, joint rotation, foundation sliding displacement,
and rebar strain. `plot_from_csv.py` reads only these CSV files; Excel, NPZ and
raw data are not plotting inputs. Use it by itself after changing figure format,
axes, colours or font sizes. `--then-plot` is only an explicit convenience for a
full raw-to-figure rerun.

Peak selection and figure appearance are kept in the shared
`common/config/plot_config.json`. The 2015
rule selects the four lowest local negative-drift peaks in 10--30 s, applies no
minimum time separation, and labels the selected samples A--D chronologically.
The contribution is `abs(joint rotation / story drift) * 100`. Each plot run
writes the exact samples to `csv/selected_peaks.csv` and source hashes to
`plot_metadata.json`. Optional manual times can be added per case and floor in
`manual_peak_times_s`.

```json
"manual_peak_times_s": {
  "20151211-2(JMAKobe100%)": {"4F": [13.03, 14.02, 15.68, 17.31]}
}
```

The implementation preserves the archived MATLAB FFT filtering, resampling,
manual correction, displacement-residual inheritance and eight-case rebar
residual inheritance rules. Historical MATLAB workbooks remain numerical
baselines in `results/archive/2026-07-30_before_cleanup/2015/spreadsheets/`.

All figures use `common/python/publication_style.py`. The default `paper`
mode exports a 600 dpi PNG and a vector PDF with the same geometry.
