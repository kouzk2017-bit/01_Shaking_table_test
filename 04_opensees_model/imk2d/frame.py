"""2D frame-direction (model X) IMK model of the 2015 ten-story specimen.

Two plane frames share the floor displacement (equalDOF, rigid diaphragm):

* outer: grid lines y = 0 / 8000 (C1-C2-C2-C1, G1-G2-G3), multiplicity 2;
* inner: y = 3100 / 4900 (G4-G5-G6). Stories 1-7 each line carries half a
  Y-direction wall (C3 boundary + half web) bending about its weak axis;
  stories 8-10 the C3 columns. Multiplicity 2.

Each member is an elastic element between two zero-length IMKPeakOriented
rotational springs at the joint faces (Ibarra & Krawinkler n-factor
stiffness split). Joint panels are stiff elastic links from the joint centre
to the member faces. Positive beam-hinge rotation is sagging (bottom
tension); the slab flange (AIJ effective width, S1 bars) enters beam
strength only, while stiffness follows Haselton's web-only EIy.
N-mm-tonne-s; model X = drawing Y.
"""
from __future__ import annotations

from copy import deepcopy

import openseespy.opensees as ops

from imk2d.hinges import Section, haselton
from model.build import BAR_AREA, aij_overhang, beam_bars, column_bars

RIGID_E, RIGID_A, RIGID_I = 2.0e5, 1.0e7, 1.0e12


def member_table(spec, cfg):
    """Geometry, gravity axial forces and hinge parameters (no OpenSees calls)."""
    geom, stories, settings = spec['geometry'], spec['stories'], spec['section_settings']
    wall = spec['wall']
    xgrid, ygrid = geom['x_grid_mm'], geom['y_grid_mm']
    heights = geom['story_heights_mm']
    elev = [0.0]
    for h in heights:
        elev.append(elev[-1] + h)
    cover = settings['bar_centre_cover_mm']
    steel = {int(k): v for k, v in settings['steel_by_diameter'].items()}
    tr, hcfg = cfg['transverse_reinforcement'], cfg['hinges']
    tie_area = BAR_AREA[tr['bar_diameter_mm']]
    plan_area = (xgrid[-1] - xgrid[0]) * (ygrid[-1] - ygrid[0])
    frames = cfg['frames']

    def bar(z, area, diameter):
        return (z, area, steel[diameter]['fy_mpa'], steel[diameter]['es_mpa'])

    def is_pier(fname, story):
        return story <= frames[fname].get('wall_pier_through_story', 0)

    def column_depth(fname, story, ix):
        name = frames[fname]['columns'][ix]
        return stories[story - 1]['columns'][name]['b_x_mm']

    def panel_width(fname, floor, ix):
        # Joint panel along X: deepest of the columns below and above.
        return max(column_depth(fname, s, ix) for s in (floor, floor + 1) if 1 <= s <= 10)

    def beam_depth(fname, floor, ix):
        if floor == 0:
            return 0.0
        beams = stories[floor - 1]['beams']
        return max(beams[frames[fname]['beams'][bay]]['depth_mm'] for bay in (ix - 1, ix) if 0 <= bay < 3)

    def tributary_y(fname):
        y = frames[fname]['y_lines_mm'][0]
        i = ygrid.index(y)
        return sum(abs(ygrid[j] - y) / 2 for j in (i - 1, i + 1) if 0 <= j < len(ygrid))

    joints, beams, columns = [], [], []
    for fname, frame in frames.items():
        m, ty = frame['multiplicity'], tributary_y(fname)
        for floor in range(11):
            for ix, x in enumerate(xgrid):
                joints.append(dict(frame=fname, floor=floor, ix=ix, x_mm=x, z_mm=elev[floor],
                                   panel_mm=panel_width(fname, floor, ix) if floor else 0.0,
                                   beam_depth_mm=beam_depth(fname, floor, ix)))
        jt = {(j['floor'], j['ix']): j for j in joints if j['frame'] == fname}
        # Gravity: floor pressure x tributary width, uniform on the clear spans
        # and the joint-panel remainder as a point load at the joint centre.
        line_load = {f: stories[f - 1]['weight_kN'] * 1e3 / plan_area * ty for f in range(1, 11)}
        joint_load = {}
        for floor in range(1, 11):
            for ix in range(4):
                panel = jt[floor, ix]['panel_mm'] * (0.5 if ix in (0, 3) else 1.0)
                spans = [xgrid[b + 1] - xgrid[b] - jt[floor, b]['panel_mm'] / 2 - jt[floor, b + 1]['panel_mm'] / 2
                         for b in (ix - 1, ix) if 0 <= b < 3]
                jt[floor, ix]['gravity_point_N'] = line_load[floor] * panel
                joint_load[floor, ix] = line_load[floor] * (panel + sum(spans) / 2)

        for story in range(1, 11):
            for ix, x in enumerate(xgrid):
                data = stories[story - 1]['columns'][frame['columns'][ix]]
                axial = sum(joint_load[f, ix] for f in range(story, 11))
                clear = heights[story - 1] - jt[story - 1, ix]['beam_depth_mm'] / 2 - jt[story, ix]['beam_depth_mm'] / 2
                pier = is_pier(fname, story)
                db = data['bar_diameter_mm']
                bars = [bar(b['z'], b['area_mm2'], db) for b in column_bars(data, cover)]
                h, b = data['b_x_mm'], data['b_y_mm']
                rects = [(-h / 2, h / 2, b)]
                legs = tr['column_hoop_legs_frame_direction'][frame['columns'][ix]][story - 1]
                if pier:
                    # Half of the Y-direction wall web beside the C3 boundary.
                    t = wall['thickness_mm_by_story'][story - 1]
                    a, c = wall['y_centrelines_mm']
                    web = (c - a - b) / 2
                    dv = wall['vertical_diameter_mm_by_story'][story - 1]
                    per_face = BAR_AREA[dv] / wall['vertical_spacing_mm_by_story'][story - 1] * web
                    zv = t / 2 - wall['cover_mm'] - dv / 2
                    rects.append((-t / 2, t / 2, web))
                    bars += [bar(zv, per_face, dv), bar(-zv, per_face, dv)]
                concretes = [stories[story - 1]['concrete'],
                             stories[story - 1].get('concrete_upper', stories[story - 1]['concrete'])]
                ends = []
                for end, conc in zip(('bottom', 'top'), concretes):
                    sec = Section(rects, [bb for bb in bars], conc['fc_mpa'], conc['ec_mpa'])
                    my, phi, gov = sec.yield_point(axial, hcfg['yield_concrete_strain_factor'])
                    nu = axial / (sec.area * conc['fc_mpa'])
                    rho = sum(bb[1] for bb in bars) / sec.area
                    rho_sh = legs * tie_area / (b * tr['column_hoop_spacing_mm'])
                    p = haselton(nu, rho_sh, tr['column_hoop_spacing_mm'], db, steel[db]['fy_mpa'],
                                 conc['fc_mpa'], rho, hcfg['bond_slip_a_sl'], clear / 2 / h,
                                 tr['column_hoop_spacing_mm'] / (h - cover))
                    ends.append(dict(end=end, fc_mpa=conc['fc_mpa'], ec_mpa=conc['ec_mpa'], nu=nu,
                                     rho=rho, rho_sh=rho_sh, my_pos=my, my_neg=my, governs=gov,
                                     phi_y=phi, i_gross=sec.i_gross, area=sec.area, **p))
                columns.append(dict(frame=fname, multiplicity=m, story=story, ix=ix, x_mm=x,
                                    member='pier' if pier else frame['columns'][ix],
                                    b_mm=b, h_mm=h, bar_mm=db, clear_mm=clear, axial_N=axial,
                                    hoop_legs=legs, hoop_spacing_mm=tr['column_hoop_spacing_mm'],
                                    ends=ends))

        for floor in range(1, 11):
            story = stories[floor - 1]
            conc = story.get('concrete_upper', story['concrete'])
            for bay in range(3):
                name = frame['beams'][bay]
                data = deepcopy(story['beams'][name])
                if bay == 2:  # schedule i end is the outer end
                    data['top_counts_i_mid_j'].reverse()
                    data['bottom_counts_i_mid_j'].reverse()
                w, depth, db = data['width_mm'], data['depth_mm'], data['bar_diameter_mm']
                span = xgrid[bay + 1] - xgrid[bay]
                clear = span - jt[floor, bay]['panel_mm'] / 2 - jt[floor, bay + 1]['panel_mm'] / 2
                y = frame['y_lines_mm'][0]
                i = ygrid.index(y)
                overhang = sum(aij_overhang(abs(ygrid[j] - y) - w if 0 <= j < len(ygrid) else None, span)
                               for j in (i - 1, i + 1)) if cfg.get('slab_flange_in_beam_strength', True) else 0.0
                slab = spec['frame']['slab_flange']
                t = geom['slab_thickness_mm']
                spacing = tr['beam_stirrup_spacing_mm'][name][floor - 1]
                ends = []
                for end, loc in (('left', 0), ('right', 2)):
                    web_bars = [bar(bb['z'], bb['area_mm2'], db) for bb in beam_bars(data, loc, cover)]
                    rects = [(-depth / 2, depth / 2, w)]
                    bars = list(web_bars)
                    if overhang > 0:
                        rects.append((depth / 2 - t, depth / 2, overhang))
                        area = slab['long_direction_bar_area_per_mm'] * overhang
                        zc = slab['bar_centre_cover_mm']
                        bars += [bar(depth / 2 - zc, area, slab['bar_diameter_mm']),
                                 bar(depth / 2 - t + zc, area, slab['bar_diameter_mm'])]
                    sec = Section(rects, bars, conc['fc_mpa'], conc['ec_mpa'])
                    my_pos, phi_pos, gov_pos = sec.yield_point(0.0, hcfg['yield_concrete_strain_factor'])
                    my_neg, phi_neg, gov_neg = sec.flipped().yield_point(0.0, hcfg['yield_concrete_strain_factor'])
                    rho = sum(bb[1] for bb in web_bars) / (w * depth)
                    rho_sh = tr['beam_stirrup_legs'] * tie_area / (w * spacing)
                    p = haselton(0.0, rho_sh, spacing, db, steel[db]['fy_mpa'], conc['fc_mpa'], rho,
                                 hcfg['bond_slip_a_sl'], clear / 2 / depth, spacing / (depth - cover))
                    ends.append(dict(end=end, fc_mpa=conc['fc_mpa'], ec_mpa=conc['ec_mpa'], nu=0.0,
                                     rho=rho, rho_sh=rho_sh, my_pos=my_pos, my_neg=-my_neg,
                                     governs=f'{gov_pos}/{gov_neg}', phi_y=phi_pos,
                                     top_bars=data['top_counts_i_mid_j'][loc],
                                     bottom_bars=data['bottom_counts_i_mid_j'][loc],
                                     i_gross=w * depth ** 3 / 12, area=w * depth, **p))
                beams.append(dict(frame=fname, multiplicity=m, floor=floor, bay=bay, member=name,
                                  x_mm=xgrid[bay], b_mm=w, h_mm=depth, bar_mm=db, clear_mm=clear,
                                  slab_overhang_mm=overhang, stirrup_spacing_mm=spacing,
                                  line_load_N_mm=line_load[floor], ends=ends))

    # Effective stiffness and IMK spring input, per real member.
    basis = {'EIy': 'eiy_ratio', 'EIstf40': 'eistf40_ratio'}[hcfg['stiffness_basis']]
    n = hcfg['n_factor']
    for member in columns + beams:
        ratio = sum(e[basis] for e in member['ends']) / 2 * hcfg['stiffness_scale']
        ec = sum(e['ec_mpa'] for e in member['ends']) / 2
        ei = ratio * ec * member['ends'][0]['i_gross']
        member.update(ei_ratio=ratio, ec_mpa=ec, ei_eff=ei, area_mm2=member['ends'][0]['area'],
                      ei_element=ei * (n + 1) / n)
        length = member['clear_mm']
        for e in member['ends']:
            # Member chord yield rotation in double curvature: My L / (6 EI).
            e['theta_y'] = e['my_pos'] * length / (6 * ei)
            e['theta_y_neg'] = abs(e['my_neg']) * length / (6 * ei)
            e['spring_k'] = (n + 1) * 6 * ei / length
            e['lamda'] = e['lam'] * (e['theta_y'] + e['theta_y_neg']) / 2
    return dict(joints=joints, columns=columns, beams=beams, elevations=elev,
                floor_mass_t=[s['weight_kN'] * 1e3 / geom['gravity_mm_s2'] for s in stories])


def build(table, cfg):
    """Create the OpenSees domain. Returns node/element bookkeeping."""
    hcfg = cfg['hinges']
    ops.wipe()
    ops.model('basic', '-ndm', 2, '-ndf', 3)
    ops.geomTransf('Linear', 1)
    ops.geomTransf('PDelta', 2)
    tags = dict(node=0, ele=0, mat=0)

    def new(kind):
        tags[kind] += 1
        return tags[kind]

    def node(x, z):
        tag = new('node')
        ops.node(tag, float(x), float(z))
        return tag

    def rigid(i, j):
        tag = new('ele')
        ops.element('elasticBeamColumn', tag, i, j, RIGID_A, RIGID_E, RIGID_I, 1)
        return tag

    def spring(i, j, member, end):
        m = member['multiplicity']
        mat = new('mat')
        cr = hcfg['cyclic_rate_c']
        uu, res = hcfg['ultimate_rotation_rad'], hcfg['residual_strength_ratio']
        ops.uniaxialMaterial('IMKPeakOriented', mat, m * end['spring_k'],
                             end['theta_p'], end['theta_pc'], uu, m * end['my_pos'], end['mc_my'], res,
                             end['theta_p'], end['theta_pc'], uu, m * abs(end['my_neg']), end['mc_my'], res,
                             *[end['lamda']] * 4, cr, cr, cr, cr, 1.0, 1.0)
        if i in base_set:
            # Support: fix the member end directly so reactions include it.
            ops.fix(j, 1, 1, 0)
            support_ends.append(j)
        else:
            ops.equalDOF(i, j, 1, 2)
        tag = new('ele')
        ops.element('zeroLength', tag, i, j, '-mat', mat, '-dir', 3)
        end['spring_element'] = tag
        return tag

    centre, faces, bases, rigid_links = {}, {}, {}, []
    base_set, support_ends = set(), []
    for j in table['joints']:
        key = (j['frame'], j['floor'], j['ix'])
        c = node(j['x_mm'], j['z_mm'])
        centre[key] = c
        if j['floor'] == 0:
            ops.fix(c, 1, 1, 1)
            bases[key] = c
            base_set.add(c)
            continue
        f = {}
        half_b, half_c = j['beam_depth_mm'] / 2, j['panel_mm'] / 2
        if j['ix'] > 0:
            f['left'] = node(j['x_mm'] - half_c, j['z_mm'])
        if j['ix'] < 3:
            f['right'] = node(j['x_mm'] + half_c, j['z_mm'])
        f['bottom'] = node(j['x_mm'], j['z_mm'] - half_b)
        if j['floor'] < 10:
            f['top'] = node(j['x_mm'], j['z_mm'] + half_b)
        for face in f.values():
            rigid_links.append(rigid(c, face))
        faces[key] = f

    members, springs = [], []
    for col in table['columns']:
        fr, s, ix = col['frame'], col['story'], col['ix']
        lower = bases[fr, 0, ix] if s == 1 else faces[fr, s - 1, ix]['top']
        upper = faces[fr, s, ix]['bottom']
        z1, z2 = ops.nodeCoord(lower)[1], ops.nodeCoord(upper)[1]
        a, b = node(col['x_mm'], z1), node(col['x_mm'], z2)
        springs.append((spring(lower, a, col, col['ends'][0]), col, col['ends'][0]))
        springs.append((spring(upper, b, col, col['ends'][1]), col, col['ends'][1]))
        m = col['multiplicity']
        tag = new('ele')
        ops.element('elasticBeamColumn', tag, a, b, m * col['area_mm2'], col['ec_mpa'],
                    m * col['ei_element'] / col['ec_mpa'], 2)
        col['element'] = tag
        members.append(tag)

    for beam in table['beams']:
        fr, f, bay = beam['frame'], beam['floor'], beam['bay']
        left, right = faces[fr, f, bay]['right'], faces[fr, f, bay + 1]['left']
        z = ops.nodeCoord(left)[1]
        a = node(ops.nodeCoord(left)[0], z)
        b = node(ops.nodeCoord(right)[0], z)
        # Positive spring deformation = sagging at both ends.
        springs.append((spring(left, a, beam, beam['ends'][0]), beam, beam['ends'][0]))
        springs.append((spring(b, right, beam, beam['ends'][1]), beam, beam['ends'][1]))
        m = beam['multiplicity']
        tag = new('ele')
        ops.element('elasticBeamColumn', tag, a, b, m * beam['area_mm2'], beam['ec_mpa'],
                    m * beam['ei_element'] / beam['ec_mpa'], 1)
        beam['element'] = tag
        members.append(tag)

    # Rigid floor in X: every joint centre follows the outer-frame x=0 joint.
    masters = []
    for floor in range(1, 11):
        master = centre['outer', floor, 0]
        masters.append(master)
        for key, tag in centre.items():
            if key[1] == floor and tag != master:
                ops.equalDOF(master, tag, 1)
        ops.mass(master, table['floor_mass_t'][floor - 1], 0.0, 0.0)
    return dict(centre=centre, faces=faces, bases=list(bases.values()) + support_ends, masters=masters,
                members=members, springs=springs, rigid_links=rigid_links,
                node_count=tags['node'], element_count=tags['ele'])


def apply_gravity_loads(table, domain):
    """Uniform clear-span load on beams plus joint-panel point loads (x multiplicity)."""
    ops.timeSeries('Linear', 1)
    ops.pattern('Plain', 1, 1)
    total = 0.0
    for beam in table['beams']:
        w = beam['line_load_N_mm'] * beam['multiplicity']
        ops.eleLoad('-ele', beam['element'], '-type', '-beamUniform', -w)
        total += w * beam['clear_mm']
    mult = {b['frame']: b['multiplicity'] for b in table['beams']}
    for j in table['joints']:
        if j['floor']:
            p = j['gravity_point_N'] * mult[j['frame']]
            ops.load(domain['centre'][j['frame'], j['floor'], j['ix']], 0.0, -p, 0.0)
            total += p
    return total
