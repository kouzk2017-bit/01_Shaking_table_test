"""Model-information figures for review: materials, sections, geometry, mass,
damping and input.  Builds the model only; no gravity, modal or transient run.

Uniaxial curves come from fresh OpenSees copies of the exact recorded material
arguments (section/steel audits).  Wall shell concrete is driven through a
one-element plane-stress quad coupon, because NDTest needs 3D strain vectors.
Appearance and sizes follow 08_common/publication_style (user matplotlibrc; fixed width).

    python -B -m postprocessing.model_info_figures
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon, Rectangle  # noqa: E402
import numpy as np  # noqa: E402
import openseespy.opensees as ops  # noqa: E402
import sys  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '08_common' / 'python'))
from publication_style import apply_style, line_width, reference_line_kwargs, standard_size  # noqa: E402

from entrypoints import output  # noqa: E402

ROOT = output.ROOT
EXPERIMENT_ROOT = output.EXPERIMENT_ROOT
KIND_COLOR = {'column': 'C0', 'beam': 'C1', 'wall': 'C2', 'slab': 'C5', 'joint': 'C3'}
REGION_COLOR = {'boundary': 'C0', 'web': 'C2', 'beam_top': 'C1', 'beam_bottom': 'C1', 'beam_core': 'C3'}


def style(i):
    # The global cycle has six colours; vary the dash pattern beyond that.
    return dict(color=f'C{i % 6}', ls=('-', '--', ':', '-.')[i // 6 % 4])


def save(fig, out, name, index):
    path = out / f'{len(index) + 1:02d}_{name}.png'
    fig.savefig(path)
    plt.close(fig)
    index.append(path.name)
    return path


def uniaxial(material, args, path):
    """Stress history of a fresh uniaxial material copy along a strain path."""
    ops.wipe()
    ops.model('basic', '-ndm', 1, '-ndf', 1)
    ops.uniaxialMaterial(material, 1, *args)
    ops.testUniaxialMaterial(1)
    stress = []
    for strain in path:
        ops.setStrain(float(strain))
        stress.append(ops.getStress())
    return np.asarray(stress)


def steel_curve(params, rupture, path):
    ops.wipe()
    ops.model('basic', '-ndm', 1, '-ndf', 1)
    ops.uniaxialMaterial('Steel02', 1, params['fy_mpa'], params['es_mpa'], params['b'],
                         params['r0'], params['cr1'], params['cr2'])
    tag = 1
    if rupture:
        ops.uniaxialMaterial('MinMax', 2, 1, '-max', rupture)
        tag = 2
    ops.testUniaxialMaterial(tag)
    out = []
    for strain in path:
        ops.setStrain(float(strain))
        out.append(ops.getStress())
    return np.asarray(out)


def psumat_coupon(params, path):
    """Uniaxial (vertical) stress of a 1x1x1 mm PlaneStressUserMaterial quad."""
    ops.wipe()
    ops.model('basic', '-ndm', 2, '-ndf', 2)
    for tag, xy in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)], 1):
        ops.node(tag, *map(float, xy))
    ops.fix(1, 1, 1)
    ops.fix(2, 0, 1)
    ops.fix(4, 1, 0)
    ops.equalDOF(3, 4, 2)
    ops.nDMaterial('PlaneStressUserMaterial', 1, 40, 7, *params)
    ops.element('quad', 1, 1, 2, 3, 4, 1., 'PlaneStress', 1)
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)
    ops.load(3, 0., 1.)
    ops.constraints('Transformation')
    ops.numberer('Plain')
    ops.system('FullGeneral')
    ops.test('NormDispIncr', 1e-12, 50, 0)
    ops.algorithm('Newton')
    stress, done = [], []
    current = 0.
    for strain in path:
        ops.integrator('DisplacementControl', 3, 2, float(strain - current))
        ops.analysis('Static')
        if ops.analyze(1) != 0:
            break
        current = float(strain)
        ops.reactions()
        stress.append(-(ops.nodeReaction(1, 2) + ops.nodeReaction(2, 2)))
        done.append(current)
    return np.asarray(done), np.asarray(stress)


def cyclic(peaks, step=1e-5):
    path, current = [0.], 0.
    for peak in peaks:
        count = max(2, int(abs(peak - current) / step))
        path.extend(np.linspace(current, peak, count)[1:])
        current = peak
    return np.asarray(path)


def story_concretes(cfg):
    rows = []
    for story in cfg['stories']:
        rows.append((f"{story['story']}F", story['concrete']))
        if 'concrete_upper' in story:
            rows.append((f"{story['story']}F upper", story['concrete_upper']))
    return rows


def section_outline(ax, record):
    w, d, z0 = record['width_mm'], record['depth_mm'], record.get('reference_axis_above_web_centre_mm', 0.)
    c = record['cover_mm']
    ax.add_patch(Rectangle((-w / 2, -d / 2 - z0), w, d, fill=False))
    ax.add_patch(Rectangle((-w / 2 + c, -d / 2 + c - z0), w - 2 * c, d - 2 * c, fill=False, ls='--'))
    flange = record.get('flange')
    if flange:
        t = flange['thickness_mm']
        top = d / 2 - z0
        if flange['overhang_neg_mm'] > 0:
            ax.add_patch(Rectangle((-w / 2 - flange['overhang_neg_mm'], top - t), flange['overhang_neg_mm'], t,
                                   fill=False))
        if flange['overhang_pos_mm'] > 0:
            ax.add_patch(Rectangle((w / 2, top - t), flange['overhang_pos_mm'], t, fill=False))
    for bar in record['bars']:
        if bar['region'] == 'flange':
            ax.plot(bar['y'], bar['z'] - z0, 's', color='C1', ms=3)
        else:
            ax.add_patch(Circle((bar['y'], bar['z'] - z0), bar['diameter_mm'] / 2, color='C0'))
    ax.axhline(0., **reference_line_kwargs(color='C3'))
    ax.set_aspect('equal')
    ax.autoscale_view()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'config' / 'specimen_2015.json')
    parser.add_argument('--analysis-config', type=Path, default=ROOT / 'config' / 'analysis.json')
    parser.add_argument('--modal-run', type=str, default='modal',
                        help='Existing modal result folder used for the damping figure; nothing is rerun')
    args = parser.parse_args(argv)
    out = output.start('model_info')
    try:
        make(out, args)
    except BaseException:
        output.finish(out, 'model_info', False)
        raise
    out = output.finish(out, 'model_info', True)
    print(out)
    return out


def make(out, args):
    apply_style('paper')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ') + '_model_info'
    results = output.RESULTS
    (out / 'audit').mkdir()
    cfg = json.loads(args.config.read_text(encoding='utf-8'))
    analysis = json.loads(args.analysis_config.read_text(encoding='utf-8'))

    from model.build import build_model
    model = build_model(cfg, out / 'audit')
    sections = json.loads((out / 'audit' / 'section_audit.json').read_text(encoding='utf-8'))
    shells = json.loads((out / 'audit' / 'shell_section_audit.json').read_text(encoding='utf-8'))
    steel = json.loads((out / 'audit' / 'steel_material_audit.json').read_text(encoding='utf-8'))
    by_key = {r['key']: r for r in sections}
    nodes = {n['node']: np.array([n['x_mm'], n['y_mm'], n['z_mm']]) for n in model['nodes']}
    transforms = {t['tag']: t for t in model['transforms']}
    index = []

    # 1. Concrete properties by story.
    rows = story_concretes(cfg)
    labels = [r[0] for r in rows]
    fc = np.array([r[1]['fc_mpa'] for r in rows])
    ec = np.array([r[1]['ec_mpa'] for r in rows])
    ypos = np.arange(len(rows))
    fig, axes = plt.subplots(1, 3, figsize=standard_size(10, 4.5), sharey=True)
    axes[0].barh(ypos, fc)
    axes[0].set_xlabel('Measured $f_c$ (MPa)')
    axes[1].barh(ypos, ec / 1000.)
    axes[1].set_xlabel('$E_c$ (GPa)')
    core = cfg['section_settings'].get('concrete', {})
    sf, pf = core.get('core_strength_factor', 1.18), core.get('core_peak_strain_factor', 1.35)
    axes[2].plot(2 * fc / ec * 1000, ypos, 'o-', label=r'cover $\varepsilon_0=2f_c/E_c$')
    axes[2].plot(2 * fc / ec * pf * 1000, ypos, 's-', label=r'core $\varepsilon_0\times$' + f'{pf}')
    axes[2].set_xlabel(r'Peak strain $\varepsilon_0$ (‰)')
    axes[2].legend(loc='upper right', fontsize='small')
    axes[0].set_yticks(ypos, labels)
    axes[0].set_ylabel('Story')
    save(fig, out, 'concrete_properties_by_story', index)

    # 2. Steel properties.
    frame_steel = steel['frame_steel02_by_diameter']
    dias = sorted(frame_steel, key=float)
    fig, axes = plt.subplots(1, 2, figsize=standard_size(9, 3.8))
    for ax, key, label in ((axes[0], 'fy_mpa', '$f_y$ (MPa)'), (axes[1], 'es_mpa', '$E_s$ (GPa)')):
        values = [frame_steel[d][key] / (1000. if key == 'es_mpa' else 1.) for d in dias]
        bars = ax.bar([f'D{d}' for d in dias], values)
        for d, bar in zip(dias, bars):
            if 'Assumption' in cfg['section_settings']['steel_by_diameter'][d].get('source', ''):
                bar.set_hatch('//')
                bar.set_alpha(.5)
        ax.set_ylabel(label)
        for bar, v in zip(bars, values):
            ax.annotate(f'{v:.1f}', (bar.get_x() + bar.get_width() / 2, v), ha='center', va='bottom')
    axes[0].set_xlabel('Hatched: assumed')
    axes[1].set_xlabel('Others: measured mean')
    save(fig, out, 'steel_properties', index)

    # 3-4. Concrete02 monotonic (cover/core) and tension, from recorded args.
    first = {}
    for rec in sections:
        story = rec['key'].split('_')[0]
        part = rec['key'].split('_')[2] if rec['key'].count('_') == 2 else None
        if rec['key'].split('_')[1] in ('C1', 'C2'):
            label = f'{story}F' + (' upper' if part == '1' else '')
            first.setdefault(label, rec)
    comp = np.linspace(0., -0.02, 801)
    ten = np.linspace(0., 0.004, 401)
    fig, axes = plt.subplots(3, 1, figsize=standard_size(6.5, 11))
    for i, (label, rec) in enumerate(first.items()):
        axes[0].plot(-comp * 1000, -uniaxial('Concrete02', rec['concrete02_cover_args'], comp), label=label, **style(i))
        axes[1].plot(-comp * 1000, -uniaxial('Concrete02', rec['concrete02_core_args'], comp), **style(i))
        axes[2].plot(ten * 1000, uniaxial('Concrete02', rec['concrete02_cover_args'], ten), **style(i))
    axes[0].set(xlabel='Compressive strain (‰)', ylabel='Compressive stress (MPa)')
    axes[1].set(xlabel='Compressive strain (‰)', ylabel='Core compressive stress (MPa)')
    axes[2].set(xlabel='Tensile strain (‰)', ylabel='Tensile stress (MPa)')
    axes[0].legend(ncol=2, fontsize='small')
    save(fig, out, 'concrete02_frame_monotonic_cover_core_tension', index)

    rec = first['1F']
    path = cyclic([-0.002, 0.0003, -0.004, 0.0006, -0.008, 0.001, -0.014, 0.])
    fig, axes = plt.subplots(1, 2, figsize=standard_size(10, 4))
    for ax, key, name in ((axes[0], 'concrete02_cover_args', 'cover'), (axes[1], 'concrete02_core_args', 'core')):
        ax.plot(path * 1000, uniaxial('Concrete02', rec[key], path))
        ax.set(xlabel='Strain (‰)', ylabel=f'1F {name} stress (MPa)')
    save(fig, out, 'concrete02_frame_cyclic_1F', index)

    # 5. Steel02 (frame MinMax rupture and shell continuous).
    fig, axes = plt.subplots(1, 2, figsize=standard_size(10, 4))
    mono = np.linspace(0., 0.08, 1601)
    rupture = steel['frame_rupture_minmax']['max_strain'] if steel['frame_rupture_minmax']['enabled'] else None
    for d in dias:
        axes[0].plot(mono * 100, steel_curve(frame_steel[d], rupture, mono), label=f'D{d}')
    axes[0].set(xlabel='Tensile strain (%)', ylabel='Stress (MPa)')
    axes[0].legend()
    path = cyclic([0.01, -0.005, 0.02, -0.01, 0.03, -0.015, 0.])
    axes[1].plot(path * 100, steel_curve(frame_steel['22'], rupture, path))
    axes[1].set(xlabel='Strain (%)', ylabel='D22 cyclic stress (MPa)')
    save(fig, out, 'steel02_frame_monotonic_cyclic', index)

    # 6. Wall shell concrete (PlaneStressUserMaterial) coupon curves.
    seen = {}
    for rec in shells:
        for layer in rec['plane_stress_user_material']:
            name = f"{rec['key'].split('_')[1]}F {'confined' if layer['confined'] else 'unconfined'}"
            if 'upper' in rec['key']:
                name += ' upper'
            seen.setdefault(name, [layer[k] for k in ('fc', 'ft', 'fcu', 'epsc0', 'epscu', 'epstu', 'stc')])
    fig, axes = plt.subplots(2, 1, figsize=standard_size(6.5, 8))
    comp = np.linspace(0., -0.02, 401)
    ten = np.linspace(0., 0.003, 301)
    stories = sorted({n.split(' ', 1)[0] + (' upper' if 'upper' in n else '') for n in seen})
    for name, params in seen.items():
        key = name.split(' ', 1)[0] + (' upper' if 'upper' in name else '')
        kw = dict(color=f'C{stories.index(key) % 6}', ls='-' if 'unconfined' in name else '--',
                  marker=None if stories.index(key) < 6 else '.', markevery=40)
        strain, stress = psumat_coupon(params, comp)
        axes[0].plot(-strain * 1000, -stress, label=name, **kw)
        strain, stress = psumat_coupon(params, ten)
        axes[1].plot(strain * 1000, stress, **kw)
    axes[0].set(xlabel='Compressive strain (‰)', ylabel='Uniaxial stress (MPa)')
    axes[1].set(xlabel='Tensile strain (‰)', ylabel='Uniaxial stress (MPa)')
    axes[1].legend(*axes[0].get_legend_handles_labels(), ncol=2, fontsize='x-small', loc='upper right')
    save(fig, out, 'wall_shell_concrete_psumat_coupon', index)

    # 7. Wall layered-shell sections.
    keys = [r['key'] for r in shells]
    fig, axes = plt.subplots(1, 2, figsize=standard_size(11, max(5, .22 * len(keys))), sharey=True)
    y = np.arange(len(keys))
    thickness = np.array([r['thickness_mm'] for r in shells])
    vertical = np.array([2 * r['vertical_steel_face_mm'] / r['thickness_mm'] * 100 for r in shells])
    horizontal = np.array([2 * r['horizontal_steel_face_mm'] / r['thickness_mm'] * 100 for r in shells])
    axes[0].barh(y, thickness)
    axes[0].set_xlabel('Shell thickness (mm)')
    axes[1].plot(vertical, y, 'o', label='vertical')
    axes[1].plot(horizontal, y, 's', label='horizontal')
    axes[1].set_xlabel('Smeared reinforcement ratio (%)')
    axes[1].legend()
    axes[0].set_yticks(y, keys, fontsize='x-small')
    save(fig, out, 'wall_layered_shell_sections', index)

    # 8. Column fiber sections.
    for name in ('C1', 'C2', 'C3'):
        fig, axes = plt.subplots(5, 2, figsize=standard_size(6.5, 12))
        for ax, f in zip(axes.flat, range(1, 11)):
            r = by_key.get(f'{f}_{name}_0')
            if not r:
                ax.set_axis_off()
                ax.text(.5, .5, f'{f}F {name}: wall boundary (shell)', ha='center', transform=ax.transAxes)
                continue
            section_outline(ax, r)
            n = sum(1 for b in r['bars'] if b['region'] != 'flange')
            ax.set_title(f"{f}F {name} {r['width_mm']:.0f}x{r['depth_mm']:.0f}, {n}-D{r['bars'][0]['diameter_mm']:g}",
                         fontsize='small')
        fig.supxlabel('local y = -global Y (mm)')
        fig.supylabel('local z = global X (mm)')
        save(fig, out, f'column_sections_{name}', index)

    # 9. Beam fiber sections, one sheet per floor; the first flange variant per beam.
    names = [f'G{i}' for i in range(1, 10)] + ['B1']
    for floor in range(1, 11):
        fig, axes = plt.subplots(len(names), 3, figsize=standard_size(9, 2.1 * len(names)))
        for row, name in enumerate(names):
            variants = sorted(k for k in by_key if k.startswith(f'{floor}_{name}_0_'))
            variants = variants or sorted(k for k in by_key if k.startswith(f'{floor}_{name}_1_'))
            for col in range(3):
                ax = axes[row, col]
                match = [k for k in variants if k.split('_')[3].startswith(str(col))]
                if not match:
                    ax.set_axis_off()
                    ax.text(.5, .5, f'{name}: shell band', ha='center', transform=ax.transAxes)
                    continue
                r = by_key[match[0]]
                section_outline(ax, r)
                top = sum(1 for b in r['bars'] if b['region'] != 'flange' and b['z'] > 0)
                bottom = sum(1 for b in r['bars'] if b['region'] != 'flange' and b['z'] < 0)
                ax.set_title(f"{name} {('i-end', 'mid', 'j-end')[col]} {r['width_mm']:.0f}x{r['depth_mm']:.0f} "
                             f"top {top}/bot {bottom}-D{r['bars'][0]['diameter_mm']:g}", fontsize='x-small')
        fig.supxlabel('local y (mm); horizontal line = reference axis (gross centroid); squares = slab bars')
        save(fig, out, f"beam_sections_floor{cfg['stories'][floor - 1]['floor_label']}", index)

    # 10. 3D model by element kind.
    fig = plt.figure(figsize=standard_size(7, 9))
    ax = fig.add_subplot(111, projection='3d')
    for e in model['elements']:
        if e['kind'] == 'slab':
            continue
        tags = [int(t) for t in e['nodes'].split(';')]
        if len(tags) == 4:
            tags.append(tags[0])
        xyz = np.array([nodes[t] for t in tags]) / 1000
        ax.plot(*xyz.T, color=KIND_COLOR[e['kind']], lw=.5)
    for kind, color in KIND_COLOR.items():
        if kind != 'slab':
            ax.plot([], [], color=color, label=kind)
    ax.legend()
    ax.set(xlabel='X (m)', ylabel='Y (m)', zlabel='Z (m)')
    ax.set_box_aspect((12, 8, 25.75))
    save(fig, out, 'model_3d_element_kinds', index)

    # 11. Floor plans (2F and 3F: alternating stair opening) with mass lumps.
    lumps = {}
    for m in model['mass_lumps']:
        lumps.setdefault(m['story'], []).append(m)
    fig, axes = plt.subplots(2, 1, figsize=standard_size(6.5, 9))
    for ax, story in zip(axes, (1, 2)):
        z = model['floor_mass_properties'][story - 1]
        for e in model['elements']:
            if e['story'] != story or e['kind'] not in ('slab', 'beam', 'joint'):
                continue
            tags = [int(t) for t in e['nodes'].split(';')]
            xy = np.array([nodes[t][:2] for t in tags]) / 1000
            if e['kind'] == 'slab':
                ax.add_patch(Polygon(xy, closed=True, fill=False, ec='C5', lw=.4))
            else:
                ax.plot(*xy.T, color=KIND_COLOR[e['kind']], lw=3 if e['kind'] == 'joint' else 1.2)
        st = cfg['stories'][story - 1]
        for ix, x in enumerate(cfg['geometry']['x_grid_mm']):
            for iy, y in enumerate(cfg['geometry']['y_grid_mm']):
                name = 'C3' if iy in (1, 2) else 'C1' if ix in (0, 3) else 'C2'
                c = st['columns'][name]
                ax.add_patch(Rectangle(((x - c['b_x_mm'] / 2) / 1000, (y - c['b_y_mm'] / 2) / 1000),
                                       c['b_x_mm'] / 1000, c['b_y_mm'] / 1000, color='C0', alpha=.6))
        if story <= cfg['wall']['last_story']:
            for ix in cfg['wall']['grid_x_indices']:
                x = cfg['geometry']['x_grid_mm'][ix] / 1000
                ax.plot([x, x], [2.875, 5.125], color='C2', lw=4, alpha=.6)
        masses = lumps[story]
        xy = np.array([nodes[m['node']][:2] for m in masses]) / 1000
        size = np.array([m['mass_t'] for m in masses])
        ax.scatter(*xy.T, s=size / size.max() * 40, color='C4', zorder=3)
        ax.plot(z['cm_x_mm'] / 1000, z['cm_y_mm'] / 1000, '*', color='C3', ms=12, zorder=4)
        ax.set_title(f"Floor {z['floor_label']} (story {story} top): mass {z['mass_t']:.1f} t", fontsize='small')
        ax.set(xlabel='X (m)', ylabel='Y (m)')
        ax.set_aspect('equal')
    save(fig, out, 'floor_plans_mass_lumps', index)

    # 12. Elevations: wall line x=0 and frame line y=0, with rigid offsets.
    fig, axes = plt.subplots(1, 2, figsize=standard_size(12, 10))
    for ax, (axis, value, h) in zip(axes, ((0, 0., 1), (1, 0., 0))):
        for e in model['elements']:
            tags = [int(t) for t in e['nodes'].split(';')]
            pts = np.array([nodes[t] for t in tags])
            if not np.allclose(pts[:, axis], value) or e['kind'] == 'slab':
                continue
            pts2 = pts[:, [h, 2]] / 1000
            if e['kind'] == 'wall':
                region = e['member'].split('_', 1)[1]
                ax.add_patch(Polygon(pts2, closed=True, fc=REGION_COLOR[region], ec='k', lw=.2, alpha=.5))
                continue
            if e['kind'] == 'joint':
                ax.plot(*pts2.T, color='C3', lw=4)
                continue
            t = transforms.get(e['transform'])
            oi = np.array(t['offset_i_mm'])[[h, 2]] / 1000 if t else np.zeros(2)
            oj = np.array(t['offset_j_mm'])[[h, 2]] / 1000 if t else np.zeros(2)
            a, b = pts2[0], pts2[1]
            ax.plot([a[0], a[0] + oi[0]], [a[1], a[1] + oi[1]], color='C3', lw=4)
            ax.plot([b[0], b[0] + oj[0]], [b[1], b[1] + oj[1]], color='C3', lw=4)
            ax.plot([a[0] + oi[0], b[0] + oj[0]], [a[1] + oi[1], b[1] + oj[1]], color=KIND_COLOR[e['kind']], lw=1)
        ax.set(xlabel=('Y' if h == 1 else 'X') + ' (m)', ylabel='Z (m)')
        ax.set_aspect('equal')
    for region, color in REGION_COLOR.items():
        axes[0].add_patch(Rectangle((0, 0), 0, 0, fc=color, alpha=.5, label=f'shell {region}'))
    axes[0].plot([], [], color='C3', lw=4, label='rigid offset / joint zone')
    fig.legend(loc='lower center', ncol=3, fontsize='small', bbox_to_anchor=(.5, -.06))
    axes[0].set_title('Wall line X=0 (YZ elevation)', fontsize='small')
    axes[1].set_title('Frame line Y=0 (XZ elevation)', fontsize='small')
    save(fig, out, 'elevations_wall_frame_rigid_offsets', index)

    # 13. Floor masses and heights.
    props = model['floor_mass_properties']
    labels = [p['floor_label'] for p in props]
    y = np.arange(len(props))
    fig, axes = plt.subplots(1, 3, figsize=standard_size(11, 4.2), sharey=True)
    axes[0].barh(y, [p['mass_t'] for p in props])
    axes[0].set_xlabel('Floor mass (t)')
    axes[1].barh(y, cfg['geometry']['story_heights_mm'])
    axes[1].set_xlabel('Story height (mm)')
    axes[2].plot([p['cm_x_mm'] - 6000 for p in props], y, 'o-', label='X')
    axes[2].plot([p['cm_y_mm'] - 4000 for p in props], y, 's-', label='Y')
    axes[2].set_xlabel('CM offset (mm)')
    axes[2].legend()
    axes[0].set_yticks(y, labels)
    save(fig, out, 'floor_mass_height_cm', index)

    # 14. Rayleigh damping versus period, existing modal run (not rerun).
    modal_csv = results / args.modal_run / 'modal_after_gravity.csv'
    if modal_csv.exists():
        with modal_csv.open(encoding='utf-8-sig') as stream:
            modes = list(csv.DictReader(stream))
        periods = np.array([float(m['period_s']) for m in modes])
        w1 = 2 * np.pi / periods.max()
        w2 = w1 / analysis.get('damping_anchor_period_ratio', 0.2)
        zeta = analysis['damping_ratio']
        alpha, beta = 2 * zeta * w1 * w2 / (w1 + w2), 2 * zeta / (w1 + w2)
        t = np.linspace(.03, 1.2, 500)
        w = 2 * np.pi / t
        fig, ax = plt.subplots()
        ax.plot(t, (alpha / (2 * w) + beta * w / 2) * 100, label='Rayleigh (current model periods)')
        for m in modes:
            mx, my = float(m['effective_mass_X_ratio']), float(m['effective_mass_Y_ratio'])
            if max(mx, my) > .01:
                ax.axvline(float(m['period_s']), **reference_line_kwargs(color='C0' if mx > my else 'C1', linestyle=':'))
        ax.axvline(.85, color='C3', label='measured T1 frame (X) 0.85 s')
        ax.axvline(.58, color='C2', label='measured T1 wall (Y) 0.58 s')
        ax.set(xlabel='Period (s)', ylabel='Damping ratio (%)')
        ax.legend(fontsize='small')
        save(fig, out, 'rayleigh_damping_vs_period', index)

    # 15. Table input: SW, NE and their mean in model axes.
    from analysis import ground_motion as gm
    name, date, folder = gm.LOADING_CASES[13]
    path = EXPERIMENT_ROOT / 'data' / 'raw' / date / folder / f'{folder}_ENG_001-14.csv'
    raw_dt, _ = gm._read_headers(path)
    source = np.loadtxt(path, delimiter=',', skiprows=3, usecols=(0, *gm.SOURCE_CHANNELS), encoding='latin1')
    corners = gm._filter_and_decimate(source[:, 1:], raw_dt)
    time = np.arange(len(corners)) * gm.OUTPUT_DT_S + gm.OUTPUT_DT_S
    fig, axes = plt.subplots(2, 1, figsize=standard_size(9, 6), sharex=True)
    for ax, column, label in ((axes[0], 1, 'Model X'), (axes[1], 0, 'Model Y')):
        ax.plot(time, corners[:, column], lw=line_width(0.5), label='SW')
        ax.plot(time, corners[:, column + 3], lw=line_width(0.5), label='NE')
        ax.plot(time, .5 * (corners[:, column] + corners[:, column + 3]), label='mean (model input)')
        ax.set_ylabel(f'{label} acc. (m/s$^2$)')
        ax.legend(fontsize='small')
    axes[1].set(xlabel='Time (s)', xlim=(0, 20))
    save(fig, out, f'table_input_case13_{name.split("(")[1].rstrip(")")}', index)

    (out / 'figure_index.json').write_text(json.dumps(
        {'run_id': run_id, 'figures': index, 'modal_run_for_damping': args.modal_run,
         'note': 'Model built only; no gravity/modal/transient analysis was run.'},
        ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# 模型信息图', '',
             f'由 `04_opensees_model/postprocessing/model_info_figures.py` 于 {run_id[:15]}Z 生成；只建模，未做分析。',
             '材料曲线由 `audit/` 中记录的实际材料参数重新生成后加载得到。',
             '各图的检查要点和待确认事项见 `04_opensees_model/docs/MODEL_REVIEW.md`。', '']
    lines += [f'- `{name}`' for name in index]
    (out / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
