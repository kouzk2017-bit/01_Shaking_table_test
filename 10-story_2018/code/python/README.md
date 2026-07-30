# 2018 E-Defense 10-story Python processing

This directory processes only case 20: `20190109-2(JMAKobe100%)`.
Existing MATLAB files and MATLAB-generated results are not modified.

From this directory, run with Python 3 available in the active environment:

```powershell
python run_case20.py
```

The workflow is intentionally separated into calculation modules:

- `process_acceleration.py`: 1F--RF and table acceleration
- `process_story_shear.py`: 1F--10F story shear
- `process_story_drift.py`: story displacement, story drift, absolute displacement
- `process_joint_rotation.py`: JNT1--JNT6 rotations
- `plot_results.py`: six 4F/6F publication figures
- `export_tabular.py`: CSV tables and processing metadata
- `process_rebar_strain.py`: 4F/6F longitudinal-rebar strain calculation
- `plot_rebar_strain.py`: 4F/6F publication-style rebar-strain figures

All results are written below:

`../../results/python/20190109-2(JMAKobe100%)/`

## Legacy manual corrections retained

1. NW/SE horizontal acceleration replacement is applied only when their
   difference exceeds `1 m/s2`; the larger absolute value is replaced.
2. The old `j==3` acceleration interval around `18.398--18.998 s` is
   replaced with the corresponding `29.999 s` value for 2F--RF.
3. 8F NW bottom X displacement is replaced by 8F NW top X.
4. 10F SE bottom X displacement is replaced by 10F SE top X.
5. Story displacement uses the four-gauge NW/SE top/bottom average.
6. Story shear is low-pass filtered at 50 Hz before 100 Hz output.

## Rebar-strain treatment

1. Only case 20 is used; previous-case residual strain is not inherited because
   the earlier cases do not contain the same JB04/JB06 acquisition layout.
2. The mean of the first 1 s is subtracted independently from every channel.
3. No high-pass filter is applied, so the plastic residual-strain plateau is kept.
4. The legacy mirrored-FFT method resamples 1000 Hz data to 100 Hz.
5. Strain is normalized by the 2015 yield strain of 2000 microstrain.
6. All longitudinal candidates are exported; stirrup channels are excluded.
7. Publication plots currently use JB04 CH41/CH14 for the 4F beam/column and
   JB06 CH52/CH61 for the 6F beam/column. These choices were selected by matching
   peak timing and rise/fall direction and are editable in `config.py`.
