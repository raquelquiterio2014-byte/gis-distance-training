import json
import math
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from api import app
from core import distance_m, load_dataset, all_distances, export_dataset


class DistanceTests(unittest.TestCase):
    def test_known_equatorial_degree(self):
        self.assertAlmostEqual(distance_m(0, 0, 0, 1), 111319.49079327357, places=6)

    def test_zero_and_symmetry(self):
        self.assertEqual(distance_m(-22, -43, -22, -43), 0)
        self.assertAlmostEqual(distance_m(-22, -43, -23, -44), distance_m(-23, -44, -22, -43), places=8)

    def test_invalid_coordinates(self):
        for lat, lon in [(91, 0), (0, 181), (math.nan, 0), (0, math.inf), (True, 0)]:
            with self.subTest(lat=lat, lon=lon), self.assertRaises(ValueError):
                distance_m(lat, lon, 0, 0)

    def test_three_pairs_and_triangle(self):
        rows = all_distances(load_dataset())
        self.assertEqual(len(rows), 3)
        sides = [r['distance_m'] for r in rows]
        self.assertTrue(all(x > 0 for x in sides))
        self.assertLess(max(sides), sum(sides) - max(sides))

    def test_exports_coordinate_order_and_metadata(self):
        dataset = load_dataset()
        with tempfile.TemporaryDirectory() as directory:
            paths = export_dataset(dataset, directory)
            self.assertEqual(len(paths), 4)
            geo = json.loads((Path(directory) / 'rio_points.geojson').read_text(encoding='utf-8'))
            p = dataset['locations'][0]
            self.assertEqual(geo['features'][0]['geometry']['coordinates'], [p['longitude'], p['latitude']])
            lines = json.loads((Path(directory) / 'rio_geodesics.geojson').read_text(encoding='utf-8'))
            self.assertEqual(len(lines['features']), 3)
            self.assertEqual(len(lines['features'][0]['geometry']['coordinates']), 41)


class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_and_locations(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        data = self.client.get('/locations').json()
        self.assertEqual(len(data['locations']), 3)
        self.assertIn('PENDING', data['coordinate_status'])

    def test_all_pairs_equal_local(self):
        response = self.client.get('/distances')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['distances'], all_distances(load_dataset()))

    def test_unknown_id(self):
        self.assertEqual(self.client.get('/distance?from_id=BAD&to_id=RIO02').status_code, 404)

    def test_paris_style_points_endpoint(self):
        self.assertEqual(self.client.get('/points').json(), self.client.get('/locations').json())

    def test_paris_style_pair_request(self):
        response = self.client.post('/distance', json={'origin': 'RIO01', 'destination': 'RIO02'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['distance_m'], all_distances(load_dataset())[0]['distance_m'])
        self.assertEqual(self.client.post('/distance', json={'origin': 'BAD', 'destination': 'RIO02'}).status_code, 404)
        self.assertEqual(self.client.post('/distance', json={'origin': 'RIO01', 'destination': 'RIO01'}).status_code, 422)

    def test_known_pair_and_same_point(self):
        result = self.client.get('/distance?from_id=RIO01&to_id=RIO02').json()
        self.assertGreater(result['distance_m'], 0)
        self.assertEqual(self.client.get('/distance?from_id=RIO01&to_id=RIO01').json()['distance_m'], 0)

    def test_custom_distance(self):
        response = self.client.post('/distance', json={'origin': {'latitude': 0, 'longitude': 0},
                                                     'destination': {'latitude': 0, 'longitude': 1}})
        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(response.json()['distance_m'], 111319.49079327357, places=6)

    def test_invalid_requests(self):
        for origin in [{'latitude': 100, 'longitude': 0}, {'latitude': 0, 'longitude': 181},
                       {'latitude': 'NaN', 'longitude': 0}, {'latitude': 0, 'longitude': 0, 'typo': 5}]:
            with self.subTest(origin=origin):
                self.assertEqual(self.client.post('/distance', json={'origin': origin,
                    'destination': {'latitude': 0, 'longitude': 0}}).status_code, 422)
        self.assertEqual(self.client.get('/distance').status_code, 422)

    def test_geojson_and_openapi(self):
        for path in ['/geojson/points', '/geojson/geodesics']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()['features']), 3)
        self.assertEqual(self.client.get('/openapi.json').status_code, 200)


if __name__ == '__main__':
    unittest.main()
