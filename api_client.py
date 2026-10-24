"""Compare an HTTP API response against a desktop calculation snapshot."""
import json
import math
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def compare_with_api(desktop_result, base_url='http://127.0.0.1:8000'):
    payload = {key: desktop_result[key] for key in ('origin', 'destination')}
    request = Request(base_url.rstrip('/') + '/distance',
                      data=json.dumps(payload).encode('utf-8'),
                      headers={'Content-Type': 'application/json'}, method='POST')
    try:
        with urlopen(request, timeout=5) as response:
            api_result = json.load(response)
    except HTTPError as error:
        detail = error.read().decode('utf-8', errors='replace')
        raise ValueError(f'HTTP {error.code}: {detail}') from error
    difference = abs(api_result['distance_m'] - desktop_result['distance_m'])
    if not math.isfinite(difference):
        raise ValueError('The API returned a non-finite distance.')
    coordinates_match = all(
        math.isclose(a, b, rel_tol=0, abs_tol=1e-9)
        for point_a, point_b in zip(api_result['centroids_lon_lat'], desktop_result['centroids_lon_lat'], strict=True)
        for a, b in zip(point_a, point_b, strict=True)
    )
    method_matches = all(api_result.get(key) == desktop_result.get(key) for key in
                         ('origin', 'destination', 'centroid_crs', 'coordinate_crs', 'ellipsoid', 'method'))
    report = {'api_distance_m': api_result['distance_m'],
              'desktop_distance_m': desktop_result['distance_m'],
              'difference_m': difference, 'coordinates_match': coordinates_match,
              'method_matches': method_matches,
              'within_1m': difference <= 1 and coordinates_match and method_matches}
    if 'qgis_reference_m' in desktop_result:
        report['qgis_difference_m'] = abs(api_result['distance_m'] - desktop_result['qgis_reference_m'])
    return report
