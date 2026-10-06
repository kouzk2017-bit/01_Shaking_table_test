"""One command to (re)build everything for a joint-model case after exporting it from DIANA.

    python 05_joint_models/update_case.py --model solid --case <folder under diana_solid/data/raw>
    python 05_joint_models/update_case.py --model shell
    python 05_joint_models/update_case.py --ppt-only

solid: raw -> processed (prepare_rebar_response, joint angle) -> its own result pack
       (06_results/diana/solid/<case>) -> comparison with the test (history protocol: response-vs-drift
       figures and time histories in 06_results/comparison/test_vs_solid/...; standard: response-vs-drift).
shell: regenerate_all_figures.py rebuilds every registered shell condition. A NEW shell case must first be
       registered (node numbers differ per mesh) in diana_shell/code/python/prepare_cyclic_comparison_data.py
       (CONDITIONS) and regenerate_all_figures.py (JOINT_ANGLE_ARGS).
Afterwards, if a final case (final_cases.json) was touched, the failure-mechanism summary is rebuilt;
--ppt also refreshes the PPT folder. Solid exports must sit in diana_solid/data/raw/<case>/ (not raw/ itself).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
JM = PROJECT / "05_joint_models"
sys.path.insert(0, str(PROJECT / "08_common" / "python"))
import final_cases  # noqa: E402

PY = JM / "comparison" / "code" / "python"
SOLID_PY = JM / "diana_solid" / "code" / "python"
SOLID_CORNERS = ["--a-mm", "300", "--b-mm", "366.67", "--upper-left", "3149", "--upper-right", "3152",
                 "--lower-left", "3165", "--lower-right", "3168", "--node-file-suffix", "3149_3152_3165_3168"]


def run(*args) -> None:
    print("+", " ".join(str(a) for a in args), flush=True)
    subprocess.run([sys.executable, *map(str, args)], check=True, cwd=PROJECT)


def update_solid(case: str, protocol: str) -> None:
    raw = JM / "diana_solid" / "data" / "raw" / case
    if not raw.is_dir():
        sys.exit(f"No export folder {raw}; put the DIANA CSVs in diana_solid/data/raw/{case}/")
    processed = JM / "diana_solid" / "data" / "processed" / case
    run(SOLID_PY / "prepare_rebar_response.py", "--partial", "--input-dir", raw, "--output-dir", processed)
    run(JM / "diana_shell" / "code" / "python" / "calculate_joint_deformation_angle.py", "--input-dir", raw,
        "--output", processed / "joint_deformation_angle.csv", *SOLID_CORNERS)
    run(SOLID_PY / "plot_solid_results.py", "--case", case)
    run(PY / "plot_experiment_vs_model_joint_drift.py", "--model", "solid", "--protocol", protocol,
        "--diana-condition", case, "--diana-label", f"DIANA solid, {case}")
    if protocol == "history":
        run(PY / "plot_solid_history_vs_test.py", "--case", case)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", choices=("solid", "shell"))
    parser.add_argument("--case", help="solid case folder name")
    parser.add_argument("--protocol", choices=("standard", "history"),
                        help="loading protocol of the run (default: 'history' if the case name contains it)")
    parser.add_argument("--ppt", action="store_true", help="also refresh the PPT folder")
    parser.add_argument("--ppt-only", action="store_true")
    args = parser.parse_args()

    finals = {final_cases.case("solid"), final_cases.case("shell_history")}
    touched_final = False
    if not args.ppt_only:
        if args.model == "solid":
            if not args.case:
                sys.exit("--case is required for --model solid")
            update_solid(args.case, args.protocol or ("history" if "history" in args.case else "standard"))
            touched_final = args.case in finals
        elif args.model == "shell":
            run(JM / "diana_shell" / "code" / "python" / "regenerate_all_figures.py")
            touched_final = True
        else:
            sys.exit("give --model solid|shell, or --ppt-only")
        if touched_final:
            run(PY / "failure_mechanism_summary.py")
    if args.ppt or args.ppt_only:
        run(PROJECT / "07_scripts" / "presentation" / "collect_joint_figures.py")
    print("Done. Update STATUS.md if this case changes a conclusion.")


if __name__ == "__main__":
    main()
