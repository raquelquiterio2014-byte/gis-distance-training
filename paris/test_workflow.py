import json
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from api import app
from core import load_points, calculate, all_distances, export_lines


class WorkflowTests(unittest.TestCase):
    def test_all_qgis_references(self):
        rows=all_distances(load_points())
        self.assertEqual(len(rows),3)
        for row in rows:self.assertLess(row['difference_m'],.001)

    def test_reversed_endpoints(self):
        points=load_points()
        self.assertAlmostEqual(calculate(points,'louvre','eiffel_tower')['distance_m'],calculate(points,'eiffel_tower','louvre')['distance_m'],places=8)

    def test_same_and_unknown_rejected(self):
        points=load_points()
        for a,b in [('louvre','louvre'),('unknown','louvre')]:
            with self.assertRaises(ValueError):calculate(points,a,b)

    def test_export_endpoints(self):
        points=load_points()
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'lines.geojson';export_lines(points,path)
            features=json.loads(path.read_text())['features']
            self.assertEqual(len(features),3)
            for feature in features:
                self.assertEqual(feature['geometry']['coordinates'][0],points[feature['properties']['origin']]['coordinates'])

    def test_api_all_pairs(self):
        with TestClient(app) as client:
            self.assertEqual(client.get('/health').json()['point_count'],3)
            self.assertEqual(len(client.get('/points').json()),3)
            self.assertEqual(len(client.get('/distances').json()),3)
            for row in all_distances(load_points()):
                response=client.post('/distance',json={k:row[k] for k in ('origin','destination')})
                self.assertEqual(response.status_code,200)
                self.assertEqual(response.json(),row)

    def test_api_invalid_requests(self):
        with TestClient(app) as client:
            for payload,status in [({'origin':'unknown','destination':'louvre'},404),({'origin':'louvre','destination':'louvre'},422),({'origin':'louvre'},422),({'origin':'louvre','destination':'notre_dame','extra':1},422)]:
                self.assertEqual(client.post('/distance',json=payload).status_code,status)


if __name__=='__main__':unittest.main()
