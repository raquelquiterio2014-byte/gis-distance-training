"""Run against an already-started local API: python verify_api.py."""
import argparse
import json
from pathlib import Path
from core import calculate, load_regions
from api_client import compare_with_api


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    rows = load_regions(Path(__file__).resolve().parent / 'data' / 'NUTS_2024.geojson')
    report = compare_with_api(calculate(rows, 'FR10', 'FRF3'), args.url)
    print(json.dumps(report, indent=2))
    if not report['within_1m'] or report['qgis_difference_m'] > 1:
        raise SystemExit('Comparison failed.')


if __name__ == '__main__':
    main()
