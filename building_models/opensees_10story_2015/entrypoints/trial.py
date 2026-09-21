"""Create a unique record before importing or building the OpenSees model."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
# This model lives outside the experiment directory it was extracted from;
# the measured table motion it reads as input still lives there.
EXPERIMENT_ROOT = PROJECT.parent / '10-story_2015'


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main(argv=None):
    parser = argparse.ArgumentParser(description='2015 RC specimen: model, gravity, modal and short measured-input trial')
    parser.add_argument('--stage', choices=('model', 'gravity', 'modal', 'trial'), default='trial')
    parser.add_argument('--case', type=int, default=13, help='Fixed-base case; default 13, JMA Kobe 10%%')
    parser.add_argument('--duration', type=float, default=20.0, help='Seconds from start; default includes the main pulse')
    parser.add_argument('--config', type=Path, default=ROOT / 'config' / 'specimen_2015.json')
    parser.add_argument('--analysis-config', type=Path, default=ROOT / 'config' / 'analysis.json')
    args = parser.parse_args(argv)
    # Outputs are separate from experimental figures and use an exclusive directory.
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ') + f'_{args.stage}'
    out = PROJECT.parent / 'results' / 'opensees' / '10story_2015' / run_id
    out.mkdir(parents=True, exist_ok=False)
    status = {'run_id': run_id, 'state': 'running', 'stage': args.stage,
              'started_utc': datetime.now(timezone.utc).isoformat(),
              'purpose': 'Model construction and numerical trial; experimental agreement is not yet validated.',
              'case_index': args.case, 'duration_s': args.duration}
    write_json(out / 'run_status.json', status)
    print(f'Run directory: {out}', flush=True)
    started = time.perf_counter()
    # Capture Python and native OpenSees stdout/stderr in the durable log.
    saved_stdout, saved_stderr = os.dup(1), os.dup(2)
    log = (out / 'solver.log').open('w', encoding='utf-8', buffering=1)
    sys.stdout.flush()
    sys.stderr.flush()
    os.dup2(log.fileno(), 1)
    os.dup2(log.fileno(), 2)
    code = 0
    try:
        os.environ.setdefault('MPLCONFIGDIR', str(out / 'mplconfig'))
        cfg = json.loads(args.config.read_text(encoding='utf-8'))
        analysis = json.loads(args.analysis_config.read_text(encoding='utf-8'))
        write_json(out / 'specimen_config_used.json', cfg)
        write_json(out / 'analysis_config_used.json', analysis)
        source_dir = out / 'source_snapshot'
        manifest = []
        for source in sorted(ROOT.rglob('*')):
            if source.is_file() and source.suffix in {'.py', '.json', '.md', '.ps1', '.txt'}:
                relative = source.relative_to(ROOT)
                target = source_dir / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                manifest.append({'path': relative.as_posix(),
                                 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
        write_json(out / 'source_manifest.json', manifest)
        import numpy as np
        import openseespy.opensees as ops
        from model.build import build_model
        from analysis.solver import gravity, modal, transient, write_csv
        from analysis.ground_motion import load_ground_motion
        from postprocessing.figures import make_figures

        status['runtime'] = {'python': sys.version, 'opensees': ops.version(), 'numpy': np.__version__}
        print('Building 2015 ten-story wall-frame specimen', flush=True)
        model = build_model(cfg, out)
        summary = {k: v for k, v in model.items() if k not in ('nodes', 'elements', 'mass_lumps')}
        summary['total_mass_t'] = sum(x['mass_t'] for x in model['mass_lumps'])
        summary['node_count'] = len(model['nodes'])
        summary['element_count'] = len(model['elements'])
        write_json(out / 'model_summary.json', summary)
        write_csv(out / 'nodes.csv', model['nodes'])
        write_csv(out / 'elements.csv', model['elements'])
        write_csv(out / 'mass_lumps.csv', model['mass_lumps'])
        status['model'] = {key: summary[key] for key in ('total_mass_t', 'node_count', 'element_count')}
        if args.stage in ('gravity', 'modal', 'trial'):
            print('Applying gravity', flush=True)
            status['gravity'] = gravity(model, analysis, out)
        if args.stage in ('modal', 'trial'):
            print('Computing gravity-loaded modes', flush=True)
            modes = modal(model, analysis, out)
            status['modal'] = modes
        if args.stage == 'trial':
            times, acceleration, motion = load_ground_motion(EXPERIMENT_ROOT, args.case, args.duration)
            if motion['test_base_condition'] != 'fixed':
                raise ValueError('This fixed-base model requires a December fixed-base record (cases 13/15/17/20/22).')
            # Measured axes are explicitly mapped in the specimen configuration.
            mapping = cfg['geometry']['input_axis_map']
            mapped = acceleration.copy()
            for index, axis in enumerate(('x', 'y')):
                mapped[:, index] = mapping[axis]['sign'] * acceleration[:, mapping[axis]['source_column']]
            motion['model_axis_map'] = mapping
            motion['prior_damage_inherited'] = False
            motion['vertical_excitation_applied'] = False
            write_json(out / 'ground_motion_metadata.json', motion)
            np.savetxt(out / 'input_motion.csv', np.column_stack((times, mapped)), delimiter=',',
                       header='time_s,model_ax_mm_s2,model_ay_mm_s2,record_az_mm_s2_not_applied', comments='')
            print(f'Input {motion["case_name"]}, {times[-1]:.2f} seconds', flush=True)
            status['transient'] = transient(model, analysis, modes, times, mapped, out)
        make_figures(model, out)
        status['state'] = 'completed'
    except Exception as exc:
        code = 1
        status['state'] = 'failed'
        status['error'] = f'{type(exc).__name__}: {exc}'
        traceback.print_exc()
    finally:
        status['wall_time_s'] = time.perf_counter() - started
        status['finished_utc'] = datetime.now(timezone.utc).isoformat()
        write_json(out / 'run_status.json', status)
        sys.stdout.flush()
        sys.stderr.flush()
        os.dup2(saved_stdout, 1)
        os.dup2(saved_stderr, 2)
        os.close(saved_stdout)
        os.close(saved_stderr)
        log.close()
    print(f'{status["state"]}: {out}', flush=True)
    if code:
        print(status['error'], file=sys.stderr)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
