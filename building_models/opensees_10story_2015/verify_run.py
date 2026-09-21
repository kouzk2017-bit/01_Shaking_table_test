"""Read-only audit of a completed trial; does not import OpenSees or rerun it."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def check_run(run):
    run = Path(run).resolve()
    status = json.loads((run/'run_status.json').read_text(encoding='utf-8'))
    assert status['state'] == 'completed', status.get('error', status['state'])
    assert status['stage'] == 'trial', 'Expected a complete measured-input trial'
    cfg=json.loads((run/'specimen_config_used.json').read_text(encoding='utf-8'))
    meta=json.loads((run/'ground_motion_metadata.json').read_text(encoding='utf-8'))
    model=json.loads((run/'model_summary.json').read_text(encoding='utf-8'))
    expected_mass=sum(s['weight_kN'] for s in cfg['stories'])*1000/cfg['geometry']['gravity_mm_s2']
    assert math.isclose(model['total_mass_t'],expected_mass,rel_tol=1e-12)
    masses=read_csv(run/'mass_lumps.csv')
    assert math.isclose(sum(float(x['mass_t']) for x in masses),expected_mass,rel_tol=1e-12)
    assert status['gravity']['relative_balance_error']<1e-5
    assert all(x['eigenvalue_s-2']>0 and math.isfinite(x['period_s']) for x in status['modal'])
    assert meta['test_base_condition']=='fixed' and meta['additional_amplitude_scale']==1.
    assert meta['model_axis_map']['x']['source_column']==1
    assert meta['model_axis_map']['y']['source_column']==0
    assert meta['unit_conversion_factor']==1000.
    assert not meta['prior_damage_inherited']
    motion=np.loadtxt(run/'input_motion.csv',delimiter=',',skiprows=1)
    assert np.isfinite(motion).all() and np.allclose(motion[0],0.)
    assert np.all(np.diff(motion[:,0])>0)
    assert math.isclose(motion[-1,0],status['duration_s'],abs_tol=1e-9)
    rows=read_csv(run/'floor_response.csv')
    assert len(rows)==10*len(motion)
    for floor in range(1,11):
        floor_rows=[r for r in rows if int(r['story'])==floor]
        t=np.array([float(r['time_s']) for r in floor_rows])
        assert np.allclose(t,motion[:,0],rtol=0,atol=1e-8)
        for j,axis in enumerate(('x','y')):
            rel=np.array([float(r[f'a{axis}_relative_mm_s2']) for r in floor_rows])
            absolute=np.array([float(r[f'a{axis}_absolute_mm_s2']) for r in floor_rows])
            assert np.isfinite(absolute).all()
            assert np.allclose(absolute-rel,motion[:,j+1],atol=1e-7,rtol=1e-9)
            disp=np.array([float(r[f'u{axis}_relative_mm']) for r in floor_rows])
            drift=np.array([float(r[f'drift_{axis}_rad']) for r in floor_rows])
            below=np.zeros_like(disp) if floor==1 else np.array(
                [float(r[f'u{axis}_relative_mm']) for r in rows if int(r['story'])==floor-1])
            assert np.allclose(drift,(disp-below)/model['story_heights_mm'][floor-1],atol=1e-12)
    for record in json.loads((run/'section_audit.json').read_text(encoding='utf-8')):
        assert math.isclose(record['represented_area_mm2'],record['gross_area_mm2'],rel_tol=1e-12)
        assert record['initial_ea_n']>0
    for record in json.loads((run/'shell_section_audit.json').read_text(encoding='utf-8')):
        assert math.isclose(record['layer_thickness_sum_mm'],record['thickness_mm'],rel_tol=1e-12)
    for item in json.loads((run/'source_manifest.json').read_text(encoding='utf-8')):
        assert hashlib.sha256((run/'source_snapshot'/item['path']).read_bytes()).hexdigest()==item['sha256']
    return {'passed':True,'response_rows':len(rows),'total_mass_t':expected_mass,
            'completed_time_s':float(motion[-1,0]),'source_snapshot_hashes_verified':True,
            'absolute_acceleration_identity_verified':True,'story_drift_identity_verified':True}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    args=parser.parse_args()
    print(json.dumps(check_run(args.run),indent=2))
