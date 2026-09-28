"""Standalone figures for inspection, not an experimental validation claim."""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

COMMON_PYTHON = Path(__file__).resolve().parents[3] / '08_common' / 'python'
sys.path.insert(0, str(COMMON_PYTHON))

from publication_style import apply_style, standard_size  # noqa: E402


def make_figures(model, out):
    apply_style('paper')
    nodes = {n['node']: np.array([n['x_mm'], n['y_mm'], n['z_mm']]) / 1000 for n in model['nodes']}
    fig = plt.figure(figsize=standard_size(8, 9), layout='constrained')
    ax = fig.add_subplot(111, projection='3d')
    colors = {'column': '#334e68', 'beam': '#627d98', 'wall': '#c05621', 'slab': '#bcccdc', 'joint': '#102a43'}
    for element in model['elements']:
        tags = [int(t) for t in element['nodes'].split(';')]
        if element['kind'] == 'slab':
            continue
        if len(tags) == 4:
            tags.append(tags[0])
        coordinates = np.array([nodes[t] for t in tags])
        ax.plot(*coordinates.T, color=colors[element['kind']], lw=.6, alpha=.85)
    ax.set(xlabel='X (m)', ylabel='Y (m)', zlabel='Elevation Z (m)',
           title='2015 ten-story RC specimen | OpenSees mesh')
    ax.set_box_aspect((12, 8, 25.75))
    ax.view_init(elev=18, azim=-50)
    fig.savefig(out / 'model_3d.png')
    plt.close(fig)
    path = out / 'floor_response.csv'
    if not path.exists():
        return
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = [r for r in csv.DictReader(stream) if int(r['story']) == 10]
    time = np.array([float(r['time_s']) for r in rows])
    motion = np.loadtxt(out / 'input_motion.csv', delimiter=',', skiprows=1)
    fig, axes = plt.subplots(3, 2, figsize=standard_size(12, 8), sharex=True, layout='constrained')
    for j, axis in enumerate(('x', 'y')):
        axes[0, j].plot(motion[:, 0], motion[:, j + 1] / 1000, color='C0')
        axes[0, j].set(title=f'{axis.upper()} direction', ylabel='Table accel. (m/s²)')
        axes[1, j].plot(time, [float(r[f'u{axis}_relative_mm']) for r in rows], color='C0')
        axes[1, j].set_ylabel('Roof relative disp. (mm)')
        axes[2, j].plot(time, [float(r[f'a{axis}_absolute_mm_s2']) / 1000 for r in rows], color='C1')
        axes[2, j].set(ylabel='Roof absolute accel. (m/s²)', xlabel='Analysis time (s)')
    for ax in axes.flat:
        ax.grid(True)
    metadata = json.loads((out / 'ground_motion_metadata.json').read_text(encoding='utf-8'))
    fig.suptitle(f'Fixed-base Case {metadata["case_index"]} measured-input trial | prior test damage not inherited')
    fig.savefig(out / 'trial_response.png')
    plt.close(fig)


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Render existing result CSVs without numerical analysis')
    parser.add_argument('run',type=Path)
    args=parser.parse_args()
    out=args.run.resolve()
    with (out/'nodes.csv').open(encoding='utf-8-sig',newline='') as stream:
        nodes=[{**r,'node':int(r['node']),'x_mm':float(r['x_mm']),
                'y_mm':float(r['y_mm']),'z_mm':float(r['z_mm'])} for r in csv.DictReader(stream)]
    with (out/'elements.csv').open(encoding='utf-8-sig',newline='') as stream:
        elements=list(csv.DictReader(stream))
    make_figures({'nodes':nodes,'elements':elements},out)
