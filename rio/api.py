"""Run in PyCharm, or: python -m uvicorn api:app --reload"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from core import load_dataset, result_bundle, pair_result, distance_m, points_geojson, lines_geojson

app = FastAPI(title='Rio de Janeiro GIS Distance Training', version='1.0.0',
              description='Approximate access references. WGS 84 ellipsoidal geodesics; no routes or altitude.')


class Coordinate(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class DistanceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    origin: Coordinate
    destination: Coordinate


class SiteDistanceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    origin: str = Field(min_length=1, examples=['RIO01'])
    destination: str = Field(min_length=1, examples=['RIO02'])


@app.get('/health')
def health():
    dataset = load_dataset()
    return {'status': 'ok', 'dataset_version': dataset['dataset_version']}


@app.get('/locations')
@app.get('/points')
def locations():
    dataset = load_dataset()
    return {k: dataset[k] for k in ['dataset_version', 'crs', 'ellipsoid',
                                   'coordinate_status', 'note', 'locations']}


@app.get('/distances')
def distances():
    return result_bundle(load_dataset())


@app.get('/distance')
def distance(from_id: str = Query(...), to_id: str = Query(...)):
    dataset = load_dataset()
    points = {p['id']: p for p in dataset['locations']}
    if from_id not in points or to_id not in points:
        raise HTTPException(status_code=404, detail='Unknown location ID. See /locations.')
    return {'dataset_version': dataset['dataset_version'], 'ellipsoid': 'WGS84',
            'coordinate_status': dataset['coordinate_status'],
            **pair_result(points[from_id], points[to_id])}


@app.post('/distance')
def custom_distance(request: SiteDistanceRequest | DistanceRequest):
    if isinstance(request, SiteDistanceRequest):
        if request.origin == request.destination:
            raise HTTPException(status_code=422, detail='Select two different access points.')
        return distance(request.origin, request.destination)
    meters = distance_m(request.origin.latitude, request.origin.longitude,
                        request.destination.latitude, request.destination.longitude)
    return {'ellipsoid': 'WGS84', 'method': 'ellipsoidal geodesic',
            'distance_m': meters, 'distance_km': meters / 1000,
            'origin': request.origin.model_dump(), 'destination': request.destination.model_dump(),
            'note': 'User-supplied coordinates; no route or altitude.'}


@app.get('/geojson/points')
def geojson_points():
    return points_geojson(load_dataset())


@app.get('/geojson/geodesics')
def geojson_lines():
    return lines_geojson(load_dataset())


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8002)
