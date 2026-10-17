"""
Prism — physics reference implementation.

This is the ground truth the browser engine gets checked against.
Pure numpy, no heavy deps — runs fine on a 2-core laptop.

Run:  python optics.py

Why this file matters: almost every jewellery visualiser fakes the light.
Faking is why buyers don't trust them. Everything here is the real
thing at a level you can verify by hand, so when the WebGPU renderer
disagrees with these numbers, the renderer is wrong.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# --------------------------------------------------------------------------
# Refractive index models
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Cauchy:
    """n(lambda) = A + B/lambda^2, lambda in micrometres.

    Good enough for crown glass and diamond across the visible band.
    Sellmeier is more accurate for sapphire; Cauchy is fine for a first cut.
    """

    name: str
    A: float
    B: float

    def n(self, wavelength_nm: float) -> float:
        lam_um = wavelength_nm / 1000.0
        return self.A + self.B / (lam_um * lam_um)


# Reference values check out against published figures at 589 nm (sodium D line).
AIR = Cauchy("air", 1.0000, 0.0000)
WATER = Cauchy("water", 1.3250, 0.0035)
CROWN_GLASS = Cauchy("crown glass (BK7-ish)", 1.5046, 0.0042)
SAPPHIRE = Cauchy("sapphire", 1.7350, 0.0100)
DIAMOND = Cauchy("diamond", 2.3800, 0.0115)

MATERIALS = {m.name: m for m in (AIR, WATER, CROWN_GLASS, SAPPHIRE, DIAMOND)}

# Visible band we sample for dispersion.
LAMBDA_MIN_NM = 400.0
LAMBDA_MAX_NM = 700.0


# --------------------------------------------------------------------------
# Snell, Fresnel, total internal reflection
# --------------------------------------------------------------------------


def refract(direction: np.ndarray, normal: np.ndarray, eta: float) -> np.ndarray | None:
    """Refract `direction` across a surface, given eta = n_incident / n_transmitted.

    `normal` must face the incoming ray (i.e. dot(direction, normal) < 0).
    Returns None on total internal reflection.
    """
    d = direction / np.linalg.norm(direction)
    n = normal / np.linalg.norm(normal)
    cos_i = -float(np.dot(d, n))
    if cos_i < 0.0:
        raise ValueError("normal must face the incoming ray")

    sin2_t = eta * eta * (1.0 - cos_i * cos_i)
    if sin2_t > 1.0:
        return None  # total internal reflection

    cos_t = math.sqrt(1.0 - sin2_t)
    return eta * d + (eta * cos_i - cos_t) * n


def fresnel_reflectance(direction: np.ndarray, normal: np.ndarray, eta: float) -> float:
    """Unpolarised Fresnel reflectance. eta = n_incident / n_transmitted.

    This is the number that decides how much light bounces off a facet
    versus entering the stone. Diamond's high index is why it reflects
    so much — the whole reason it sparkles.
    """
    d = direction / np.linalg.norm(direction)
    n = normal / np.linalg.norm(normal)
    cos_i = abs(float(np.dot(d, n)))
    cos_i = min(1.0, max(1e-6, cos_i))

    sin2_t = (eta * eta) * (1.0 - cos_i * cos_i)
    if sin2_t >= 1.0:
        return 1.0  # TIR: all of it comes back

    cos_t = math.sqrt(1.0 - sin2_t)

    # Amplitude coefficients (Fresnel equations), s and p polarisations.
    r_s = (eta * cos_i - cos_t) / (eta * cos_i + cos_t)
    r_p = (cos_i - eta * cos_t) / (cos_i + eta * cos_t)
    return 0.5 * (r_s * r_s + r_p * r_p)


def critical_angle_deg(n_from: float, n_to: float) -> float:
    """Beyond this incidence angle, light cannot escape the stone."""
    if n_from <= n_to:
        return float("nan")
    return math.degrees(math.asin(n_to / n_from))


# --------------------------------------------------------------------------
# Wavelength -> sRGB (Bruton's approximation), for turning a spectrum
# into something a screen can show.
# --------------------------------------------------------------------------


def wavelength_to_rgb(wavelength_nm: float) -> tuple[float, float, float]:
    wl = float(wavelength_nm)
    if wl < 380.0 or wl > 780.0:
        return (0.0, 0.0, 0.0)

    if wl < 440.0:
        r = -(wl - 440.0) / 60.0
        g, b = 0.0, 1.0
    elif wl < 490.0:
        r, g = 0.0, (wl - 440.0) / 50.0
        b = 1.0
    elif wl < 510.0:
        r, g = 0.0, 1.0
        b = -(wl - 510.0) / 20.0
    elif wl < 580.0:
        r, g = (wl - 510.0) / 70.0, 1.0
        b = 0.0
    elif wl < 645.0:
        r, g = 1.0, -(wl - 645.0) / 65.0
        b = 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0

    # Intensity roll-off near the ends of the visible band.
    if wl < 420.0:
        factor = 0.3 + 0.7 * (wl - 380.0) / 40.0
    elif wl > 700.0:
        factor = 0.3 + 0.7 * (780.0 - wl) / 80.0
    else:
        factor = 1.0

    return (r * factor, g * factor, b * factor)


# --------------------------------------------------------------------------
# The domain problem: why one stone costs more than another.
# --------------------------------------------------------------------------


# Cross-section of a simplified brilliant, in 2-D. Table on top, girdle at
# y = 0, culet at the bottom. The pavilion angle is what generates the
# geometry, so sweeping it sweeps a real family of stones.
GIRDLE_RADIUS = 1.0
TABLE_HALF_WIDTH = 0.5
CROWN_HEIGHT = 0.30


def _outline(pavilion_angle_deg: float) -> list[tuple[float, float]]:
    culet_y = -math.tan(math.radians(pavilion_angle_deg))
    return [
        (-TABLE_HALF_WIDTH, CROWN_HEIGHT),
        (TABLE_HALF_WIDTH, CROWN_HEIGHT),
        (GIRDLE_RADIUS, 0.0),
        (0.0, culet_y),
        (-GIRDLE_RADIUS, 0.0),
    ]


def _edges(poly):
    """Edges with normals pointing into the interior (the polygon is convex)."""
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    out = []
    for i in range(n):
        a = np.array(poly[i], dtype=float)
        b = np.array(poly[(i + 1) % n], dtype=float)
        e = b - a
        nrm = np.array([-e[1], e[0]])
        nrm /= np.linalg.norm(nrm)
        if float(np.dot(nrm, np.array([cx, cy]) - 0.5 * (a + b))) < 0.0:
            nrm = -nrm
        out.append((a, b, nrm))
    return out


def _cross(u: np.ndarray, v: np.ndarray) -> float:
    return float(u[0] * v[1] - u[1] * v[0])


def _nearest_hit(origin: np.ndarray, direction: np.ndarray, edges, eps: float = 1e-9):
    best_t, best_n = math.inf, None
    for a, b, nrm in edges:
        e = b - a
        denom = _cross(direction, e)
        if abs(denom) < 1e-12:
            continue
        ao = a - origin
        t = _cross(ao, e) / denom
        s = _cross(ao, direction) / denom
        if t > eps and -1e-9 <= s <= 1.0 + 1e-9 and t < best_t:
            best_t, best_n = t, nrm
    return best_t, best_n


def light_return(
    pavilion_angle_deg: float,
    material: Cauchy = DIAMOND,
    n_bounces: int = 12,
    wavelength_nm: float = 589.0,
) -> float:
    """Light returned to the viewer, for a given pavilion angle.

    Fire a ray straight down through the table and follow it. Inside the
    stone, each facet is either a mirror (total internal reflection, light
    kept) or a window (light escapes). Light that escapes upwards reaches
    the viewer; light that escapes downwards or sideways is lost. Weight
    each escape by how directly it points at the viewer.

    Returns a fraction in [0, 1]. This is, roughly, the number a jeweller
    is arguing about when they say one stone is better cut than another.

    Accuracy note: this is a 2-D cross-section, so it ignores the 3-D crown
    arrangement and treats the girdle as a point. Treat it as a shape, not a
    grade — good enough to show *why* the angle matters, not to certify a stone.
    """
    n_glass = material.n(wavelength_nm)
    edges = _edges(_outline(pavilion_angle_deg))
    eta = n_glass / 1.0

    def trace(x0: float) -> float:
        pos = np.array([x0, CROWN_HEIGHT - 1e-3])
        direction = np.array([0.0, -1.0])
        intensity = 1.0
        visible = 0.0
        for _ in range(n_bounces):
            t, nrm = _nearest_hit(pos, direction, edges)
            if nrm is None:
                break
            pos = pos + t * direction

            # Inside the stone the normal facing the ray is the inward normal,
            # and we are travelling glass -> air.
            r = fresnel_reflectance(direction, nrm, eta)
            refracted = refract(direction, nrm, eta)

            if refracted is None:
                # Total internal reflection: it all stays inside. This is the
                # mechanism that makes a well-cut stone bright.
                direction = direction - 2.0 * float(np.dot(direction, nrm)) * nrm
                pos = pos + direction * 1e-6
                continue

            # Escaped. Weight by how squarely it heads back toward a viewer
            # directly above. The cube is a modelling choice: light leaving
            # sideways still looks bright inside the stone, but it never
            # reaches the eye, so it should not count as returned.
            visible += intensity * (1.0 - r) * max(0.0, float(refracted[1])) ** 3
            intensity *= r
            direction = direction - 2.0 * float(np.dot(direction, nrm)) * nrm
            pos = pos + direction * 1e-6
            if intensity < 1e-4:
                break
        return visible

    # Fire a bundle of rays across the table rather than one ray down the axis.
    # A single central ray lands exactly on the culet, where the two pavilion
    # facets meet — a degenerate hit that reflects numerically outside the
    # stone. Off-axis rays meet real facet surfaces, as light actually does.
    span = TABLE_HALF_WIDTH - 0.05
    rays = 60
    total = 0.0
    for i in range(rays):
        x0 = -span + (i + 0.5) * (2.0 * span / rays)
        total += trace(x0)

    return float(min(1.0, max(0.0, total / rays)))


# --------------------------------------------------------------------------
# Self-tests
# --------------------------------------------------------------------------


def _check(name: str, got: float, want: float, tol: float) -> bool:
    ok = abs(got - want) <= tol
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}: got {got:.4f}, expected {want:.4f} (+/-{tol})")
    return ok


def run_tests() -> bool:
    print("Reference checks\n" + "-" * 60)
    ok = True

    print("Refractive index at 589 nm (sodium D):")
    for name, want, tol in (
        ("air", 1.0000, 1e-4),
        ("crown glass (BK7-ish)", 1.52, 0.02),
        ("sapphire", 1.77, 0.03),
        ("diamond", 2.42, 0.02),
    ):
        got = MATERIALS[name].n(589.0)
        ok &= _check(name, got, want, tol)

    print("\nTotal internal reflection (critical angles):")
    ok &= _check("diamond -> air", critical_angle_deg(2.417, 1.0), 24.4, 0.3)
    ok &= _check("crown glass -> air", critical_angle_deg(1.52, 1.0), 41.1, 0.3)
    ok &= _check("water -> air", critical_angle_deg(1.333, 1.0), 48.6, 0.3)

    print("\nFresnel reflectance (normal incidence):")
    # At normal incidence, R = ((n1-n2)/(n1+n2))^2. Diamond: ((0.417)/(3.417))^2 = 0.0149
    d = np.array([0.0, -1.0, 0.0])
    nrm = np.array([0.0, 1.0, 0.0])
    # ((n2-n1)/(n2+n1))^2 with diamond n=2.417 -> (1.417/3.417)^2 = 0.172.
    # Diamond throws ~17% of light back at you at normal incidence. That is
    # the whole reason it looks brighter than glass, which returns ~4%.
    ok &= _check("diamond normal incidence", fresnel_reflectance(d, nrm, 1.0 / 2.417), 0.172, 0.004)
    ok &= _check("crown glass normal incidence", fresnel_reflectance(d, nrm, 1.0 / 1.52), 0.0426, 0.003)

    print("\nSnell refraction, diamond (589 nm), 30 deg from the surface normal:")
    eta = 1.0 / 2.417
    theta_i = math.radians(30.0)
    inc = np.array([math.sin(theta_i), -math.cos(theta_i), 0.0])
    ref = refract(inc, nrm, eta)
    if ref is None:
        print("  [FAIL] refraction returned TIR unexpectedly")
        ok = False
    else:
        theta_t = math.degrees(math.acos(abs(float(ref[1]))))
        want = math.degrees(math.asin(math.sin(theta_i) / 2.417))
        ok &= _check("refracted angle", theta_t, want, 0.05)

    print("\nDispersion (diamond), index spread across the visible band:")
    n_red = DIAMOND.n(700.0)
    n_violet = DIAMOND.n(400.0)
    print(f"  red 700nm n={n_red:.4f}")
    print(f"  violet 400nm n={n_violet:.4f}")
    print(f"  spread = {n_violet - n_red:.4f} (diamond is prized for a wide spread)")
    ok &= (n_violet > n_red)

    print("\nSpectrum sampling (wavelength -> sRGB):")
    for wl, label in ((450.0, "blue"), (520.0, "green"), (620.0, "red")):
        r, g, b = wavelength_to_rgb(wl)
        print(f"  {wl:.0f}nm {label:5s} -> rgb({r:.2f}, {g:.2f}, {b:.2f})")

    return ok


def light_return_curve(material: Cauchy = DIAMOND) -> None:
    print(f"\nLight return vs pavilion angle — {material.name}")
    print("-" * 60)
    print("Two-dimensional cross-section only. It shows that the pavilion angle")
    print("is what decides how much light comes back, but it does NOT reproduce")
    print("the textbook ~40.75 deg optimum: that needs the 3-D crown, a spread of")
    print("entry points and a ray count. Treat this as mechanism, not a grade.\n")
    best_angle, best_value = 0.0, -1.0
    for angle in range(30, 51):
        v = light_return(float(angle), material)
        if v > best_value:
            best_angle, best_value = float(angle), v
        bar = "#" * int(round(v * 50))
        flag = "  <-- ideal" if angle == 41 else ""
        print(f"  {angle:2d} deg  {v:6.3f}  {bar}{flag}")
    print(f"\n  peak in this model: {best_angle:.0f} deg  (value {best_value:.3f})")


if __name__ == "__main__":
    passed = run_tests()
    light_return_curve(DIAMOND)
    light_return_curve(CROWN_GLASS)
    print("\n" + ("ALL CHECKS PASSED" if passed else "SOME CHECKS FAILED"))
