# GIS Training — Rio de Janeiro v2.2

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
access references. QGIS visual review and measurement comparison are pending. The independent
Vincenty numerical cross-check now passes for all six Rio pairs. Per-location status and source provenance are recorded in `data/locations.json`.

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
The coordinate dashboard works offline after dependency installation, without starting the API.
The street basemap requires online access when tiles for the current view are not cached.

Portuguese instructions: [LEIA_ME.md](LEIA_ME.md).

## Dashboard

- Choose any two of the four IDs and calculate the selected pair.
- The coordinate overview draws all **six connections**, and the chart/table list all six distances.
- Locations & Evidence shows each source, coordinate, point type and coordinate status.
- Export CSV + GeoJSON writes four result files in the chosen directory.
- Save chart as PNG exports the current coordinate chart.
- Reload coordinates refreshes data, selectors, counts and charts; previous comparisons clear.
- Compare with local API checks the complete dataset, method, units and all six pair results.
- Numerical & QGIS Checks runs the independent Vincenty calculation, exports a blank QGIS
  template, imports measured values and saves the latest check report as JSON.

The chart can display an OpenStreetMap street basemap or the original coordinate overview.
Neither is a QGIS screenshot. The plotted and exported lines sample the ellipsoidal geodesic.

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
| GET `/validation` | Independent GeographicLib/Vincenty numerical cross-check |
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

## Numerical checks completed in code

Three different checks now have separate purposes:

1. **Desktop/API consistency** checks the HTTP transport, data, counts, units and method.
   Both use GeographicLib, so this is not an independent implementation.
2. **Independent numerical check** compares GeographicLib with a Vincenty inverse
   implementation in `independent_geodesic.py`, using only Python's `math` module.
   It does not call GeographicLib, PyProj or PROJ. All six Rio pairs pass the 0.01 m
   numerical tolerance. Vincenty's iterative method is suitable for these short
   baselines; near-antipodal cases can fail. Failure is reported explicitly, with
   no hidden fallback to the primary engine.
3. **QGIS measurement comparison** consumes the actual measured values supplied
   by the user. It remains PENDING until measurements are entered. None are invented.

None of these checks establishes ground positional accuracy.

### Import measured QGIS results

Use **Save QGIS CSV template** in the new dashboard tab, or copy the bundled
`data/qgis_reference_template.csv`. The six `qgis_distance_m` cells are deliberately
blank. Confirm that QGIS uses the exact current points, WGS 84 ellipsoid and meters;
fill only those cells, using a decimal point. Preserve the identifiers, version,
coordinate hash, CRS, ellipsoid, measurement method and distance-unit columns.
Then choose **Import QGIS measurements**.

The importer requires every pair once (either direction), checks the declared
settings and coordinate fingerprint, and rejects invalid numbers, wrong units,
stale coordinates, duplicate/unknown pairs and missing rows. Blank measurements
remain PENDING; some measured/blank rows produce INCOMPLETE; differences above
0.01 m produce FAIL. PASS requires all six measurements to agree within tolerance.
The file's metadata is a declaration of the settings used, not proof of how the
measurements were obtained. Use sufficient measurement precision for the chosen tolerance.

### Verify in PowerShell without opening the dashboard

```powershell
.\.venv312\Scripts\python.exe verify_project.py
```

This runs the independent calculation; API is NOT_RUN and QGIS is PENDING.
With the API running in another window:

```powershell
.\.venv312\Scripts\python.exe verify_project.py --api-url http://127.0.0.1:8002 --output verification.json
```

To include actual QGIS values:

```powershell
.\.venv312\Scripts\python.exe verify_project.py --api-url http://127.0.0.1:8002 --qgis-csv completed_qgis.csv --output verification.json
```

A supplied incomplete/blank QGIS file, failed independent calculation, inconsistent
API result or connection error returns a nonzero exit code. No QGIS file provided
means PENDING, not an overall completed QGIS validation. `VERIFY_API.cmd` runs the
independent and live API checks; start `RUN_API.cmd` first.

`RUN_TESTS.cmd` installs test requirements and runs the full automated suite.
Both API and dashboard launchers now call `SETUP.cmd`, so either can create the
Python 3.12 environment. Initial setup requires internet.

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

### Added in v2.1

- `independent_geodesic.py`: separate Vincenty numerical implementation.
- `validation.py`: independent, API and QGIS report logic.
- `verify_project.py`: CLI checks with JSON export and meaningful exit status.
- `data/qgis_reference_template.csv`: six blank reference measurements.
- `SETUP.cmd`, `RUN_TESTS.cmd`, `VERIFY_API.cmd`: Windows setup and verification.
- `docs/numerical_validation.json`: actual independent-check result for the bundled coordinates.

Walking/driving routes remain a separate future exercise. This release measures
ellipsoidal point separations and does not model routes or transport itineraries.

## Street map and screenshot gallery — v2.2

**Distance Dashboard** now draws the same four points and all six geodesic
connections over an OpenStreetMap basemap with streets and neighborhood labels.
The selected pair is highlighted. The numerical engine and source coordinates
have not changed. The basemap is displayed in Web Mercator solely for visualization;
all distances remain ellipsoidal WGS 84 values.

- **Street basemap** toggles between streets and the coordinate overview.
- **Load street map** requests only the current Rio viewport and respects the local cache.
- **Open Rio in OpenStreetMap** opens the region in your browser.
- **Open origin in OpenStreetMap** opens a marker for the selected origin point.
- The Matplotlib toolbar supports pan/zoom on the loaded image and reset to the
  original view; it does not request other regions or higher-resolution tiles.
- **Save chart as PNG** preserves the visible map and attribution.
- The six-row table is now in **All Distances**, giving the map more room.

Network loading runs in a worker, keeping the window responsive. Online access
is required for uncached tiles. If loading fails, the coordinate view remains
available and a message explains how to retry. The application caches the
current view with HTTP expiry/conditional requests. Cached revisits can reuse
already obtained tiles; there is no offline-area download or tile archive.
Only a single viewport is loaded, with at most two concurrent requests and 24
tiles. User-Agent identification and visible OpenStreetMap attribution are included.
Service policy: https://operations.osmfoundation.org/policies/tiles/
OSM attribution: https://www.openstreetmap.org/copyright
Tile cache `.map_cache/` is local and ignored by Git.

**QGIS Screenshots** starts empty. Choose **Add QGIS screenshots** to import
your actual PNG/JPEG/WebP captures. They are copied into `assets/qgis_screenshots/`;
existing captures are preserved, identical images are reused, and same-name
different files receive a suffix. The selector switches captures and the preview
resizes proportionally. **Reload gallery** discovers files copied into the folder.
Local screenshot imports are ignored by Git and are not automatically uploaded.
No promotional or generated image is passed off as an original QGIS capture.
Viewing a screenshot does not automatically complete numerical or positional validation.

New files: `basemap.py`, `gallery.py`, `tests/test_maps.py`. Pillow is now an explicit
dependency; run `SETUP.cmd` after updating, then `RUN_DASHBOARD.cmd`.
