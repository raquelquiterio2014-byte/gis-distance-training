# GIS Training — Paris

English Python desktop dashboard and local FastAPI service using the three entrance points digitized by the user in QGIS. The original GeoJSON is included unchanged.

## Quick start on Windows

1. Extract the entire ZIP to a normal folder (do not run inside the ZIP).
2. Open the extracted `GIS_Paris_Training` folder.
3. Double-click **RUN_DASHBOARD.cmd**. The first run creates a Python 3.12 environment and installs requirements (internet required).
4. To use API comparison, double-click **RUN_API.cmd** in the same folder after setup finishes. Keep its window open.
5. In the dashboard, open **API comparison** and click **Compare all three pairs with API**.

The dashboard works without starting the API. Select two sites and click **Calculate and show map**. The **All distances** tab lists all three pairs and QGIS comparisons. **QGIS screenshots** shows the user's actual map captures. The primary map is an offline coordinate plot with geodesic connections, not a street basemap. The OpenStreetMap button opens an online map separately.

## PyCharm / PowerShell

Open this folder in PyCharm. Use Python 3.12 and run:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\python.exe -m pip install -r requirements.txt
.\.venv312\Scripts\python.exe main.py
```

In a separate terminal in this folder:

```powershell
.\.venv312\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8001
```

Paris uses **port 8001**, separate from the earlier regional-centroid API on port 8000. Stop the API with Ctrl+C.

API documentation: http://127.0.0.1:8001/docs

| Endpoint | Purpose |
|---|---|
| GET /health | Status and point count |
| GET /points | Point coordinates, entrance descriptions and sources |
| GET /distances | All three pairs |
| POST /distance | One pair selected by site identifiers |

Example POST body:

```json
{"origin": "notre_dame", "destination": "eiffel_tower"}
```

Valid identifiers: `notre_dame`, `louvre`, `eiffel_tower`. Unknown identifiers return 404; invalid requests or identical endpoints return 422.

## Results

| Pair | WGS 84 geodesic distance (m) |
|---|---:|
| Notre-Dame – Louvre | 1274.9159126132859 |
| Notre-Dame – Eiffel Tower | 4065.956709285214 |
| Louvre – Eiffel Tower | 3124.051968075597 |

The QGIS references were transcribed from the user's distance matrix screenshots. Differences below the displayed precision can occur with different library versions. A 1 m tolerance checks numerical agreement only.

## Method and scope

Read longitude/latitude from the user's WGS 84 Point GeoJSON, then calculate the inverse geodesic with `pyproj.Geod(ellps='WGS84')`. No centroids or polygon reprojection are used in this exercise. API and desktop share the same module and points; their agreement is an integration check, not independent validation of location accuracy.

The manually digitized entrance positions are approximate and were not surveyed. The Notre-Dame point was retained at the user's chosen position. These distances apply to those recorded points; they are not road routes or verified door-to-door measurements. Source website references identify entrance descriptions, not surveyed coordinates.

## Exports

- JSON: all three calculation reports.
- GeoJSON: three two-vertex connection lines, reusable in QGIS with WGS 84 ellipsoidal measurements.
- PNG: the current coordinate plot.

## Tests

```powershell
.\.venv312\Scripts\python.exe -m unittest -v
```

Six tests cover QGIS agreement, reversed endpoints, rejected same/unknown sites, export endpoints, HTTP API agreement for all pairs, and invalid API requests.

## Files

`main.py`: English Tkinter/Matplotlib dashboard.
`core.py`: point loading, geodesic calculations and exports.
`api.py`: FastAPI service.
`test_workflow.py`: calculation and API tests.
`data/`: original user-provided GeoJSON.
`assets/`: original QGIS screenshots and a generated coordinate plot preview.

Desktop syntax and map rendering were checked here; complete window interaction still needs the local Windows run. The live API and all three pair responses were checked over HTTP. See SOURCES.md for attribution.
