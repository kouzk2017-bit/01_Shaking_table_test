"""Run the complete 2018 case 20 processing workflow."""

from __future__ import annotations

from process_acceleration import process as process_acceleration
from process_joint_rotation import process as process_joint_rotation
from process_story_drift import process as process_story_drift
from process_story_shear import process as process_story_shear
from plot_results import process as plot_results
from export_tabular import process as export_tabular
from process_rebar_strain import process as process_rebar_strain
from plot_rebar_strain import process as plot_rebar_strain


def main() -> int:
    process_acceleration()
    process_story_shear()
    process_story_drift()
    process_joint_rotation()
    plot_results()
    export_tabular()
    process_rebar_strain()
    plot_rebar_strain()
    print("2018 case 20 processing completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
