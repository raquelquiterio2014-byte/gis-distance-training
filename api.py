"""Local FastAPI service using the same calculation engine as the desktop."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from core import calculate, load_regions

DATA_PATH = Path(__file__).resolve().parent / 'data' / 'NUTS_2024.geojson'


class DistanceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    origin: str = Field(min_length=1, max_length=20, examples=['FR10'])
    destination: str = Field(min_length=1, max_length=20, examples=['FRF3'])


class DistanceResult(BaseModel):
    origin: str
    destination: str
    origin_name: str
    destination_name: str
    centroids_lon_lat: list[tuple[float, float]]
    distance_m: float
    distance_km: float
    centroid_crs: str
    coordinate_crs: str
    ellipsoid: str
    method: str
    qgis_reference_m: float | None = None
    difference_m: float | None = None
    within_1m: bool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.regions = load_regions(DATA_PATH)
    yield


app = FastAPI(
    title='GIS Distance Training API', version='2.0.0', lifespan=lifespan,
    description='WGS 84 geodesic distances between regional centroids computed in EPSG:3035. '
                'Educational local API; numerical agreement does not establish territorial accuracy.',
)


@app.get('/health')
def health(request: Request):
    return {'status': 'ok', 'region_count': len(request.app.state.regions)}


@app.get('/regions')
def regions(request: Request):
    return [{'code': code, 'name': row['name'], 'country': row['country']}
            for code, row in sorted(request.app.state.regions.items())]


@app.post('/distance', response_model=DistanceResult, response_model_exclude_none=True)
def regional_distance(payload: DistanceRequest, request: Request):
    rows = request.app.state.regions
    for code in (payload.origin, payload.destination):
        if code not in rows:
            raise HTTPException(status_code=404, detail=f'Unknown region: {code}')
    try:
        return calculate(rows, payload.origin, payload.destination)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
