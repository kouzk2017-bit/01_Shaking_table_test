"""When does each stage of the joint-yielding failure mechanism occur? Test vs shell vs solid.

Criteria follow Tsuji & Nagae (AIJ, "flexural yielding failure at RC beam-column
joints", 2015 4F joint): (1) column and beam bars yield in tension at the member
faces, (2) joint hoops yield, (3) through bars yield inside the joint, then the
joint takes a growing share of the story drift while the shear does not drop.
Diagnostic comparison of mechanisms, not the paused shell-vs-solid result set.

Both models use the 1119-step test-history protocol, so a step maps to the same
story drift in both. Face / interior nodes (identified 2026-10-05 from where each
bar's strain jumps; DIANA right = test west):

  solid  beam bottom 10380-10419 faces 10397/10402   beam top 10128-10167 faces 10145/10150
         left column 11145-11172 faces 11156 (bottom)/11162 (top), right 11285-11312 faces 11296/11302
         hoops: three layers 10061-10082 (top), 10083-10104 (middle), 10105-10126 (bottom), EXX + EYY
  shell  beam bottom 1606-1645 faces 1623/1628       beam top 1396-1435 faces 1413/1418
         left column 1829-1856 faces 1845 (bottom)/1839 (top), right 1969-1996 faces 1985/1979
         hoops: 2373-2408 (EXX, in-plane legs)

Test (2015 Kobe 100%, joint 4 = top of story 4 = 5F floor, column 2-A, the JNT4 joint): beam gauges
5G11-W01..05 and 5G21-E01..05 (JB06 ch15-24), upper column foot 5F2AC-01/02/08/09 (JB16 ch1-4), lower
column head 4F2AC-11/12/18/19 (JB06 ch11-14). Hoops and through
bars were not gauged.

Test joint diagonals: JNT pair JB11 ch7/ch8 (the pipeline's 4F joint; its labels match the
paper's 4F/6F joint ratios), read and filtered exactly as ten_story_pipeline.process_joint_rotation
but WITHOUT the 0.05 Hz high-pass for the diagonal strains: the high-pass removes the slowly
accumulating joint expansion (both diagonals lengthening), which is exactly what is compared here;
only the offset of the first 1000 samples is removed. The joint angle (difference of the two
diagonals) is cyclic and unaffected. Diagonal strain = displacement / 508.1 mm, the diagonal of the
286 x 420 mm anchor rectangle (anchors 107 mm from the column faces, 50 mm below the slab top,
80 mm above the beam bottom; paper Fig. 2 and the anchor memo). The pipeline's joint angle uses
a 270 x 270 mm square instead; that is checked here (same channels) but not changed.

Output: 06_results/comparison/failure_mechanism/mechanism_stages.csv (first yield
step/drift per group) and reversal_states.csv (state at each large reversal).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WORKSPACE = Path(__file__).resolve().parents[4]
JOINT = WORKSPACE / "05_joint_models"
sys.path.insert(0, str(JOINT / "diana_solid" / "code" / "python"))
sys.path.insert(0, str(WORKSPACE / "02_10-story_2015" / "code" / "python"))

from prepare_rebar_response import find_raw, load_export  # noqa: E402
sys.path.insert(0, str(WORKSPACE / "08_common" / "python"))
import final_cases  # noqa: E402
from survey_4f_joint_rebar_gauges import read_group  # noqa: E402
from workflow_config import CASES, SPEC  # noqa: E402
from ten_story_pipeline import DT, OUTPUT_DT, _time, read_channels  # noqa: E402
from legacy_signal import fft_filter, resample_decimate  # noqa: E402

YIELD_STRAIN = 0.002
OUTPUT = WORKSPACE / "06_results" / "comparison" / "failure_mechanism"
PROTOCOL = JOINT / "loading_protocols" / "2015_20151211-2(JMAKobe100%)_4F"
TEST_CSV = WORKSPACE / "06_results" / "experiment" / "2015" / "20151211-2(JMAKobe100%)" / "csv"
NODE = re.compile(r"node (\d+) element (\d+)")

# bar line: (raw prefix, face_a, face_b); interior = strictly between the faces
MODELS = {
    "solid": dict(
        raw=JOINT / "diana_solid" / "data" / "raw" / final_cases.case("solid"),
        processed=JOINT / "diana_solid" / "data" / "processed" / final_cases.case("solid"),
        shear_file="story_shear_response.csv", shear="column_e1783_shear_kN",
        beams=[("EXX_nodes_10380", 10397, 10402), ("EXX_nodes_10128", 10145, 10150)],
        columns=[("EZZ_nodes_11145", 11156, 11162), ("EZZ_nodes_11285", 11296, 11302)],
        hoops=["EXX_nodes_10061", "EXX_nodes_10083", "EXX_nodes_10105",
               "EYY_nodes_10061", "EYY_nodes_10083", "EYY_nodes_10105"],
    ),
    "shell": dict(
        raw=JOINT / "diana_shell" / "data" / "raw" / final_cases.raw("shell_history"),
        processed=JOINT / "diana_shell" / "data" / "processed" / final_cases.case("shell_history"),
        shear_file="cyclic_response.csv", shear="story_shear_kN",
        beams=[("EXX_nodes_1606", 1623, 1628), ("EXX_nodes_1396", 1413, 1418)],
        columns=[("EZZ_nodes_1829", 1839, 1845), ("EZZ_nodes_1969", 1979, 1985)],
        hoops=["EXX_nodes_2373"],
    ),
}


def bar_ratios(raw: Path, prefix: str) -> tuple[pd.DataFrame, dict[str, int]]:
    frame = load_export(find_raw(raw, prefix)).set_index("case_id")
    columns = {c: int(NODE.search(c).group(1)) for c in frame.columns if NODE.search(c)}
    return frame[list(columns)] / YIELD_STRAIN, columns


def group_max(raw: Path, lines, where: str) -> pd.Series:
    """Largest tensile strain ratio per step over the face nodes or the joint-interior nodes."""
    parts = []
    for prefix, face_a, face_b in lines:
        ratios, nodes = bar_ratios(raw, prefix)
        lo, hi = sorted((face_a, face_b))
        keep = [c for c, n in nodes.items() if (n in (face_a, face_b) if where == "face" else lo < n < hi)]
        parts.append(ratios[keep].max(axis=1))
    return pd.concat(parts, axis=1).max(axis=1)


def model_states(spec: dict) -> pd.DataFrame:
    shear = pd.read_csv(spec["processed"] / spec["shear_file"]).set_index("case_id")
    joint = pd.read_csv(spec["processed"] / "joint_deformation_angle.csv").set_index("load_step")
    diagonals = sorted({c.rsplit("_length", 1)[0] for c in joint.columns if c.endswith("_length_change_mm")})
    strain = {d: joint[f"{d}_length_change_mm"] / (joint[f"{d}_length_mm"] - joint[f"{d}_length_change_mm"]) for d in diagonals}
    hoops = pd.concat([bar_ratios(spec["raw"], p)[0].max(axis=1) for p in spec["hoops"]], axis=1).max(axis=1)
    out = pd.DataFrame({
        "column_face": group_max(spec["raw"], spec["columns"], "face"),
        "beam_face": group_max(spec["raw"], spec["beams"], "face"),
        "column_in_joint": group_max(spec["raw"], spec["columns"], "interior"),
        "beam_in_joint": group_max(spec["raw"], spec["beams"], "interior"),
        "hoop": hoops,
    })
    out["shear_kN"] = shear[spec["shear"]]
    out["joint_angle_rad"] = joint["deformation_angle_rad"]
    out["diag_max_strain"] = pd.concat(strain, axis=1).max(axis=1)
    out["diag_min_strain"] = pd.concat(strain, axis=1).min(axis=1)
    return out.dropna()


def test_stages(drift_t: np.ndarray, drift: np.ndarray) -> dict[str, float]:
    beam_t, beam = read_group(6, range(15, 25))
    upper_t, upper = read_group(16, range(1, 5))
    lower_t, lower = read_group(6, range(11, 15))
    groups = {"beam_face": (beam_t, beam), "column_face_upper": (upper_t, upper), "column_face_lower": (lower_t, lower)}
    first = {}
    for name, (t, gauges) in groups.items():
        window = (t >= 10.0) & (t <= 30.0)
        peak = np.max(np.vstack([g[window] for g in gauges.values()]), axis=0)
        hit = np.flatnonzero(peak >= 1.0)
        first[name] = t[window][hit[0]] if hit.size else np.nan
    return {k: float(np.interp(v, drift_t, drift)) if np.isfinite(v) else np.nan for k, v in first.items()} | {
        f"{k}_time_s": v for k, v in first.items()}


TEST_DIAGONAL_MM = float(np.hypot(500 - 2 * 107, 550 - 50 - 80))
PIPELINE_COEFFICIENT = np.sqrt(270.0**2 + 270.0**2) / (2 * 270.0 * 270.0)


def test_diagonals() -> pd.DataFrame:
    """4F joint diagonal displacements (JB11 ch7, ch8) as strains, on the 100 Hz pipeline time axis."""
    case = next(c for c in CASES if c.name == "20151211-2(JMAKobe100%)")
    raw = read_channels(SPEC, case, 11, range(7, 9))
    unfiltered = resample_decimate(raw - raw[:1000].mean(axis=0), DT, OUTPUT_DT)
    displacement = resample_decimate(fft_filter(raw, 1 / DT, (0.05, 100.0), "fft_BPF"), DT, OUTPUT_DT)
    frame = pd.DataFrame({"Time_s": _time(unfiltered.shape[0]),
                          "ch7_strain": unfiltered[:, 0] / TEST_DIAGONAL_MM,
                          "ch8_strain": unfiltered[:, 1] / TEST_DIAGONAL_MM})
    rotation = pd.read_csv(TEST_CSV / "joint_rotation.csv")["4F_rad"].to_numpy()
    rebuilt = PIPELINE_COEFFICIENT * (displacement[:, 0] - displacement[:, 1])
    n = min(rotation.size, rebuilt.size)
    if not np.allclose(rebuilt[:n], rotation[:n], atol=1e-6):
        raise ValueError("JNT ch7/ch8 do not reproduce joint_rotation.csv 4F; check the channel pair")
    return frame


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    steps = pd.read_csv(PROTOCOL / "load_steps.csv").set_index("step")
    reversals = pd.read_csv(PROTOCOL / "reversal_points.csv").iloc[1:9]
    stage_rows, state_rows = [], []
    for name, spec in MODELS.items():
        states = model_states(spec)
        for group in ("column_face", "beam_face", "hoop", "column_in_joint", "beam_in_joint"):
            hit = states.index[states[group] >= 1.0]
            step = int(hit[0]) if len(hit) else None
            stage_rows.append(dict(source=name, group=group, first_yield_step=step,
                                   drift_rad=steps.loc[step, "story_drift_rad"] if step else np.nan,
                                   leg=int(steps.loc[step, "leg"]) if step else None))
        for _, rev in reversals.iterrows():
            step = int(rev["end_step"])
            if step in states.index:
                row = states.loc[step]
                state_rows.append(dict(source=name, reversal=int(rev["index"]), step=step, drift_rad=rev["target_drift_rad"],
                                       V_over_Vmax=row["shear_kN"] / states["shear_kN"].abs().max(),
                                       joint_ratio=row["joint_angle_rad"] / rev["target_drift_rad"],
                                       diag_tension=row["diag_max_strain"], diag_compression=row["diag_min_strain"],
                                       column_face=row["column_face"], beam_face=row["beam_face"],
                                       column_in_joint=row["column_in_joint"], beam_in_joint=row["beam_in_joint"], hoop=row["hoop"]))
    drift = pd.read_csv(TEST_CSV / "story_drift_y.csv")
    test = test_stages(drift["Time_s"].to_numpy(), drift["4F_rad"].to_numpy())
    for group in ("column_face_upper", "column_face_lower", "beam_face"):
        stage_rows.append(dict(source="test", group=group, first_yield_step=None, drift_rad=test[group],
                               leg=None, time_s=test[f"{group}_time_s"]))
    diag = test_diagonals()
    diag.round(6).to_csv(OUTPUT / "test_joint_diagonal_strain.csv", index=False)
    shear = pd.read_csv(TEST_CSV / "story_shear_y.csv")
    angle = pd.read_csv(TEST_CSV / "joint_rotation.csv")
    t, x = drift["Time_s"].to_numpy(), drift["4F_rad"].to_numpy()
    vmax = shear["4F_kN"].abs().max()
    for _, rev in reversals.iterrows():
        window = np.flatnonzero(np.abs(t - rev["time_s"]) <= 0.15)
        k = window[np.argmax(np.abs(x[window]))]
        strains = [np.interp(t[k], diag["Time_s"], diag[c]) for c in ("ch7_strain", "ch8_strain")]
        state_rows.append(dict(source="test", reversal=int(rev["index"]), step=None, drift_rad=x[k],
                               V_over_Vmax=np.interp(t[k], shear["Time_s"], shear["4F_kN"]) / vmax,
                               joint_ratio=np.interp(t[k], angle["Time_s"], angle["4F_rad"]) / x[k],
                               diag_tension=max(strains), diag_compression=min(strains)))
    stages, states = pd.DataFrame(stage_rows), pd.DataFrame(state_rows)
    stages.round(4).to_csv(OUTPUT / "mechanism_stages.csv", index=False)
    states.round(4).to_csv(OUTPUT / "reversal_states.csv", index=False)
    pd.set_option("display.width", 250)
    print(stages.round(4).to_string(index=False))
    print(states.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
