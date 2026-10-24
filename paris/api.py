"""Local API for geodesic distances between the included Paris entrance points."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from core import all_distances, calculate, load_points


class DistanceRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    origin: str = Field(min_length=1, examples=['notre_dame'])
    destination: str = Field(min_length=1, examples=['eiffel_tower'])


@asynccontextmanager
async def lifespan(app):
    app.state.points = load_points()
    yield


app = FastAPI(title='Paris GIS Distance Training API', version='1.0.0', lifespan=lifespan,
              description='WGS 84 geodesic distances between approximate digitized entrance points. No road routing.')


@app.get('/health')
def health(request: Request):
    return {'status': 'ok', 'point_count': len(request.app.state.points)}


@app.get('/points')
def points(request: Request):
    return request.app.state.points


@app.get('/distances')
def distances(request: Request):
    return all_distances(request.app.state.points)


@app.post('/distance')
def distance(payload: DistanceRequest, request: Request):
    rows = request.app.state.points
    if payload.origin not in rows or payload.destination not in rows:
        raise HTTPException(404, 'Unknown site identifier.')
    try:
        return calculate(rows, payload.origin, payload.destination)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
