"""Independent 3D 2015 wall-frame specimen, following the TJU formulation.

Model X = drawing/instrument Y (12 m long); model Y = drawing/instrument X
(8 m short); Z is vertical. N-mm-tonne-s. No import of the TJU global model.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import json
import math

import numpy as np
import openseespy.opensees as ops

from model.sections import SectionFactory


BAR_AREA = {10: 71.33, 13: 126.7, 16: 198.6, 19: 286.5, 22: 387.1}
LOBATTO_X = np.array([0., (1. - math.sqrt(3./7.))/2., .5, (1. + math.sqrt(3./7.))/2., 1.])
LOBATTO_W = [.05, 49./180., 16./45., 49./180., .05]


def column_bars(data, cover):
    # Vertical member vecxz=global X => local y=-global Y, local z=global X.
    width, depth = data['b_y_mm'], data['b_x_mm']
    yc, zc = width / 2 - cover, depth / 2 - cover
    count = data['bars_per_short_face']
    intermediate = data['intermediate_bars_per_long_face']
    diameter = data['bar_diameter_mm']
    points = [(y, float(z)) for y in [-yc, yc] for z in np.linspace(-zc, zc, count)]
    points += [(float(y), z) for z in [-zc, zc]
               for y in np.linspace(-yc, yc, intermediate + 2)[1:-1]]
    if len(points) != data['rebar_count']:
        raise ValueError('Column bar count does not match schedule')
    return [dict(y=y, z=z, area_mm2=BAR_AREA[diameter], diameter_mm=diameter) for y,z in points]


def beam_bars(data, position, cover):
    width, depth = data['width_mm'], data['depth_mm']
    diameter = data['bar_diameter_mm']
    yc, zc = width / 2 - cover, depth / 2 - cover
    points = []
    for sign, counts in [(1, data['top_counts_i_mid_j']), (-1, data['bottom_counts_i_mid_j'])]:
        count = counts[position]
        # The report shows these bars in one row, including 5/6-bar faces.
        # Fall back to two rows only when the assumed 25 mm clear gap cannot fit.
        capacity = int((2 * yc + diameter + 25.) // (diameter + 25.))
        layers = [count] if count <= capacity else [capacity, count-capacity]
        for layer, n in enumerate(layers):
            z = sign * (zc - layer * (diameter + 25.))
            # A single bar in a row sits on the centreline (linspace(.., 1) gives -yc).
            points.extend((float(y), z) for y in (np.linspace(-yc, yc, n) if n > 1 else [0.]))
    return [dict(y=y, z=z, area_mm2=BAR_AREA[diameter], diameter_mm=diameter) for y,z in points]


class ShellFactory:
    """TJU PlaneStressUserMaterial / PlateFromPlaneStress / LayeredShell."""
    def __init__(self, settings):
        self.settings = settings
        self.next_tag = 2000000
        self.cache = {}
        self.records = []

    def tag(self):
        self.next_tag += 1
        return self.next_tag

    def section(self, key, concrete, thickness, cover, vertical_face, horizontal_face,
                vertical_diameter, horizontal_diameter, confined=False):
        # Steel face values are area per unit in-plane length, i.e. layer mm.
        if key in self.cache:
            return self.cache[key]
        fc, ec = concrete['fc_mpa'], concrete['ec_mpa']
        ft = .23 * fc ** (2./3.)
        eps = -2. * fc / ec
        mats, psumat = [], []
        for core in [False, True]:
            plane, plate = self.tag(), self.tag()
            use_core = core and confined
            params = [fc * (1.18 if use_core else 1.), ft,
                      -fc * (.15 if use_core else .10),
                      eps * (1.35 if use_core else 1.),
                      -.018 if use_core else -.006, .001, .08]
            ops.nDMaterial('PlaneStressUserMaterial', plane, 40, 7, *params)
            psumat.append(dict(layer='core' if core else 'cover', confined=use_core,
                               **dict(zip(('fc','ft','fcu','epsc0','epscu','epstu','stc'), params))))
            ops.nDMaterial('PlateFromPlaneStress', plate, plane, ec / 2.4)
            mats.append(plate)
        steel_mats = []
        for diameter, angle in [(horizontal_diameter, 0.), (vertical_diameter, 90.)]:
            steel = self.settings['steel_by_diameter'][str(diameter)]
            raw, plate = self.tag(), self.tag()
            # Continuous Steel02 in shells; fracture is uncalibrated and disabled
            # for this low-amplitude initial-state trial (frame MinMax remains).
            ops.uniaxialMaterial('Steel02', raw, steel['fy_mpa'], steel['es_mpa'], .012, 18., .925, .15)
            ops.nDMaterial('PlateRebar', plate, raw, angle)
            steel_mats.append(plate)
        core_thickness = thickness - 2*cover - 2*(vertical_face + horizontal_face)
        if core_thickness <= 0:
            raise ValueError(f'Invalid layered shell thickness: {key}')
        layers = [(mats[0],cover), (steel_mats[1],vertical_face), (steel_mats[0],horizontal_face),
                  (mats[1],core_thickness), (steel_mats[0],horizontal_face),
                  (steel_mats[1],vertical_face), (mats[0],cover)]
        tag = self.tag()
        args = [item for pair in layers for item in pair]
        ops.section('LayeredShell', tag, len(layers), *args)
        self.cache[key] = tag
        self.records.append(dict(key=key, section_tag=tag, thickness_mm=thickness,
                                 fc_mpa=fc, ec_mpa=ec, confined=confined,
                                 vertical_steel_face_mm=vertical_face,
                                 horizontal_steel_face_mm=horizontal_face,
                                 vertical_steel_centroid_from_midplane_mm=thickness/2-cover-vertical_face/2,
                                 layers=[dict(material=m, thickness_mm=t) for m, t in
                                         zip(('cover','vertical_steel','horizontal_steel','core',
                                              'horizontal_steel','vertical_steel','cover'),
                                             (v for _, v in layers))],
                                 vertical_diameter_mm=vertical_diameter,
                                 horizontal_diameter_mm=horizontal_diameter,
                                 plane_stress_user_material=psumat, plate_shear_modulus_mpa=ec/2.4,
                                 layer_thickness_sum_mm=sum(v for _,v in layers)))
        return tag


def aij_overhang(clear_mm, span_mm):
    """AIJ RC standard effective slab width on one side of a continuous beam."""
    if clear_mm is None:
        return 0.
    if clear_mm < .5 * span_mm:
        return max(0., (.5 - .6 * clear_mm / span_mm) * clear_mm)
    return .1 * span_mm


def build_model(config, out):
    cfg = deepcopy(config)
    geom, wall, settings = cfg['geometry'], cfg['wall'], cfg['section_settings']
    frame = cfg.get('frame', {})
    xgrid, ygrid = geom['x_grid_mm'], geom['y_grid_mm']
    heights = geom['story_heights_mm']
    if len(cfg['stories']) != 10 or len(heights) != 10:
        raise ValueError('2015 specimen requires ten stories')
    elevations = np.r_[0., np.cumsum(heights)]
    formulation_frame = frame.get('element', 'forceBeamColumn')
    if formulation_frame not in ('forceBeamColumn', 'dispBeamColumn'):
        raise ValueError('frame.element must be forceBeamColumn or dispBeamColumn')
    use_offsets = frame.get('rigid_joint_offsets', True)
    joint_factor = float(frame.get('joint_zone_stiffness_factor', 10.))
    slab_flange = frame.get('slab_flange', {})
    ops.wipe()
    ops.model('basic', '-ndm', 3, '-ndf', 6)
    transforms = {}

    def transform(vecxz, di=(0., 0., 0.), dj=(0., 0., 0.)):
        # One PDelta transformation per distinct orientation and joint offset.
        # Offsets are global vectors from each node to the flexible member end.
        if not use_offsets:
            di = dj = (0., 0., 0.)
        key = (tuple(vecxz), tuple(round(v, 6) for v in di), tuple(round(v, 6) for v in dj))
        if key not in transforms:
            tag = len(transforms) + 1
            args = ['PDelta', tag, *vecxz]
            if any(key[1]) or any(key[2]):
                args += ['-jntOffset', *key[1], *key[2]]
            ops.geomTransf(*args)
            transforms[key] = tag
        return transforms[key]

    def column_at(floor, ix, iy):
        # Column whose top is at this floor (roof: story 10); walls use C3.
        story = cfg['stories'][max(floor, 1) - 1]
        name = 'C3' if iy in (1, 2) else 'C1' if ix in (0, 3) else 'C2'
        return story['columns'][name]

    def joint_depth(floor, ix, iy):
        # Largest depth of beams framing into grid node (ix, iy) at this floor.
        if floor == 0:
            return 0.
        beams = cfg['stories'][floor - 1]['beams']
        names = []
        for bay in (ix - 1, ix):
            if 0 <= bay < 3:
                names.append(f'G{bay + 1 if iy in (0, 3) else bay + 4}')
        for bay in (iy - 1, iy):
            if 0 <= bay < 3:
                names.append(f'G{bay + 7}')
        return max(beams[n]['depth_mm'] for n in names)

    transform((0., 0., 1.))
    transform((1., 0., 0.))
    sections, shells = SectionFactory(settings), ShellFactory(settings)
    nodes, elements, base_nodes = [], [], []
    node_lookup, coordinates = {}, {}
    element_tag, integration_tag = 0, 3000000
    cover = settings['bar_centre_cover_mm']
    floor_nodes = defaultdict(set)

    def node(x,y,z):
        coord = tuple(round(float(v), 7) for v in (x,y,z))
        if coord in node_lookup:
            return node_lookup[coord]
        tag = len(nodes) + 1
        ops.node(tag, *coord)
        nodes.append(dict(node=tag,x_mm=coord[0],y_mm=coord[1],z_mm=coord[2],kind='structural'))
        coordinates[tag] = coord
        node_lookup[coord] = tag
        if abs(z) < 1.e-8:
            ops.fix(tag,1,1,1,1,1,1)
            base_nodes.append(tag)
        for floor in range(1, 11):
            if abs(z-elevations[floor]) < 1.e-7:
                floor_nodes[floor].add(tag)
                break
        return tag

    def element(kind, formulation, tags, sec, floor, member, integration=None, transform=None):
        nonlocal element_tag
        element_tag += 1
        if formulation in ('dispBeamColumn', 'forceBeamColumn'):
            ops.element(formulation, element_tag, *tags, transform, integration)
        elif formulation == 'elasticBeamColumn':
            ops.element(formulation, element_tag, *tags, *sec, transform)
            sec = None
        elif formulation == 'ASDShellQ4' and not wall.get('enhanced_assumed_strain', True):
            ops.element(formulation, element_tag, *tags, sec, '-noeas')
        else:
            ops.element(formulation, element_tag, *tags, sec)
        elements.append(dict(element=element_tag,kind=kind,formulation=formulation,
                             nodes=';'.join(map(str,tags)),section_tag=sec,story=floor,member=member,
                             transform=transform))

    # Plate mesh resolves wall boundary centre/edges and the central stair opening.
    xmesh = sorted(set(xgrid + [4920,7080]))
    ymesh = sorted(set(ygrid + [2875,3325,4000,4675,5125]))
    for floor in range(11):
        for x in xgrid:
            for y in ygrid:
                node(x,y,elevations[floor])

    # Frames outside the integrated wall.  One prismatic line member per story,
    # except the documented concrete-pour change at 6F.
    for index, story in enumerate(cfg['stories']):
        floor = index+1
        bottom, top = elevations[index:index+2]
        for ix,x in enumerate(xgrid):
            for iy,y in enumerate(ygrid):
                if iy in (1,2) and floor <= wall['last_story']:
                    continue
                name = 'C3' if iy in (1,2) else 'C1' if ix in (0,3) else 'C2'
                data = story['columns'][name]
                breaks = [bottom,top]
                if 'concrete_upper' in story:
                    breaks.insert(1,bottom+story['upper_pour_starts_above_floor_mm'])
                # Rigid joint zones: half the deepest framing beam at each floor.
                off_bottom = joint_depth(index,ix,iy)/2.
                off_top = joint_depth(floor,ix,iy)/2.
                for part,(z1,z2) in enumerate(zip(breaks[:-1],breaks[1:])):
                    concrete = story['concrete_upper'] if part else story['concrete']
                    sec, integ = sections.rect_section(f'{floor}_{name}_{part}',data['b_y_mm'],data['b_x_mm'],
                                                       concrete,column_bars(data,cover))
                    di = (0.,0.,off_bottom if z1==bottom else 0.)
                    dj = (0.,0.,-off_top if z2==top else 0.)
                    element('column',formulation_frame,[node(x,y,z1),node(x,y,z2)],sec,floor,name,integ,
                            transform((1.,0.,0.),di,dj))

    # Integrated shell walls: C3 boundaries occupy their full 450 mm width and
    # the G8 top band occupies its physical depth. This avoids line/shell overlap.
    for index, story in enumerate(cfg['stories'][:wall['last_story']]):
        floor = index+1
        bottom, top = elevations[index:index+2]
        col, beam = story['columns']['C3'], story['beams']['G8']
        col_length = col['b_y_mm']
        a,b = wall['y_centrelines_mm']
        web = [float(v) for v in np.linspace(a+col_length/2,b-col_length/2,int(wall.get('web_divisions',2))+1)]
        ys = [a-col_length/2,a,*web,b,b+col_length/2]
        beam_bottom = top - beam['depth_mm']
        divisions = max(1,math.ceil((beam_bottom-bottom)/wall['mesh_target_mm']))
        zs = list(np.linspace(bottom,beam_bottom,divisions+1)) + [beam_bottom+100,top-100,top]
        if 'concrete_upper' in story:
            zs.append(bottom+story['upper_pour_starts_above_floor_mm'])
        zs = sorted(set(round(float(z),7) for z in zs))
        for ix in wall['grid_x_indices']:
            x=xgrid[ix]
            for ya,yb in zip(ys[:-1],ys[1:]):
                for za,zb in zip(zs[:-1],zs[1:]):
                    ym,zm=(ya+yb)/2,(za+zb)/2
                    is_boundary=ym<a+col_length/2 or ym>b-col_length/2
                    is_beam=zm>beam_bottom and not is_boundary
                    concrete=story['concrete']
                    pour='lower'
                    if 'concrete_upper' in story and zm>bottom+story['upper_pour_starts_above_floor_mm']:
                        concrete=story['concrete_upper'];pour='upper'
                    if is_boundary:
                        region='boundary'
                        thickness=col['b_x_mm']
                        vd=col['bar_diameter_mm'];hd=10
                        vertical_face=col['rebar_count']*BAR_AREA[vd]/(2*col_length)
                        horizontal_face=BAR_AREA[hd]/100.
                    elif is_beam:
                        thickness=beam['width_mm'];vd=10;hd=beam['bar_diameter_mm']
                        vertical_face=BAR_AREA[vd]/200.
                        if zm>top-100:
                            region='beam_top'
                            horizontal_face=beam['top_counts_i_mid_j'][1]*BAR_AREA[hd]/200.
                        elif zm<beam_bottom+100:
                            region='beam_bottom'
                            horizontal_face=beam['bottom_counts_i_mid_j'][1]*BAR_AREA[hd]/200.
                        else:
                            region='beam_core';horizontal_face=1.e-6
                    else:
                        region='web';thickness=wall['thickness_mm_by_story'][index]
                        vd=wall['vertical_diameter_mm_by_story'][index]
                        hd=wall['horizontal_diameter_mm_by_story'][index]
                        vertical_face=BAR_AREA[vd]/wall['vertical_spacing_mm_by_story'][index]
                        horizontal_face=BAR_AREA[hd]/wall['horizontal_spacing_mm_by_story'][index]
                    key=f'wall_{floor}_{region}_{pour}'
                    # Match the frame C3 longitudinal bar centroid across wall
                    # thickness, instead of using the thinner web cover.
                    shell_cover = cover - vertical_face/2 if is_boundary else wall['cover_mm']
                    sec=shells.section(key,concrete,thickness,shell_cover,vertical_face,horizontal_face,
                                       vd,hd,is_boundary)
                    tags=[node(x,ya,za),node(x,yb,za),node(x,yb,zb),node(x,ya,zb)]
                    element('wall','ASDShellQ4',tags,sec,floor,f'W{ix+1}_{region}')

    # Beam sections at five Lobatto points preserve distinct end/midspan bars.
    # Sub-elements lying wholly inside a column's plan width become stiff
    # elastic joint zones; partly overlapping ones get a rigid -jntOffset.
    # ``joint_only`` builds just those zones, used to embed the wall-line G8
    # into the C3 boundary shells so beam/column moments reach the wall as
    # force couples rather than through the ASDShellQ4 drilling DOF alone.
    def add_beam(floor, name, start, end, cuts, reverse=False, joints=(0.,0.), flange=None,
                 joint_only=False):
        nonlocal integration_tag
        story=cfg['stories'][floor-1]
        data=deepcopy(story['beams'][name])
        if reverse:
            data['top_counts_i_mid_j'].reverse();data['bottom_counts_i_mid_j'].reverse()
        concrete=story.get('concrete_upper',story['concrete'])
        start,end=np.array(start,dtype=float),np.array(end,dtype=float)
        length=float(np.linalg.norm(end-start));unit=(end-start)/length
        hi,hj=joints if use_offsets else (0.,0.)
        sec_tags=None
        if not joint_only:
            sec_tags=[]
            fkey='' if not flange else f"_f{flange['overhang_neg_mm']:.0f}_{flange['overhang_pos_mm']:.0f}"
            for loc in range(3):
                sec,_=sections.rect_section(f'{floor}_{name}_{int(reverse)}_{loc}{fkey}',data['width_mm'],
                                           data['depth_mm'],concrete,beam_bars(data,loc,cover),flange)
                sec_tags.append(sec)
        for r1,r2 in zip(cuts[:-1],cuts[1:]):
            s1,s2=r1*length,r2*length
            i=node(*(start+(end-start)*r1));j=node(*(start+(end-start)*r2))
            if s2<=hi+1e-6 or s1>=length-hj-1e-6:
                w,d,ec=data['width_mm'],data['depth_mm'],concrete['ec_mpa']
                props=(w*d*joint_factor,ec,ec/2.4,joint_factor*d*w**3/3.,
                       joint_factor*w*d**3/12.,joint_factor*d*w**3/12.)
                element('joint','elasticBeamColumn',[i,j],props,floor,f'{name}_joint',None,
                        transform((0.,0.,1.)))
                continue
            if joint_only:
                continue
            di,dj=max(0.,hi-s1),max(0.,s2-(length-hj))
            integration_tag+=1
            f1,f2=(s1+di)/length,(s2-dj)/length
            positions=f1+(f2-f1)*LOBATTO_X
            tags=[sec_tags[0 if p<.25 else 2 if p>.75 else 1] for p in positions]
            ops.beamIntegration('UserDefined',integration_tag,5,*tags,*LOBATTO_X,*LOBATTO_W)
            element('beam',formulation_frame,[i,j],tags[2],floor,name,integration_tag,
                    transform((0.,0.,1.),tuple(unit*di),tuple(-unit*dj)))

    def beam_flange(floor, name, span, clear_neg, clear_pos, per_mm):
        # Local y is +global Y for X-direction beams and -global X for Y beams.
        if not slab_flange.get('enabled', True):
            return None
        return dict(thickness_mm=geom['slab_thickness_mm'],
                    overhang_neg_mm=aij_overhang(clear_neg,span),
                    overhang_pos_mm=aij_overhang(clear_pos,span),
                    bar_area_per_mm=per_mm,
                    bar_diameter_mm=slab_flange.get('bar_diameter_mm',10),
                    bar_centre_cover_mm=slab_flange.get('bar_centre_cover_mm',30.))

    def clear(grid, index, step, width):
        # Clear distance to the adjacent parallel beam; None at a slab edge.
        other=index+step
        if not 0<=other<len(grid):
            return None
        return abs(grid[other]-grid[index])-width

    for floor in range(1,11):
        z=elevations[floor]
        beams=cfg['stories'][floor-1]['beams']
        for iy,y in enumerate(ygrid):
            for ix in range(3):
                name=f'G{ix+1 if iy in (0,3) else ix+4}'
                x1,x2=xgrid[ix:ix+2]
                cuts=[(x-x1)/(x2-x1) for x in xmesh if x1<=x<=x2]
                w=beams[name]['width_mm']
                flange=beam_flange(floor,name,x2-x1,clear(ygrid,iy,-1,w),clear(ygrid,iy,1,w),
                                   slab_flange.get('long_direction_bar_area_per_mm',0.))
                joints=(column_at(floor,ix,iy)['b_x_mm']/2.,column_at(floor,ix+1,iy)['b_x_mm']/2.)
                add_beam(floor,name,(x1,y,z),(x2,y,z),cuts,reverse=ix==2,joints=joints,flange=flange)
        for ix,x in enumerate(xgrid):
            for iy in range(3):
                y1,y2=ygrid[iy:iy+2]
                name=f'G{iy+7}'
                cuts=[(y-y1)/(y2-y1) for y in ymesh if y1<=y<=y2]
                w=beams[name]['width_mm']
                # Local +y is -global X, so the -X neighbour is on the positive side.
                flange=beam_flange(floor,name,y2-y1,clear(xgrid,ix,1,w),clear(xgrid,ix,-1,w),
                                   slab_flange.get('short_direction_bar_area_per_mm',0.))
                joints=(column_at(floor,ix,iy)['b_y_mm']/2.,column_at(floor,ix,iy+1)['b_y_mm']/2.)
                add_beam(floor,name,(x,y1,z),(x,y2,z),cuts,reverse=iy==2,joints=joints,flange=flange,
                         joint_only=iy==1 and floor<=wall['last_story'])

    # ShellMITC4 requires the eight-component membrane+plate section. The
    # five-component ElasticPlateSection used in TJU is not compatible with
    # this element (verified against OpenSees section source). Rigid floor
    # kinematics make the membrane strain zero, retaining the intended floor
    # in-plane constraint while providing a compatible bending/shear response.
    # Alternating stair opening x=4.92..8 / 4..7.08, y=B..C from S-9.
    tributary=defaultdict(float)
    for index,story in enumerate(cfg['stories']):
        floor=index+1;z=elevations[floor]
        ec=story.get('concrete_upper',story['concrete'])['ec_mpa']
        slab_tag=4000000+floor
        ops.section('ElasticMembranePlateSection',slab_tag,ec,.2,geom['slab_thickness_mm'],0.)
        opening=(4000,7080) if (floor+1) in (3,5,7) else (4920,8000)
        for xa,xb in zip(xmesh[:-1],xmesh[1:]):
            for ya,yb in zip(ymesh[:-1],ymesh[1:]):
                xm,ym=(xa+xb)/2,(ya+yb)/2
                if opening[0]<xm<opening[1] and 3100<ym<4900:
                    continue
                tags=[node(xa,ya,z),node(xb,ya,z),node(xb,yb,z),node(xa,yb,z)]
                element('slab','ShellMITC4',tags,slab_tag,floor,'S1')
                for tag in tags:
                    tributary[(floor,tag)]+=(xb-xa)*(yb-ya)/4

    # B1 at the edge of the central stair opening, as a fiber small beam.
    for floor in range(1,11):
        story=cfg['stories'][floor-1]
        story['beams']['B1']=dict(width_mm=200,depth_mm=250,bar_diameter_mm=16,
                                top_counts_i_mid_j=[2]*3,bottom_counts_i_mid_j=[2]*3)
        x=7080 if (floor+1) in (3,5,7) else 4920
        cuts=[(y-3100)/1800 for y in ymesh if 3100<=y<=4900]
        add_beam(floor,'B1',(x,3100,elevations[floor]),(x,4900,elevations[floor]),cuts)

    mass_lumps, monitors, masses = [],[],[]
    for index,story in enumerate(cfg['stories']):
        floor=index+1
        weights={tag:area for (f,tag),area in tributary.items() if f==floor}
        mass=story['weight_kN']*1000/geom['gravity_mm_s2']
        area_sum=sum(weights.values())
        if area_sum<=0 or mass<=0:
            raise ValueError('Missing floor tributary area or invalid floor mass')
        cx=sum(coordinates[tag][0]*area for tag,area in weights.items())/area_sum
        cy=sum(coordinates[tag][1]*area for tag,area in weights.items())/area_sum
        # Separate retained node, not constrained through any other MP relation.
        master=len(nodes)+1
        ops.node(master,cx,cy,float(elevations[floor]))
        ops.fix(master,0,0,1,1,1,0)
        nodes.append(dict(node=master,x_mm=cx,y_mm=cy,z_mm=float(elevations[floor]),kind='diaphragm_master'))
        coordinates[master]=(cx,cy,float(elevations[floor]))
        slaves=sorted(floor_nodes[floor])
        ops.rigidDiaphragm(3,master,*slaves)
        monitors.append(master)
        for tag,area in weights.items():
            nodal_mass=mass*area/area_sum
            # Same horizontal-only inertia convention as TJU; gravity load is
            # applied independently in global Z to these physical slab nodes.
            ops.mass(tag,nodal_mass,nodal_mass,0.,0.,0.,0.)
            mass_lumps.append(dict(story=floor,node=tag,mass_t=nodal_mass))
        inertia=sum(mass*area/area_sum*((coordinates[tag][0]-cx)**2+(coordinates[tag][1]-cy)**2)
                    for tag,area in weights.items())
        masses.append(dict(story=floor,floor_label=story['floor_label'],mass_t=mass,
                           weight_kN=story['weight_kN'],cm_x_mm=cx,cm_y_mm=cy,
                           inertia_z_t_mm2=inertia))

    # Connectivity and representation audits before the first solver call.
    used={int(n) for e in elements for n in e['nodes'].split(';')}
    uncon=sorted(set(coordinates)-used-set(monitors)-set(base_nodes))
    if uncon:
        raise ValueError(f'Unconnected non-base nodes: {uncon}')
    if len(ops.getNodeTags()) != len(nodes) or len(ops.getEleTags()) != len(elements):
        raise ValueError('OpenSees domain count mismatch')
    seen=set()
    for e in elements:
        key=tuple(sorted(int(n) for n in e['nodes'].split(';')))
        if key in seen:
            raise ValueError(f'Duplicate element connectivity: {key}')
        seen.add(key)
    represented=sum(x['mass_t'] for x in mass_lumps)
    expected=sum(x['mass_t'] for x in masses)
    if not math.isclose(represented,expected,rel_tol=1.e-12):
        raise ValueError('Floor mass audit failed')
    (out/'section_audit.json').write_text(json.dumps(sections.records,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'steel_material_audit.json').write_text(json.dumps(dict(
        frame_steel02_by_diameter={f'{d:g}':v for d,v in sections._steel.items()},
        frame_rupture_minmax=dict(enabled=sections.rupture,max_strain=sections.ultimate),
        shell_steel02=dict(b=.012,r0=18.,cr1=.925,cr2=.15,rupture='none')),
        ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'shell_section_audit.json').write_text(json.dumps(shells.records,ensure_ascii=False,indent=2),encoding='utf-8')
    return dict(nodes=nodes,elements=elements,mass_lumps=mass_lumps,base_nodes=base_nodes,
                floor_monitors=monitors,story_heights_mm=heights,floor_mass_properties=masses,
                gravity_mm_s2=geom['gravity_mm_s2'],total_height_mm=float(elevations[-1]),
                formulation_counts=dict(Counter(e['formulation'] for e in elements)),
                assumptions=cfg['assumptions'],axis_map=geom['input_axis_map'],
                boundary='fixed at structural 1F datum',moving_mass_excludes_base=True,
                transforms=[dict(tag=tag,vecxz=list(k[0]),offset_i_mm=list(k[1]),offset_j_mm=list(k[2]))
                            for k,tag in transforms.items()])
