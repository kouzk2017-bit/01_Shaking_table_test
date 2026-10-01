"""2D IMK frame-direction model: parameters, gravity + modal, pushover, trial.

    python -B -m imk2d.run --stage params
    python -B -m imk2d.run --stage modal
    python -B -m imk2d.run --stage pushover
    python -B -m imk2d.run --stage trial --case 13 --duration 20

Results: 06_results/opensees/imk2d_<stage>[_case<N>_<T>s]/ (fixed names, see
entrypoints/output.py). Only the X (frame) component of the measured table
motion is applied.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path

import numpy as np
import openseespy.opensees as ops

from entrypoints import output
from imk2d.frame import apply_gravity_loads, build, member_table

ROOT = output.ROOT


def write_csv(path: Path, rows):
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def hinge_rows(table):
    rows = []
    for kind, members in (('column', table['columns']), ('beam', table['beams'])):
        for mem in members:
            for e in mem['ends']:
                rows.append({
                    'frame': mem['frame'], 'kind': kind, 'member': mem['member'],
                    'story_or_floor': mem.get('story', mem.get('floor')),
                    'grid_or_bay': mem.get('ix', mem.get('bay')), 'end': e['end'],
                    'multiplicity': mem['multiplicity'], 'b_mm': mem['b_mm'], 'h_mm': mem['h_mm'],
                    'clear_mm': round(mem['clear_mm'], 1), 'fc_mpa': e['fc_mpa'],
                    'axial_kN': round(mem.get('axial_N', 0.0) / 1e3, 1), 'nu': round(e['nu'], 4),
                    'rho': round(e['rho'], 5), 'rho_sh': round(e['rho_sh'], 5),
                    'My_pos_kNm': round(e['my_pos'] / 1e6, 2), 'My_neg_kNm': round(abs(e['my_neg']) / 1e6, 2),
                    'yield_governs': e['governs'], 'EI_ratio': round(mem['ei_ratio'], 3),
                    'theta_y': round(e['theta_y'], 5), 'theta_p': round(e['theta_p'], 4),
                    'theta_pc': round(e['theta_pc'], 4), 'Mc_My': round(e['mc_my'], 3),
                    'lambda': round(e['lam'], 1), 'Lamda_rad': round(e['lamda'], 4),
                    'spring_k_kNm_rad': round(e['spring_k'] / 1e6, 1)})
    return rows


def configure(acfg, algorithm='Newton', tol=None):
    ops.wipeAnalysis()
    ops.constraints('Transformation')
    ops.numberer('RCM')
    ops.system('UmfPack')
    ops.test('NormDispIncr', tol or acfg['tolerance_mm'], acfg['max_iterations'], 0)
    ops.algorithm(algorithm)


def gravity(table, domain, acfg):
    applied = apply_gravity_loads(table, domain)
    configure(acfg)
    ops.integrator('LoadControl', 1.0 / acfg['gravity_steps'])
    ops.analysis('Static')
    if ops.analyze(acfg['gravity_steps']):
        raise RuntimeError('Gravity analysis failed')
    ops.reactions()
    reaction = sum(ops.nodeReaction(n, 2) for n in domain['bases'])
    error = abs(reaction - applied) / applied
    if error > 1e-6:
        raise RuntimeError(f'Gravity equilibrium error {error:.3g}')
    # Gravity column axial forces versus the tributary values used for nu.
    checks = []
    for col in table['columns']:
        if col['story'] == 1:
            n_model = -ops.eleResponse(col['element'], 'localForce')[0] / col['multiplicity']
            checks.append({'frame': col['frame'], 'ix': col['ix'], 'model_kN': n_model / 1e3,
                           'tributary_kN': col['axial_N'] / 1e3})
    ops.loadConst('-time', 0.0)
    ops.wipeAnalysis()
    return {'applied_N': applied, 'reaction_N': reaction, 'relative_error': error,
            'story1_axial_check': checks}


def modal(domain, acfg, out):
    configure(acfg)
    count = acfg['num_modes']
    eig = ops.eigen('-genBandArpack', count)
    total = sum(ops.nodeMass(n, 1) for n in domain['masters'])
    rows, shapes = [], []
    for k, value in enumerate(eig, 1):
        phi = np.array([ops.nodeEigenvector(n, k, 1) for n in domain['masters']])
        mass = np.array([ops.nodeMass(n, 1) for n in domain['masters']])
        gamma = (mass @ phi) / (mass @ phi ** 2)
        rows.append({'mode': k, 'period_s': 2 * math.pi / math.sqrt(value),
                     'effective_mass_ratio': float(gamma * (mass @ phi) / total)})
        top = phi[-1] if abs(phi[-1]) > 0 else 1.0
        shapes += [{'mode': k, 'story': i + 1, 'ux_normalised': float(v / top)} for i, v in enumerate(phi)]
    write_csv(out / 'modal.csv', rows)
    write_csv(out / 'mode_shapes.csv', shapes)
    return rows


def story_heights(table):
    e = table['elevations']
    return [e[i + 1] - e[i] for i in range(10)]


def spring_state(domain):
    return [(ops.eleResponse(tag, 'deformation')[0], ops.eleResponse(tag, 'basicForce')[0])
            for tag, _, _ in domain['springs']]


def hinge_peaks(domain, history):
    """history: list of per-step [(rot, mom), ...] in spring order."""
    arr = np.asarray(history)  # steps x springs x 2
    rows = []
    for k, (tag, member, end) in enumerate(domain['springs']):
        rot, mom = arr[:, k, 0], arr[:, k, 1] / member['multiplicity']
        ty_spring_pos = end['my_pos'] / end['spring_k']
        ty_spring_neg = abs(end['my_neg']) / end['spring_k']
        rows.append({
            'kind': 'column' if 'story' in member else 'beam', 'frame': member['frame'],
            'member': member['member'], 'story_or_floor': member.get('story', member.get('floor')),
            'grid_or_bay': member.get('ix', member.get('bay')), 'end': end['end'],
            'max_rot_rad': float(rot.max()), 'min_rot_rad': float(rot.min()),
            'plastic_rot_pos_rad': float(max(0.0, rot.max() - ty_spring_pos)),
            'plastic_rot_neg_rad': float(max(0.0, -rot.min() - ty_spring_neg)),
            'M_max_over_My_pos': float(mom.max() / end['my_pos']),
            'M_min_over_My_neg': float(-mom.min() / abs(end['my_neg'])),
            'theta_p': end['theta_p']})
    return rows


def pushover(table, domain, acfg, out, modes):
    # Lateral pattern: first-mode shape x floor mass.
    ops.timeSeries('Linear', 2)
    ops.pattern('Plain', 2, 2)
    configure(acfg)
    phi = [ops.nodeEigenvector(n, 1, 1) for n in domain['masters']]
    sign = 1.0 if phi[-1] > 0 else -1.0
    forces = [sign * p * ops.nodeMass(n, 1) for p, n in zip(phi, domain['masters'])]
    scale = 1.0 / sum(forces)
    for n, f in zip(domain['masters'], forces):
        ops.load(n, f * scale, 0.0, 0.0)
    roof = domain['masters'][-1]
    height = table['elevations'][-1]
    step = acfg['pushover_step_mm']
    target = acfg['pushover_roof_drift'] * height
    ops.integrator('DisplacementControl', roof, 1, step)
    ops.analysis('Static')
    weight = sum(table['floor_mass_t']) * 9800.0
    heights = story_heights(table)
    curve, history = [], []
    while ops.nodeDisp(roof, 1) < target:
        ok = ops.analyze(1)
        if ok:
            for algorithm in ('KrylovNewton', 'NewtonLineSearch'):
                ops.algorithm(algorithm)
                ok = ops.analyze(1)
                ops.algorithm('Newton')
                if not ok:
                    break
        if ok:
            print(f'Pushover stopped at roof {ops.nodeDisp(roof, 1):.1f} mm', flush=True)
            break
        ops.reactions()
        base = -sum(ops.nodeReaction(n, 1) for n in domain['bases'])
        disp = [ops.nodeDisp(n, 1) for n in domain['masters']]
        drifts = np.diff([0.0] + disp) / heights
        curve.append({'roof_mm': disp[-1], 'roof_drift': disp[-1] / height, 'base_shear_kN': base / 1e3,
                      'base_shear_coeff': base / weight,
                      'max_story_drift': float(np.max(np.abs(drifts))),
                      'max_drift_story': int(np.argmax(np.abs(drifts)) + 1)})
        history.append(spring_state(domain))
    write_csv(out / 'pushover_curve.csv', curve)
    write_csv(out / 'pushover_hinge_peaks.csv', hinge_peaks(domain, history))
    peak = max(curve, key=lambda r: r['base_shear_kN'])
    return {'points': len(curve), 'final_roof_drift': curve[-1]['roof_drift'],
            'peak_base_shear_kN': peak['base_shear_kN'], 'peak_base_shear_coeff': peak['base_shear_coeff'],
            'roof_drift_at_peak': peak['roof_drift']}


def transient(table, domain, acfg, modes, times, acc, out):
    w1 = 2 * math.pi / modes[0]['period_s']
    w2 = w1 / acfg['damping_anchor_period_ratio']
    zeta = acfg['damping_ratio']
    alpha = 2 * zeta * w1 * w2 / (w1 + w2)
    beta = 2 * zeta / (w1 + w2)
    n = table['n_factor']
    ops.region(1, '-node', *domain['masters'], '-rayleigh', alpha, 0.0, 0.0, 0.0)
    ops.region(2, '-ele', *domain['members'], '-rayleigh', 0.0, 0.0, beta * (n + 1) / n, 0.0)
    time_file, motion_file = out / 'input_time_s.txt', out / 'input_x_mm_s2.txt'
    np.savetxt(time_file, times, fmt='%.12g')
    np.savetxt(motion_file, acc, fmt='%.12g')
    ops.timeSeries('Path', 10, '-fileTime', str(time_file), '-filePath', str(motion_file), '-useLast')
    ops.pattern('UniformExcitation', 10, 1, '-accel', 10)
    configure(acfg)
    ops.integrator('Newmark', 0.5, 0.25)
    ops.analysis('Transient')
    heights = story_heights(table)
    events, response, base, history = [], [], [], []

    def advance(dt, depth=0):
        start = ops.getTime()
        for algorithm in ('Newton', 'KrylovNewton', 'NewtonLineSearch'):
            ops.algorithm(algorithm)
            if ops.analyze(1, dt) == 0:
                if algorithm != 'Newton' or depth:
                    events.append({'start_s': start, 'dt_s': dt, 'algorithm': algorithm, 'subdivision': depth})
                return
        if dt / 2 < acfg['min_dt_s'] - 1e-12:
            raise RuntimeError(f'Transient failed at t={start:.6g} s')
        advance(dt / 2, depth + 1)
        advance(dt / 2, depth + 1)

    def record():
        t = ops.getTime()
        ag = float(np.interp(t, times, acc))
        disp = [ops.nodeDisp(nd, 1) for nd in domain['masters']]
        drifts = np.diff([0.0] + disp) / heights
        for s, nd in enumerate(domain['masters']):
            response.append({'time_s': t, 'story': s + 1, 'ux_relative_mm': disp[s],
                             'drift_x_rad': float(drifts[s]),
                             'ax_absolute_mm_s2': ops.nodeAccel(nd, 1) + ag})
        ops.reactions('-dynamic')
        base.append({'time_s': t, 'base_shear_N': -sum(ops.nodeReaction(b, 1) for b in domain['bases'])})
        history.append(spring_state(domain))

    record()
    try:
        for k in range(1, len(times)):
            advance(float(times[k] - ops.getTime()))
            record()
            if k % 200 == 0:
                print(f'Transient {ops.getTime():.2f}/{times[-1]:.2f} s', flush=True)
    finally:
        write_csv(out / 'floor_response.csv', response)
        write_csv(out / 'base_shear.csv', base)
        write_csv(out / 'solver_recovery.csv', events)
        if history:
            write_csv(out / 'hinge_peaks.csv', hinge_peaks(domain, history))
    peaks = []
    for s in range(1, 11):
        rows = [r for r in response if r['story'] == s]
        peaks.append({'story': s, **{f'peak_abs_{key}': max(abs(r[key]) for r in rows)
                                     for key in ('ux_relative_mm', 'drift_x_rad', 'ax_absolute_mm_s2')}})
    write_csv(out / 'response_peaks.csv', peaks)
    return {'completed_time_s': ops.getTime(), 'recovery_events': len(events),
            'rayleigh_alphaM': alpha, 'rayleigh_betaK_elastic_members': beta * (n + 1) / n,
            'peak_base_shear_kN': max(abs(b['base_shear_N']) for b in base) / 1e3,
            'peaks_by_story': peaks}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--stage', choices=('params', 'modal', 'pushover', 'trial'), default='modal')
    parser.add_argument('--case', type=int, default=13)
    parser.add_argument('--duration', type=float, default=20.0)
    parser.add_argument('--config', type=Path, default=ROOT / 'config' / 'imk2d.json')
    args = parser.parse_args(argv)
    cfg = json.loads(args.config.read_text(encoding='utf-8'))
    spec = json.loads((args.config.parent / cfg['specimen_config']).read_text(encoding='utf-8'))
    acfg = cfg['analysis']
    name = f'imk2d_trial_case{args.case}_{args.duration:g}s' if args.stage == 'trial' else f'imk2d_{args.stage}'
    out = output.start(name)
    status = {'stage': args.stage, 'state': 'running', 'opensees': ops.version()}
    started = time.perf_counter()
    ok = False
    try:
        write_json(out / 'imk2d_config_used.json', cfg)
        table = member_table(spec, cfg)
        table['n_factor'] = cfg['hinges']['n_factor']
        write_csv(out / 'hinge_parameters.csv', hinge_rows(table))
        status['total_mass_t'] = sum(table['floor_mass_t'])
        if args.stage != 'params':
            domain = build(table, cfg)
            status['model'] = {'nodes': domain['node_count'], 'elements': domain['element_count'],
                               'springs': len(domain['springs'])}
            status['gravity'] = gravity(table, domain, acfg)
            modes = modal(domain, acfg, out)
            status['modal'] = modes
            print('Periods: ' + ', '.join(f"{m['period_s']:.3f}" for m in modes), flush=True)
            if args.stage == 'pushover':
                status['pushover'] = pushover(table, domain, acfg, out, modes)
            if args.stage == 'trial':
                from analysis.ground_motion import load_ground_motion
                times, acc, motion = load_ground_motion(output.EXPERIMENT_ROOT, args.case, args.duration)
                axis = spec['geometry']['input_axis_map']['x']
                ax = axis['sign'] * acc[:, axis['source_column']]
                motion.update(model_axis='x only', prior_damage_inherited=False)
                write_json(out / 'ground_motion_metadata.json', motion)
                status['transient'] = transient(table, domain, acfg, modes, times, ax, out)
        status['state'] = 'completed'
        ok = True
    except Exception as exc:
        status['state'] = 'failed'
        status['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        status['wall_time_s'] = time.perf_counter() - started
        write_json(out / 'run_status.json', status)
        final = output.finish(out, name, ok)
        print(f"{status['state']}: {final}", flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
