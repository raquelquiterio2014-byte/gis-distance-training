"""CLI checks. QGIS values remain pending when no measured CSV is supplied."""
import argparse
import json
from pathlib import Path
from urllib.request import urlopen
from core import load_dataset
from validation import independent_report, qgis_report, compare_api_payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-url', help='Running local API, for example http://127.0.0.1:8002')
    parser.add_argument('--qgis-csv', type=Path, help='QGIS template with actual measured distances')
    parser.add_argument('--output', type=Path, help='Optional JSON report path')
    args = parser.parse_args(argv)
    dataset = load_dataset()
    report = {'dataset_version': dataset['dataset_version'], 'independent': independent_report(dataset),
              'api': {'status': 'NOT_RUN'}, 'qgis': {'status': 'PENDING'}}
    for key, action in [('api', lambda: fetch_api(dataset, args.api_url)),
                        ('qgis', lambda: qgis_report(dataset, args.qgis_csv))]:
        if (key == 'api' and args.api_url) or (key == 'qgis' and args.qgis_csv):
            try:
                report[key] = action()
            except Exception as exc:
                report[key] = {'status': 'ERROR', 'error': str(exc)}
    text = json.dumps(report, indent=2, allow_nan=False)
    print(text)
    if args.output:
        args.output.write_text(text + '\n', encoding='utf-8')
    failed = any(report[key]['status'] in {'FAIL', 'ERROR', 'INCOMPLETE'} for key in ['independent', 'api', 'qgis'])
    # Pending unprovided QGIS data is informational; supplied blank/partial CSV is not a completed check.
    failed = failed or bool(args.qgis_csv and report['qgis']['status'] != 'PASS')
    return 1 if failed else 0


def fetch_api(dataset, base_url):
    with urlopen(base_url.rstrip('/') + '/distances', timeout=5) as response:
        payload = json.load(response)
    return compare_api_payload(dataset, payload)


if __name__ == '__main__':
    raise SystemExit(main())
