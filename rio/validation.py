"""Numerical validation and explicit, user-supplied QGIS reference comparison."""
import csv
import hashlib
import json
import math
from itertools import combinations
from pathlib import Path
from core import METHOD, all_distances
from independent_geodesic import vincenty_distance_m

TOLERANCE_M = 0.01
QGIS_FIELDS = ['from_id', 'to_id', 'qgis_distance_m', 'dataset_version', 'coordinate_sha256',
               'coordinate_crs', 'ellipsoid', 'measurement_method', 'distance_unit']


def coordinate_fingerprint(dataset):
    points = sorted((p['id'], p['latitude'], p['longitude']) for p in dataset['locations'])
    return hashlib.sha256(json.dumps(points, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_tolerance(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError('Tolerance must be finite and nonnegative')


def independent_report(dataset, tolerance_m=TOLERANCE_M):
    validate_tolerance(tolerance_m)
    rows = []
    local = all_distances(dataset)
    for (a, b), result in zip(combinations(dataset['locations'], 2), local):
        row = dict(result)
        try:
            reference = vincenty_distance_m(a['latitude'], a['longitude'], b['latitude'], b['longitude'])
            difference = abs(reference - row['distance_m'])
            row.update(independent_distance_m=reference, difference_m=difference,
                       status='PASS' if difference <= tolerance_m else 'FAIL')
        except ValueError as exc:
            row.update(independent_distance_m=None, difference_m=None, status='ERROR', error=str(exc))
        rows.append(row)
    return {'dataset_version': dataset['dataset_version'], 'coordinate_sha256': coordinate_fingerprint(dataset),
            'primary_method': METHOD, 'independent_method': 'Vincenty inverse (1975), local Python math implementation',
            'tolerance_m': tolerance_m, 'status': 'PASS' if all(r['status'] == 'PASS' for r in rows) else 'FAIL',
            'note': 'Independent numerical cross-check of the same coordinates; not positional or field validation.',
            'rows': rows}


def write_qgis_template(dataset, path):
    with Path(path).open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=QGIS_FIELDS)
        writer.writeheader()
        for row in all_distances(dataset):
            writer.writerow({'from_id': row['from_id'], 'to_id': row['to_id'], 'qgis_distance_m': '',
                'dataset_version': dataset['dataset_version'], 'coordinate_sha256': coordinate_fingerprint(dataset),
                'coordinate_crs': dataset['crs'], 'ellipsoid': dataset['ellipsoid'],
                'measurement_method': 'ellipsoidal', 'distance_unit': 'm'})
    return Path(path)


def qgis_report(dataset, path, tolerance_m=TOLERANCE_M):
    validate_tolerance(tolerance_m)
    expected = {frozenset((r['from_id'], r['to_id'])): r for r in all_distances(dataset)}
    seen, results = set(), []
    metadata = {'dataset_version': dataset['dataset_version'], 'coordinate_sha256': coordinate_fingerprint(dataset),
                'coordinate_crs': dataset['crs'], 'ellipsoid': dataset['ellipsoid'],
                'measurement_method': 'ellipsoidal', 'distance_unit': 'm'}
    with Path(path).open(newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or set(reader.fieldnames) != set(QGIS_FIELDS) or len(reader.fieldnames) != len(QGIS_FIELDS):
            raise ValueError('Use the QGIS CSV template: its column names must be preserved')
        for line, entry in enumerate(reader, start=2):
            if None in entry or any(v is None for v in entry.values()):
                raise ValueError(f'Malformed CSV row {line}')
            entry = {k: v.strip() for k, v in entry.items()}
            for key, value in metadata.items():
                if entry.get(key) != value:
                    raise ValueError(f'QGIS row {line}: {key} differs from current coordinates/settings')
            pair = frozenset((entry['from_id'], entry['to_id']))
            if pair not in expected or pair in seen:
                raise ValueError(f'QGIS row {line}: unknown, repeated or identical pair')
            seen.add(pair)
            result = dict(expected[pair])
            value = entry['qgis_distance_m']
            if not value:
                result.update(qgis_distance_m=None, difference_m=None, status='PENDING')
            else:
                try:
                    distance = float(value)
                except ValueError as exc:
                    raise ValueError(f'QGIS row {line}: use a decimal point for distance in meters') from exc
                if not math.isfinite(distance) or distance < 0:
                    raise ValueError(f'QGIS row {line}: distance must be finite and nonnegative')
                difference = abs(distance - result['distance_m'])
                result.update(qgis_distance_m=distance, difference_m=difference,
                              status='PASS' if difference <= tolerance_m else 'FAIL')
            results.append(result)
    if seen != set(expected):
        raise ValueError('QGIS CSV must contain each expected pair exactly once; leave unknown distances blank')
    statuses = [r['status'] for r in results]
    status = ('FAIL' if 'FAIL' in statuses else 'PENDING' if all(s == 'PENDING' for s in statuses)
              else 'INCOMPLETE' if 'PENDING' in statuses else 'PASS')
    return {'dataset_version': dataset['dataset_version'], 'coordinate_sha256': coordinate_fingerprint(dataset),
            'tolerance_m': tolerance_m, 'status': status, 'rows': results,
            'note': 'User-supplied QGIS measurements. Matching declared coordinates/settings does not establish positional accuracy.'}


def compare_api_payload(dataset, payload, tolerance_m=TOLERANCE_M):
    validate_tolerance(tolerance_m)
    for key in ['dataset_version', 'crs', 'ellipsoid', 'coordinate_status', 'locations']:
        if payload.get(key) != dataset[key]:
            raise ValueError(f'API dataset mismatch: {key}')
    if payload.get('method') != METHOD:
        raise ValueError('API calculation method differs')
    local = all_distances(dataset)
    if payload.get('location_count') != len(dataset['locations']) or payload.get('pair_count') != len(local):
        raise ValueError('API counts differ')
    remote = {(r['from_id'], r['to_id']): r for r in payload['distances']}
    if set(remote) != {(r['from_id'], r['to_id']) for r in local} or len(payload['distances']) != len(local):
        raise ValueError('API pair set differs')
    results = []
    for row in local:
        candidate = remote[(row['from_id'], row['to_id'])]
        for key in ['distance_m', 'distance_km']:
            value = candidate.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError('API distance must be a finite nonnegative number')
        if abs(candidate['distance_km'] * 1000 - candidate['distance_m']) > tolerance_m:
            raise ValueError('API distance units are inconsistent')
        delta = abs(row['distance_m'] - candidate['distance_m'])
        results.append({**row, 'difference_m': delta, 'status': 'PASS' if delta <= tolerance_m else 'FAIL'})
    return {'dataset_version': dataset['dataset_version'], 'rows': results,
            'status': 'PASS' if all(r['status'] == 'PASS' for r in results) else 'FAIL',
            'note': 'Shared-engine HTTP consistency check; not an independent geodesic method.'}


def format_report(report, title):
    lines = [title, f"Dataset: {report['dataset_version']}", f"Status: {report['status']}",
             f"Numerical tolerance: {report.get('tolerance_m', TOLERANCE_M)} m", '']
    for row in report['rows']:
        difference = 'pending' if row['difference_m'] is None else f"{row['difference_m']:.8f} m"
        lines.append(f"{row['from_id']} / {row['to_id']}: delta = {difference} | {row['status']}")
        if row.get('error'):
            lines.append(row['error'])
    lines.extend(['', report['note']])
    return '\n'.join(lines)
