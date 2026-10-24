import json
import tempfile
import unittest
from pathlib import Path
from core import load_regions, calculate, distance, export_geojson, REFERENCE_M

class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regions=load_regions(Path(__file__).parent/'data'/'NUTS_2024.geojson')
    def test_qgis_reference(self):
        r=calculate(self.regions,'FR10','FRF3')
        self.assertLess(abs(r['distance_m']-REFERENCE_M),.001)
        self.assertAlmostEqual(r['centroids_lon_lat'][0][0],2.5106953496118245,places=9)
    def test_reverse_and_same(self):
        a=calculate(self.regions,'FR10','FRF3');b=calculate(self.regions,'FRF3','FR10')
        self.assertAlmostEqual(a['distance_m'],b['distance_m'],places=6)
        with self.assertRaises(ValueError):calculate(self.regions,'FR10','FR10')
    def test_invalid_coordinate(self):
        with self.assertRaises(ValueError):distance((0,95),(0,1))
    def test_geojson_roundtrip(self):
        r=calculate(self.regions,'FR10','FRF3')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'out.geojson';export_geojson(r,p)
            obj=json.loads(p.read_text());self.assertEqual(len(obj['features']),3)
            self.assertEqual(obj['features'][-1]['geometry']['type'],'LineString')
    def test_reject_bad_input(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.json';p.write_text('{"type":"Point"}')
            with self.assertRaises(ValueError):load_regions(p)
if __name__=='__main__':unittest.main()
