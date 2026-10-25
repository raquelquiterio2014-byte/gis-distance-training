# GIS Distance Training — New York

English Tkinter/Matplotlib desktop dashboard and FastAPI on port **8003**.
Adapted from `rio/` in raquelquiterio2014-byte/gis-distance-training.
The dashboard and API use `core.py` and the same `data/locations.json`.

## Local Windows / PowerShell setup

Open PowerShell inside this `new_york` folder:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
.\.venv312\Scripts\python.exe main.py
```

In a second PowerShell window, inside the same folder:

```powershell
.\.venv312\Scripts\python.exe api.py
```

Open http://127.0.0.1:8003/docs, then click **Compare with local API**
in the dashboard. Keep both windows open.
Alternatively run `RUN_DASHBOARD.cmd`, then `RUN_API.cmd`.
No virtual environment activation or execution policy change is required.
Both entry points also run directly in PyCharm with the project interpreter.

```powershell
Invoke-RestMethod http://127.0.0.1:8003/health
(Invoke-RestMethod http://127.0.0.1:8003/distances).distances | Format-Table
```

## Access references

| ID | Reference | Latitude | Longitude |
| --- | --- | ---: | ---: |
| NYC01 | Empire State Building, observatory access near 20 West 34th Street | 40.7486 | -73.9857 |
| NYC02 | Statue of Liberty, approximate pedestal access area behind monument | 40.6897 | -74.0452 |
| NYC03 | Fifth Avenue, St. Patrick's Cathedral frontage | 40.7585 | -73.9765 |

These are **proposed approximate training coordinates**, not surveyed entrance
positions. Official sources identify the locations/access descriptions, not
the exact numerical coordinates. Sources and notes are recorded per point
in `data/locations.json`. Dataset status: `APPROXIMATE_PENDING_QGIS_REVIEW`.
Fifth Avenue is represented by one specific frontage reference.
The Liberty Island point is not the Manhattan ferry departure point.

## Method and exports

GeographicLib solves the inverse geodesic problem on the WGS 84 ellipsoid.
Coordinates use EPSG:4326. No street routes, ferry routes or altitude are used.
GeoJSON coordinate order is **[longitude, latitude]**.
The dashboard coordinate plot has no basemap and is not a QGIS screenshot.

Use **Export CSV + GeoJSON**, or:

```powershell
.\.venv312\Scripts\python.exe export_results.py
```

Outputs in `exports/`: `new_york_points.geojson`, `new_york_geodesics.geojson`,
`python_results.json`, `python_distances.csv`.
The script also regenerates `data/new_york_entrances.geojson`.
All exports in the starter package use the provisional coordinates.

## QGIS and comparison

1. Add `data/new_york_entrances.geojson` in QGIS (EPSG:4326).
2. Inspect each proposed access reference on a suitable basemap.
3. Record any final coordinate changes in `data/locations.json`, including
   provenance/review date, and increment `dataset_version`.
4. Reload the dashboard and regenerate exports after coordinate edits.
5. Set the QGIS measurement ellipsoid to WGS 84 and units to meters.
6. Calculate all three ellipsoidal distances using those exact coordinates.
7. Compare with `exports/python_distances.csv`, recording values and differences.

Dashboard/API tolerance is 0.01 m. This checks integration using a shared engine;
it is not independent positional validation. For QGIS use a tolerance consistent
with exported rounding. Decimal places do not imply coordinate accuracy.
**Local Windows run verified by user screenshots on 2026-10-25:** 14 tests passed, dashboard opened, API comparison passed for all three pairs, and QGIS QgsDistanceArea produced matching distances to 0.001 m as displayed. Entrance positions remain approximate; no survey or exact doorway validation is claimed. QGIS also uses GeographicLib internally, so this is cross-application consistency, not an independent-algorithm check.
See `docs/validation.md` for observed QGIS values and evidence scope.

## API

GET `/health`, `/locations`, `/points`, `/distances`,
`/distance?from_id=NYC01&to_id=NYC02`, `/geojson/points`, `/geojson/geodesics`.
POST `/distance` accepts location IDs as `origin` and `destination`, or two
coordinate objects containing `latitude` and `longitude`. See `/docs`.

## Tests

```powershell
.\.venv312\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv312\Scripts\python.exe -m unittest discover -s tests -v
```

Fourteen automated tests cover geodesics, coordinate validation, exports,
API request validation and agreement with the shared engine.
