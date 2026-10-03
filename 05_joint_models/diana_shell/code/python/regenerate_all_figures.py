"""Regenerate every DIANA cyclic-comparison figure package end to end.

One command rebuilds 05_joint_models/diana_shell/data/processed/ and every
06_results/diana/shell/*_comparison/ package from the raw exports under
05_joint_models/diana_shell/data/raw/. Run this any time raw data changes,
instead of re-typing the individual prepare/calculate/plot commands.

IMPORTANT (fonts): run this with a Python that has matplotlib resolving
"Times New Roman" -- i.e. your own Windows Python, not a Linux sandbox --
to get correctly-fonted PNGs. A Linux sandbox lacking that font will silently
fall back to DejaVu Serif; SVGs are unaffected either way (they only record
the font name, not its glyphs).

Usage (from the repo root, in your own PowerShell):
    python 05_joint_models\\diana_shell\\code\\python\\regenerate_all_figures.py
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[4]
CODE = WORKSPACE / "05_joint_models" / "diana_shell" / "code" / "python"
PROCESSED = WORKSPACE / "05_joint_models" / "diana_shell" / "data" / "processed"
RESULTS = WORKSPACE / "06_results" / "diana" / "shell"

# Joint-panel dimensions and 4-node layout confirmed 2026-09-04:
# a (horizontal) = 300 mm, b (vertical) = 366.67 mm, applies to ALL conditions.
# v2018 uses a different mesh's node numbers for the same physical layout.
JOINT_ANGLE_ARGS = {
    "origin": dict(input_dir="05_joint_models/diana_shell/data/raw/origin_2015", ul=623, ur=620, ll=639, lr=636),
    "origin_history": dict(input_dir="05_joint_models/diana_shell/data/raw/origin_2015_history", ul=623, ur=620, ll=639, lr=636),
    # Remeshed slab model: its measuring frame is 375 x 361.42 mm.
    "origin_history_slab": dict(input_dir="05_joint_models/diana_shell/data/raw/origin_2015_history_slab", ul=242, ur=248, ll=278, lr=279, a=375.0, b=361.42, suffix="242_248_278_279"),
    "j16_l":  dict(input_dir="05_joint_models/diana_shell/data/raw/J16-L",       ul=623, ur=620, ll=639, lr=636),
    "j12_h":  dict(input_dir="05_joint_models/diana_shell/data/raw/J12-H",       ul=623, ur=620, ll=639, lr=636),
    "j12_m":  dict(input_dir="05_joint_models/diana_shell/data/raw/J12-M",       ul=623, ur=620, ll=639, lr=636),
    "j16_m":  dict(input_dir="05_joint_models/diana_shell/data/raw/J16-M",       ul=623, ur=620, ll=639, lr=636),
    "j16_h":  dict(input_dir="05_joint_models/diana_shell/data/raw/J16-H",       ul=623, ur=620, ll=639, lr=636),
    "v2018":  dict(input_dir="05_joint_models/diana_shell/data/raw/origin_2018", ul=840, ur=837, ll=852, lr=849),
}
A_MM = 300.0
B_MM = 366.67

COMPARISONS = [
    dict(output="j16_l_comparison", baseline="origin", baseline_label="Original", variant="j16_l", variant_label="J16-L"),
    dict(output="j12_h_comparison", baseline="origin", baseline_label="Original", variant="j12_h", variant_label="J12-H"),
    dict(output="j12_m_comparison", baseline="origin", baseline_label="Original", variant="j12_m", variant_label="J12-M"),
    dict(output="j16_m_comparison", baseline="origin", baseline_label="Original", variant="j16_m", variant_label="J16-M"),
    dict(output="j16_h_comparison", baseline="origin", baseline_label="Original", variant="j16_h", variant_label="J16-H"),
    dict(output="v2018_vs_j16h_comparison", baseline="j16_h", baseline_label="J16-H", variant="v2018", variant_label="2018 Validation"),
]


def run(*args: str | Path) -> None:
    printable = " ".join(str(a) for a in args)
    print(f"+ {printable}")
    subprocess.run([sys.executable, *[str(a) for a in args]], check=True, cwd=WORKSPACE)


def write_filtered_registry(output_dir: Path, condition_codes: set[str]) -> None:
    source = RESULTS / "curve-source-registry.csv"
    with source.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames
        rows = [row for row in reader if row["工况代码"] in condition_codes]
    with (output_dir / "curve-source-registry.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows: {output_dir / 'curve-source-registry.csv'}")


def main() -> int:
    run(CODE / "prepare_cyclic_comparison_data.py", "--dry-run")
    run(CODE / "prepare_cyclic_comparison_data.py")

    for code, cfg in JOINT_ANGLE_ARGS.items():
        run(
            CODE / "calculate_joint_deformation_angle.py",
            "--input-dir", cfg["input_dir"],
            "--output", PROCESSED / code / "joint_deformation_angle.csv",
            "--a-mm", cfg.get("a", A_MM), "--b-mm", cfg.get("b", B_MM),
            "--upper-left", cfg["ul"], "--upper-right", cfg["ur"],
            "--lower-left", cfg["ll"], "--lower-right", cfg["lr"],
            *(("--node-file-suffix", cfg["suffix"]) if "suffix" in cfg else ()),
        )

    for comparison in COMPARISONS:
        output_dir = RESULTS / comparison["output"]
        output_dir.mkdir(parents=True, exist_ok=True)
        run(
            CODE / "plot_cyclic_comparison.py",
            "--output-directory", output_dir,
            "--baseline", comparison["baseline"], "--baseline-label", comparison["baseline_label"],
            "--variant", comparison["variant"], "--variant-label", comparison["variant_label"],
        )
        run(
            CODE / "plot_joint_deformation_angle.py",
            "--output-dir", output_dir,
            "--baseline", comparison["baseline"], "--baseline-label", comparison["baseline_label"],
            "--variant", comparison["variant"], "--variant-label", comparison["variant_label"],
        )
        write_filtered_registry(output_dir, {comparison["baseline"], comparison["variant"]})

    print("\nDone. PNG fonts match whichever Python ran this -- run it with your "
          "own Windows Python (not a Linux sandbox) for correct-font PNGs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
