"""
native_accel.py — Python wrapper for C++ vision accelerator.

Tries to import the compiled C++ module `monica_vision_accel`.
If not available, provides pure-Python/NumPy fallbacks so the rest
of the codebase works identically (just slower).

Usage:
    from vision.native_accel import accel
    accel.composite_overlay(base, overlay, x, y)
    accel.draw_hand_skeleton(frame, landmarks, ...)
    accel.render_globe(texture, dst, cx, cy, radius, rotation, tilt)
"""
import numpy as np
import math
import logging

logger = logging.getLogger("Monica.NativeAccel")

# ── Try to load the compiled C++ extension ──
_USE_CPP = False
try:
    import monica_vision_accel as _cpp
    _USE_CPP = True
    logger.info("[NativeAccel] C++ vision accelerator loaded (10-50x faster)")
except ImportError:
    _cpp = None
    logger.info("[NativeAccel] C++ module not compiled — using Python fallbacks")


# ══════════════════════════════════════════════════════════════
#  Pure-Python fallbacks (used when C++ module is not compiled)
# ══════════════════════════════════════════════════════════════

# Hand connections (MediaPipe 21-landmark topology)
_HAND_CONNS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (13,17),(17,18),(18,19),(19,20),
    (0,17),
]
_FINGERTIP_IDS = {4, 8, 12, 16, 20}


def _py_composite_overlay(base, overlay, offset_x, offset_y):
    """Alpha-blend BGRA overlay onto BGR base (NumPy fallback)."""
    bh, bw = base.shape[:2]
    oh, ow = overlay.shape[:2]

    y1 = max(0, offset_y)
    y2 = min(bh, offset_y + oh)
    x1 = max(0, offset_x)
    x2 = min(bw, offset_x + ow)

    oy1 = y1 - offset_y
    oy2 = y2 - offset_y
    ox1 = x1 - offset_x
    ox2 = x2 - offset_x

    if y2 <= y1 or x2 <= x1:
        return

    ov_region = overlay[oy1:oy2, ox1:ox2]
    alpha = ov_region[:, :, 3:4].astype(np.float32) / 255.0
    base[y1:y2, x1:x2] = (
        ov_region[:, :, :3].astype(np.float32) * alpha +
        base[y1:y2, x1:x2].astype(np.float32) * (1.0 - alpha)
    ).astype(np.uint8)


def _py_fast_resize(src, dst_h, dst_w):
    """Bilinear resize (NumPy fallback — use cv2.resize if available)."""
    try:
        import cv2
        return cv2.resize(src, (dst_w, dst_h), interpolation=cv2.INTER_LINEAR)
    except ImportError:
        # Pure NumPy nearest-neighbor fallback
        sh, sw = src.shape[:2]
        y_idx = (np.arange(dst_h) * sh / dst_h).astype(int)
        x_idx = (np.arange(dst_w) * sw / dst_w).astype(int)
        return src[np.ix_(y_idx, x_idx)]


def _py_swap_channels(frame):
    """BGR<->RGB swap in-place."""
    frame[:, :, [0, 2]] = frame[:, :, [2, 0]]


def _py_draw_hand_skeleton(frame, landmarks,
                            bone_color=(0, 255, 0),
                            joint_color=(0, 200, 255),
                            tip_color=(0, 255, 255),
                            bone_thickness=2,
                            joint_radius=4,
                            tip_radius=6):
    """Draw hand skeleton using cv2 (Python fallback)."""
    try:
        import cv2
    except ImportError:
        return  # Can't draw without cv2

    n = landmarks.shape[0]
    if n < 21:
        return

    pts = landmarks.astype(int)

    # Draw bones
    for a, b in _HAND_CONNS:
        if a < n and b < n:
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]),
                     bone_color, bone_thickness, cv2.LINE_AA)

    # Draw joints and tips
    for i in range(n):
        if i in _FINGERTIP_IDS:
            cv2.circle(frame, tuple(pts[i]), tip_radius, tip_color, -1, cv2.LINE_AA)
            cv2.circle(frame, tuple(pts[i]), tip_radius + 1, bone_color, 1, cv2.LINE_AA)
        else:
            cv2.circle(frame, tuple(pts[i]), joint_radius, joint_color, -1, cv2.LINE_AA)
            cv2.circle(frame, tuple(pts[i]), joint_radius + 1, bone_color, 1, cv2.LINE_AA)


def _py_globe_project(lat, lng, cx, cy, radius, rotation=0.0, tilt=23.5):
    """Project lat/lng to screen coords on 3D sphere (Python fallback)."""
    lat_r = math.radians(lat)
    lng_r = math.radians(lng - rotation)
    tilt_r = math.radians(tilt)

    x = math.cos(lat_r) * math.sin(lng_r)
    y = math.sin(lat_r) * math.cos(tilt_r) - math.cos(lat_r) * math.cos(lng_r) * math.sin(tilt_r)
    z = math.sin(lat_r) * math.sin(tilt_r) + math.cos(lat_r) * math.cos(lng_r) * math.cos(tilt_r)

    visible = z > 0
    sx = cx + int(x * radius)
    sy = cy - int(y * radius)
    return (sx, sy, visible)


def _py_render_globe(texture, dst, cx, cy, radius, rotation=0.0, tilt=23.5):
    """Render textured globe (NumPy fallback)."""
    tex_h, tex_w = texture.shape[:2]
    dst_h, dst_w = dst.shape[:2]
    r = float(radius)
    rot_rad = math.radians(rotation)
    tilt_rad = math.radians(tilt)
    cos_t = math.cos(tilt_rad)
    sin_t = math.sin(tilt_rad)

    y_min = max(0, cy - radius)
    y_max = min(dst_h - 1, cy + radius)
    x_min = max(0, cx - radius)
    x_max = min(dst_w - 1, cx + radius)

    # Vectorized with NumPy for reasonable speed
    ys = np.arange(y_min, y_max + 1)
    xs = np.arange(x_min, x_max + 1)
    yy, xx = np.meshgrid(ys, xs, indexing='ij')

    dy = (cy - yy).astype(np.float32)
    dx = (xx - cx).astype(np.float32)
    dist2 = dx * dx + dy * dy
    r2 = r * r
    mask = dist2 <= r2

    z = np.sqrt(np.maximum(r2 - dist2, 0))
    y_untilt = dy * cos_t + z * sin_t
    z_untilt = -dy * sin_t + z * cos_t

    lat = np.arcsin(np.clip(y_untilt / r, -1, 1))
    lng = np.arctan2(dx, z_untilt) + rot_rad
    lng = lng % (2 * np.pi)

    u = lng / (2 * np.pi)
    v = 0.5 - lat / np.pi

    tx = np.clip((u * (tex_w - 1)).astype(int), 0, tex_w - 1)
    ty = np.clip((v * (tex_h - 1)).astype(int), 0, tex_h - 1)

    light = z / r
    light = 0.3 + 0.7 * light

    sampled = texture[ty, tx]
    lit = np.clip(sampled * light[:, :, np.newaxis], 0, 255).astype(np.uint8)

    dst[y_min:y_max+1, x_min:x_max+1][mask] = lit[mask]


def _py_draw_globe_dot(frame, lat, lng, cx, cy, radius,
                        rotation=0.0, tilt=23.5,
                        color=(0, 200, 255), dot_radius=3, pulse_phase=0.0):
    """Draw pulsating dot on globe (Python fallback)."""
    try:
        import cv2
    except ImportError:
        return

    sx, sy, visible = _py_globe_project(lat, lng, cx, cy, radius, rotation, tilt)
    if not visible:
        return

    pulse = 1.0 + 0.4 * math.sin(pulse_phase)
    r = int(dot_radius * pulse)

    glow = tuple(c // 3 for c in color)
    cv2.circle(frame, (sx, sy), r + 2, glow, -1, cv2.LINE_AA)
    cv2.circle(frame, (sx, sy), r, color, -1, cv2.LINE_AA)
    if r > 2:
        cv2.circle(frame, (sx, sy), 1, (255, 255, 255), -1, cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════
#  Unified API — dispatches to C++ or Python fallback
# ══════════════════════════════════════════════════════════════

class _VisionAccelerator:
    """Unified vision accelerator API with automatic C++/Python dispatch."""

    @property
    def is_native(self) -> bool:
        """True if using compiled C++ module."""
        return _USE_CPP

    # ── Frame ops ──

    def composite_overlay(self, base, overlay, offset_x, offset_y):
        if _USE_CPP:
            _cpp.composite_overlay(base, overlay, offset_x, offset_y)
        else:
            _py_composite_overlay(base, overlay, offset_x, offset_y)

    def fast_resize(self, src, dst_h, dst_w):
        if _USE_CPP:
            return _cpp.fast_resize(src, dst_h, dst_w)
        return _py_fast_resize(src, dst_h, dst_w)

    def swap_channels(self, frame):
        if _USE_CPP:
            _cpp.swap_channels(frame)
        else:
            _py_swap_channels(frame)

    # ── Skeleton ──

    def draw_hand_skeleton(self, frame, landmarks,
                           bone_color=(0, 255, 0),
                           joint_color=(0, 200, 255),
                           tip_color=(0, 255, 255),
                           bone_thickness=2, joint_radius=4, tip_radius=6):
        if _USE_CPP:
            _cpp.draw_hand_skeleton(frame, landmarks,
                                    bone_color, joint_color, tip_color,
                                    bone_thickness, joint_radius, tip_radius)
        else:
            _py_draw_hand_skeleton(frame, landmarks,
                                   bone_color, joint_color, tip_color,
                                   bone_thickness, joint_radius, tip_radius)

    # ── Globe ──

    def globe_project(self, lat, lng, cx, cy, radius, rotation=0.0, tilt=23.5):
        if _USE_CPP:
            return _cpp.globe_project(lat, lng, cx, cy, radius, rotation, tilt)
        return _py_globe_project(lat, lng, cx, cy, radius, rotation, tilt)

    def render_globe(self, texture, dst, cx, cy, radius, rotation=0.0, tilt=23.5):
        if _USE_CPP:
            _cpp.render_globe(texture, dst, cx, cy, radius, rotation, tilt)
        else:
            _py_render_globe(texture, dst, cx, cy, radius, rotation, tilt)

    def draw_globe_dot(self, frame, lat, lng, cx, cy, radius,
                       rotation=0.0, tilt=23.5,
                       color=(0, 200, 255), dot_radius=3, pulse_phase=0.0):
        if _USE_CPP:
            _cpp.draw_globe_dot(frame, lat, lng, cx, cy, radius,
                                rotation, tilt, color, dot_radius, pulse_phase)
        else:
            _py_draw_globe_dot(frame, lat, lng, cx, cy, radius,
                               rotation, tilt, color, dot_radius, pulse_phase)


# Singleton
accel = _VisionAccelerator()
