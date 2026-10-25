"""Export the current coordinate dataset without opening the dashboard."""
from core import ROOT, load_dataset, export_dataset, points_geojson
import json

if __name__ == '__main__':
    dataset = load_dataset()
    for path in export_dataset(dataset, ROOT / 'exports'):
        print(path)
    (ROOT / 'data' / 'new_york_entrances.geojson').write_text(
        json.dumps(points_geojson(dataset), indent=2, ensure_ascii=False), encoding='utf-8')
