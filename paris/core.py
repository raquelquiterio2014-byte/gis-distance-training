"""WGS 84 geodesic calculations for the user's digitized Paris entrance points."""
import json
import math
from itertools import combinations
from pathlib import Path
from pyproj import Geod

ROOT = Path(__file__).resolve().parent
GEOD = Geod(ellps='WGS84')
QGIS_REFERENCE_M = {
    frozenset(('notre_dame', 'louvre')): 1274.9159126132859,
    frozenset(('notre_dame', 'eiffel_tower')): 4065.956709285214,
    frozenset(('louvre', 'eiffel_tower')): 3124.0519680755096,
}


def load_points(path=ROOT / 'data' / 'paris_entrances.geojson'):
    obj = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if obj.get('type') != 'FeatureCollection':
        raise ValueError('Expected a GeoJSON FeatureCollection.')
    crs = obj.get('crs', {}).get('properties', {}).get('name', '')
    if crs and not ('CRS84' in crs or crs.endswith('4326')):
        raise ValueError('Points must use WGS 84 longitude/latitude.')
    points = {}
    for feature in obj['features']:
        prop, geom = feature['properties'], feature['geometry']
        code = prop['site_id']
        if code in points or geom['type'] != 'Point':
            raise ValueError('Each site must have one unique Point geometry.')
        lon, lat = geom['coordinates']
        if not all(math.isfinite(v) for v in (lon, lat)) or not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError('Invalid longitude or latitude.')
        points[code] = {'name': prop.get('Nome', code), 'coordinates': [lon, lat],
                        'entrance': prop.get('Entrance', ''), 'source': prop.get('Source', ''),
                        'accuracy_note': prop.get('accuracy_note', '')}
    if len(points) < 2:
        raise ValueError('At least two points are required.')
    return points


def calculate(points, origin, destination):
    for code in (origin, destination):
        if code not in points:
            raise ValueError(f'Unknown site: {code}')
    if origin == destination:
        raise ValueError('Choose two different sites.')
    a, b = points[origin], points[destination]
    meters = GEOD.inv(*a['coordinates'], *b['coordinates'])[2]
    result = {'origin': origin, 'destination': destination,
              'origin_name': a['name'], 'destination_name': b['name'],
              'coordinates_lon_lat': [a['coordinates'], b['coordinates']],
              'distance_m': meters, 'distance_km': meters / 1000,
              'coordinate_crs': 'EPSG:4326', 'ellipsoid': 'WGS84',
              'method': 'Geodesic between manually digitized entrance points; no road routing',
              'accuracy_note': 'Approximate entrance positions; not surveyed. Numerical agreement is not positional accuracy.'}
    reference = QGIS_REFERENCE_M.get(frozenset((origin, destination)))
    if reference is not None:
        result.update(qgis_reference_m=reference, difference_m=abs(meters-reference),
                      within_1m=abs(meters-reference) <= 1)
    return result


def all_distances(points):
    return [calculate(points, a, b) for a, b in combinations(points, 2)]


def export_lines(points, path):
    features = []
    for row in all_distances(points):
        features.append({'type': 'Feature', 'properties': row,
                         'geometry': {'type': 'LineString', 'coordinates': row['coordinates_lon_lat']}})
    Path(path).write_text(json.dumps({'type': 'FeatureCollection', 'features': features}, indent=2), encoding='utf-8')
