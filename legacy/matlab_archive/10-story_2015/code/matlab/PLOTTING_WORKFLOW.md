# Rebar strain calculation and plotting

`Rebar_Strain.m` performs the existing data calculation and writes the same
Excel result. It also writes one sidecar `*.status.json` per case. A status is
`running` while processing and changes to `completed` only after the Excel
file has been written successfully.

`plot_rebar_strain_results.m` is independent of the calculation script. It
scans only status files, skips anything not marked `completed`, reads the
referenced Excel result, and calls the public `plot_style.m` exporter.

Typical use from the MATLAB project folder:

```matlab
Rebar_Strain
plot_rebar_strain_results([], 'paper')
% or
plot_rebar_strain_results([], 'ppt')
```

The plotting step produces matching PNG (600 dpi) and PDF files. It never
calls the calculation script or reads raw test CSV files.
