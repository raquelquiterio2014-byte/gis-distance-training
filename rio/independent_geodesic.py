"""Independent WGS 84 inverse: Vincenty (1975), implemented with Python math only.

Source: https://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf
Used to cross-check the short Rio baselines; not a global replacement for GeographicLib.
Nonconvergence (notably near antipodes) raises an error, never a hidden fallback.
"""
import math

A = 6378137.0
F = 1 / 298.257223563
B = A * (1 - F)


def vincenty_distance_m(lat1, lon1, lat2, lon2):
    for value, limit in [(lat1, 90), (lat2, 90), (lon1, 180), (lon2, 180)]:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError('Coordinates must be numbers')
        if not math.isfinite(value) or abs(value) > limit:
            raise ValueError('Invalid coordinate')
    if lat1 == lat2 and ((lon1 - lon2) % 360 == 0 or abs(lat1) == 90):
        return 0.0
    u1 = math.atan((1 - F) * math.tan(math.radians(lat1)))
    u2 = math.atan((1 - F) * math.tan(math.radians(lat2)))
    su1, cu1, su2, cu2 = math.sin(u1), math.cos(u1), math.sin(u2), math.cos(u2)
    longitude = math.radians((lon2 - lon1 + 180) % 360 - 180)
    lam = longitude
    for _ in range(200):
        sl, cl = math.sin(lam), math.cos(lam)
        sin_sigma = math.hypot(cu2 * sl, cu1 * su2 - su1 * cu2 * cl)
        cos_sigma = su1 * su2 + cu1 * cu2 * cl
        if sin_sigma < 1e-15:
            if cos_sigma > 0:
                return 0.0
            raise ValueError('Vincenty is undefined for antipodal points')
        sigma = math.atan2(sin_sigma, cos_sigma)
        sin_alpha = cu1 * cu2 * sl / sin_sigma
        cos2_alpha = max(0.0, 1 - sin_alpha * sin_alpha)
        cos2_sigma_m = cos_sigma - 2 * su1 * su2 / cos2_alpha if cos2_alpha > 1e-15 else 0.0
        c = F / 16 * cos2_alpha * (4 + F * (4 - 3 * cos2_alpha))
        updated = longitude + (1 - c) * F * sin_alpha * (
            sigma + c * sin_sigma * (cos2_sigma_m + c * cos_sigma * (-1 + 2 * cos2_sigma_m**2)))
        if abs(updated - lam) <= 1e-13:
            lam = updated
            break
        lam = updated
    else:
        raise ValueError('Vincenty did not converge; no fallback was used')
    # Recompute the final trigonometric terms at the converged lambda.
    sl, cl = math.sin(lam), math.cos(lam)
    sin_sigma = math.hypot(cu2 * sl, cu1 * su2 - su1 * cu2 * cl)
    cos_sigma = su1 * su2 + cu1 * cu2 * cl
    sigma = math.atan2(sin_sigma, cos_sigma)
    sin_alpha = cu1 * cu2 * sl / sin_sigma
    cos2_alpha = max(0.0, 1 - sin_alpha**2)
    cos2_sigma_m = cos_sigma - 2 * su1 * su2 / cos2_alpha if cos2_alpha > 1e-15 else 0.0
    u_sq = cos2_alpha * (A * A - B * B) / (B * B)
    aa = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    bb = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))
    delta_sigma = bb * sin_sigma * (
        cos2_sigma_m + bb / 4 * (cos_sigma * (-1 + 2 * cos2_sigma_m**2)
        - bb / 6 * cos2_sigma_m * (-3 + 4 * sin_sigma**2) * (-3 + 4 * cos2_sigma_m**2)))
    return B * aa * (sigma - delta_sigma)
