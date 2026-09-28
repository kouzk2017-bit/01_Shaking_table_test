"""Plot saved shell states; failure-query values are not committed damage."""
import argparse
import csv
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm

COMMON_PYTHON = Path(__file__).resolve().parents[3] / '08_common' / 'python'
sys.path.insert(0, str(COMMON_PYTHON))

from publication_style import apply_style, standard_size  # noqa: E402


def main():
    apply_style('paper')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path)
    out=p.parse_args().run.resolve()
    summary=json.loads((out/'localization_summary.json').read_text(encoding='utf-8'))
    wall=json.loads((out/'wall_index.json').read_text(encoding='utf-8'))
    with (out/'nodes.csv').open(encoding='utf-8-sig',newline='') as f:
        nodes={int(r['node']):np.array([float(r[k]) for k in ('x_mm','y_mm','z_mm')])/1000 for r in csv.DictReader(f)}
    data=np.load(out/'frames'/summary['last_frame']['frame'])
    eps=data['strain'].reshape(-1,4,8)
    values=np.max(np.abs(eps[:,:,:3]),axis=(1,2))
    upper=max(1e-3,float(np.nanmax(values)))
    norm=LogNorm(vmin=1e-5,vmax=upper)
    fig,axes=plt.subplots(1,4,figsize=standard_size(12,8),sharey=True,layout='constrained')
    for j,ax in enumerate(axes,1):
        ix=[i for i,e in enumerate(wall) if e['member'].startswith(f'W{j}_')]
        polys=[np.array([nodes[int(n)][1:] for n in wall[i]['nodes'].split(';')]) for i in ix]
        col=PolyCollection(polys,array=np.maximum(values[ix],1e-12),cmap='magma',norm=norm,
                           edgecolors='#777777',linewidths=.3)
        ax.add_collection(col);ax.autoscale_view()
        peak=ix[int(np.argmax(values[ix]))]
        xyz=np.array([nodes[int(n)] for n in wall[peak]['nodes'].split(';')]).mean(axis=0)
        ax.plot(xyz[1],xyz[2],marker='*',color='cyan',ms=10)
        ax.set(title=f'W{j}, X={(j-1)*4} m\npeak element {wall[peak]["element"]}',xlabel='Model Y (m)')
        ax.set_ylim(0,18.6)
        ax.grid(True)
    axes[0].set_ylabel('Elevation Z (m)')
    fig.colorbar(col,ax=axes,shrink=.75,label='Maximum absolute membrane strain component')
    failed=bool(int(data['code']))
    fig.suptitle('Wall strain after rollback at 12.69 s (not a failure-location map)' if failed else 'Committed shell state')
    fig.savefig(out/'wall_localization.png')
    plt.close(fig)
    rows=[r for r in summary['history'] if r['frame'][0].isdigit()]
    fig,ax=plt.subplots(figsize=standard_size(9,4),layout='constrained')
    ax.semilogy([r['time_s'] for r in rows],[r['max_membrane_strain'] for r in rows],label='Membrane component')
    ax.semilogy([r['time_s'] for r in rows],[r['max_surface_component_strain'] for r in rows],label='Outer-face component bound')
    ax.set(xlabel='Committed / rollback time (s)',ylabel='Maximum absolute strain',title='Recorded wall strains; final rollback equals last committed strain')
    ax.grid(True);ax.legend()
    fig.savefig(out/'wall_strain_history.png')
    plt.close(fig)


if __name__=='__main__': main()
