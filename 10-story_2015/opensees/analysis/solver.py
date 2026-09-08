"""TJU-style analysis sequence. Internal units: N, mm, tonne, second."""
from __future__ import annotations

import csv
import math
import time
from pathlib import Path

import numpy as np
import openseespy.opensees as ops


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def configure(config):
    ops.wipeAnalysis()
    ops.constraints('Transformation')
    ops.numberer('RCM')
    if config.get('linear_system', 'UmfPack') == 'SparseGeneral':
        ops.system('SparseGeneral', '-piv')
    else:
        ops.system(config.get('linear_system', 'UmfPack'))
    ops.test('NormDispIncr', config['tolerance_mm'], config['max_iterations'], 0)
    ops.algorithm('NewtonLineSearch')


def gravity(model, config, out):
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)
    g = model['gravity_mm_s2']
    for lump in model['mass_lumps']:
        ops.load(lump['node'], 0., 0., -lump['mass_t'] * g, 0., 0., 0.)
    configure(config)
    steps = config['gravity_steps']
    ops.integrator('LoadControl', 1. / steps)
    ops.analysis('Static')
    history = []
    for step in range(steps):
        code = ops.analyze(1)
        if code:
            raise RuntimeError(f'Gravity failed at increment {step + 1}/{steps}, code={code}')
        roof_nodes = [lump['node'] for lump in model['mass_lumps']
                      if lump['story'] == len(model['floor_monitors'])]
        history.append({'load_factor': ops.getTime(),
                        'roof_min_uz_mm': min(ops.nodeDisp(node, 3) for node in roof_nodes)})
    ops.reactions()
    reactions = [{'node': node, 'rx_N': ops.nodeReaction(node, 1),
                  'ry_N': ops.nodeReaction(node, 2), 'rz_N': ops.nodeReaction(node, 3)}
                 for node in model['base_nodes']]
    expected = sum(x['mass_t'] for x in model['mass_lumps']) * g
    reaction = sum(x['rz_N'] for x in reactions)
    error = abs(reaction - expected) / expected
    write_csv(out / 'gravity_steps.csv', history)
    write_csv(out / 'gravity_reactions.csv', reactions)
    if not math.isfinite(error) or error > 1.e-5:
        raise RuntimeError(f'Gravity equilibrium error {error:.6g} exceeds 1e-5')
    # The compatible eight-resultant shell must have zero membrane strain
    # under the rigid diaphragm. This verifies the intended floor kinematics.
    membrane = []
    for element in model['elements']:
        if element['kind'] == 'slab':
            deformation = ops.eleResponse(element['element'], 'material', 1, 'deformations')
            if len(deformation) != 8:
                raise RuntimeError('ShellMITC4 slab must have an eight-component section')
            membrane.extend(deformation[:3])
    max_membrane = max(abs(float(value)) for value in membrane)
    if max_membrane > 1.e-10:
        raise RuntimeError(f'Slab membrane strain violates rigid-floor constraint: {max_membrane}')
    ops.loadConst('-time', 0.)
    ops.wipeAnalysis()
    return {'passed': True, 'applied_weight_N': expected, 'reaction_N': reaction,
            'relative_balance_error': error, 'increments': steps,
            'max_slab_membrane_strain': max_membrane,
            'roof_min_uz_mm': history[-1]['roof_min_uz_mm']}


def modal(model, config, out, label='modal_after_gravity'):
    configure(config)
    eig = np.asarray(ops.eigen('-genBandArpack', config['num_modes']), dtype=float)
    if not np.all(np.isfinite(eig)) or np.any(eig <= 0):
        raise RuntimeError(f'Nonpositive or nonfinite eigenvalues: {eig}')
    rows, shapes = [], []
    total = sum(x['mass_t'] for x in model['mass_lumps'])
    for index, value in enumerate(eig, 1):
        denominator = 0.
        participation = np.zeros(2)
        for lump in model['mass_lumps']:
            v = np.asarray(ops.nodeEigenvector(lump['node'], index)[:2])
            mass = lump['mass_t']
            denominator += mass * float(v @ v)
            participation += mass * v
        effective = participation ** 2 / denominator / total if denominator > 0 else np.zeros(2)
        rows.append({'mode': index, 'eigenvalue_s-2': float(value),
                     'frequency_Hz': float(math.sqrt(value) / (2 * math.pi)),
                     'period_s': float(2 * math.pi / math.sqrt(value)),
                     'effective_mass_X_ratio': float(effective[0]),
                     'effective_mass_Y_ratio': float(effective[1])})
        for floor, node in enumerate(model['floor_monitors'], 1):
            v = ops.nodeEigenvector(node, index)
            shapes.append({'mode': index, 'story': floor, 'node': node,
                           'ux': v[0], 'uy': v[1], 'rz': v[5]})
    write_csv(out / f'{label}.csv', rows)
    write_csv(out / f'{label}_shapes.csv', shapes)
    return rows


def transient(model, config, modes, times, acc, out):
    # Initial stiffness Rayleigh, matching TJU; zeta remains an explicit assumption.
    frequencies = sorted(math.sqrt(row['eigenvalue_s-2']) for row in modes)
    w1, w2 = frequencies[0], frequencies[min(2, len(frequencies) - 1)]
    zeta = config['damping_ratio']
    alpha = 2 * zeta * w1 * w2 / (w1 + w2)
    beta = 2 * zeta / (w1 + w2)
    ops.rayleigh(alpha, 0., beta, 0.)
    directions = config['directions']
    time_file = out / 'input_time_s.txt'
    np.savetxt(time_file, times, fmt='%.12g')
    for axis in directions:
        column = {'x': 0, 'y': 1}[axis]
        tag = 10 + column
        motion_file = out / f'input_{axis}_mm_s2.txt'
        np.savetxt(motion_file, acc[:, column], fmt='%.12g')
        ops.timeSeries('Path', tag, '-fileTime', str(time_file),
                       '-filePath', str(motion_file), '-useLast')
        ops.pattern('UniformExcitation', tag, column + 1, '-accel', tag)
    configure(config)
    ops.integrator('HHT', config['hht_alpha'])
    ops.analysis('Transient')
    events, response, base = [], [], []
    gravity_offsets = {node: np.asarray(ops.nodeDisp(node)[:3])
                       for node in model['floor_monitors']}

    cached_dt = None
    default_algorithm = config.get('transient_algorithm', 'KrylovNewton')

    def advance(step_dt, depth=0):
        nonlocal cached_dt
        start = ops.getTime()
        algorithms = list(dict.fromkeys([default_algorithm, 'KrylovNewton', 'NewtonLineSearch', 'Newton']))
        for algorithm in algorithms:
            if algorithm == 'ModifiedNewtonFactorOnce':
                # Reuse the factorization for a fixed dt, but still iterate the
                # full nonlinear residual to the same convergence criterion.
                # Any dt change or recovery invalidates the cached matrix.
                if cached_dt is None or not math.isclose(cached_dt, step_dt, rel_tol=0., abs_tol=1.e-10):
                    ops.algorithm('ModifiedNewton', '-factoronce')
                    cached_dt = step_dt
            else:
                ops.algorithm(algorithm)
                cached_dt = None
            code = ops.analyze(1, step_dt)
            if code == 0:
                if algorithm != default_algorithm or depth:
                    events.append({'start_s': start, 'dt_s': step_dt,
                                   'algorithm': algorithm, 'subdivision': depth,
                                   'return_code': 0})
                return
            cached_dt = None
            events.append({'start_s': start, 'dt_s': step_dt,
                           'algorithm': algorithm, 'subdivision': depth,
                           'return_code': code})
        if step_dt / 2 < config['min_dt_s'] - 1.e-12:
            raise RuntimeError(f'Transient failed at t={start:.8g} s, dt={step_dt:.8g} s')
        advance(step_dt / 2, depth + 1)
        advance(step_dt / 2, depth + 1)

    def record():
        t = float(ops.getTime())
        input_acc = np.array([np.interp(t, times, acc[:, i]) if axis in directions else 0.
                              for i, axis in enumerate(('x', 'y'))])
        previous = np.zeros(2)
        for floor, node in enumerate(model['floor_monitors'], 1):
            disp = np.asarray(ops.nodeDisp(node)[:3]) - gravity_offsets[node]
            relative_acc = np.asarray(ops.nodeAccel(node)[:2])
            drift = (disp[:2] - previous) / model['story_heights_mm'][floor - 1]
            previous = disp[:2]
            row = {'time_s': t, 'story': floor, 'node': node,
                   'ux_relative_mm': float(disp[0]), 'uy_relative_mm': float(disp[1]),
                   'drift_x_rad': float(drift[0]), 'drift_y_rad': float(drift[1]),
                   'ax_relative_mm_s2': float(relative_acc[0]),
                   'ay_relative_mm_s2': float(relative_acc[1]),
                   'ax_absolute_mm_s2': float(relative_acc[0] + input_acc[0]),
                   'ay_absolute_mm_s2': float(relative_acc[1] + input_acc[1])}
            if not all(math.isfinite(v) for v in row.values()):
                raise RuntimeError(f'Nonfinite response at t={t}, floor={floor}')
            response.append(row)
        # Include inertial and damping terms in the support equilibrium.
        # OpenSees accepts one reaction option; -dynamic already includes
        # damping. Passing two flags silently selects the static response.
        ops.reactions('-dynamic')
        base.append({'time_s': t,
                     'support_rx_N': sum(ops.nodeReaction(n, 1) for n in model['base_nodes']),
                     'support_ry_N': sum(ops.nodeReaction(n, 2) for n in model['base_nodes'])})

    record()
    try:
        for sample in range(1, len(times)):
            step_started = time.perf_counter()
            if sample == 1:
                print('Starting first transient increment', flush=True)
            advance(float(times[sample] - ops.getTime()))
            advance_elapsed = time.perf_counter() - step_started
            if sample == 1:
                print('First transient increment converged; collecting responses', flush=True)
            record()
            if sample <= 3:
                print(f'Increment timing: solve={advance_elapsed:.3f}s, record={time.perf_counter()-step_started-advance_elapsed:.3f}s, iterations={ops.testIter()}',flush=True)
            if sample == 1 or sample % 20 == 0:
                print(f'Transient {ops.getTime():.2f}/{times[-1]:.2f} s', flush=True)
                (out / 'progress.json').write_text(
                    __import__('json').dumps({'completed_time_s':ops.getTime(),
                                               'target_time_s':float(times[-1]),'output_step':sample}),
                    encoding='utf-8')
    finally:
        write_csv(out / 'floor_response.csv', response)
        write_csv(out / 'base_reactions.csv', base)
        write_csv(out / 'solver_recovery.csv', events)
    if abs(ops.getTime() - times[-1]) > 1.e-8:
        raise RuntimeError('Transient did not reach the requested end time')
    peaks = []
    for floor in range(1, len(model['floor_monitors']) + 1):
        rows = [r for r in response if r['story'] == floor]
        peaks.append({'story': floor, **{f'peak_abs_{key}': max(abs(r[key]) for r in rows)
                      for key in ('ux_relative_mm', 'uy_relative_mm', 'drift_x_rad',
                                  'drift_y_rad', 'ax_absolute_mm_s2', 'ay_absolute_mm_s2')}})
    write_csv(out / 'response_peaks.csv', peaks)
    return {'passed': True, 'completed_time_s': float(ops.getTime()),
            'output_steps': len(times) - 1, 'directions': directions,
            'recovery_events': len(events), 'damping_ratio_assumed': zeta,
            'default_algorithm': default_algorithm,
            'rayleigh_alphaM': alpha, 'rayleigh_betaKinit': beta,
            'rayleigh_anchor_periods_s': [2 * math.pi / w1, 2 * math.pi / w2],
            'peaks_by_story': peaks}
