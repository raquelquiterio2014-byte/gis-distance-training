"""Load only the currently viewed OSM viewport, with HTTP-aware local caching.

No tile archive, offline-area download, background prefetch or extra zoom levels.
https://operations.osmfoundation.org/policies/tiles/
"""
import io
import json
import math
import re
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from PIL import Image
from core import ROOT

RADIUS = 6378137.0
USER_AGENT = 'GISDistanceTraining-Rio/2.2 (+https://github.com/raquelquiterio2014-byte/gis-distance-training)'
DEFAULT_PROVIDER = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
ATTRIBUTION = '© OpenStreetMap contributors'
CACHE_DIR = ROOT / '.map_cache'


@dataclass
class StreetMap:
    image: Image.Image
    extent: tuple
    bounds_lon_lat: tuple
    view_key: tuple
    attribution: str = ATTRIBUTION
    stale: bool = False


def mercator(longitude, latitude):
    if not (-85.05112878 <= latitude <= 85.05112878):
        raise ValueError('Street basemap supports latitudes within Web Mercator limits')
    return RADIUS * math.radians(longitude), RADIUS * math.asinh(math.tan(math.radians(latitude)))


def lon_lat(x, y):
    return math.degrees(x / RADIUS), math.degrees(math.atan(math.sinh(y / RADIUS)))


def view_spec(dataset, provider=DEFAULT_PROVIDER):
    points = dataset['locations']
    longitudes = [p['longitude'] for p in points]
    latitudes = [p['latitude'] for p in points]
    dx = max(max(longitudes) - min(longitudes), .008) * .22
    dy = max(max(latitudes) - min(latitudes), .008) * .28
    bounds = (min(longitudes) - dx, max(longitudes) + dx,
              min(latitudes) - dy, max(latitudes) + dy)
    west, east, south, north = bounds
    if west < -180 or east > 180:
        raise ValueError('Dateline-crossing basemaps are not supported; use coordinate view')
    mercator(west, south)
    mercator(east, north)
    for zoom in range(14, 1, -1):
        n = 2 ** zoom
        def tile(lon, lat):
            return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
        x0, y0 = tile(west, north)
        x1, y1 = tile(east, south)
        tile_bounds = (math.floor(x0), math.floor(x1), math.floor(y0), math.floor(y1))
        xmin, xmax, ymin, ymax = tile_bounds
        if (xmax - xmin + 1) * (ymax - ymin + 1) <= 24:
            return bounds, (provider, zoom, *tile_bounds)
    raise ValueError('Map viewport too large')


def _expiry(headers, now):
    max_age = re.search(r'(?:^|,)\s*max-age=(\d+)', headers.get('Cache-Control', ''), re.I)
    if max_age:
        return now + max(0, int(max_age[1]) - int(headers.get('Age', '0') or '0'))
    try:
        return parsedate_to_datetime(headers['Expires']).timestamp()
    except (KeyError, TypeError, ValueError, OverflowError):
        return now + 7 * 86400


def _read_image(data):
    with Image.open(io.BytesIO(data)) as image:
        if image.size != (256, 256):
            raise ValueError('Unexpected basemap tile size')
        return image.convert('RGB')


def _tile(zoom, x, y, provider, cache_dir, opener=urlopen):
    import hashlib
    folder = Path(cache_dir) / hashlib.sha256(provider.encode()).hexdigest()[:12]
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{zoom}_{x}_{y}.png'
    metadata_path = path.with_suffix('.json')
    cached, metadata = None, {}
    try:
        cached = _read_image(path.read_bytes())
        metadata = json.loads(metadata_path.read_text())
        if not isinstance(metadata, dict):
            metadata = {}
    except (OSError, ValueError, json.JSONDecodeError):
        metadata = {}
    now = time.time()
    if cached is not None and metadata.get('expires_at', 0) > now:
        return cached, False
    headers = {'User-Agent': USER_AGENT}
    if cached is not None:
        if metadata.get('etag'): headers['If-None-Match'] = metadata['etag']
        if metadata.get('last_modified'): headers['If-Modified-Since'] = metadata['last_modified']
    request = Request(provider.format(z=zoom, x=x, y=y), headers=headers)
    try:
        with opener(request, timeout=8) as response:
            data = response.read(2 * 1024 * 1024)
            image = _read_image(data)
            metadata = {'expires_at': _expiry(response.headers, now),
                        'etag': response.headers.get('ETag'), 'last_modified': response.headers.get('Last-Modified')}
            path.write_bytes(data)
            metadata_path.write_text(json.dumps(metadata), encoding='utf-8')
            return image, False
    except HTTPError as exc:
        if exc.code == 304 and cached is not None:
            metadata['expires_at'] = _expiry(exc.headers, now)
            metadata_path.write_text(json.dumps(metadata), encoding='utf-8')
            return cached, False
        if cached is not None:
            return cached, True
        raise
    except (OSError, ValueError):
        if cached is not None:
            return cached, True
        raise


def load_street_map(dataset, cache_dir=CACHE_DIR, provider=DEFAULT_PROVIDER, opener=urlopen):
    """Called from a worker for a single visible viewport; never accesses Tk."""
    bounds, key = view_spec(dataset, provider)
    _, zoom, xmin, xmax, ymin, ymax = key
    image = Image.new('RGB', ((xmax - xmin + 1) * 256, (ymax - ymin + 1) * 256))
    stale = False
    tiles = [(x, y) for y in range(ymin, ymax + 1) for x in range(xmin, xmax + 1)]
    def fetch(position):
        x, y = position
        return position, _tile(zoom, x, y, provider, cache_dir, opener)
    with ThreadPoolExecutor(max_workers=2) as pool:
        for (x, y), (tile, is_stale) in pool.map(fetch, tiles):
            image.paste(tile, ((x - xmin) * 256, (y - ymin) * 256))
            stale = stale or is_stale
    n = 2 ** zoom
    left, right = (xmin / n * 2 - 1) * math.pi * RADIUS, ((xmax + 1) / n * 2 - 1) * math.pi * RADIUS
    top, bottom = (1 - ymin / n * 2) * math.pi * RADIUS, (1 - (ymax + 1) / n * 2) * math.pi * RADIUS
    return StreetMap(image=image, extent=(left, right, bottom, top), bounds_lon_lat=bounds,
                     view_key=key, stale=stale)


def openstreetmap_url(dataset, point=None):
    if point is not None:
        lat, lon = point['latitude'], point['longitude']
        return f'https://www.openstreetmap.org/?mlat={lat:.7f}&mlon={lon:.7f}#map=16/{lat:.7f}/{lon:.7f}'
    west, east, south, north = view_spec(dataset)[0]
    return f'https://www.openstreetmap.org/#map=14/{(south + north) / 2:.7f}/{(west + east) / 2:.7f}'
