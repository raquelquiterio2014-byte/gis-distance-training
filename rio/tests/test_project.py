import json
import math
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from api import app
from core import distance_m, load_dataset, all_distances, export_dataset


class DistanceTests(unittest.TestCase):
    def test_four_distinct_locations_and_cosme_retained(self):
        points = {p['id']: p for p in load_dataset()['locations']}
        self.assertEqual(set(points), {'RIO01', 'RIO02', 'RIO03', 'RIO04'})
        self.assertEqual(points['RIO02']['point_type'], 'monument')
        self.assertEqual(points['RIO03']['point_type'], 'summit')
        self.assertEqual(points['RIO04']['point_type'], 'station_access_reference')
        self.assertEqual((points['RIO04']['latitude'], points['RIO04']['longitude']), (-22.9406, -43.1985))
        by_pair = {(r['from_id'], r['to_id']): r['distance_m'] for r in all_distances(load_dataset())}
        self.assertGreater(by_pair['RIO02', 'RIO04'], 1500)
        self.assertLess(by_pair['RIO02', 'RIO04'], 2000)

    def test_duplicate_ids_and_small_dataset_rejected(self):
        dataset = load_dataset()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'invalid.json'
            dataset['locations'][1]['id'] = dataset['locations'][0]['id']
            path.write_text(json.dumps(dataset))
            with self.assertRaises(ValueError):
                load_dataset(path)
            dataset['locations'] = dataset['locations'][:1]
            path.write_text(json.dumps(dataset))
            with self.assertRaises(ValueError):
                load_dataset(path)

    def test_all_six_connections_rendered(self):
        from matplotlib.figure import Figure
        from plotting import draw_distance_figure
        ax, bars = draw_distance_figure(Figure(figsize=(11.5, 3.8)), load_dataset())
        self.assertEqual(len(ax.lines), 6)
        self.assertEqual(len(ax.collections), 4)
        self.assertEqual(len(bars.patches), 6)

    def test_known_equatorial_degree(self):
        self.assertAlmostEqual(distance_m(0, 0, 0, 1), 111319.49079327357, places=6)

    def test_zero_and_symmetry(self):
        self.assertEqual(distance_m(-22, -43, -22, -43), 0)
        self.assertAlmostEqual(distance_m(-22, -43, -23, -44), distance_m(-23, -44, -22, -43), places=8)

    def test_invalid_coordinates(self):
        for lat, lon in [(91, 0), (0, 181), (math.nan, 0), (0, math.inf), (True, 0)]:
            with self.subTest(lat=lat, lon=lon), self.assertRaises(ValueError):
                distance_m(lat, lon, 0, 0)

    def test_six_unique_pairs_and_triangle(self):
        rows = all_distances(load_dataset())
        self.assertEqual(len(rows), 6)
        self.assertEqual(len({frozenset([r['from_id'], r['to_id']]) for r in rows}), 6)
        sides = [r['distance_m'] for r in rows]
        self.assertTrue(all(x > 0 for x in sides))
        from itertools import combinations
        points = load_dataset()['locations']
        for triple in combinations(points, 3):
            sides = [distance_m(a['latitude'], a['longitude'], b['latitude'], b['longitude'])
                     for a, b in combinations(triple, 2)]
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
            self.assertEqual(len(lines['features']), 6)
            self.assertEqual(len(lines['features'][0]['geometry']['coordinates']), 41)


class APITests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_and_locations(self):
        self.assertEqual(self.client.get('/health').status_code, 200)
        data = self.client.get('/locations').json()
        self.assertEqual(len(data['locations']), 4)
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

    def test_new_station_pairs_and_counts(self):
        health = self.client.get('/health').json()
        self.assertEqual((health['location_count'], health['pair_count']), (4, 6))
        bundle = self.client.get('/distances').json()
        self.assertEqual((bundle['location_count'], bundle['pair_count']), (4, 6))
        for site in ['RIO01', 'RIO02', 'RIO03']:
            response = self.client.post('/distance', json={'origin': site, 'destination': 'RIO04'})
            reverse = self.client.post('/distance', json={'origin': 'RIO04', 'destination': site})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(reverse.status_code, 200)
            self.assertAlmostEqual(response.json()['distance_m'], reverse.json()['distance_m'], places=7)

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
            self.assertEqual(len(response.json()['features']), 4 if path.endswith('/points') else 6)
        self.assertEqual(self.client.get('/openapi.json').status_code, 200)


if __name__ == '__main__':
    unittest.main()
