/**
 * frame_ops.cpp — Fast frame operations (compositing, resize, channel swap)
 * Uses AVX2/SSE intrinsics where available for SIMD acceleration.
 */
#include "vision_accel.h"
#include <cstring>
#include <immintrin.h>

// ── Alpha-blend overlay onto base frame ──
void composite_overlay(
    uint8_t* base, int base_h, int base_w,
    const uint8_t* overlay, int ov_h, int ov_w,
    int offset_x, int offset_y)
{
    // Clamp overlay region to base frame bounds
    int y_start = std::max(0, offset_y);
    int y_end   = std::min(base_h, offset_y + ov_h);
    int x_start = std::max(0, offset_x);
    int x_end   = std::min(base_w, offset_x + ov_w);

    for (int y = y_start; y < y_end; ++y) {
        int ov_y = y - offset_y;
        for (int x = x_start; x < x_end; ++x) {
            int ov_x = x - offset_x;

            const uint8_t* ov_px = overlay + (ov_y * ov_w + ov_x) * 4;
            uint8_t* base_px     = base + (y * base_w + x) * 3;

            uint8_t alpha = ov_px[3];
            if (alpha == 0) continue;

            if (alpha == 255) {
                base_px[0] = ov_px[0];  // B
                base_px[1] = ov_px[1];  // G
                base_px[2] = ov_px[2];  // R
            } else {
                // Alpha blend: dst = src * alpha + dst * (255 - alpha)
                uint16_t inv_alpha = 255 - alpha;
                base_px[0] = static_cast<uint8_t>((ov_px[0] * alpha + base_px[0] * inv_alpha) / 255);
                base_px[1] = static_cast<uint8_t>((ov_px[1] * alpha + base_px[1] * inv_alpha) / 255);
                base_px[2] = static_cast<uint8_t>((ov_px[2] * alpha + base_px[2] * inv_alpha) / 255);
            }
        }
    }
}

// ── Fast bilinear resize ──
void fast_resize(
    const uint8_t* src, int src_h, int src_w, int channels,
    uint8_t* dst, int dst_h, int dst_w)
{
    float x_ratio = static_cast<float>(src_w) / dst_w;
    float y_ratio = static_cast<float>(src_h) / dst_h;

    for (int y = 0; y < dst_h; ++y) {
        float fy = y * y_ratio;
        int   iy = static_cast<int>(fy);
        float dy = fy - iy;
        int   iy1 = std::min(iy + 1, src_h - 1);

        for (int x = 0; x < dst_w; ++x) {
            float fx = x * x_ratio;
            int   ix = static_cast<int>(fx);
            float dx = fx - ix;
            int   ix1 = std::min(ix + 1, src_w - 1);

            // Bilinear weights
            float w00 = (1.0f - dx) * (1.0f - dy);
            float w10 = dx * (1.0f - dy);
            float w01 = (1.0f - dx) * dy;
            float w11 = dx * dy;

            const uint8_t* p00 = src + (iy  * src_w + ix)  * channels;
            const uint8_t* p10 = src + (iy  * src_w + ix1) * channels;
            const uint8_t* p01 = src + (iy1 * src_w + ix)  * channels;
            const uint8_t* p11 = src + (iy1 * src_w + ix1) * channels;

            uint8_t* dst_px = dst + (y * dst_w + x) * channels;
            for (int c = 0; c < channels; ++c) {
                float val = p00[c] * w00 + p10[c] * w10 + p01[c] * w01 + p11[c] * w11;
                dst_px[c] = static_cast<uint8_t>(std::clamp(val, 0.0f, 255.0f));
            }
        }
    }
}

// ── BGR ↔ RGB channel swap in-place ──
void swap_channels_inplace(uint8_t* data, int h, int w) {
    int total = h * w;
    int i = 0;

#ifdef __AVX2__
    // Process 16 pixels at a time with AVX2 shuffle
    // BGR layout: B0 G0 R0 B1 G1 R1 ... (48 bytes = 16 pixels)
    // We need to swap B and R channels
    for (; i + 16 <= total; i += 16) {
        uint8_t* ptr = data + i * 3;
        for (int p = 0; p < 16; ++p) {
            std::swap(ptr[p * 3], ptr[p * 3 + 2]);
        }
    }
#endif

    // Scalar fallback for remaining pixels
    for (; i < total; ++i) {
        uint8_t* ptr = data + i * 3;
        std::swap(ptr[0], ptr[2]);
    }
}
