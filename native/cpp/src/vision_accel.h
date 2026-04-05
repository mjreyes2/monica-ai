#pragma once
/**
 * monica_vision_accel — C++ accelerated vision primitives for Monica AI
 *
 * Provides 10-50x speedup over pure Python/NumPy for:
 *   - Frame compositing (alpha-blend overlays onto video)
 *   - Hand skeleton drawing (lines + circles with anti-aliasing)
 *   - Globe projection math (lat/lng → screen coords, texture sampling)
 *   - Fast frame resize with area interpolation
 *
 * All functions accept NumPy arrays via pybind11 and return NumPy arrays.
 * Falls back gracefully to Python if this module is not compiled.
 */

#include <cstdint>
#include <cmath>
#include <vector>
#include <array>
#include <algorithm>
#include <tuple>

// ── Frame Operations ──

/// Alpha-blend overlay onto base frame (both HWC uint8, overlay has 4 channels BGRA)
void composite_overlay(
    uint8_t* base, int base_h, int base_w,
    const uint8_t* overlay, int ov_h, int ov_w,
    int offset_x, int offset_y);

/// Fast bilinear resize (HWC uint8)
void fast_resize(
    const uint8_t* src, int src_h, int src_w, int channels,
    uint8_t* dst, int dst_h, int dst_w);

/// BGR ↔ RGB swap in-place (avoids cv2.cvtColor copy)
void swap_channels_inplace(uint8_t* data, int h, int w);

// ── Skeleton Drawing ──

struct Point2D { int x, y; };
struct Color3 { uint8_t b, g, r; };

/// Draw anti-aliased line on HWC uint8 frame
void draw_aa_line(
    uint8_t* frame, int h, int w,
    int x0, int y0, int x1, int y1,
    Color3 color, int thickness);

/// Draw filled circle with optional outline
void draw_circle(
    uint8_t* frame, int h, int w,
    int cx, int cy, int radius,
    Color3 fill_color, Color3 outline_color, int outline_thickness);

/// Draw full hand skeleton (21 landmarks, 21 connections) in one call
void draw_hand_skeleton(
    uint8_t* frame, int h, int w,
    const float* landmarks_xy, int num_landmarks,  // flat array [x0,y0,x1,y1,...]
    Color3 bone_color, Color3 joint_color, Color3 tip_color,
    int bone_thickness, int joint_radius, int tip_radius);

// ── Globe Projection ──

struct GlobeParams {
    int cx, cy;          // center of globe on screen
    int radius;          // globe radius in pixels
    float rotation_deg;  // current rotation angle (longitude offset)
    float tilt_deg;      // axial tilt (default 23.5)
};

/// Project lat/lng to screen coordinates on a 3D sphere
/// Returns (x, y, visible) — visible=false if point is on the back side
std::tuple<int, int, bool> globe_project(
    float lat_deg, float lng_deg, const GlobeParams& params);

/// Sample earth texture for a globe pixel
/// texture is HWC uint8, globe renders to dst (HWC uint8)
void render_globe_texture(
    const uint8_t* texture, int tex_h, int tex_w,
    uint8_t* dst, int dst_h, int dst_w,
    const GlobeParams& params);

/// Draw a pulsating dot on the globe at lat/lng
void draw_globe_dot(
    uint8_t* frame, int h, int w,
    float lat_deg, float lng_deg,
    const GlobeParams& params,
    Color3 color, int base_radius, float pulse_phase);
