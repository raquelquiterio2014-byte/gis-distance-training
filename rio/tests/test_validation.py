import contextlib
import copy
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from core import load_dataset, result_bundle, distance_m
from independent_geodesic import vincenty_distance_m
from validation import (independent_report, qgis_report, write_qgis_template,
                        coordinate_fingerprint, compare_api_payload, QGIS_FIELDS)
from verify_project import main as verify_main
from fastapi.testclient import TestClient
from api import app


class IndependentChecks(unittest.TestCase):
    def test_known_equator_and_coincident(self):
        self.assertAlmostEqual(vincenty_distance_m(0, 0, 0, 1), 111319.49079327357, places=6)
        self.assertEqual(vincenty_distance_m(-22, -43, -22, -43), 0)
        self.assertEqual(vincenty_distance_m(0, -180, 0, 180), 0)
        self.assertEqual(vincenty_distance_m(90, 0, 90, 80), 0)

    def test_six_rio_baselines(self):
        report = independent_report(load_dataset())
        self.assertEqual(report['status'], 'PASS')
        self.assertEqual(len(report['rows']), 6)
        self.assertTrue(all(r['difference_m'] < 0.001 for r in report['rows']))

    def test_antipodal_has_no_fallback(self):
        with self.assertRaises(ValueError):
            vincenty_distance_m(0, 0, 0, 180)
        with self.assertRaises(ValueError):
            vincenty_distance_m(0, 0, 0.5, 179.7)

    def test_short_dateline_and_polar(self):
        for coords in [(10, 179.9, 10, -179.9), (89, 10, 89, 20), (50, 0, -20, 40)]:
            self.assertAlmostEqual(vincenty_distance_m(*coords), distance_m(*coords), delta=0.001)

    def test_bad_input(self):
        for lat, lon in [(100, 0), (True, 0), (0, float('nan')), (0, 200)]:
            with self.assertRaises(ValueError):
                vincenty_distance_m(lat, lon, 0, 0)

    def test_disagreement_and_error_are_visible(self):
        with patch('validation.vincenty_distance_m', return_value=0):
            self.assertEqual(independent_report(load_dataset())['status'], 'FAIL')
        with patch('validation.vincenty_distance_m', side_effect=ValueError('not converged')):
            report = independent_report(load_dataset())
            self.assertEqual(report['status'], 'FAIL')
            self.assertTrue(all(r['status'] == 'ERROR' for r in report['rows']))

    def test_api_validation_and_strict_numbers(self):
        client = TestClient(app)
        response = client.get('/validation')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'PASS')
        for value in [True, '1']:
            self.assertEqual(client.post('/distance', json={'origin': {'latitude': value, 'longitude': 0},
                'destination': {'latitude': 0, 'longitude': 1}}).status_code, 422)


class QGISChecks(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'qgis.csv'
        self.dataset = load_dataset()
        write_qgis_template(self.dataset, self.path)
        with self.path.open(encoding='utf-8-sig', newline='') as stream:
            self.rows = list(csv.DictReader(stream))

    def save(self):
        with self.path.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=QGIS_FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)

    def fill_synthetic_test_values(self):
        # Synthetic fixture only: never persisted or described as actual QGIS observations.
        for row, local in zip(self.rows, result_bundle(self.dataset)['distances']):
            row['qgis_distance_m'] = str(local['distance_m'])

    def test_template_never_invents_measurements(self):
        self.assertTrue(all(not r['qgis_distance_m'] for r in self.rows))
        self.assertEqual(qgis_report(self.dataset, self.path)['status'], 'PENDING')

    def test_partial_and_complete_fixture(self):
        self.rows[0]['qgis_distance_m'] = str(result_bundle(self.dataset)['distances'][0]['distance_m'])
        self.save()
        self.assertEqual(qgis_report(self.dataset, self.path)['status'], 'INCOMPLETE')
        self.fill_synthetic_test_values()
        self.rows[0]['from_id'], self.rows[0]['to_id'] = self.rows[0]['to_id'], self.rows[0]['from_id']
        self.save()
        self.assertEqual(qgis_report(self.dataset, self.path)['status'], 'PASS')

    def test_changed_coordinates_rejected_even_with_same_version(self):
        changed = copy.deepcopy(self.dataset)
        changed['locations'][0]['latitude'] += 0.0001
        self.assertNotEqual(coordinate_fingerprint(changed), coordinate_fingerprint(self.dataset))
        with self.assertRaisesRegex(ValueError, 'coordinate_sha256'):
            qgis_report(changed, self.path)

    def test_missing_duplicate_unknown_rejected(self):
        originals = copy.deepcopy(self.rows)
        for case in ['missing', 'duplicate', 'unknown']:
            self.rows = copy.deepcopy(originals)
            if case == 'missing': self.rows.pop()
            if case == 'duplicate': self.rows[-1] = copy.deepcopy(self.rows[0])
            if case == 'unknown': self.rows[0]['from_id'] = 'RIO99'
            self.save()
            with self.assertRaises(ValueError): qgis_report(self.dataset, self.path)

    def test_invalid_distance_rejected(self):
        for value in ['NaN', 'inf', '-1', 'abc', '12,3']:
            self.rows[0]['qgis_distance_m'] = value
            self.save()
            with self.assertRaises(ValueError): qgis_report(self.dataset, self.path)

    def test_difference_is_failure(self):
        self.fill_synthetic_test_values()
        self.rows[0]['qgis_distance_m'] = str(float(self.rows[0]['qgis_distance_m']) + 5)
        self.save()
        self.assertEqual(qgis_report(self.dataset, self.path)['status'], 'FAIL')

    def test_units_and_ellipsoid_rejected(self):
        for field, value in [('distance_unit', 'km'), ('ellipsoid', 'sphere'), ('measurement_method', 'planar')]:
            previous = self.rows[0][field]
            self.rows[0][field] = value
            self.save()
            with self.assertRaises(ValueError): qgis_report(self.dataset, self.path)
            self.rows[0][field] = previous

    def test_cli_without_api_or_measurements(self):
        out = Path(self.folder.name) / 'report.json'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(verify_main(['--output', str(out)]), 0)
            self.assertEqual(verify_main(['--qgis-csv', str(self.path)]), 1)
        report = json.loads(out.read_text())
        self.assertEqual(report['independent']['status'], 'PASS')
        self.assertEqual(report['qgis']['status'], 'PENDING')


class APIConsistencyChecks(unittest.TestCase):
    def test_valid_payload(self):
        dataset = load_dataset()
        self.assertEqual(compare_api_payload(dataset, result_bundle(dataset))['status'], 'PASS')

    def test_tampered_payload_rejected(self):
        dataset = load_dataset()
        for problem in ['method', 'count', 'nan', 'units', 'duplicate', 'bool']:
            payload = result_bundle(dataset)
            if problem == 'method': payload['method'] = 'sphere'
            if problem == 'count': payload['pair_count'] = 3
            if problem == 'nan': payload['distances'][0]['distance_m'] = float('nan')
            if problem == 'bool': payload['distances'][0]['distance_m'] = True
            if problem == 'units': payload['distances'][0]['distance_km'] *= 1000
            if problem == 'duplicate': payload['distances'][-1] = copy.deepcopy(payload['distances'][0])
            with self.subTest(problem=problem), self.assertRaises(ValueError):
                compare_api_payload(dataset, payload)

    def test_wrong_distance_visible(self):
        dataset = load_dataset()
        payload = result_bundle(dataset)
        payload['distances'][0]['distance_m'] += 10
        payload['distances'][0]['distance_km'] = payload['distances'][0]['distance_m'] / 1000
        self.assertEqual(compare_api_payload(dataset, payload)['status'], 'FAIL')

    def test_bad_dataset_shape_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            for data in [[], {}, {'locations': None}]:
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError): load_dataset(path)
