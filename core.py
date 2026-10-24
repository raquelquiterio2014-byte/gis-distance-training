"""GIS calculations shared by the desktop and future API. Longitude always precedes latitude."""
import json
import math
from pathlib import Path
from pyproj import Geod, Transformer
from shapely.geometry import shape, mapping, Point
from shapely.ops import transform

GEOD = Geod(ellps='WGS84')
FORWARD = Transformer.from_crs(4326, 3035, always_xy=True)
BACKWARD = Transformer.from_crs(3035, 4326, always_xy=True)
REFERENCE_M = 267492.77227324113
REFERENCE_POINTS = [(2.5106953496118245, 48.71303095314115), (6.146890443692983, 48.76078944599512)]

def load_regions(path):
    """Accept NUTS polygon GeoJSON in WGS84, not arbitrary unknown CRS."""
    obj = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if obj.get('type') != 'FeatureCollection':
        raise ValueError('The file must be a GeoJSON FeatureCollection.')
    crs = obj.get('crs', {}).get('properties', {}).get('name', '')
    if crs and not (crs.endswith('4326') or 'CRS84' in crs):
        raise ValueError('Export the GeoJSON in EPSG:4326 from QGIS before loading.')
    rows = {}
    for f in obj.get('features', []):
        p = f.get('properties') or {}
        code = p.get('NUTS_ID')
        if not code:
            raise ValueError('Missing NUTS_ID field.')
        if code in rows:
            raise ValueError(f'Duplicate code: {code}')
        g = shape(f['geometry'])
        if g.geom_type not in ('Polygon', 'MultiPolygon') or g.is_empty or not g.is_valid:
            raise ValueError(f'Invalid or non-polygon geometry: {code}')
        a,b,c,d = g.bounds
        if not (-180 <= a <= c <= 180 and -90 <= b <= d <= 90):
            raise ValueError('Coordinates outside WGS84 bounds.')
        rows[code] = {'name': p.get('NAME_LATN', p.get('NUTS_NAME', code)), 'country':p.get('CNTR_CODE',''), 'geometry':g}
    if len(rows) < 2:
        raise ValueError('At least two regions are required.')
    return rows

def centroid(region):
    projected = transform(FORWARD.transform, region['geometry'])
    point = projected.centroid
    lon,lat = BACKWARD.transform(point.x, point.y)
    return lon,lat

def distance(a,b):
    if any(not math.isfinite(v) for v in (*a,*b)):
        raise ValueError('Coordinates must be finite.')
    if any(not (-180 <= p[0] <= 180 and -90 <= p[1] <= 90) for p in (a,b)):
        raise ValueError('Longitude or latitude outside valid bounds.')
    return GEOD.inv(*a,*b)[2]

def calculate(regions, origin, destination):
    for code in (origin, destination):
        if code not in regions:
            raise ValueError(f'Unknown region: {code}')
    if origin == destination:
        raise ValueError('Choose two different regions.')
    points = [centroid(regions[c]) for c in (origin,destination)]
    meters = distance(*points)
    result = {'origin':origin,'destination':destination,'origin_name':regions[origin]['name'],
              'destination_name':regions[destination]['name'],'centroids_lon_lat':points,
              'distance_m':meters,'distance_km':meters/1000,'centroid_crs':'EPSG:3035',
              'coordinate_crs':'EPSG:4326','ellipsoid':'WGS84','method':'Geodesic between polygon centroids; no road routing'}
    if {origin,destination} == {'FR10','FRF3'}:
        result['qgis_reference_m'] = REFERENCE_M
        result['difference_m'] = abs(meters - REFERENCE_M)
        result['within_1m'] = result['difference_m'] <= 1
    return result

def export_geojson(result, path):
    features=[]
    for i,code in enumerate((result['origin'],result['destination'])):
        features.append({'type':'Feature','properties':{'NUTS_ID':code},'geometry':mapping(Point(result['centroids_lon_lat'][i]))})
    features.append({'type':'Feature','properties':{'distance_m':result['distance_m'],'ellipsoid':'WGS84'},
                     'geometry':{'type':'LineString','coordinates':result['centroids_lon_lat']}})
    Path(path).write_text(json.dumps({'type':'FeatureCollection','features':features},indent=2),encoding='utf-8')
