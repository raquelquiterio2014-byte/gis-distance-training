# GIS Training — Rio de Janeiro

English Python desktop dashboard and local FastAPI service following the Paris
exercise in this repository: **QGIS → Python → FastAPI → comparison → GitHub**.
The code is published first; visual QGIS review and independent reference measurements
are still pending. This is an educational exercise.

## Access points

| ID | Access reference | Latitude | Longitude |
|---|---|---:|---:|
| RIO01 | Copacabana Palace — Main Entrance | -22.9670 | -43.1786 |
| RIO02 | Christ the Redeemer — Cosme Velho Train Access | -22.9406 | -43.1985 |
| RIO03 | Sugarloaf Cable Car — Praia Vermelha Access | -22.9558 | -43.1670 |

**APPROXIMATE_PENDING_QGIS_REVIEW**: these are provisional nearby reference positions,
not surveyed or visually confirmed entrance coordinates. RIO02 is the lower railway
station at Cosme Velho, not the Christ statue. RIO03 is the lower cable car station,
not the summit. Distances ignore street routes, railway/cable car paths and altitude.
Official address sources and coordinate provenance are in `data/locations.json`.

## Quick start on Windows / PyCharm

1. Download/extract the repository and open the `rio` folder.
2. Double-click **RUN_DASHBOARD.cmd** (Python 3.12 required). First setup installs dependencies.
3. After setup, double-click **RUN_API.cmd** and keep that window open.
4. Click **Compare with local API** in the English dashboard.

The dashboard also runs without starting the API. Select origin/destination IDs
and click **Calculate selected pair**. Three tabs show the distance dashboard,
access points/evidence, and API comparison. Export CSV/GeoJSON or save a chart as PNG.
The coordinate overview has no street basemap; it is not a QGIS screenshot.

Alternatively, from this `rio` folder:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
.\.venv312\Scripts\python.exe main.py
```

In another terminal in the same folder:

```powershell
.\.venv312\Scripts\python.exe api.py
```

Or use `.\.venv312\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8002`.
Run `api.py` directly in PyCharm using the same environment. Open this folder as
the project to avoid importing the root or Paris modules with the same names.

**Rio uses port 8002**, Paris uses 8001, the regional exercise uses 8000.
Documentation: http://127.0.0.1:8002/docs. Stop the server with Ctrl+C.
Python for Windows normally includes Tkinter; Linux may require python3-tk.
Portuguese instructions: [LEIA_ME.md](LEIA_ME.md).

## API

| Endpoint | Purpose |
|---|---|
| GET `/health` | Status and dataset version |
| GET `/points` | Dataset metadata and three points; alias of `/locations` |
| GET `/distances` | All three pairs with source coordinates and metadata |
| GET `/distance?from_id=RIO01&to_id=RIO02` | One known pair |
| POST `/distance` | A pair of IDs, as in Paris, or custom coordinates |
| GET `/geojson/points` | Three Point features |
| GET `/geojson/geodesics` | Three sampled geodesic lines |

Paris-style POST body:

```json
{"origin": "RIO01", "destination": "RIO02"}
```

Custom coordinate POST body:

```json
{
  "origin": {"latitude": -22.9670, "longitude": -43.1786},
  "destination": {"latitude": -22.9406, "longitude": -43.1985}
}
```

Unknown IDs return 404; invalid POST input returns 422. Same-ID POST requests
return 422; GET/custom-coordinate requests can return zero distance. The API binds
to localhost and does not edit the dataset.

## Method and comparison

`core.py` uses `Geodesic.WGS84.Inverse(...)["s12"]` from GeographicLib, in meters.
Like Paris, this solves the inverse geodesic problem on the WGS 84 ellipsoid.
Paris uses PyProj; Rio uses GeographicLib. No spherical Haversine approximation,
centroids or projected planar lengths are used. GeographicLib samples each line
for the coordinate chart and GeoJSON output.

`data/locations.json` is the single coordinate source. After edits, increment
`dataset_version`, then use **Reload coordinates**. The API reloads that JSON
per request. The API comparison checks version, coordinates, CRS, ellipsoid,
status and all three pair results, with a 0.01 m numerical tolerance. The desktop
and API share the calculation engine: agreement checks integration and consistency,
not independent geodetic accuracy. Decimal places do not imply positional accuracy.

For the QGIS stage:

1. Export/import `rio_points.geojson` (EPSG:4326; order: longitude, latitude).
2. Visually review and adjust the three access references on a suitable basemap.
   Update `data/locations.json` with final coordinates, provenance and review date;
   change its status only after review. Reload/re-export before comparing.
3. Set QGIS measurement ellipsoid to WGS 84 and distance units to meters.
4. Record all three independently calculated ellipsoidal distances, with exactly
   the same coordinates. Compare to `python_distances.csv`.
5. Use a numerical tolerance consistent with displayed rounding; 0.01 m is suitable
   for unrounded values with matching coordinates/method. It is not positional accuracy.

**QGIS reference values: pending.** No QGIS measurements, actual QGIS screenshots,
or full workflow validation are claimed. Add actual screenshots under `assets/`
after running that stage; the final LinkedIn post/images follow validation.

## Tests and files

```powershell
.\.venv312\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv312\Scripts\python.exe -m unittest discover -s tests -v
```

Tests cover a known equatorial distance, symmetry, zero distance, triangle
inequality, invalid/nonfinite coordinates, exports, request validation, point
endpoints, ID/coordinate requests and desktop/API results. Full window interaction
still needs a local Windows run. See `VALIDATION.txt` for checks performed.

- `main.py`: English desktop dashboard, pair selection and live HTTP comparison.
- `api.py`: local FastAPI service.
- `core.py`: shared distance engine and exports.
- `data/locations.json`: coordinates and evidence notes.
- `data/rio_entrances.geojson`: generated QGIS starter snapshot; regenerate after coordinate edits.
- `tests/`: automated checks.
- `RUN_DASHBOARD.cmd`, `RUN_API.cmd`: Windows launchers.
- `assets/`: future genuine QGIS captures; none included yet.
- `SOURCES.md`: sources and approximation notes.
