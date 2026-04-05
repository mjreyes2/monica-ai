/**
 * vision_accel.cpp — pybind11 bindings for Monica vision accelerator
 *
 * Exposes C++ vision functions to Python as:
 *   import monica_vision_accel as accel
 *   accel.composite_overlay(base, overlay, x, y)
 *   accel.fast_resize(src, dst_h, dst_w)
 *   accel.swap_channels(frame)
 *   accel.draw_hand_skeleton(frame, landmarks, ...)
 *   accel.globe_project(lat, lng, cx, cy, radius, rotation, tilt)
 *   accel.render_globe(texture, dst, cx, cy, radius, rotation, tilt)
 *   accel.draw_globe_dot(frame, lat, lng, params..., color, radius, phase)
 */
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "vision_accel.h"

namespace py = pybind11;

// ── Frame operations ──

static void py_composite_overlay(
    py::array_t<uint8_t, py::array::c_style> base,
    py::array_t<uint8_t, py::array::c_style> overlay,
    int offset_x, int offset_y)
{
    auto b = base.mutable_unchecked<3>();
    auto o = overlay.unchecked<3>();

    if (b.shape(2) != 3)
        throw std::runtime_error("base must be HxWx3 (BGR)");
    if (o.shape(2) != 4)
        throw std::runtime_error("overlay must be HxWx4 (BGRA)");

    composite_overlay(
        base.mutable_data(), b.shape(0), b.shape(1),
        overlay.data(), o.shape(0), o.shape(1),
        offset_x, offset_y);
}

static py::array_t<uint8_t> py_fast_resize(
    py::array_t<uint8_t, py::array::c_style> src,
    int dst_h, int dst_w)
{
    auto s = src.unchecked<3>();
    int channels = s.shape(2);

    auto result = py::array_t<uint8_t>({dst_h, dst_w, channels});
    fast_resize(
        src.data(), s.shape(0), s.shape(1), channels,
        result.mutable_data(), dst_h, dst_w);
    return result;
}

static void py_swap_channels(py::array_t<uint8_t, py::array::c_style> frame) {
    auto f = frame.mutable_unchecked<3>();
    if (f.shape(2) != 3)
        throw std::runtime_error("frame must be HxWx3");
    swap_channels_inplace(frame.mutable_data(), f.shape(0), f.shape(1));
}

// ── Skeleton drawing ──

static void py_draw_hand_skeleton(
    py::array_t<uint8_t, py::array::c_style> frame,
    py::array_t<float, py::array::c_style> landmarks,
    py::tuple bone_color_t, py::tuple joint_color_t, py::tuple tip_color_t,
    int bone_thickness, int joint_radius, int tip_radius)
{
    auto f = frame.mutable_unchecked<3>();
    auto lm = landmarks.unchecked<2>();

    if (lm.shape(1) != 2)
        throw std::runtime_error("landmarks must be Nx2 (x, y)");

    Color3 bone_c  = {bone_color_t[0].cast<uint8_t>(),
                      bone_color_t[1].cast<uint8_t>(),
                      bone_color_t[2].cast<uint8_t>()};
    Color3 joint_c = {joint_color_t[0].cast<uint8_t>(),
                      joint_color_t[1].cast<uint8_t>(),
                      joint_color_t[2].cast<uint8_t>()};
    Color3 tip_c   = {tip_color_t[0].cast<uint8_t>(),
                      tip_color_t[1].cast<uint8_t>(),
                      tip_color_t[2].cast<uint8_t>()};

    draw_hand_skeleton(
        frame.mutable_data(), f.shape(0), f.shape(1),
        landmarks.data(), lm.shape(0),
        bone_c, joint_c, tip_c,
        bone_thickness, joint_radius, tip_radius);
}

// ── Globe projection ──

static py::tuple py_globe_project(
    float lat, float lng,
    int cx, int cy, int radius, float rotation, float tilt)
{
    GlobeParams params = {cx, cy, radius, rotation, tilt};
    auto [sx, sy, visible] = globe_project(lat, lng, params);
    return py::make_tuple(sx, sy, visible);
}

static void py_render_globe(
    py::array_t<uint8_t, py::array::c_style> texture,
    py::array_t<uint8_t, py::array::c_style> dst,
    int cx, int cy, int radius, float rotation, float tilt)
{
    auto tex = texture.unchecked<3>();
    auto d = dst.mutable_unchecked<3>();

    if (tex.shape(2) != 3 || d.shape(2) != 3)
        throw std::runtime_error("texture and dst must be HxWx3");

    GlobeParams params = {cx, cy, radius, rotation, tilt};
    render_globe_texture(
        texture.data(), tex.shape(0), tex.shape(1),
        dst.mutable_data(), d.shape(0), d.shape(1),
        params);
}

static void py_draw_globe_dot(
    py::array_t<uint8_t, py::array::c_style> frame,
    float lat, float lng,
    int cx, int cy, int radius, float rotation, float tilt,
    py::tuple color_t, int dot_radius, float pulse_phase)
{
    auto f = frame.mutable_unchecked<3>();
    GlobeParams params = {cx, cy, radius, rotation, tilt};
    Color3 color = {color_t[0].cast<uint8_t>(),
                    color_t[1].cast<uint8_t>(),
                    color_t[2].cast<uint8_t>()};

    draw_globe_dot(
        frame.mutable_data(), f.shape(0), f.shape(1),
        lat, lng, params, color, dot_radius, pulse_phase);
}

// ── Module definition ──

PYBIND11_MODULE(monica_vision_accel, m) {
    m.doc() = "Monica AI C++ vision accelerator — 10-50x faster frame ops, skeleton drawing, globe rendering";

    // Frame operations
    m.def("composite_overlay", &py_composite_overlay,
        "Alpha-blend a BGRA overlay onto a BGR base frame in-place",
        py::arg("base"), py::arg("overlay"), py::arg("offset_x"), py::arg("offset_y"));

    m.def("fast_resize", &py_fast_resize,
        "Bilinear resize a HWC frame (faster than cv2.resize for small targets)",
        py::arg("src"), py::arg("dst_h"), py::arg("dst_w"));

    m.def("swap_channels", &py_swap_channels,
        "Swap BGR<->RGB in-place (avoids cv2.cvtColor copy)",
        py::arg("frame"));

    // Skeleton drawing
    m.def("draw_hand_skeleton", &py_draw_hand_skeleton,
        "Draw full hand skeleton (21 landmarks + connections) in one C++ call",
        py::arg("frame"), py::arg("landmarks"),
        py::arg("bone_color") = py::make_tuple(0, 255, 0),
        py::arg("joint_color") = py::make_tuple(0, 200, 255),
        py::arg("tip_color") = py::make_tuple(0, 255, 255),
        py::arg("bone_thickness") = 2,
        py::arg("joint_radius") = 4,
        py::arg("tip_radius") = 6);

    // Globe projection
    m.def("globe_project", &py_globe_project,
        "Project lat/lng to screen coords on a 3D sphere. Returns (x, y, visible)",
        py::arg("lat"), py::arg("lng"),
        py::arg("cx"), py::arg("cy"), py::arg("radius"),
        py::arg("rotation") = 0.0f, py::arg("tilt") = 23.5f);

    m.def("render_globe", &py_render_globe,
        "Render textured globe into destination frame buffer",
        py::arg("texture"), py::arg("dst"),
        py::arg("cx"), py::arg("cy"), py::arg("radius"),
        py::arg("rotation") = 0.0f, py::arg("tilt") = 23.5f);

    m.def("draw_globe_dot", &py_draw_globe_dot,
        "Draw a pulsating dot on the globe at given lat/lng",
        py::arg("frame"), py::arg("lat"), py::arg("lng"),
        py::arg("cx"), py::arg("cy"), py::arg("radius"),
        py::arg("rotation") = 0.0f, py::arg("tilt") = 23.5f,
        py::arg("color") = py::make_tuple(0, 200, 255),
        py::arg("dot_radius") = 3, py::arg("pulse_phase") = 0.0f);

    // Version info
    m.attr("__version__") = "1.0.0";
    m.attr("__author__") = "Monica AI";
}
