# Sources and attribution

Data and derived maps: Eurostat GISCO, NUTS 2024, level 2 regions, scale 1:20 million, EPSG:4326. © EuroGeographics for administrative boundaries.

- Dataset: https://gisco-services.ec.europa.eu/distribution/v2/nuts/geojson/NUTS_RG_20M_2024_4326_LEVL_2.geojson
- Catalogue: https://gisco-services.ec.europa.eu/distribution/v2/nuts/nuts-2024-files.html
- Applicable conditions: https://ec.europa.eu/eurostat/web/gisco/geodata/statistical-units/territorial-units-statistics

Check GISCO/EuroGeographics conditions before reuse or redistribution. No software license overrides third-party data conditions.

## Technical documentation

- https://pyproj4.github.io/pyproj/stable/api/geod.html
- https://pyproj4.github.io/pyproj/stable/api/transformer.html
- https://shapely.readthedocs.io/en/stable/reference/shapely.centroid.html
- https://fastapi.tiangolo.com/tutorial/testing/
- https://fastapi.tiangolo.com/advanced/events/

## Numerical reference

The user's QGIS measurement for FR10–FRF3: 267492.77227324113 meters. This is a recorded calculation reference, not a field measurement. Desktop and API deliberately share the same calculation engine and bundled data; their agreement checks integration consistency.
