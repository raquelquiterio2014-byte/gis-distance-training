"""Shared WGS 84 ellipsoidal distance engine; no GUI or server side effects."""
import csv
import json
import math
from itertools import combinations
from pathlib import Path
from geographiclib.geodesic import Geodesic

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / 'data' / 'locations.json'
METHOD = 'WGS 84 ellipsoidal geodesic (GeographicLib inverse)'


def validate_coordinate(latitude, longitude):
    for value, lower, upper, label in (
        (latitude, -90, 90, 'latitude'), (longitude, -180, 180, 'longitude')
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f'{label} must be a number')
        if not math.isfinite(value) or not lower <= value <= upper:
            raise ValueError(f'{label} must be finite and between {lower} and {upper}')


def distance_m(lat1, lon1, lat2, lon2):
    validate_coordinate(lat1, lon1)
    validate_coordinate(lat2, lon2)
    return Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)['s12']


def load_dataset(path=DATA_FILE):
    try:
        dataset = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f'Cannot read locations dataset: {exc}') from exc
    if not isinstance(dataset, dict):
        raise ValueError('Dataset must be a JSON object')
    for key in ['dataset_version', 'crs', 'ellipsoid', 'coordinate_status', 'note']:
        if not isinstance(dataset.get(key), str) or not dataset[key].strip():
            raise ValueError(f'Dataset field {key} must be a nonempty string')
    if dataset['crs'] != 'EPSG:4326' or dataset['ellipsoid'] != 'WGS84':
        raise ValueError('Dataset must use EPSG:4326 and WGS84')
    locations = dataset.get('locations')
    if not isinstance(locations, list) or len(locations) < 2:
        raise ValueError('At least two locations with distinct IDs are required')
    ids = set()
    for point in locations:
        if not isinstance(point, dict):
            raise ValueError('Each location must be a JSON object')
        for key in ['id', 'name', 'access_note', 'source_url', 'coordinate_basis']:
            if not isinstance(point.get(key), str) or not point[key].strip():
                raise ValueError(f'Location field {key} must be a nonempty string')
        if point['id'] in ids:
            raise ValueError('Location IDs must be distinct')
        ids.add(point['id'])
        validate_coordinate(point.get('latitude'), point.get('longitude'))
    return dataset



def pair_result(a, b):
    meters = distance_m(a['latitude'], a['longitude'], b['latitude'], b['longitude'])
    return {'from_id': a['id'], 'to_id': b['id'], 'from_name': a['name'],
            'to_name': b['name'], 'distance_m': meters, 'distance_km': meters / 1000}


def all_distances(dataset):
    return [pair_result(a, b) for a, b in combinations(dataset['locations'], 2)]


def result_bundle(dataset):
    return {'dataset_version': dataset['dataset_version'], 'crs': dataset['crs'],
            'ellipsoid': dataset['ellipsoid'], 'method': METHOD,
            'coordinate_status': dataset['coordinate_status'],
            'location_count': len(dataset['locations']),
            'pair_count': len(dataset['locations']) * (len(dataset['locations']) - 1) // 2,
            'note': dataset['note'], 'locations': dataset['locations'],
            'distances': all_distances(dataset)}


def points_geojson(dataset):
    return {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'geometry': {'type': 'Point',
         'coordinates': [p['longitude'], p['latitude']]},
         'properties': {**p, 'dataset_coordinate_status': dataset['coordinate_status'],
                        'dataset_version': dataset['dataset_version']}}
        for p in dataset['locations']]}


def geodesic_coordinates(a, b, segments=40):
    line = Geodesic.WGS84.InverseLine(a['latitude'], a['longitude'], b['latitude'], b['longitude'])
    result = []
    for i in range(segments + 1):
        p = line.Position(line.s13 * i / segments)
        result.append([p['lon2'], p['lat2']])
    return result


def lines_geojson(dataset):
    return {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'geometry': {'type': 'LineString',
         'coordinates': geodesic_coordinates(a, b)},
         'properties': {**pair_result(a, b), 'method': METHOD,
                        'dataset_version': dataset['dataset_version'],
                        'coordinate_status': dataset['coordinate_status']}}
        for a, b in combinations(dataset['locations'], 2)]}


def export_dataset(dataset, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    files = []
    for name, obj in [('rio_points.geojson', points_geojson(dataset)),
                      ('rio_geodesics.geojson', lines_geojson(dataset)),
                      ('python_results.json', result_bundle(dataset))]:
        path = directory / name
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding='utf-8')
        files.append(path)
    rows = all_distances(dataset)
    path = directory / 'python_distances.csv'
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        fields = list(rows[0]) + ['dataset_version', 'coordinate_status']
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, 'dataset_version': dataset['dataset_version'],
                             'coordinate_status': dataset['coordinate_status']})
    files.append(path)
    return files
