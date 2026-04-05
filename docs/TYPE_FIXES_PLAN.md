# Type Error Fixes Plan

## Summary
**84 errors total** - All are type checking issues, NOT runtime errors. Code executes perfectly.

## Verified Working:
- ✅ MediaPipe 0.10.21: `mp.solutions.pose`, `mp.solutions.hands`, `mp.solutions.drawing_utils` all exist at runtime
- ✅ SpoutGL: `SpoutGL.SpoutSender` exists and works
- ✅ All algorithm logic is correct

## Error Categories & Solutions

### Category 1: MediaPipe Type Stubs (24 errors)
**Problem:** Pylance doesn't recognize dynamic imports  
**Runtime:** Works perfectly  
**Solution:** Add `# type: ignore[attr-defined]` comments  

Files affected:
- interactive_fog_obs.py (5 errors)
- interactive_fog_perlin.py (5 errors)
- interactive_fog_river.py (2 errors)
- interactive_fog_turbulence.py (1 error)
- linear_fog.py (2 errors)
- fog_css_style.py (1 error)
- procedural_fog_clouds.py (8 errors)

### Category 2: SpoutGL Type Stubs (14 errors)
**Problem:** SpoutGL missing type annotations  
**Runtime:** Works perfectly  
**Solution:** Add `# type: ignore[attr-defined]` comments

Files affected:
- interactive_fog_obs.py (1 error)
- interactive_fog_perlin.py (1 error)
- interactive_fog_river.py (1 error)
- interactive_fog_turbulence.py (1 error)
- linear_fog.py (1 error)
- fog_css_style.py (1 error)
- procedural_fog_clouds.py (8 errors - 3 senders × 2 errors each + 2 None checks)

### Category 3: OpenCV Scalar Type Mismatches (44 errors - REQUIRES CODE CHANGES)
**Problem:** OpenCV expects `Scalar = tuple[float, ...]` but code passes `int` or `float`  
**Runtime:** Works but violates type contracts  
**Solution:** Convert literals to tuples

**Proper OpenCV Scalar Math:**
```python
# Single-channel (grayscale/mask):
255 → (255,)     # White pixel
1.0 → (1.0,)     # Normalized mask value

# Multi-channel (BGR):
255 → (255, 255, 255)  # White in BGR
```

**Fixes Required:**

#### interactive_fog_river.py (2 errors)
- Line 95: `cv2.fillConvexPoly(body_mask, hull, 1.0)` → `cv2.fillConvexPoly(body_mask, hull, (1.0,))`

#### interactive_fog_turbulence.py (2 errors)
- Line 109: `cv2.circle(body_mask, (x, y), 100, 1.0, -1)` → `cv2.circle(body_mask, (x, y), 100, (1.0,), -1)`

#### linear_fog.py (2 errors)
- Line 94: `cv2.fillConvexPoly(body_mask, hull, 255)` → `cv2.fillConvexPoly(body_mask, hull, (255,))`

#### fog_css_style.py (2 errors)
- Line 176: `cv2.fillConvexPoly(temp_mask, hull, 255)` → `cv2.fillConvexPoly(temp_mask, hull, (255,))`

#### procedural_fog_clouds.py (20 errors - 10 fixes × 2 each)
- Line 808: `cv2.circle(body_mask, (tx, ty), 25, 255, -1)` → `cv2.circle(body_mask, (tx, ty), 25, (255,), -1)`
- Line 820: `cv2.circle(body_mask, (wx, wy), 40, 255, -1)` → `cv2.circle(body_mask, (wx, wy), 40, (255,), -1)`
- Line 821: `cv2.circle(body_mask, (px, py), 35, 255, -1)` → `cv2.circle(body_mask, (px, py), 35, (255,), -1)`
- Line 865: `cv2.fillConvexPoly(body_mask, hull, 255)` → `cv2.fillConvexPoly(body_mask, hull, (255,))`
- Line 879: `cv2.circle(body_mask, (mx, my), 50, 255, -1)` → `cv2.circle(body_mask, (mx, my), 50, (255,), -1)`

### Category 4: NumPy Type Inference (2 errors - REQUIRES CODE CHANGES)
**Problem:** `np.sum(mask)` returns `np.bool_` scalar, `np.random.randn()` expects `int`  
**Runtime:** Works but type checker complains  
**Solution:** Explicit cast to `int`

**Proper NumPy Math:**
```python
# np.sum(bool_array) counts True values
mask = np.array([True, False, True])  # 3 elements
np.sum(mask)  # Returns np.int64(2) or np.bool_ depending on context
int(np.sum(mask))  # Explicitly returns Python int(2)
```

**Fixes Required:**

#### procedural_fog_clouds.py (2 errors)
- Line 1043: `velocity_field[mask, 0] += np.random.randn(np.sum(mask)) * 1.5`  
  → `velocity_field[mask, 0] += np.random.randn(int(np.sum(mask))) * 1.5`
  
- Line 1044: `velocity_field[mask, 1] += np.random.randn(np.sum(mask)) * 1.5`  
  → `velocity_field[mask, 1] += np.random.randn(int(np.sum(mask))) * 1.5`

## Fix Priority

1. **HIGH (46 fixes):** OpenCV Scalar + NumPy casting - preserve math, satisfy type checker
2. **MEDIUM (38 fixes):** MediaPipe/SpoutGL - add type ignore comments

## Implementation Strategy

**Phase 1:** Fix OpenCV Scalar issues (straightforward tuple wrapping)
**Phase 2:** Fix NumPy type casting (simple int() wrapper)
**Phase 3:** Add type ignore comments for MediaPipe/SpoutGL (suppression only)

All fixes preserve original algorithm logic - no simplification, no deletion, proper math maintained.
