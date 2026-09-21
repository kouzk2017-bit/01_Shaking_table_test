"""TJU-style rectangular RC fiber sections, in N, mm, t, s.

Adapted from ``02_TJU_test/.../model/prototype_and_scale_model.py``:
Concrete02 core/cover, Steel02 bars, displaced-concrete subtraction, elastic
torsion and shear section terms, and Lobatto integration. The chosen 3D
dispBeamColumn uses P/My/Mz/T only, so the Vy/Vz terms do not add member
shear flexibility. No TJU geometry or material
strengths are imported.  Create one factory after each ``ops.wipe()``.

Local x is the member axis; local y spans width and local z spans depth.
The 3D FiberSection strain convention is epsilon_x = epsilon_0 - y*kappa_z
+ z*kappa_y.  Thus bars separated in z resist My and bars separated in y
resist Mz.  The member's geomTransf defines those axes in the global model.

Factory settings are a dedicated dictionary, with required
``steel_by_diameter`` mapping diameter strings to ``fy_mpa`` and ``es_mpa``.
Optional steel fields: b, r0, cr1, cr2.  Optional global settings: cover_mm,
poisson, fiber_ny, fiber_nz, integration_points, subtract_displaced_concrete,
steel_rupture_enabled, steel_ultimate_strain, and tag_base.  ``concrete`` may
contain lambda, cover_epsu, cover_residual_ratio, tension_softening_strain,
core_strength_factor, core_peak_strain_factor, core_residual_ratio, core_epsu.
Values supplied to rect_section override those concrete settings.

The defaults for confinement and post-peak behavior are inherited analysis
assumptions, not measured properties of the 2015 specimen.  The cover initial
tangent equals measured Ec.  As in TJU, the core tangent is Ec times
core_strength_factor/core_peak_strain_factor; this is reported explicitly.
"""

from __future__ import annotations

from copy import deepcopy
import json
import math

import openseespy.opensees as ops


def _finite(value, name):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _positive(value, name):
    result = _finite(value, name)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive.")
    return result


def _positive_integer(value, name, minimum=1):
    result = _positive(value, name)
    if int(result) != result or result < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}.")
    return int(result)


class SectionFactory:
    """Build cached sections and expose numerical input audits in ``records``."""

    def __init__(self, config):
        self.config = deepcopy(config)
        self.cover_mm = _positive(config.get("cover_mm", 40.0), "cover_mm")
        self.poisson = _finite(config.get("poisson", 0.2), "poisson")
        if not -1.0 < self.poisson < 0.5:
            raise ValueError("poisson must lie strictly between -1 and 0.5.")
        self.ny = _positive_integer(config.get("fiber_ny", 8), "fiber_ny", 2)
        self.nz = _positive_integer(config.get("fiber_nz", 8), "fiber_nz", 2)
        self.nip = _positive_integer(config.get("integration_points", 5), "integration_points", 2)
        self.subtract = config.get("subtract_displaced_concrete", True)
        self.rupture = config.get("steel_rupture_enabled", False)
        if not isinstance(self.subtract, bool) or not isinstance(self.rupture, bool):
            raise ValueError("subtract_displaced_concrete and steel_rupture_enabled must be booleans.")
        self.ultimate = _positive(config.get("steel_ultimate_strain", 0.06), "steel_ultimate_strain")
        self._next_tag = _positive_integer(config.get("tag_base", 100000), "tag_base")
        self._steel = {}
        source = config.get("steel_by_diameter", {})
        if not source:
            raise ValueError("steel_by_diameter must provide measured fy_mpa and es_mpa for each bar diameter.")
        for raw_diameter, material in source.items():
            diameter = _positive(raw_diameter, "steel diameter")
            if diameter in self._steel:
                raise ValueError(f"Duplicate steel diameter {diameter:g}.")
            parameters = {
                "fy_mpa": _positive(material["fy_mpa"], "steel fy_mpa"),
                "es_mpa": _positive(material["es_mpa"], "steel es_mpa"),
                "b": _finite(material.get("b", 0.012), "steel b"),
                "r0": _positive(material.get("r0", 18.0), "steel r0"),
                "cr1": _finite(material.get("cr1", 0.925), "steel cr1"),
                "cr2": _positive(material.get("cr2", 0.15), "steel cr2"),
            }
            if not 0.0 <= parameters["b"] < 1.0 or not 0.0 < parameters["cr1"] < 1.0:
                raise ValueError("Steel02 requires 0 <= b < 1 and 0 < cr1 < 1.")
            if self.rupture and self.ultimate <= parameters["fy_mpa"] / parameters["es_mpa"]:
                raise ValueError("Steel rupture strain must exceed the yield strain.")
            self._steel[diameter] = parameters
        self._steel_tags = {}
        self._cache = {}
        self.records = []

    def _tag(self):
        result = self._next_tag
        self._next_tag += 1
        return result

    def _steel_material(self, diameter):
        if diameter not in self._steel_tags:
            data = self._steel[diameter]
            raw = self._tag()
            ops.uniaxialMaterial("Steel02", raw, data["fy_mpa"], data["es_mpa"],
                                 data["b"], data["r0"], data["cr1"], data["cr2"])
            material = raw
            if self.rupture:
                material = self._tag()
                ops.uniaxialMaterial("MinMax", material, raw, "-max", self.ultimate)
            self._steel_tags[diameter] = material
        return self._steel_tags[diameter]

    def rect_section(self, key, width_mm, depth_mm, concrete, bars):
        """Return (Aggregator section tag, Lobatto integration tag).

        ``concrete`` requires positive fc_mpa and ec_mpa; ft_mpa and cover_mm
        are optional.  Every bar needs y, z, area_mm2, diameter_mm.  Bar areas
        may be nominal JIS areas and need not equal pi*d**2/4.  Geometry and
        material checks are completed before any OpenSees command is issued.
        """
        key = str(key)
        if not key:
            raise ValueError("Section key must not be empty.")
        width = _positive(width_mm, "width_mm")
        depth = _positive(depth_mm, "depth_mm")
        data = {
            "lambda": 0.1, "cover_epsu": -0.006,
            "cover_residual_ratio": 0.2, "tension_softening_strain": 0.006,
            "core_strength_factor": 1.18, "core_peak_strain_factor": 1.35,
            "core_residual_ratio": 0.55, "core_epsu": -0.018,
            **self.config.get("concrete", {}), **concrete,
        }
        fc = _positive(data["fc_mpa"], "fc_mpa")
        ec = _positive(data["ec_mpa"], "ec_mpa")
        ft = _positive(data.get("ft_mpa", 0.23 * fc ** (2.0 / 3.0)), "ft_mpa")
        cover = _positive(data.get("cover_mm", self.cover_mm), "cover_mm")
        if 2.0 * cover >= min(width, depth):
            raise ValueError(f"Section {key}: cover leaves no confined core.")
        strength_factor = _positive(data["core_strength_factor"], "core_strength_factor")
        strain_factor = _positive(data["core_peak_strain_factor"], "core_peak_strain_factor")
        residual = _positive(data["cover_residual_ratio"], "cover_residual_ratio")
        core_residual = _positive(data["core_residual_ratio"], "core_residual_ratio")
        if residual > 1.0 or core_residual > strength_factor:
            raise ValueError("Concrete residual stress must not exceed its peak stress.")
        lam = _finite(data["lambda"], "lambda")
        if not 0.0 <= lam <= 1.0:
            raise ValueError("Concrete02 lambda must lie in [0, 1].")
        eps_peak = -2.0 * fc / ec
        core_eps_peak = eps_peak * strain_factor
        epsu = _finite(data["cover_epsu"], "cover_epsu")
        core_epsu = _finite(data["core_epsu"], "core_epsu")
        if not epsu < eps_peak < 0.0 or not core_epsu < core_eps_peak < 0.0:
            raise ValueError("Concrete ultimate strain must be more negative than its peak strain.")
        ets = ft / _positive(data["tension_softening_strain"], "tension_softening_strain")
        checked_bars = []
        y_core = width / 2.0 - cover
        z_core = depth / 2.0 - cover
        for index, bar in enumerate(bars):
            y = _finite(bar["y"], f"bar {index} y")
            z = _finite(bar["z"], f"bar {index} z")
            area = _positive(bar["area_mm2"], f"bar {index} area_mm2")
            diameter = _positive(bar["diameter_mm"], f"bar {index} diameter_mm")
            matches = [d for d in self._steel if math.isclose(d, diameter, rel_tol=0.0, abs_tol=1e-8)]
            if len(matches) != 1:
                raise ValueError(f"Section {key}: no steel properties for diameter {diameter:g} mm.")
            diameter = matches[0]
            radius = diameter / 2.0
            if abs(y) + radius > width / 2.0 + 1e-8 or abs(z) + radius > depth / 2.0 + 1e-8:
                raise ValueError(f"Section {key}: bar {index} crosses the concrete boundary.")
            for other in checked_bars:
                separation = math.hypot(y - other["y"], z - other["z"])
                if separation < (diameter + other["diameter_mm"]) / 2.0 - 1e-8:
                    raise ValueError(f"Section {key}: bar {index} overlaps another bar.")
            checked_bars.append({
                "y": y, "z": z, "area_mm2": area, "diameter_mm": diameter,
                "region": "core" if abs(y) <= y_core + 1e-8 and abs(z) <= z_core + 1e-8 else "cover",
            })
        if not checked_bars:
            raise ValueError(f"RC section {key} has no longitudinal reinforcement.")
        area_gross = width * depth
        area_core = 4.0 * y_core * z_core
        area_cover = area_gross - area_core
        area_steel = sum(bar["area_mm2"] for bar in checked_bars)
        area_steel_core = sum(bar["area_mm2"] for bar in checked_bars if bar["region"] == "core")
        area_steel_cover = area_steel - area_steel_core
        if area_steel >= area_gross or area_steel_core >= area_core or area_steel_cover >= area_cover:
            raise ValueError(f"Section {key}: reinforcement area exceeds its concrete region.")
        # Independent area and unit audit: each gross patch covers the rectangle
        # once; Parallel removes the steel area from that concrete contribution.
        patch_areas = [area_core, cover * depth, cover * depth,
                       (width - 2.0 * cover) * cover, (width - 2.0 * cover) * cover]
        if not math.isclose(sum(patch_areas), area_gross, rel_tol=1e-12):
            raise ValueError(f"Section {key}: concrete patches do not conserve gross area.")
        signature = json.dumps([width, depth, data, checked_bars], sort_keys=True)
        if key in self._cache:
            previous, tags = self._cache[key]
            if signature != previous:
                raise ValueError(f"Section key {key!r} was reused with different properties.")
            return tags

        core_ec = ec * strength_factor / strain_factor
        core_concrete_area = area_core - (area_steel_core if self.subtract else 0.0)
        cover_concrete_area = area_cover - (area_steel_cover if self.subtract else 0.0)
        ea_initial = ec * cover_concrete_area + core_ec * core_concrete_area
        ea_initial += sum(self._steel[bar["diameter_mm"]]["es_mpa"] * bar["area_mm2"] for bar in checked_bars)
        long_side, short_side = max(width, depth), min(width, depth)
        ratio = short_side / long_side
        torsion_j = long_side * short_side ** 3 * (1.0 / 3.0 - 0.21 * ratio * (1.0 - ratio ** 4 / 12.0))
        shear_modulus = ec / (2.0 * (1.0 + self.poisson))
        gj = shear_modulus * torsion_j  # MPa * mm^4 = N*mm^2
        ga = shear_modulus * (5.0 / 6.0) * area_gross  # MPa * mm^2 = N

        cover_tag, core_tag = self._tag(), self._tag()
        ops.uniaxialMaterial("Concrete02", cover_tag, -fc, eps_peak, -residual * fc,
                             epsu, lam, ft, ets)
        ops.uniaxialMaterial("Concrete02", core_tag, -fc * strength_factor,
                             core_eps_peak, -core_residual * fc, core_epsu, lam, ft, ets)
        replacement_tags = {}
        for bar in checked_bars:
            steel_tag = self._steel_material(bar["diameter_mm"])
            concrete_tag = core_tag if bar["region"] == "core" else cover_tag
            pair = (steel_tag, concrete_tag)
            if pair not in replacement_tags:
                material_tag = steel_tag
                if self.subtract:
                    material_tag = self._tag()
                    ops.uniaxialMaterial("Parallel", material_tag, steel_tag,
                                         concrete_tag, "-factors", 1.0, -1.0)
                replacement_tags[pair] = material_tag
            bar["steel_material_tag"] = steel_tag
            bar["assigned_material_tag"] = replacement_tags[pair]

        fiber_tag, section_tag, integration_tag = self._tag(), self._tag(), self._tag()
        ops.section("Fiber", fiber_tag, "-GJ", gj)
        y1, y2 = -width / 2.0, width / 2.0
        z1, z2 = -depth / 2.0, depth / 2.0
        ops.patch("rect", core_tag, self.ny, self.nz, -y_core, -z_core, y_core, z_core)
        ops.patch("rect", cover_tag, 2, self.nz, y1, z1, -y_core, z2)
        ops.patch("rect", cover_tag, 2, self.nz, y_core, z1, y2, z2)
        ops.patch("rect", cover_tag, self.ny, 2, -y_core, z1, y_core, -z_core)
        ops.patch("rect", cover_tag, self.ny, 2, -y_core, z_core, y_core, z2)
        for bar in checked_bars:
            ops.fiber(bar["y"], bar["z"], bar["area_mm2"], bar["assigned_material_tag"])
        shear_y_tag, shear_z_tag = self._tag(), self._tag()
        ops.uniaxialMaterial("Elastic", shear_y_tag, ga)
        ops.uniaxialMaterial("Elastic", shear_z_tag, ga)
        ops.section("Aggregator", section_tag, shear_y_tag, "Vy", shear_z_tag,
                    "Vz", "-section", fiber_tag)
        ops.beamIntegration("Lobatto", integration_tag, section_tag, self.nip)
        record = {
            "key": key, "width_mm": width, "depth_mm": depth, "cover_mm": cover,
            "section_tag": section_tag, "fiber_section_tag": fiber_tag,
            "integration_tag": integration_tag, "integration_points": self.nip,
            "fiber_ny": self.ny, "fiber_nz": self.nz,
            "cover_material_tag": cover_tag, "core_material_tag": core_tag,
            "fc_mpa": fc, "cover_ec_mpa": ec, "core_ec_mpa": core_ec,
            "cover_peak_strain": eps_peak, "core_peak_strain": core_eps_peak,
            "ft_mpa": ft, "ft_source": "input" if "ft_mpa" in data else "assumed Japanese 0.23*fc^(2/3)",
            "gross_area_mm2": area_gross, "core_patch_area_mm2": area_core,
            "cover_patch_area_mm2": area_cover, "steel_area_mm2": area_steel,
            "net_concrete_area_mm2": core_concrete_area + cover_concrete_area,
            "represented_area_mm2": core_concrete_area + cover_concrete_area + area_steel,
            "initial_ea_n": ea_initial, "elastic_gj_n_mm2": gj, "elastic_shear_ga_n": ga,
            "gross_iy_mm4": width * depth ** 3 / 12.0,
            "gross_iz_mm4": depth * width ** 3 / 12.0,
            "subtract_displaced_concrete": self.subtract,
            "steel_rupture_enabled": self.rupture,
            "steel_ultimate_strain": self.ultimate if self.rupture else None,
            "bars": checked_bars,
            "concrete_assumptions": {name: data[name] for name in (
                "lambda", "cover_epsu", "cover_residual_ratio", "tension_softening_strain",
                "core_strength_factor", "core_peak_strain_factor", "core_residual_ratio", "core_epsu")},
        }
        self.records.append(record)
        self._cache[key] = (signature, (section_tag, integration_tag))
        return section_tag, integration_tag
