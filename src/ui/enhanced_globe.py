"""
Enhanced Globe Renderer — holographic Earth with live data overlays.

Features:
- NASA Blue Marble texture-mapped sphere (proper continents)
- Real-time earthquakes from USGS (free, no API key)
- Animated cloud cover from Open-Meteo (free, no API key)
- Temperature heatmap from Open-Meteo
- Lightning indicators from thunderstorm weather codes
- Holographic visual effects (scan lines, edge glow, blue tint)
"""

import numpy as np
import cv2
import time
import threading
import json
import urllib.request
import urllib.parse
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

logger = logging.getLogger("Monica.EnhancedGlobe")


@dataclass
class GeoEvent:
    """A geo-located event (earthquake, etc.)."""
    lat: float
    lng: float
    name: str = ""
    magnitude: float = 0.0
    timestamp: float = 0.0


class EnhancedGlobeRenderer:
    """Texture-mapped Earth globe with live data overlays and holographic FX."""

    TEXTURE_PATHS = [
        Path(__file__).parent / "earth_texture_cache.jpg",
        Path(__file__).parent.parent.parent / "assets" / "earth_texture_cache.jpg",
    ]
    TEXTURE_URL = (
        "https://eoimages.gsfc.nasa.gov/images/imagerecords/57000/57752/"
        "land_shallow_topo_2048.jpg"
    )

    # 30 representative points for global weather sampling
    WEATHER_GRID = [
        (64, -20), (60, 25), (55, -3), (52, 13), (48, 2), (40, -4),
        (41, 29), (56, 37), (35, 139), (37, 127), (39, 116), (22, 114),
        (13, 100), (1, 104), (-6, 107), (19, 73), (30, 31), (-1, 37),
        (-34, 18), (-23, -43), (-34, -58), (19, -99), (25, -80),
        (34, -118), (41, -74), (47, -122), (51, -114), (-34, 151),
        (-37, 175), (21, -158),
    ]

    def __init__(self, size: int = 180):
        self.size = size

        # Textures
        self._texture: Optional[np.ndarray] = None
        self._holo_texture: Optional[np.ndarray] = None

        # Sphere projection (pre-computed)
        self._sphere_mask: Optional[np.ndarray] = None
        self._nx: Optional[np.ndarray] = None
        self._ny: Optional[np.ndarray] = None
        self._nz: Optional[np.ndarray] = None
        self._edge_factor: Optional[np.ndarray] = None
        self._radius = 0
        self._cx = 0
        self._cy = 0

        # Data layers
        self._earthquakes: List[GeoEvent] = []
        self._clouds: List[Dict] = []
        self._temperatures: List[Dict] = []
        self._lightning: List[Dict] = []

        # Fetch timing
        self._last_eq_fetch = 0.0
        self._last_wx_fetch = 0.0

        # Animation
        self._cloud_drift = 0.0
        self._frame_count = 0

        self._load_texture()
        self._precompute_sphere()
        self._start_data_fetch()

    # ------------------------------------------------------------------ #
    #  Texture loading                                                     #
    # ------------------------------------------------------------------ #

    def _load_texture(self):
        for path in self.TEXTURE_PATHS:
            if path.exists():
                self._texture = cv2.imread(str(path))
                if self._texture is not None:
                    logger.info(f"Earth texture loaded: {path} {self._texture.shape}")
                    break

        if self._texture is None:
            try:
                logger.info("Downloading NASA Blue Marble texture...")
                save_path = self.TEXTURE_PATHS[0]
                save_path.parent.mkdir(parents=True, exist_ok=True)
                req = urllib.request.Request(
                    self.TEXTURE_URL, headers={"User-Agent": "Monica-AI/1.0"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    with open(save_path, "wb") as f:
                        f.write(resp.read())
                self._texture = cv2.imread(str(save_path))
                logger.info(f"Texture downloaded: {self._texture.shape}")
            except Exception as e:
                logger.error(f"Earth texture download failed: {e}")
                self._texture = np.full((512, 1024, 3), (120, 80, 40), dtype=np.uint8)

        self._build_holo_texture()

    def _build_holo_texture(self):
        """Blue/cyan-tinted version for holographic look."""
        tex = self._texture.astype(np.float32)
        gray = 0.114 * tex[:, :, 0] + 0.587 * tex[:, :, 1] + 0.299 * tex[:, :, 2]

        holo = np.zeros_like(self._texture)
        holo[:, :, 0] = np.clip(gray * 0.85 + 30, 0, 255)  # Blue
        holo[:, :, 1] = np.clip(gray * 0.95 + 20, 0, 255)  # Green
        holo[:, :, 2] = np.clip(gray * 0.30, 0, 255)        # Red (low)
        self._holo_texture = holo.astype(np.uint8)

    # ------------------------------------------------------------------ #
    #  Pre-computed sphere projection                                      #
    # ------------------------------------------------------------------ #

    def _precompute_sphere(self):
        s = self.size
        cx = cy = s // 2
        r = s // 2 - 2

        yg, xg = np.mgrid[0:s, 0:s]
        nx = (xg.astype(np.float32) - cx) / r
        ny = (cy - yg.astype(np.float32)) / r
        d2 = nx ** 2 + ny ** 2
        mask = d2 <= 1.0

        nz = np.zeros_like(nx)
        nz[mask] = np.sqrt(np.maximum(0, 1.0 - d2[mask]))

        edge = np.zeros_like(nx)
        edge[mask] = 1.0 - nz[mask]

        self._sphere_mask = mask
        self._nx, self._ny, self._nz = nx, ny, nz
        self._edge_factor = edge
        self._radius, self._cx, self._cy = r, cx, cy

    # ------------------------------------------------------------------ #
    #  Main render                                                         #
    # ------------------------------------------------------------------ #

    def render(
        self,
        rotation_deg: float,
        tilt_deg: float = 0.0,
        highlight_lat: Optional[float] = None,
        highlight_lng: Optional[float] = None,
        highlight_name: str = "",
        user_lat: Optional[float] = None,
        user_lng: Optional[float] = None,
        user_name: str = "You",
        show_earthquakes: bool = True,
        show_clouds: bool = True,
        show_temperature: bool = False,
        show_lightning: bool = True,
        holographic: bool = True,
    ) -> np.ndarray:
        """Render one frame of the globe (BGR, size x size)."""
        self._frame_count += 1

        # 1. Textured sphere
        globe = self._render_sphere(rotation_deg, tilt_deg, holographic)
        rot_r = np.radians(rotation_deg)

        # 2. Data overlays
        if show_earthquakes:
            self._draw_earthquakes(globe, rot_r, tilt_deg)
        if show_lightning:
            self._draw_lightning(globe, rot_r, tilt_deg)
        if show_clouds:
            self._draw_clouds(globe, rot_r, tilt_deg)
        if show_temperature:
            self._draw_temperatures(globe, rot_r, tilt_deg)

        # 3. User location
        if user_lat is not None and user_lng is not None:
            self._draw_dot(
                globe, rot_r, tilt_deg, user_lat, user_lng,
                (0, 255, 255), True, user_name, 5,
            )

        # 4. Highlighted location
        if highlight_lat is not None and highlight_lng is not None:
            self._draw_dot(
                globe, rot_r, tilt_deg, highlight_lat, highlight_lng,
                (0, 140, 255), True, highlight_name, 6,
            )

        # 5. Holographic post-FX
        if holographic:
            self._apply_holo_fx(globe)

        # 6. Outer glow rings
        cv2.circle(globe, (self._cx, self._cy), self._radius + 2,
                   (100, 70, 20), 1, cv2.LINE_AA)
        cv2.circle(globe, (self._cx, self._cy), self._radius + 5,
                   (50, 35, 10), 1, cv2.LINE_AA)

        return globe

    # ------------------------------------------------------------------ #
    #  Sphere texture mapping                                              #
    # ------------------------------------------------------------------ #

    def _render_sphere(self, rot_deg, tilt_deg, holographic):
        out = np.zeros((self.size, self.size, 3), dtype=np.uint8)
        tex = self._holo_texture if holographic else self._texture
        if tex is None:
            return out

        th, tw = tex.shape[:2]
        m = self._sphere_mask
        ry = np.radians(rot_deg)
        rx = np.radians(tilt_deg)
        cy_, sy_ = np.cos(ry), np.sin(ry)
        cx_, sx_ = np.cos(rx), np.sin(rx)

        # Y rotation
        px = self._nx * cy_ + self._nz * sy_
        py = self._ny
        pz = -self._nx * sy_ + self._nz * cy_

        # X rotation (tilt)
        py2 = py * cx_ - pz * sx_
        pz2 = py * sx_ + pz * cx_

        lat = np.arcsin(np.clip(py2, -1, 1))
        lng = np.arctan2(px, pz2)

        u = ((lng / np.pi + 1.0) * 0.5 * tw).astype(np.int32) % tw
        v = np.clip(((0.5 - lat / np.pi) * th).astype(np.int32), 0, th - 1)

        out[m] = tex[v[m], u[m]]
        return out

    # ------------------------------------------------------------------ #
    #  Coordinate helpers                                                  #
    # ------------------------------------------------------------------ #

    def _to_screen(self, rot_r, tilt_deg, lat, lng):
        """lat/lng → screen (x, y) or None if on back side."""
        la = np.radians(lat)
        lo = np.radians(lng)
        x = np.cos(la) * np.sin(lo)
        y = np.sin(la)
        z = np.cos(la) * np.cos(lo)

        cy_, sy_ = np.cos(-rot_r), np.sin(-rot_r)
        rx = x * cy_ + z * sy_
        rz = -x * sy_ + z * cy_

        tr = np.radians(tilt_deg)
        cx_, sx_ = np.cos(-tr), np.sin(-tr)
        ry = y * cx_ - rz * sx_
        rz2 = y * sx_ + rz * cx_

        if rz2 <= 0:
            return None
        return int(self._cx + rx * self._radius), int(self._cy - ry * self._radius)

    # ------------------------------------------------------------------ #
    #  Drawing helpers                                                     #
    # ------------------------------------------------------------------ #

    def _draw_dot(self, img, rot_r, tilt, lat, lng, color, pulse, label, sz):
        pos = self._to_screen(rot_r, tilt, lat, lng)
        if pos is None:
            return
        x, y = pos
        if pulse:
            pv = 0.5 + 0.5 * np.sin(time.time() * 4)
            sz = int(sz + 2 * pv)
        glow = tuple(max(0, c // 3) for c in color)
        cv2.circle(img, (x, y), sz + 3, glow, -1, cv2.LINE_AA)
        cv2.circle(img, (x, y), sz, color, -1, cv2.LINE_AA)
        cv2.circle(img, (x, y), max(2, sz - 2), (255, 255, 255), -1, cv2.LINE_AA)
        if label:
            cv2.putText(img, label, (x + sz + 3, y + 3),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.25, color, 1, cv2.LINE_AA)

    def _draw_earthquakes(self, img, rot_r, tilt):
        for eq in self._earthquakes:
            pos = self._to_screen(rot_r, tilt, eq.lat, eq.lng)
            if pos is None:
                continue
            x, y = pos
            mag = eq.magnitude
            sz = max(2, int(mag))
            if mag < 3:
                clr = (0, 200, 255)     # yellow
            elif mag < 5:
                clr = (0, 140, 255)     # orange
            else:
                clr = (0, 50, 255)      # red

            age = time.time() - eq.timestamp
            if age < 3600:
                pv = 0.5 + 0.5 * np.sin(time.time() * 3)
                sz = int(sz + 2 * pv)

            cv2.circle(img, (x, y), sz + 1, (0, 0, 100), -1, cv2.LINE_AA)
            cv2.circle(img, (x, y), sz, clr, -1, cv2.LINE_AA)

    def _draw_clouds(self, img, rot_r, tilt):
        self._cloud_drift += 0.003
        for c in self._clouds:
            cover = c.get("cover", 0)
            if cover < 25:
                continue
            lat, lng = c["lat"], c["lng"] + self._cloud_drift
            pos = self._to_screen(rot_r, tilt, lat, lng)
            if pos is None:
                continue
            x, y = pos
            sz = max(3, int(cover / 12))
            alpha = min(0.45, cover / 200.0)
            overlay = img.copy()
            white = (200, 210, 220)
            cv2.circle(overlay, (x, y), sz, white, -1, cv2.LINE_AA)
            if sz > 4:
                cv2.circle(overlay, (x + sz // 2, y - sz // 3), sz - 2,
                           white, -1, cv2.LINE_AA)
            cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)

    def _draw_lightning(self, img, rot_r, tilt):
        fc = self._frame_count
        for bolt in self._lightning:
            lat, lng = bolt["lat"], bolt["lng"]
            pos = self._to_screen(rot_r, tilt, lat, lng)
            if pos is None:
                continue
            x, y = pos
            phase = (hash((int(lat * 10), int(lng * 10))) + fc) % 25
            if phase < 4:
                bright = int(180 + 75 * np.sin(time.time() * 25))
                cv2.circle(img, (x, y), 5, (bright, bright, 0), -1, cv2.LINE_AA)
                cv2.circle(img, (x, y), 2, (255, 255, 220), -1, cv2.LINE_AA)

    def _draw_temperatures(self, img, rot_r, tilt):
        for d in self._temperatures:
            pos = self._to_screen(rot_r, tilt, d["lat"], d["lng"])
            if pos is None:
                continue
            x, y = pos
            tc = d["temp_c"]
            if tc < 0:
                clr = (255, 120, 50)
            elif tc < 15:
                clr = (200, 200, 60)
            elif tc < 25:
                clr = (60, 200, 60)
            elif tc < 35:
                clr = (0, 160, 255)
            else:
                clr = (0, 0, 255)
            cv2.circle(img, (x, y), 3, clr, -1, cv2.LINE_AA)
            cv2.putText(img, f"{tc:.0f}", (x + 4, y + 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.2, clr, 1, cv2.LINE_AA)

    # ------------------------------------------------------------------ #
    #  Holographic post-FX                                                 #
    # ------------------------------------------------------------------ #

    def _apply_holo_fx(self, img):
        m = self._sphere_mask
        # Scan lines
        for y in range(0, self.size, 3):
            row = img[y].astype(np.float32)
            img[y] = (row * 0.82).astype(np.uint8)

        # Edge glow (blue rim)
        ef = self._edge_factor
        bright = ef > 0.65
        combo = m & bright
        if np.any(combo):
            g = np.clip((ef[combo] - 0.65) * 2.85, 0, 1)
            img[combo, 0] = np.clip(
                img[combo, 0].astype(np.float32) + g * 70, 0, 255
            ).astype(np.uint8)
            img[combo, 1] = np.clip(
                img[combo, 1].astype(np.float32) + g * 50, 0, 255
            ).astype(np.uint8)

    # ------------------------------------------------------------------ #
    #  Background data fetching                                            #
    # ------------------------------------------------------------------ #

    def _start_data_fetch(self):
        def _loop():
            while True:
                try:
                    self._fetch_earthquakes()
                except Exception as e:
                    logger.debug(f"EQ fetch error: {e}")
                try:
                    self._fetch_weather()
                except Exception as e:
                    logger.debug(f"Weather fetch error: {e}")
                time.sleep(300)

        threading.Thread(target=_loop, daemon=True).start()

    def _fetch_earthquakes(self):
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
        req = urllib.request.Request(url, headers={"User-Agent": "Monica-AI/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        evts = []
        for f in data.get("features", []):
            p = f.get("properties", {})
            c = f.get("geometry", {}).get("coordinates", [0, 0])
            evts.append(GeoEvent(
                lat=c[1], lng=c[0],
                name=p.get("place", ""),
                magnitude=p.get("mag", 0) or 0,
                timestamp=(p.get("time", 0) or 0) / 1000.0,
            ))
        self._earthquakes = evts
        logger.info(f"USGS: {len(evts)} earthquakes (M2.5+ today)")

    def _fetch_weather(self):
        clouds, temps, bolts = [], [], []
        for lat, lng in self.WEATHER_GRID:
            try:
                url = (
                    f"https://api.open-meteo.com/v1/forecast?"
                    f"latitude={lat}&longitude={lng}"
                    f"&current_weather=true"
                    f"&hourly=cloudcover&forecast_days=1&timezone=auto"
                )
                req = urllib.request.Request(url, headers={"User-Agent": "Monica-AI/1.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    d = json.loads(resp.read().decode())
                cw = d.get("current_weather", {})
                tc = cw.get("temperature", 0)
                wc = cw.get("weathercode", 0)
                cc_list = d.get("hourly", {}).get("cloudcover", [])
                cc = cc_list[0] if cc_list else 0

                clouds.append({"lat": lat, "lng": lng, "cover": cc})
                temps.append({"lat": lat, "lng": lng, "temp_c": tc})
                if wc in (95, 96, 99):
                    bolts.append({"lat": lat, "lng": lng, "intensity": wc - 90})
                time.sleep(0.15)
            except Exception:
                pass
        self._clouds = clouds
        self._temperatures = temps
        self._lightning = bolts
        logger.info(
            f"Weather grid: {len(clouds)} cloud, {len(temps)} temp, {len(bolts)} lightning"
        )

    def resize(self, new_size: int):
        if new_size != self.size:
            self.size = new_size
            self._precompute_sphere()


# Singleton
_instance: Optional[EnhancedGlobeRenderer] = None


def get_enhanced_globe(size: int = 180) -> EnhancedGlobeRenderer:
    global _instance
    if _instance is None:
        _instance = EnhancedGlobeRenderer(size)
    return _instance
