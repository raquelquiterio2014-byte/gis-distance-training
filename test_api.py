"""HTTP contract checks against desktop calculations and the recorded QGIS result."""
import unittest
from fastapi.testclient import TestClient
from api import app, DATA_PATH
from core import calculate, load_regions, REFERENCE_M


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_regions(DATA_PATH)

    def setUp(self):
        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_health_and_regions(self):
        self.assertEqual(self.client.get('/health').json()['region_count'], 299)
        rows = self.client.get('/regions').json()
        self.assertEqual(len(rows), 299)
        self.assertIn('FR10', [row['code'] for row in rows])

    def test_reference_matches_desktop(self):
        response = self.client.post('/distance', json={'origin': 'FR10', 'destination': 'FRF3'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        desktop = calculate(self.rows, 'FR10', 'FRF3')
        self.assertAlmostEqual(body['distance_m'], desktop['distance_m'], places=6)
        self.assertLess(abs(body['distance_m'] - REFERENCE_M), 0.001)
        self.assertEqual(body['centroids_lon_lat'], [list(p) for p in desktop['centroids_lon_lat']])
        self.assertTrue(body['within_1m'])

    def test_reverse(self):
        result = self.client.post('/distance', json={'origin': 'FRF3', 'destination': 'FR10'}).json()
        self.assertLess(abs(result['distance_m'] - REFERENCE_M), 0.001)

    def test_other_pair_has_no_qgis_reference(self):
        response = self.client.post('/distance', json={'origin': 'FR10', 'destination': 'FRB0'})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('qgis_reference_m', response.json())

    def test_unknown_region(self):
        response = self.client.post('/distance', json={'origin': 'UNKNOWN', 'destination': 'FR10'})
        self.assertEqual(response.status_code, 404)
        self.assertIn('Unknown region', response.json()['detail'])

    def test_same_region(self):
        self.assertEqual(self.client.post('/distance', json={'origin': 'FR10', 'destination': 'FR10'}).status_code, 422)

    def test_invalid_request(self):
        for payload in ({'origin': 'FR10'}, {'origin': '', 'destination': 'FRF3'},
                        {'origin': 'FR10', 'destination': 'FRF3', 'ellipsoid': 'sphere'}):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post('/distance', json=payload).status_code, 422)


if __name__ == '__main__':
    unittest.main()
