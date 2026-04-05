"""
Monica Free Maps - Tile Fetching System
Fetches satellite imagery tiles from free public tile servers.
Sources:
- ESRI World Imagery (free, high-res satellite imagery)
- OpenStreetMap (free map tiles)
- Stamen/Stadia terrain tiles
No API keys required.
"""
import math
import logging
import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger("Monica.FreeMaps")

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class FreeMapTileSystem:
    """
    Fetches map tiles from free public tile servers.
    Includes disk caching for offline use and faster loading.
    """

    # Free tile server URLs (no API key needed)
    TILE_SERVERS = {
        "esri_satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "esri_topo": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        "osm": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "stamen_terrain": "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png",
    }

    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "tile_cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Free Maps initialized (cache: {self.cache_dir})")

    def lat_lng_to_tile(self, lat: float, lng: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lng to tile x/y at given zoom level."""
        n = 2 ** zoom
        x = int((lng + 180.0) / 360.0 * n)
        lat_rad = math.radians(lat)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        x = max(0, min(n - 1, x))
        y = max(0, min(n - 1, y))
        return x, y

    def fetch_tile(self, lat: float, lng: float, zoom: int,
                   source: str = "esri_satellite") -> Optional['np.ndarray']:
        """
        Fetch a single map tile for the given lat/lng/zoom.
        Returns BGR numpy array (256x256x3) or None on failure.
        """
        if not HAS_CV2:
            return None

        tx, ty = self.lat_lng_to_tile(lat, lng, zoom)
        return self.fetch_tile_xy(tx, ty, zoom, source)

    def fetch_tile_xy(self, tx: int, ty: int, zoom: int,
                      source: str = "esri_satellite") -> Optional['np.ndarray']:
        """Fetch a tile by x/y/zoom coordinates."""
        if not HAS_CV2:
            return None

        # Check disk cache first
        cache_path = self.cache_dir / source / f"{zoom}" / f"{tx}_{ty}.jpg"
        if cache_path.exists():
            img = cv2.imread(str(cache_path))
            if img is not None:
                return img

        # Build URL
        url_template = self.TILE_SERVERS.get(source)
        if not url_template:
            logger.warning(f"Unknown tile source: {source}")
            return None

        url = url_template.format(z=zoom, x=tx, y=ty)

        try:
            import urllib.request
            req = urllib.request.Request(url, headers={
                "User-Agent": "Monica-AI/1.0 (Educational Project)",
                "Accept": "image/*",
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                img_bytes = resp.read()

            # Decode image
            img_array = np.frombuffer(img_bytes, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

            if img is not None:
                # Cache to disk
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(cache_path), img)
                return img

        except Exception as e:
            logger.debug(f"Tile fetch failed ({source} z={zoom} x={tx} y={ty}): {e}")

        return None

    def fetch_world_texture(self, width: int = 2048, height: int = 1024,
                            zoom: int = 3, source: str = "esri_satellite") -> Optional['np.ndarray']:
        """
        Fetch and stitch tiles into a full equirectangular world texture.
        
        Args:
            width: Output texture width
            height: Output texture height
            zoom: Tile zoom level (2=16 tiles, 3=64 tiles, 4=256 tiles)
            source: Tile server to use
            
        Returns:
            BGR numpy array (height x width x 3) or None
        """
        if not HAS_CV2:
            return None

        n = 2 ** zoom
        tile_size = 256
        full_w = n * tile_size
        full_h = n * tile_size

        # Create full-size stitched image
        full_img = np.zeros((full_h, full_w, 3), dtype=np.uint8)
        tiles_loaded = 0

        for ty in range(n):
            for tx in range(n):
                tile = self.fetch_tile_xy(tx, ty, zoom, source)
                if tile is not None:
                    # Resize tile if needed
                    if tile.shape[0] != tile_size or tile.shape[1] != tile_size:
                        tile = cv2.resize(tile, (tile_size, tile_size))
                    y_start = ty * tile_size
                    x_start = tx * tile_size
                    full_img[y_start:y_start + tile_size, x_start:x_start + tile_size] = tile
                    tiles_loaded += 1

        if tiles_loaded == 0:
            return None

        # Resize to requested dimensions
        texture = cv2.resize(full_img, (width, height), interpolation=cv2.INTER_AREA)
        logger.info(f"World texture: {tiles_loaded}/{n*n} tiles at zoom {zoom} -> {width}x{height}")
        return texture


# Singleton
_free_maps = None


def get_free_maps() -> FreeMapTileSystem:
    """Get singleton FreeMapTileSystem instance."""
    global _free_maps
    if _free_maps is None:
        _free_maps = FreeMapTileSystem()
    return _free_maps
