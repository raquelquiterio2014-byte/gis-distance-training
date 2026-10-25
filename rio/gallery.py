"""User-provided QGIS screenshot gallery; never substitutes generated artwork."""
import hashlib
from pathlib import Path
from PIL import Image, ImageOps
from core import ROOT

GALLERY_DIR = ROOT / 'assets' / 'qgis_screenshots'
EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}


def list_screenshots(directory=GALLERY_DIR):
    folder = Path(directory)
    return sorted((p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS),
                  key=lambda p: p.name.lower()) if folder.exists() else []


def add_screenshot(source, directory=GALLERY_DIR):
    source = Path(source)
    if source.suffix.lower() not in EXTENSIONS:
        raise ValueError('Choose a PNG, JPEG or WebP screenshot')
    with Image.open(source) as image:
        image.verify()
    content = source.read_bytes()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / source.name
    if destination.exists():
        if destination.read_bytes() == content:
            return destination
        destination = directory / f'{source.stem}_{hashlib.sha256(content).hexdigest()[:10]}{source.suffix.lower()}'
    destination.write_bytes(content)
    return destination


def screenshot_thumbnail(path, size):
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert('RGB')
        image.thumbnail(size, Image.Resampling.LANCZOS)
        return image.copy()
