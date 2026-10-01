"""Yield moments and IMK hinge parameters for the 2D frame-direction model.

Units N, mm. Rotations in rad. ``P`` is compression positive.

Yield moment: plane-section fiber analysis, Hognestad concrete (no tension,
initial tangent = Ec), elastic-perfectly plastic steel. Yield is the first of
tension steel at fy/Es or extreme concrete at ``factor``*fc/Ec (Panagiotakos &
Fardis 2001, the definition used by Haselton). Moments are taken about the
gross concrete centroid; positive moment compresses the +z face.

Deformation parameters: Haselton et al. (2016) / PEER 2007/03 equations for
RC columns (MPa units, c_units = 1).
"""
from __future__ import annotations

import math

import numpy as np


def _bisect(func, lo, hi, iterations=80):
    f_lo = func(lo)
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        f_mid = func(mid)
        if (f_mid > 0) == (f_lo > 0):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


class Section:
    """Concrete rectangles (z_bottom, z_top, width) and bars (z, area, fy, es)."""

    def __init__(self, rects, bars, fc, ec, strips=200):
        self.fc, self.ec = float(fc), float(ec)
        self.eps0 = 2.0 * self.fc / self.ec
        self.strips = []
        for z1, z2, width in rects:
            n = max(1, int(round(strips * (z2 - z1) / max(r[1] - r[0] for r in rects))))
            dz = (z2 - z1) / n
            self.strips += [(z1 + (i + 0.5) * dz, width * dz) for i in range(n)]
        self.bars = np.asarray(bars, dtype=float).reshape(-1, 4)
        self.strips = np.asarray(self.strips, dtype=float)
        z, a = self.strips[:, 0], self.strips[:, 1]
        self.area = float(a.sum())
        self.z_centroid = float((z * a).sum() / self.area)
        self.i_gross = float((a * (z - self.z_centroid) ** 2).sum())
        self.z_top = max(r[1] for r in rects)
        self.z_bottom = min(r[0] for r in rects)

    def flipped(self):
        """Same section with +z and -z exchanged (the other bending sign)."""
        out = Section.__new__(Section)
        out.__dict__.update(self.__dict__)
        out.strips = self.strips * [-1.0, 1.0]
        out.bars = self.bars * [-1.0, 1.0, 1.0, 1.0]
        out.z_centroid = -self.z_centroid
        out.z_top, out.z_bottom = -self.z_bottom, -self.z_top
        return out

    def forces(self, eps_top, phi):
        """Axial force (compression +) and moment for strain eps_top - phi*(z_top - z)."""
        z, a = self.strips[:, 0], self.strips[:, 1]
        r = np.clip((eps_top - phi * (self.z_top - z)) / self.eps0, 0.0, 1.0)
        sc = self.fc * (2.0 * r - r * r) * a
        zb, ab, fy, es = self.bars.T
        ss = np.clip(es * (eps_top - phi * (self.z_top - zb)), -fy, fy) * ab
        n = sc.sum() + ss.sum()
        m = (sc * (z - self.z_centroid)).sum() + (ss * (zb - self.z_centroid)).sum()
        return float(n), float(m)

    def _steel_ratio(self, eps_top, phi):
        zb, _, fy, es = self.bars.T
        return float(np.max(-(eps_top - phi * (self.z_top - zb)) / (fy / es)))

    def _eps_top(self, phi, axial):
        return _bisect(lambda e: self.forces(e, phi)[0] - axial, -0.05, 0.05, 60)

    def yield_point(self, axial, concrete_factor=1.8):
        """Return (My, phi_y, governing) for compression on the +z face."""
        eps_c = concrete_factor * self.fc / self.ec

        def criterion(phi):
            e = self._eps_top(phi, axial)
            steel = self._steel_ratio(e, phi)
            return max(steel, e / eps_c) - 1.0

        hi = 1e-7
        while criterion(hi) < 0.0:
            hi *= 1.5
            if hi > 1e-3:
                raise RuntimeError('Section never reaches yield')
        phi = _bisect(criterion, 0.0, hi, 40)
        e = self._eps_top(phi, axial)
        steel = self._steel_ratio(e, phi)
        return self.forces(e, phi)[1], phi, 'steel' if steel >= e / eps_c else 'concrete'


def haselton(nu, rho_sh, s_mm, db_mm, fy, fc, rho, a_sl, ls_over_h, s_over_d):
    """Haselton et al. RC column equations; nu = P/(Ag fc), MPa inputs."""
    nu = max(nu, 0.0)
    sn = (s_mm / db_mm) * math.sqrt(fy / 100.0)
    theta_p = (0.12 * (1 + 0.55 * a_sl) * 0.16 ** nu * (0.02 + 40 * rho_sh) ** 0.43
               * 0.54 ** (0.01 * fc) * 0.66 ** (0.1 * sn) * 2.27 ** (10 * rho))
    theta_pc = min(0.76 * 0.031 ** nu * (0.02 + 40 * rho_sh) ** 1.02, 0.10)
    return dict(
        mc_my=1.25 * 0.89 ** nu * 0.91 ** (0.01 * fc),
        theta_p=theta_p, theta_pc=theta_pc,
        lam=170.7 * 0.27 ** nu * 0.10 ** s_over_d,
        eiy_ratio=min(max(-0.07 + 0.59 * nu + 0.07 * ls_over_h, 0.2), 0.6),
        eistf40_ratio=min(max(-0.02 + 0.98 * nu + 0.09 * ls_over_h, 0.35), 0.8),
        sn=sn)
