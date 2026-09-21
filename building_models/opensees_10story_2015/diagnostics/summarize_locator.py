"""Read recorded shell and solver states without importing OpenSees."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np


def summarize(out):
    wall=json.loads((out/'wall_index.json').read_text(encoding='utf-8'))
    sections={r['section_tag']:r for r in json.loads((out/'shell_section_audit.json').read_text(encoding='utf-8'))}
    with (out/'nodes.csv').open(encoding='utf-8-sig',newline='') as f:
        node_rows=list(csv.DictReader(f))
    nodes={int(r['node']):{k:float(r[k]) for k in ('x_mm','y_mm','z_mm')} for r in node_rows}
    kinds={int(r['node']):r['kind'] for r in node_rows}
    floor_z={float(r['z_mm']) for r in node_rows if r['kind']=='diaphragm_master'}
    index={e['element']:e for e in wall}
    frames=sorted((out/'frames').glob('*.npz'),key=lambda p:(p.name not in ('gravity.npz','after_modal.npz'),p.name))
    history=[]
    last=None
    for path in frames:
        with np.load(path) as data:
            strain=data['strain'].reshape(-1,4,8)
            force=data['stress_resultants'].reshape(-1,4,8)
            tags=data['element_tags']
            thickness=np.array([sections[index[int(t)]['section_tag']]['thickness_mm'] for t in tags])
            fc=np.array([sections[index[int(t)]['section_tag']]['fc_mpa'] for t in tags])
            membrane=np.max(np.abs(strain[:,:,:3]),axis=(1,2))
            # Shell convention e(z)=e0-z*k; both faces bound all actual layers.
            outer=np.stack([strain[:,:,:3]+sign*thickness[:,None,None]/2*strain[:,:,3:6] for sign in (-1,1)])
            surface=np.max(np.abs(outer),axis=(0,2,3))
            force_ratio=np.max(np.abs(force[:,:,:3]),axis=(1,2))/(thickness*fc)
            row=dict(frame=path.name,time_s=float(data['time_s']),code=int(data['code']),
                     max_membrane_strain=float(membrane.max()),membrane_element=int(tags[membrane.argmax()]),
                     max_surface_component_strain=float(surface.max()),surface_element=int(tags[surface.argmax()]),
                     max_membrane_resultant_over_fc_t=float(force_ratio.max()),force_element=int(tags[force_ratio.argmax()]))
            history.append(row)
            last=dict(tags=tags.copy(),membrane=membrane,surface=surface,force_ratio=force_ratio)
    def detail(i):
        e=index[int(last['tags'][i])]
        xyz=np.array([[nodes[int(n)][k] for k in ('x_mm','y_mm','z_mm')] for n in e['nodes'].split(';')])
        return dict(**e,centroid_mm=xyz.mean(axis=0).tolist(),bounds_mm=[xyz.min(axis=0).tolist(),xyz.max(axis=0).tolist()],
                    membrane_strain=float(last['membrane'][i]),surface_component_strain=float(last['surface'][i]),
                    membrane_force_over_fc_t=float(last['force_ratio'][i]))
    result=dict(last_frame=history[-1],history=history,
                top_membrane=[detail(i) for i in np.argsort(last['membrane'])[-20:][::-1]],
                top_surface=[detail(i) for i in np.argsort(last['surface'])[-20:][::-1]],
                top_force=[detail(i) for i in np.argsort(last['force_ratio'])[-20:][::-1]])
    residual_path=out/'failed_soe_residual.npy'
    if residual_path.exists():
        residual=np.load(residual_path).reshape(-1)
        eqmap=json.loads((out/'equation_map.json').read_text(encoding='utf-8'))
        candidates=[]
        for n in eqmap:
            # TransformationDOF_Group returns [free slave Z,Rx,Ry,
            # retained master X,Y,Rz], NOT the physical nodal DOF order.
            # Map only free slave DOFs here; masters map shared equations once.
            slave=kinds[n['node']]!='diaphragm_master' and nodes[n['node']]['z_mm'] in floor_z
            pairs=zip((3,4,5),n['equations'][:3]) if slave else enumerate(n['equations'],1)
            for dof,eq in pairs:
                if 0<=eq<len(residual):
                    candidates.append(dict(node=n['node'],dof=dof,equation=eq,residual=float(residual[eq]),
                                           node_kind=kinds[n['node']],
                                           **nodes[n['node']]))
        equations=[r['equation'] for r in candidates]
        assert len(equations)==len(set(equations))==len(residual), 'Equation map must cover every equation exactly once'
        result['equation_mapping_checked']=True
        result['residual_scope']='Reassembled by printB after automatic rollback; not failed-iteration residual'
        result['residual_mixed_units_norm_not_physical_force']=float(np.linalg.norm(residual))
        for name,dofs in [('force_N',(1,2,3)),('moment_Nmm',(4,5,6))]:
            result['top_residual_'+name]=sorted([n for n in candidates if n['dof'] in dofs],key=lambda n:abs(n['residual']),reverse=True)[:30]
    (out/'localization_summary.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(last_frame=result['last_frame'],top_membrane=result['top_membrane'][:3],
                          top_force=result['top_force'][:3]),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path)
    summarize(p.parse_args().run.resolve())
