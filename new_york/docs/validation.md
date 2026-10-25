# New York validation — 2026-10-25

Observed in user-provided local Windows screenshots during the guided run:

- 14 unittest tests passed in 0.444 seconds.
- Tkinter dashboard opened and displayed all three pairwise distances.
- FastAPI documentation loaded at http://127.0.0.1:8003/docs.
- Dashboard/API comparison: PASS for all 3 pairs; displayed delta 0.000000 m, tolerance 0.01 m.
- QGIS project measurement settings: WGS 84 (EPSG:7030), meters.
- QGIS QgsDistanceArea computed distances from the imported point geometries:

| Pair | QGIS distance (m) |
| --- | ---: |
| NYC01 / NYC02 | 8249.518 |
| NYC01 / NYC03 | 1346.200 |
| NYC02 / NYC03 | 9594.769 |

These match the Python outputs at the displayed 0.001 m precision.
The QGIS script sets the source CRS from the layer and the ellipsoid to WGS84.
The API and desktop share core.py. QGIS also uses GeographicLib internally;
therefore this is application/dataset consistency, not independent algorithm validation.
The earlier GeographicLib/PyProj agreement is likewise not evidence of an independent geodesic algorithm.

Coordinates remain approximate access references. The OpenStreetMap overview
and labels do not establish exact entrance positions or field-surveyed accuracy.
No street routes, ferry routes, altitude, or travel times are included.
The point at Fifth Avenue represents St. Patrick's Cathedral frontage.
The Statue of Liberty point is on Liberty Island, not at the Manhattan ferry terminal.

The user's local new_york_training.qgz was saved on Windows and is not included
in this upload; screenshots and the local project are retained by the user.
