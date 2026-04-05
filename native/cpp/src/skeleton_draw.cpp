/**
 * skeleton_draw.cpp — Fast hand skeleton rendering with anti-aliased lines
 * Draws bones, joints, and fingertip highlights in a single C++ call,
 * avoiding per-pixel Python overhead from cv2.line / cv2.circle loops.
 */
#include "vision_accel.h"
#include <cmath>
#include <algorithm>

// Hand connections (matches MediaPipe 21-landmark topology)
static constexpr int HAND_CONNS[][2] = {
    {0,1},{1,2},{2,3},{3,4},         // Thumb
    {0,5},{5,6},{6,7},{7,8},         // Index
    {5,9},{9,10},{10,11},{11,12},    // Middle
    {9,13},{13,14},{14,15},{15,16},  // Ring
    {13,17},{17,18},{18,19},{19,20}, // Pinky
    {0,17},                          // Palm base
};
static constexpr int NUM_CONNS = 21;

// Fingertip landmark indices
static constexpr int FINGERTIP_IDS[] = {4, 8, 12, 16, 20};

// ── Xiaolin Wu anti-aliased line ──
static inline void plot_pixel(uint8_t* frame, int h, int w,
                               int x, int y, Color3 c, float brightness) {
    if (x < 0 || x >= w || y < 0 || y >= h || brightness <= 0.0f) return;
    uint8_t* px = frame + (y * w + x) * 3;
    float inv = 1.0f - brightness;
    px[0] = static_cast<uint8_t>(c.b * brightness + px[0] * inv);
    px[1] = static_cast<uint8_t>(c.g * brightness + px[1] * inv);
    px[2] = static_cast<uint8_t>(c.r * brightness + px[2] * inv);
}

static float fpart(float x) { return x - std::floor(x); }
static float rfpart(float x) { return 1.0f - fpart(x); }

void draw_aa_line(
    uint8_t* frame, int h, int w,
    int x0, int y0, int x1, int y1,
    Color3 color, int thickness)
{
    // For thickness > 1, draw multiple offset lines
    for (int t = -(thickness / 2); t <= thickness / 2; ++t) {
        bool steep = std::abs(y1 - y0) > std::abs(x1 - x0);
        int lx0 = x0, ly0 = y0, lx1 = x1, ly1 = y1;

        if (steep) {
            std::swap(lx0, ly0);
            std::swap(lx1, ly1);
        }
        if (lx0 > lx1) {
            std::swap(lx0, lx1);
            std::swap(ly0, ly1);
        }

        float dx = static_cast<float>(lx1 - lx0);
        float dy = static_cast<float>(ly1 - ly0);
        float gradient = (dx == 0.0f) ? 1.0f : dy / dx;

        // First endpoint
        float xend = std::round(static_cast<float>(lx0));
        float yend = ly0 + gradient * (xend - lx0);
        float xgap = rfpart(lx0 + 0.5f);
        int xpxl1 = static_cast<int>(xend);
        int ypxl1 = static_cast<int>(std::floor(yend));

        if (steep) {
            plot_pixel(frame, h, w, ypxl1 + t, xpxl1, color, rfpart(yend) * xgap);
            plot_pixel(frame, h, w, ypxl1 + 1 + t, xpxl1, color, fpart(yend) * xgap);
        } else {
            plot_pixel(frame, h, w, xpxl1, ypxl1 + t, color, rfpart(yend) * xgap);
            plot_pixel(frame, h, w, xpxl1, ypxl1 + 1 + t, color, fpart(yend) * xgap);
        }

        float intery = yend + gradient;

        // Second endpoint
        xend = std::round(static_cast<float>(lx1));
        yend = ly1 + gradient * (xend - lx1);
        xgap = fpart(lx1 + 0.5f);
        int xpxl2 = static_cast<int>(xend);
        int ypxl2 = static_cast<int>(std::floor(yend));

        if (steep) {
            plot_pixel(frame, h, w, ypxl2 + t, xpxl2, color, rfpart(yend) * xgap);
            plot_pixel(frame, h, w, ypxl2 + 1 + t, xpxl2, color, fpart(yend) * xgap);
        } else {
            plot_pixel(frame, h, w, xpxl2, ypxl2 + t, color, rfpart(yend) * xgap);
            plot_pixel(frame, h, w, xpxl2, ypxl2 + 1 + t, color, fpart(yend) * xgap);
        }

        // Main loop
        for (int x = xpxl1 + 1; x < xpxl2; ++x) {
            int iy = static_cast<int>(std::floor(intery));
            if (steep) {
                plot_pixel(frame, h, w, iy + t, x, color, rfpart(intery));
                plot_pixel(frame, h, w, iy + 1 + t, x, color, fpart(intery));
            } else {
                plot_pixel(frame, h, w, x, iy + t, color, rfpart(intery));
                plot_pixel(frame, h, w, x, iy + 1 + t, color, fpart(intery));
            }
            intery += gradient;
        }
    }
}

// ── Filled circle with outline ──
void draw_circle(
    uint8_t* frame, int h, int w,
    int cx, int cy, int radius,
    Color3 fill_color, Color3 outline_color, int outline_thickness)
{
    int r2 = radius * radius;
    int outer2 = (radius + outline_thickness) * (radius + outline_thickness);

    int y_min = std::max(0, cy - radius - outline_thickness);
    int y_max = std::min(h - 1, cy + radius + outline_thickness);
    int x_min = std::max(0, cx - radius - outline_thickness);
    int x_max = std::min(w - 1, cx + radius + outline_thickness);

    for (int y = y_min; y <= y_max; ++y) {
        int dy = y - cy;
        for (int x = x_min; x <= x_max; ++x) {
            int dx = x - cx;
            int dist2 = dx * dx + dy * dy;

            uint8_t* px = frame + (y * w + x) * 3;

            if (dist2 <= r2) {
                // Fill
                px[0] = fill_color.b;
                px[1] = fill_color.g;
                px[2] = fill_color.r;
            } else if (dist2 <= outer2) {
                // Outline
                px[0] = outline_color.b;
                px[1] = outline_color.g;
                px[2] = outline_color.r;
            }
        }
    }
}

// ── Draw complete hand skeleton in one call ──
void draw_hand_skeleton(
    uint8_t* frame, int h, int w,
    const float* landmarks_xy, int num_landmarks,
    Color3 bone_color, Color3 joint_color, Color3 tip_color,
    int bone_thickness, int joint_radius, int tip_radius)
{
    if (num_landmarks < 21) return;

    // Draw bones (connections)
    for (int i = 0; i < NUM_CONNS; ++i) {
        int a = HAND_CONNS[i][0];
        int b = HAND_CONNS[i][1];
        int x0 = static_cast<int>(landmarks_xy[a * 2]);
        int y0 = static_cast<int>(landmarks_xy[a * 2 + 1]);
        int x1 = static_cast<int>(landmarks_xy[b * 2]);
        int y1 = static_cast<int>(landmarks_xy[b * 2 + 1]);
        draw_aa_line(frame, h, w, x0, y0, x1, y1, bone_color, bone_thickness);
    }

    // Draw joint dots
    for (int i = 0; i < num_landmarks; ++i) {
        int px = static_cast<int>(landmarks_xy[i * 2]);
        int py = static_cast<int>(landmarks_xy[i * 2 + 1]);

        // Check if this is a fingertip
        bool is_tip = false;
        for (int t = 0; t < 5; ++t) {
            if (FINGERTIP_IDS[t] == i) { is_tip = true; break; }
        }

        if (is_tip) {
            draw_circle(frame, h, w, px, py, tip_radius, tip_color, bone_color, 1);
        } else {
            draw_circle(frame, h, w, px, py, joint_radius, joint_color, bone_color, 1);
        }
    }
}
