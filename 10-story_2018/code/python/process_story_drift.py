"""Calculate 2018 story displacement and story drift using four gauges."""

from __future__ import annotations

import numpy as np

from config import (
    DATA_DIRECTORY,
    DT,
    NW_BOTTOM_X_REPLACE_STORY,
    OUTPUT_DT,
    SE_BOTTOM_X_REPLACE_STORY,
    STORY_HEIGHTS_MM,
)
from io_utils import read_channels, save_npz
from legacy_signal import resample_decimate


def process() -> dict[str, np.ndarray]:
    jb7 = read_channels(7, (50, 51, 52, 53))
    jb10 = read_channels(10, tuple(range(29, 65)))
    jb12 = read_channels(12, tuple(range(1, 41)))

    nw_top_x = np.column_stack((jb7[:, 0], jb10[:, 0::4]))
    nw_bottom_x = np.column_stack((jb7[:, 1], jb10[:, 1::4]))
    nw_top_y = np.column_stack((jb7[:, 2], jb10[:, 2::4]))
    nw_bottom_y = np.column_stack((jb7[:, 3], jb10[:, 3::4]))
    se_top_x, se_bottom_x = jb12[:, 0::4], jb12[:, 1::4]
    se_top_y, se_bottom_y = jb12[:, 2::4], jb12[:, 3::4]

    # Old 100% (j==3) manual channel replacements.
    nw_bottom_x[:, NW_BOTTOM_X_REPLACE_STORY] = nw_top_x[:, NW_BOTTOM_X_REPLACE_STORY]
    se_bottom_x[:, SE_BOTTOM_X_REPLACE_STORY] = se_top_x[:, SE_BOTTOM_X_REPLACE_STORY]

    story_displacement_x_raw = (nw_top_x + nw_bottom_x + se_top_x + se_bottom_x) / 4.0
    story_displacement_y_raw = (nw_top_y + nw_bottom_y + se_top_y + se_bottom_y) / 4.0
    story_displacement_x = resample_decimate(story_displacement_x_raw, DT, OUTPUT_DT)
    story_displacement_y = resample_decimate(story_displacement_y_raw, DT, OUTPUT_DT)
    heights = np.asarray(STORY_HEIGHTS_MM, dtype=float)
    story_drift_x = story_displacement_x / heights
    story_drift_y = story_displacement_y / heights
    absolute_displacement_x = np.cumsum(story_displacement_x, axis=1)
    absolute_displacement_y = np.cumsum(story_displacement_y, axis=1)
    time = np.arange(story_displacement_x.shape[0], dtype=float) * OUTPUT_DT

    result = {
        "time": time,
        "story_displacement_x": story_displacement_x,
        "story_displacement_y": story_displacement_y,
        "story_drift_x": story_drift_x,
        "story_drift_y": story_drift_y,
        "absolute_displacement_x": absolute_displacement_x,
        "absolute_displacement_y": absolute_displacement_y,
    }
    save_npz(DATA_DIRECTORY / "story_drift.npz", **result)
    return result


if __name__ == "__main__":
    arrays = process()
    print(f"Story displacement processed: {arrays['time'].size} points")

