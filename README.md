# GIS Distance Training

Hands-on GIS learning with **QGIS and Python**, using European regional polygons to calculate and compare distances between geometric centroids.

This is an educational project, separate from the official ERA Energy project. The current release is a **Python desktop application** with a Portuguese interface, run locally through PyCharm. FastAPI is planned and is not implemented yet.

## Desktop application

![Map and results](docs/screenshots/map-results.png)

- Load the included 299 NUTS 2024 level 2 regions, or a compatible polygon GeoJSON.
- Select two regions and display their polygons, centroids, and geodesic connection.
- Compare FR10–FRF3 against the recorded QGIS reference.
- Export a JSON report, GeoJSON points and line, and a PNG map.
- Explore offline map images and the calculation workflow.

<details>
<summary>Map gallery and methodology screenshots</summary>

![Map gallery](docs/screenshots/map-gallery.png)
![Calculation workflow](docs/screenshots/calculation-workflow.png)

</details>

## Run in PyCharm / Windows

Python **3.12** is recommended. Download and extract the repository, open its root folder in PyCharm, and select a Python virtual environment.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Alternatively, with the environment active:

```bash
python -m pip install -r requirements.txt
python main.py
```

Tkinter is included with standard Windows Python installations when Tcl/Tk is enabled. Dependency installation requires internet; the included data and maps work offline afterwards. QGIS is not required to run the desktop app.

Portuguese instructions: [LEIA_ME.md](LEIA_ME.md).

## Calculation and reference result

1. Read WGS 84 polygon coordinates from GeoJSON.
2. Transform polygons to **EPSG:3035 — ETRS89 / LAEA Europe**.
3. Calculate one geometric centroid per region.
4. Transform centroids to **EPSG:4326 — WGS 84**.
5. Solve the inverse geodesic problem with `pyproj.Geod`, using the WGS 84 ellipsoid.

| Region | NUTS ID | Centroid longitude | Centroid latitude |
|---|---|---:|---:|
| Île-de-France | FR10 | 2.5106953496118245 | 48.71303095314115 |
| Lorraine | FRF3 | 6.146890443692983 | 48.76078944599512 |

Recorded QGIS reference: **267492.77227324113 m**, approximately **267.49 km**. The desktop result agrees at the displayed precision. The numerical reference check is shown only for this pair. A separate GeographicLib calculation of these same coordinates also agreed at the reported precision; it is not a dependency or built-in app check.

### Interpretation and limitations

- This is the geodesic distance between the computed **regional centroids**, not a road route or minimum distance between polygon boundaries.
- The included boundaries are generalized at **1:20 million**. Centroids depend on boundary geometry and the projection used to compute them, and can fall outside polygons.
- Agreement across software checks numerical consistency; it does not establish positional accuracy or constitute field validation. The app's 1 m tolerance is a numerical comparison criterion.
- EPSG:3035 is chosen for this European exercise. Adapt the projection and assumptions before applying the workflow elsewhere.
- The exported GeoJSON has two points and a two-vertex connecting line. The desktop map uses intermediate geodesic points for display. When remeasuring in QGIS, use WGS 84 ellipsoidal measurement.

## Verification

```bash
python -m unittest -v
```

Five existing tests cover the QGIS reference, reversed endpoints and same-region rejection, invalid coordinates, GeoJSON export structure, and rejected input.

## Files

| Path | Purpose |
|---|---|
| `main.py` | Tkinter interface and Matplotlib maps |
| `core.py` | Data validation, centroid calculation, geodesic distance, GeoJSON export |
| `data/NUTS_2024.geojson` | Included Eurostat GISCO NUTS 2024 level 2 data |
| `assets/` | Map images rendered from the included polygons |
| `docs/screenshots/` | Captures of the running desktop application |
| `exemplo_resultado.json` | Example calculation report |
| `test_core.py` | Calculation and validation tests |
| `FONTES.md` | Data attribution, conditions, and technical sources |

## Data attribution

Source: **Eurostat GISCO — NUTS 2024**, level 2, 1:20 million, EPSG:4326. **© EuroGeographics** for administrative boundaries.

[Official dataset](https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_4326_LEVL_2.geojson) · [GISCO catalogue](https://gisco-services.ec.europa.eu/distribution/v2/nuts/nuts-2024-files.html) · [Conditions and sources](FONTES.md).

Third-party geographic data remain subject to their source conditions; inclusion here does not grant additional reuse rights.

## Next learning stages

- Expose the calculation through FastAPI and compare API responses with the desktop and QGIS reference.
- Practice point-to-point calculations for selected landmarks.
- Repeat with US and other geographic datasets, selecting appropriate projections and methods.
