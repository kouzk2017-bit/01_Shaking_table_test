"""Replay an archived run with passive shell/DOF probes; stop at first failure.

The archived specimen, solver and input are used unchanged unless an explicit
diagnostic beta override is requested. No force/tangent
element query is made by the probes, to avoid changing ASDShellQ4 EAS state.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original', type=Path)
    parser.add_argument('--duration', type=float, default=13.)
    parser.add_argument('--beta-init-override', type=float, default=None,
                        help='Diagnostic override only; makes this a counterfactual, not an exact replay')
    args = parser.parse_args()
    original = args.original.resolve()
    out = original.parent / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'_locator')
    out.mkdir(exist_ok=False)
    shutil.copytree(original/'source_snapshot', out/'replay_source')
    shutil.copyfile(__file__, out/'locate_failure.py')
    for name in ('specimen_config_used.json','analysis_config_used.json','input_motion.csv'):
        shutil.copyfile(original/name, out/name)
    status = dict(state='running', original=str(original), purpose='Locate first failed increment using archived source and input')
    status['beta_init_override']=args.beta_init_override
    def save_status():
        (out/'locator_status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
    save_status()
    print(out,flush=True)
    started=time.perf_counter()
    saved=[os.dup(1),os.dup(2)]
    log=(out/'solver.log').open('w',encoding='utf-8',buffering=1)
    os.dup2(log.fileno(),1); os.dup2(log.fileno(),2)
    try:
        sys.path.insert(0,str(out/'replay_source'))
        import numpy as np
        import openseespy.opensees as ops
        from model.build import build_model
        from analysis.solver import gravity,modal,transient,write_csv
        cfg=json.loads((out/'specimen_config_used.json').read_text(encoding='utf-8'))
        analysis=json.loads((out/'analysis_config_used.json').read_text(encoding='utf-8'))
        model=build_model(cfg,out)
        write_csv(out/'nodes.csv',model['nodes']); write_csv(out/'elements.csv',model['elements'])
        status['gravity']=gravity(model,analysis,out)
        wall=[e for e in model['elements'] if e['kind']=='wall']
        tags=np.array([e['element'] for e in wall])
        node_tags=np.array([n['node'] for n in model['nodes']])
        (out/'wall_index.json').write_text(json.dumps(wall,indent=2),encoding='utf-8')
        frame=(out/'frames'); frame.mkdir()
        def snapshot(label,code=0):
            strain=np.asarray([ops.eleResponse(int(tag),'strains') for tag in tags])
            stress=np.asarray([ops.eleResponse(int(tag),'stresses') for tag in tags])
            if strain.shape!=(len(tags),32) or stress.shape!=strain.shape:
                raise RuntimeError(f'Invalid shell probe shape: {strain.shape}, {stress.shape}')
            disp=np.asarray([ops.nodeDisp(int(n)) for n in node_tags])
            np.savez_compressed(frame/(label+'.npz'),time_s=ops.getTime(),code=code,
                                element_tags=tags,strain=strain,stress_resultants=stress,
                                node_tags=node_tags,displacement=disp)
            # Membrane components only; curvature and shear have different units.
            score=np.max(np.abs(strain.reshape(-1,4,8)[:,:,:3]),axis=(1,2))
            indices=np.argsort(score)[-12:][::-1]
            report=[dict(**wall[int(i)],max_membrane_strain=float(score[i])) for i in indices]
            (out/'latest_shell_ranking.json').write_text(json.dumps(dict(time_s=ops.getTime(),label=label,top=report),indent=2),encoding='utf-8')
        snapshot('gravity')
        modes=modal(model,analysis,out)
        snapshot('after_modal')
        old_analyze=ops.analyze
        count=0
        def analyze(*values):
            nonlocal count
            code=old_analyze(*values)
            if len(values)>1:
                count+=1
                t=ops.getTime()
                if code or count==1 or count%10==0 or t>=12.:
                    snapshot(f'{count:05d}_code{code}',code)
                if count==1:
                    equations=[dict(node=int(n),equations=ops.nodeDOFs(int(n))) for n in node_tags]
                    (out/'equation_map.json').write_text(json.dumps(equations),encoding='utf-8')
                if count%20==0:
                    status.update(time_s=t,wall_time_s=time.perf_counter()-started)
                    save_status()
                if code:
                    # printX is passive; printB calls formUnbalance after rollback.
                    np.save(out/'last_solver_increment.npy',np.asarray(ops.printX('-ret')))
                    residual=np.asarray(ops.printB('-ret'))
                    np.save(out/'failed_soe_residual.npy',residual)
                    status.update(state='first_failure_captured',time_s=t,attempt_dt_s=values[1],return_code=code,
                                  state_note='Node state is rolled back by OpenSees. printB reassembles unbalance after rollback; saved B is NOT the failed-iteration residual. printX saves the last solver increment before that reassembly.')
                    raise RuntimeError(f'First failed increment captured after t={t}, dt={values[1]}')
            return code
        ops.analyze=analyze
        if args.beta_init_override is not None:
            original_rayleigh=ops.rayleigh
            def diagnostic_rayleigh(alpha,beta,beta_initial,beta_committed):
                return original_rayleigh(alpha,beta,args.beta_init_override,beta_committed)
            ops.rayleigh=diagnostic_rayleigh
        motion=np.loadtxt(out/'input_motion.csv',delimiter=',',skiprows=1)
        motion=motion[motion[:,0]<=args.duration+1e-9]
        status['transient']=transient(model,analysis,modes,motion[:,0],motion[:,1:],out)
        if args.beta_init_override is not None:
            status['transient']['nominal_rayleigh_betaKinit']=status['transient']['rayleigh_betaKinit']
            status['transient']['rayleigh_betaKinit']=args.beta_init_override
            status['transient']['nominal_target_damping_ratio']=status['transient'].pop('damping_ratio_assumed')
        status['state']='completed_without_failure'
    except Exception as exc:
        if status['state']=='running': status['state']='diagnostic_error'
        status['error']=str(exc)
        traceback.print_exc()
    finally:
        status['wall_time_s']=time.perf_counter()-started
        save_status()
        sys.stdout.flush();sys.stderr.flush()
        os.dup2(saved[0],1);os.dup2(saved[1],2)
        for fd in saved: os.close(fd)
        log.close()
    print(json.dumps(status,indent=2),flush=True)


if __name__=='__main__':
    main()
