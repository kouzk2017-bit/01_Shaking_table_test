"""Compare the zero/negligible-beta diagnostic and export evidence."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

COMMON_PYTHON = Path(__file__).resolve().parents[3] / 'common' / 'python'
sys.path.insert(0, str(COMMON_PYTHON))

from publication_style import apply_style  # noqa: E402


def main():
    apply_style('paper')
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);out=p.parse_args().run.resolve()
    fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
    summary=[]
    for i,eas in enumerate((1,0)):
        for j,method in enumerate(('HHT','Newmark')):
            a=np.loadtxt(out/f'eas{eas}_beta0.0_{method}.csv',delimiter=',')
            b=np.loadtxt(out/f'eas{eas}_beta1e-30_{method}.csv',delimiter=',')
            # Last row is the failed attempt with rolled-back node state.
            n=min(len(a),len(b))-1
            diff=np.abs(a[:n,1]-b[:n,1])
            hit=np.flatnonzero(diff>1e-6)
            summary.append(dict(eas=bool(eas),integrator=method,
                                max_displacement_difference_mm=float(diff.max()),
                                first_difference_over_1e_6_mm_time_s=float(a[hit[0],0]) if len(hit) else None,
                                beta_zero_last_committed_time_s=float(a[-1,0]),
                                beta_tiny_last_committed_time_s=float(b[-1,0])))
            ax=axes[i,j]
            ax.plot(a[:n,0],a[:n,1],label='betaKinit = 0',lw=1.5)
            ax.plot(b[:n,0],b[:n,1],label='betaKinit = 1e-30',lw=1.,ls='--')
            ax.set(title=f'EAS {"on" if eas else "off"} | {method}',xlabel='Time (s)',ylabel='Top displacement (mm)')
            ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Shell diagnostic: physically negligible damping coefficient, different code path')
    fig.savefig(out/'beta_zero_vs_tiny.png',dpi=180)
    (out/'beta_comparison.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__': main()
