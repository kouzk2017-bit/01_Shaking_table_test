"""Archived whole-model static screen, not an exact dynamic reproduction."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('original',type=Path)
    p.add_argument('--combined',action='store_true',help='Biaxial proportional load, Fy/Fx=1.3, control roof X')
    args=p.parse_args();original=args.original.resolve()
    out=original.parent/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'_static_screen')
    out.mkdir(exist_ok=False)
    shutil.copytree(original/'source_snapshot',out/'replay_source')
    shutil.copyfile(__file__,out/'static_screen.py')
    print(out,flush=True)
    sys.path.insert(0,str(out/'replay_source'))
    import numpy as np
    import openseespy.opensees as ops
    from model.build import build_model
    from analysis.solver import gravity,configure,write_csv
    cfg=json.loads((original/'specimen_config_used.json').read_text(encoding='utf-8'))
    analysis=json.loads((original/'analysis_config_used.json').read_text(encoding='utf-8'))
    for axis in ((1,) if args.combined else (1,2)):
        folder=out/f'axis{axis}';folder.mkdir()
        model=build_model(cfg,folder)
        gravity(model,analysis,folder)
        write_csv(folder/'nodes.csv',model['nodes']);write_csv(folder/'elements.csv',model['elements'])
        wall=[e for e in model['elements'] if e['kind']=='wall']
        ops.timeSeries('Linear',2);ops.pattern('Plain',2,2)
        for i,node in enumerate(model['floor_monitors']):
            load=[0.]*6;load[axis-1]=model['floor_mass_properties'][i]['mass_t']*(i+1)
            if args.combined: load[1]=1.3*load[0]
            ops.load(node,*load)
        configure(analysis);ops.algorithm('Newton')
        ops.integrator('DisplacementControl',model['floor_monitors'][-1],axis,.1)
        ops.analysis('Static')
        rows=[]
        for step in range(50):
            code=ops.analyze(1)
            eps=np.asarray([ops.eleResponse(e['element'],'strains') for e in wall]).reshape(-1,4,8)
            score=np.max(np.abs(eps[:,:,:3]),axis=(1,2));i=int(score.argmax())
            row=dict(step=step+1,code=code,roof_displacement_mm=ops.nodeDisp(model['floor_monitors'][-1],axis),
                     roof_ux_mm=ops.nodeDisp(model['floor_monitors'][-1],1),roof_uy_mm=ops.nodeDisp(model['floor_monitors'][-1],2),
                     max_membrane_strain=float(score[i]),element=wall[i]['element'],story=wall[i]['story'],member=wall[i]['member'],iterations=ops.testIter())
            rows.append(row)
            write_csv(folder/'screen.csv',rows)
            if code or step%10==9: print(axis,row,flush=True)
            if code:
                np.savez_compressed(folder/'failed_shells.npz',strain=eps,element_tags=[e['element'] for e in wall])
                break
        (folder/'status.json').write_text(json.dumps(rows[-1],indent=2),encoding='utf-8')
    ops.wipe()


if __name__=='__main__': main()
