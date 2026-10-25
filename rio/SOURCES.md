# Sources — Rio v2 (four locations)

## Monument and summit coordinates

Retrieved directly from the OSM API on 2026-10-24:

- Christ the Redeemer monument: https://www.openstreetmap.org/node/4919986733
  API: https://api.openstreetmap.org/api/0.6/node/4919986733.json
  Node version 33, latitude -22.9519173, longitude -43.2104585.
- Sugarloaf Mountain summit: https://www.openstreetmap.org/node/34582421
  API: https://api.openstreetmap.org/api/0.6/node/34582421.json
  Node version 47, natural=peak, latitude -22.9494891, longitude -43.1561568.

These are the mapped positions of the requested monument and summit, not the lower
transport stations. They are not survey-grade exact coordinates or validated ground
control points. All altitude metadata is excluded from this exercise.

© OpenStreetMap contributors. Open Database License:
https://www.openstreetmap.org/copyright

## Unchanged approximate access references

- RIO01: Copacabana Palace, Avenida Atlantica 1702. Official address:
  https://www.belmond.com/pt-br/hotels/south-america/brazil/copacabana-palace-rio-de-janeiro/faqs
  The retained point (-22.9670, -43.1786) is a provisional front-access reference
  based on the hotel location: https://en.wikipedia.org/wiki/Copacabana_Palace
  The entrance still requires visual review; the address does not validate coordinates.
- RIO04: Cosme Velho lower train station, Rua Cosme Velho 513:
  https://www.tremdocorcovado.rio/institucional/como-chegar
  Retained coordinates (-22.9406, -43.1985), rounded from station reference:
  https://mapcarta.com/pt/W59988621

## Change from v1

RIO02 previously referred to Cosme Velho; the unchanged station position now belongs
to RIO04. RIO02 now means the Christ statue itself. RIO03 changes from the Praia
Vermelha lower cable car station to the Sugarloaf summit. RIO01 is unchanged.
Previous three-point visualizations and reference comparisons describe v1 only.
The dataset version changed to rio-v2-four-locations. QGIS review remains pending.

## Technical references

- https://geographiclib.sourceforge.io/html/python/examples.html
- https://geographiclib.sourceforge.io/html/python/code.html
- https://fastapi.tiangolo.com/tutorial/first-steps/

This educational workflow calculates ellipsoidal separations, not routes or 3D lengths.

## Independent numerical implementation (v2.1)

T. Vincenty (1975), Direct and Inverse Solutions of Geodesics on the Ellipsoid
with Application of Nested Equations, Survey Review 23(176).
Primary paper hosted by NOAA NGS: https://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf

`independent_geodesic.py` implements the inverse iteration with Python math,
without GeographicLib/PROJ calls. It is used for the short Rio baselines; failure
to converge is surfaced explicitly. Computational agreement is not positional accuracy.

## Display basemap — v2.2

OpenStreetMap Standard raster tiles: https://tile.openstreetmap.org/{z}/{x}/{y}.png
© OpenStreetMap contributors: https://www.openstreetmap.org/copyright
Usage policy: https://operations.osmfoundation.org/policies/tiles/

Only the actively viewed viewport is requested. HTTP cache metadata and conditional
requests are retained; no tile archives or offline-area download are provided.
This map is visual context, separate from numerical measurement and positional review.
User-imported QGIS captures retain their own basemap attribution.
