/**
 * globe_math.cpp — Fast 3D globe projection and texture sampling
 * Replaces Python/NumPy globe rendering with vectorized C++ for 10-50x speedup.
 */
#include "vision_accel.h"
#include <cmath>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

static inline float deg2rad(float d) { return d * static_cast<float>(M_PI) / 180.0f; }

// ── Project lat/lng onto 3D sphere screen coordinates ──
std::tuple<int, int, bool> globe_project(
    float lat_deg, float lng_deg, const GlobeParams& params)
{
    float lat = deg2rad(lat_deg);
    float lng = deg2rad(lng_deg - params.rotation_deg);
    float tilt = deg2rad(params.tilt_deg);

    // 3D sphere coordinates
    float x = std::cos(lat) * std::sin(lng);
    float y = std::sin(lat) * std::cos(tilt) - std::cos(lat) * std::cos(lng) * std::sin(tilt);
    float z = std::sin(lat) * std::sin(tilt) + std::cos(lat) * std::cos(lng) * std::cos(tilt);

    // z > 0 means point is on the visible hemisphere
    bool visible = z > 0.0f;

    int sx = params.cx + static_cast<int>(x * params.radius);
    int sy = params.cy - static_cast<int>(y * params.radius);

    return {sx, sy, visible};
}

// ── Render textured globe into destination buffer ──
void render_globe_texture(
    const uint8_t* texture, int tex_h, int tex_w,
    uint8_t* dst, int dst_h, int dst_w,
    const GlobeParams& params)
{
    float r = static_cast<float>(params.radius);
    float r2 = r * r;
    float rot_rad = deg2rad(params.rotation_deg);
    float tilt_rad = deg2rad(params.tilt_deg);
    float cos_tilt = std::cos(tilt_rad);
    float sin_tilt = std::sin(tilt_rad);

    // Bounding box of the globe on screen
    int y_min = std::max(0, params.cy - params.radius);
    int y_max = std::min(dst_h - 1, params.cy + params.radius);
    int x_min = std::max(0, params.cx - params.radius);
    int x_max = std::min(dst_w - 1, params.cx + params.radius);

    for (int sy = y_min; sy <= y_max; ++sy) {
        float dy = static_cast<float>(params.cy - sy);  // note: y is flipped
        for (int sx = x_min; sx <= x_max; ++sx) {
            float dx = static_cast<float>(sx - params.cx);

            float dist2 = dx * dx + dy * dy;
            if (dist2 > r2) continue;

            // Inverse-project screen pixel to sphere surface
            float z = std::sqrt(r2 - dist2);

            // Undo tilt rotation (rotate around X axis)
            float y_untilt = dy * cos_tilt + z * sin_tilt;
            float z_untilt = -dy * sin_tilt + z * cos_tilt;

            // Convert to lat/lng
            float lat = std::asin(std::clamp(y_untilt / r, -1.0f, 1.0f));
            float lng = std::atan2(dx, z_untilt) + rot_rad;

            // Normalize longitude to [0, 2*PI)
            while (lng < 0) lng += 2.0f * static_cast<float>(M_PI);
            while (lng >= 2.0f * static_cast<float>(M_PI)) lng -= 2.0f * static_cast<float>(M_PI);

            // Map to texture coordinates
            float u = lng / (2.0f * static_cast<float>(M_PI));       // [0, 1)
            float v = 0.5f - lat / static_cast<float>(M_PI);         // [0, 1)

            int tx = static_cast<int>(u * (tex_w - 1));
            int ty = static_cast<int>(v * (tex_h - 1));
            tx = std::clamp(tx, 0, tex_w - 1);
            ty = std::clamp(ty, 0, tex_h - 1);

            // Sample texture
            const uint8_t* tex_px = texture + (ty * tex_w + tx) * 3;

            // Apply simple lighting (z component = how much face is towards viewer)
            float light = z / r;  // 0 at edge, 1 at center
            light = 0.3f + 0.7f * light;  // ambient + diffuse

            uint8_t* dst_px = dst + (sy * dst_w + sx) * 3;
            dst_px[0] = static_cast<uint8_t>(std::min(255.0f, tex_px[0] * light));
            dst_px[1] = static_cast<uint8_t>(std::min(255.0f, tex_px[1] * light));
            dst_px[2] = static_cast<uint8_t>(std::min(255.0f, tex_px[2] * light));
        }
    }
}

// ── Draw pulsating dot on globe ──
void draw_globe_dot(
    uint8_t* frame, int h, int w,
    float lat_deg, float lng_deg,
    const GlobeParams& params,
    Color3 color, int base_radius, float pulse_phase)
{
    auto [sx, sy, visible] = globe_project(lat_deg, lng_deg, params);
    if (!visible) return;

    // Pulsating radius
    float pulse = 1.0f + 0.4f * std::sin(pulse_phase);
    int radius = static_cast<int>(base_radius * pulse);

    // Outer glow
    Color3 glow = {
        static_cast<uint8_t>(color.b / 3),
        static_cast<uint8_t>(color.g / 3),
        static_cast<uint8_t>(color.r / 3)
    };
    draw_circle(frame, h, w, sx, sy, radius + 2, glow, glow, 0);

    // Inner dot
    draw_circle(frame, h, w, sx, sy, radius, color, color, 0);

    // Bright center
    Color3 white = {255, 255, 255};
    if (radius > 2) {
        draw_circle(frame, h, w, sx, sy, 1, white, white, 0);
    }
}
