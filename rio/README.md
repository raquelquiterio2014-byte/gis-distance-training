# GIS Training — Rio de Janeiro v2

Four reference locations, six WGS 84 geodesic distances, an English Python desktop
dashboard and a local FastAPI service. Workflow: QGIS → Python → FastAPI → comparison → GitHub.

## Locations

| ID | Location | Latitude | Longitude |
|---|---|---:|---:|
| RIO01 | Copacabana Palace — Main Entrance | -22.967 | -43.1786 |
| RIO02 | Christ the Redeemer — Monument | -22.9519173 | -43.2104585 |
| RIO03 | Sugarloaf Mountain — Summit | -22.9494891 | -43.1561568 |
| RIO04 | Cosme Velho — Train Station Entrance | -22.9406 | -43.1985 |

RIO02 now represents the **Christ statue itself**, using OSM monument node
4919986733. RIO03 now represents the **Sugarloaf summit**, using OSM peak node
34582421; the lower Praia Vermelha cable car station is no longer included.
The previous Cosme Velho reference is preserved as **RIO04** with unchanged
coordinates. RIO01, Copacabana Palace, is unchanged.

These mapped feature positions identify the monuments themselves, but are not
survey-grade exact coordinates. The hotel and lower station remain approximate
access references. QGIS visual review and independent numerical comparison are
pending. Per-location status and source provenance are recorded in `data/locations.json`.

### Migration from v1

Dataset version: `rio-v2-four-locations`. RIO02 and RIO03 changed coordinates and
meaning; old v1 comparisons and images cannot serve as v2 references. RIO04 is new.
Refresh all exported GeoJSON/CSV and rerun comparisons after upgrading. The API
remains on port 8002. Previous data are retained in the repository history.

## Run on Windows / PyCharm

Download/extract the repository and open the **rio** folder. Double-click
`RUN_DASHBOARD.cmd` (Python 3.12 required); once setup completes, start
`RUN_API.cmd` in a separate window. Keep the API running for comparisons.

Or run from the `rio` folder:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
.\.venv312\Scripts\python.exe main.py
```

In a second terminal, in that same folder:

```powershell
.\.venv312\Scripts\python.exe api.py
```

API documentation: http://127.0.0.1:8002/docs. Ctrl+C stops the API.
Alternatively: `python -m uvicorn api:app --host 127.0.0.1 --port 8002`.
Rio uses port 8002; Paris uses 8001 and the regional exercise uses 8000.
Open `rio/` as the PyCharm project so modules from other exercises are not imported.
Tkinter accompanies standard Windows Python installations; Linux may need python3-tk.
The dashboard works offline after dependency installation, without starting the API.

Portuguese instructions: [LEIA_ME.md](LEIA_ME.md).

## Dashboard

- Choose any two of the four IDs and calculate the selected pair.
- The coordinate overview draws all **six connections**, and the chart/table list all six distances.
- Locations & Evidence shows each source, coordinate, point type and coordinate status.
- Export CSV + GeoJSON writes four result files in the chosen directory.
- Save chart as PNG exports the current coordinate chart.
- Reload coordinates refreshes data, selectors, counts and charts; previous comparisons clear.
- Compare with local API checks the complete dataset and all six pair results.

This chart is a coordinate plot without a street basemap, not a QGIS screenshot.
The plotted and exported line geometries sample the ellipsoidal geodesic.

## Six pairwise results

These values apply to the coordinates recorded above; they exclude all altitude
and transport paths. Extra decimal places do not imply positional accuracy.

| Pair | Distance (m) | Distance (km) |
|---|---:|---:|
| RIO01 – RIO02 | 3669.395 | 3.669395 |
| RIO01 – RIO03 | 3009.670 | 3.009670 |
| RIO01 – RIO04 | 3565.505 | 3.565505 |
| RIO02 – RIO03 | 5575.656 | 5.575656 |
| RIO02 – RIO04 | 1753.597 | 1.753597 |
| RIO03 – RIO04 | 4453.059 | 4.453059 |

In particular, **RIO02–RIO04** is the ellipsoidal separation between the Christ
monument and Cosme Velho lower station, **not the length of the railway**.

## API

| Endpoint | Purpose |
|---|---|
| GET `/health` | Status, version, four locations and six-pair count |
| GET `/points`, GET `/locations` | Coordinates, individual provenance and dataset metadata |
| GET `/distances` | All six pairs, coordinates, method and counts |
| GET `/distance?from_id=RIO02&to_id=RIO04` | One selected pair |
| POST `/distance` | IDs or custom coordinates |
| GET `/geojson/points` | Four Point features |
| GET `/geojson/geodesics` | Six sampled geodesic lines |

POST example for station-to-monument separation:

```json
{"origin": "RIO04", "destination": "RIO02"}
```

Custom-coordinate body:

```json
{
  "origin": {"latitude": -22.9406, "longitude": -43.1985},
  "destination": {"latitude": -22.9519173, "longitude": -43.2104585}
}
```

Unknown IDs return 404; invalid POST input or same-ID POST requests return 422.
GET/custom-coordinate requests can return zero distance. The API is local and read-only.

## Calculation and QGIS comparison

The shared engine uses GeographicLib `Geodesic.WGS84.Inverse(...)["s12"]`, in meters.
It generates every unordered pair with `itertools.combinations`; counts and chart
connections follow the loaded data. No centroids, spherical Haversine approximation,
projected planar length, street routing, railway/cable car path or altitude is used.

Desktop/API agreement checks shared-engine integration, not independent geodetic
or positional validation. The comparison checks source data, version, status,
CRS, ellipsoid and all pairs. Its 0.01 m tolerance is numerical, not positional accuracy.

For the next QGIS stage:

1. Open `data/rio_entrances.geojson` (four mixed monument/access points, historical filename)
   or export `rio_points.geojson` from the dashboard. CRS: EPSG:4326. Order: longitude, latitude.
2. Review all four references on an appropriate basemap and record review provenance.
3. If editing coordinates, update `data/locations.json`, increment the dataset version,
   reload and regenerate exports before comparing. API requests reread the JSON.
4. Set the QGIS measurement ellipsoid to WGS 84 and distance units to meters.
5. Independently record all six pair distances using exactly the same coordinates.
   Compare to `python_distances.csv`, with a tolerance consistent with rounding.

No QGIS reference distances have been entered; the comparison remains pending.
Actual project screenshots and the final LinkedIn post follow local verification.

## Validation

```powershell
.\.venv312\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv312\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover all six unique pairs, four point roles, preserved Cosme Velho position,
all four three-point triangle inequalities, six rendered connections, four markers,
six bars, export counts, API counts and new RIO04 requests in both directions,
plus existing numerical and invalid-input checks. See `VALIDATION.txt`.

## Files

- `main.py`: English desktop UI and live API comparison.
- `plotting.py`: shared figure renderer, usable without a desktop for verification.
- `core.py`: distance engine, dataset loading and exports.
- `api.py`: FastAPI on port 8002.
- `data/locations.json`: authoritative coordinates and provenance.
- `data/rio_entrances.geojson`: four-point starter snapshot (legacy filename).
- `data/rio_geodesics.geojson`: all six geodesic lines, generated from the same dataset.
- `tests/`: automated tests.
- `RUN_DASHBOARD.cmd`, `RUN_API.cmd`: Windows launchers.
- `SOURCES.md`: source and approximation notes.
