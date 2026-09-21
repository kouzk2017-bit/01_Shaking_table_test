"""Small nonlinear cantilever: isolate EAS/Rayleigh/integrator interactions.

Diagnostic only; not a specimen validation. Output created before ops import.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
import shutil

def main():
    ROOT = Path(__file__).resolve().parents[1]
    OUT = ROOT.parents[1] / 'results/opensees/10story_2015' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ') + '_coupon')
    OUT.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, OUT / 'shell_coupon.py')
    shutil.copyfile(ROOT / 'config/specimen_2015.json', OUT / 'specimen_config_used.json')
    print(OUT, flush=True)

    import numpy as np
    import openseespy.opensees as ops
    from model.build import ShellFactory

    cfg = json.loads((ROOT / 'config/specimen_2015.json').read_text(encoding='utf-8'))
    results = []
    for eas in (True, False):
        # 1e-30 is physically negligible but exercises getInitialStiff in the
        # Rayleigh implementation. Differences from zero reveal state effects.
        for beta in (0., 1.e-30):
            for integrator in ('HHT', 'Newmark'):
                ops.wipe()
                ops.model('basic', '-ndm', 3, '-ndf', 6)
                factory = ShellFactory(cfg['section_settings'])
                sec = factory.section('web', cfg['stories'][0]['concrete'], 230., 25., 126.7/250., 71.33/150., 13, 10)
                # Two elements wide, four high, free axial contraction and bending.
                for j in range(5):
                    for i in range(3):
                        tag = j*3+i+1
                        ops.node(tag, i*675., j*700., 0.)
                        ops.fix(tag, *([1]*6 if j == 0 else [0,0,1,1,1,0]))
                        if j == 4:
                            ops.mass(tag, 5., 5., 0., 0., 0., 0.)
                for j in range(4):
                    for i in range(2):
                        n = j*3+i+1
                        ops.element('ASDShellQ4', j*2+i+1, n,n+1,n+4,n+3,sec,*([] if eas else ['-noeas']))
                ops.timeSeries('Linear',1)
                ops.pattern('Plain',1,1)
                for tag in (13,14,15):
                    ops.load(tag,0.,-150000.,0.,0.,0.,0.)
                ops.constraints('Transformation'); ops.numberer('RCM'); ops.system('UmfPack')
                ops.test('NormDispIncr',1e-6,50); ops.algorithm('Newton')
                ops.integrator('LoadControl',.1); ops.analysis('Static')
                gravity_code = ops.analyze(10)
                eig = ops.eigen(1)[0] if gravity_code == 0 else None
                ops.loadConst('-time',0.); ops.wipeAnalysis()
                ops.rayleigh(.5,0.,beta,0.)
                t = np.arange(0.,4.001,.005)
                accel = 20000.*np.minimum(t/2.,1.)*np.sin(2*np.pi*3*t)
                ops.timeSeries('Path',2,'-dt',.005,'-values',*accel)
                ops.pattern('UniformExcitation',2,1,'-accel',2)
                ops.constraints('Transformation'); ops.numberer('RCM'); ops.system('UmfPack')
                ops.test('NormDispIncr',1e-6,50); ops.algorithm('Newton')
                if integrator == 'HHT': ops.integrator('HHT',.9)
                else: ops.integrator('Newmark',.5,.25)
                ops.analysis('Transient')
                history = []
                code = gravity_code
                for step in range(800):
                    if code: break
                    code = ops.analyze(1,.005)
                    history.append([ops.getTime(),ops.nodeDisp(14,1),ops.testIter()])
                name = f'eas{int(eas)}_beta{beta}_{integrator}'
                np.savetxt(OUT / (name+'.csv'),history,delimiter=',',header='time_s,top_ux_mm,iterations')
                row = dict(case=name,gravity_code=gravity_code,eigenvalue=eig,code=code,time_s=ops.getTime(),
                           peak_mm=max((abs(r[1]) for r in history),default=0.))
                results.append(row)
                (OUT/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
                print(row,flush=True)
    ops.wipe()


if __name__ == '__main__':
    main()
