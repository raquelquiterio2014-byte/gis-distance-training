import io
import json
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from PIL import Image
from matplotlib.figure import Figure
from basemap import (mercator, lon_lat, view_spec, load_street_map, openstreetmap_url,
                     _tile, DEFAULT_PROVIDER, USER_AGENT)
from plotting import draw_distance_figure
from gallery import add_screenshot, list_screenshots, screenshot_thumbnail
from core import load_dataset, all_distances


def tile_png():
    stream = io.BytesIO()
    Image.new('RGB', (256, 256), '#dbe7dc').save(stream, format='PNG')
    return stream.getvalue()


class Response:
    headers = {'Cache-Control': 'max-age=604800', 'ETag': 'sample-tile'}
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, *args): return tile_png()


class MapChecks(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.data = load_dataset()

    def test_projection_roundtrip(self):
        for point in self.data['locations']:
            lon, lat = lon_lat(*mercator(point['longitude'], point['latitude']))
            self.assertAlmostEqual(lon, point['longitude'], places=9)
            self.assertAlmostEqual(lat, point['latitude'], places=9)

    def test_current_view_contains_all_points_and_is_bounded(self):
        bounds, key = view_spec(self.data)
        west, east, south, north = bounds
        for point in self.data['locations']:
            self.assertTrue(west < point['longitude'] < east)
            self.assertTrue(south < point['latitude'] < north)
        self.assertLessEqual((key[3] - key[2] + 1) * (key[5] - key[4] + 1), 24)

    def test_cache_reuse_and_identification(self):
        requests = []
        def opener(req, timeout):
            requests.append(req)
            return Response()
        _tile(14, 1, 2, DEFAULT_PROVIDER, self.folder.name, opener)
        _tile(14, 1, 2, DEFAULT_PROVIDER, self.folder.name, opener)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].get_header('User-agent'), USER_AGENT)
        self.assertNotIn('Cache-control', requests[0].headers)

    def expire(self):
        metadata_path = next(Path(self.folder.name).rglob('*.json'))
        metadata = json.loads(metadata_path.read_text())
        metadata['expires_at'] = time.time() - 1
        metadata_path.write_text(json.dumps(metadata))

    def test_expired_cache_uses_conditional_request(self):
        _tile(14, 1, 2, DEFAULT_PROVIDER, self.folder.name, lambda *a, **k: Response())
        self.expire()
        def not_modified(request, timeout):
            self.assertEqual(request.get_header('If-none-match'), 'sample-tile')
            raise HTTPError(request.full_url, 304, 'Not modified', {'Cache-Control': 'max-age=604800'}, None)
        _, stale = _tile(14, 1, 2, DEFAULT_PROVIDER, self.folder.name, not_modified)
        self.assertFalse(stale)

    def test_network_failure_uses_only_existing_cache(self):
        def offline(*args, **kwargs): raise OSError('offline')
        with self.assertRaises(OSError):
            _tile(14, 1, 2, DEFAULT_PROVIDER, self.folder.name, offline)
        _tile(14, 1, 2, DEFAULT_PROVIDER, self.folder.name, lambda *a, **k: Response())
        self.expire()
        image, stale = _tile(14, 1, 2, DEFAULT_PROVIDER, self.folder.name, offline)
        self.assertTrue(stale)
        self.assertEqual(image.size, (256, 256))

    def test_street_overlay_keeps_six_pairs_and_attribution(self):
        before = all_distances(self.data)
        basemap = load_street_map(self.data, self.folder.name, opener=lambda *a, **k: Response())
        ax, bars = draw_distance_figure(Figure(figsize=(13, 6)), self.data, basemap, ('RIO02', 'RIO04'))
        self.assertEqual(len(ax.images), 1)
        self.assertEqual(len(ax.lines), 6)
        self.assertEqual(len(ax.collections), 4)
        self.assertEqual(len(bars.patches), 6)
        self.assertTrue(any('OpenStreetMap contributors' in t.get_text() for t in ax.texts))
        self.assertEqual(all_distances(self.data), before)
        # Every plotted marker is projected from the exact source coordinates.
        for p, marker in zip(self.data['locations'], ax.collections):
            x, y = marker.get_offsets()[0]
            self.assertAlmostEqual(x, mercator(p['longitude'], p['latitude'])[0], places=7)
            self.assertAlmostEqual(y, mercator(p['longitude'], p['latitude'])[1], places=7)

    def test_osm_link_uses_origin_coordinates(self):
        point = self.data['locations'][1]
        url = openstreetmap_url(self.data, point)
        self.assertIn(f"mlat={point['latitude']:.7f}", url)
        self.assertIn(f"mlon={point['longitude']:.7f}", url)


class GalleryChecks(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.source = self.root / 'user-map.png'
        Image.new('RGB', (1000, 500), '#eef5fa').save(self.source)
        self.gallery = self.root / 'gallery'

    def test_empty_gallery_has_no_fake_screenshots(self):
        self.assertEqual(list_screenshots(self.gallery), [])

    def test_import_preserves_original_and_deduplicates(self):
        content = self.source.read_bytes()
        first = add_screenshot(self.source, self.gallery)
        second = add_screenshot(self.source, self.gallery)
        self.assertEqual(first, second)
        self.assertEqual(first.read_bytes(), content)
        self.assertEqual(self.source.read_bytes(), content)
        self.assertEqual(len(list_screenshots(self.gallery)), 1)

    def test_same_name_does_not_overwrite(self):
        first = add_screenshot(self.source, self.gallery)
        original = first.read_bytes()
        Image.new('RGB', (400, 400), 'red').save(self.source)
        second = add_screenshot(self.source, self.gallery)
        self.assertNotEqual(first, second)
        self.assertEqual(first.read_bytes(), original)
        self.assertEqual(len(list_screenshots(self.gallery)), 2)

    def test_thumbnail_keeps_proportions(self):
        image = screenshot_thumbnail(self.source, (300, 300))
        self.assertEqual(image.size, (300, 150))

    def test_invalid_image_rejected(self):
        invalid = self.root / 'invalid.png'
        invalid.write_text('not an image')
        with self.assertRaises(OSError): add_screenshot(invalid, self.gallery)
        self.assertEqual(list_screenshots(self.gallery), [])
