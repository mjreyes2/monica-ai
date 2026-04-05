cmake_minimum_required(VERSION 3.15)
project(monica_vision_accel LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find Python and pybind11
find_package(Python3 REQUIRED COMPONENTS Interpreter Development NumPy)
find_package(pybind11 CONFIG QUIET)

if(NOT pybind11_FOUND)
    # Fallback: fetch pybind11 from GitHub
    include(FetchContent)
    FetchContent_Declare(
        pybind11
        GIT_REPOSITORY https://github.com/pybind/pybind11.git
        GIT_TAG v2.12.0
    )
    FetchContent_MakeAvailable(pybind11)
endif()

# Find OpenCV (optional — used for cv::Mat interop)
find_package(OpenCV QUIET)

# ── Source files ──
set(SOURCES
    src/vision_accel.cpp
    src/frame_ops.cpp
    src/skeleton_draw.cpp
    src/globe_math.cpp
)

# ── Build the Python extension module ──
pybind11_add_module(monica_vision_accel ${SOURCES})

target_include_directories(monica_vision_accel PRIVATE
    ${Python3_NumPy_INCLUDE_DIRS}
    src/
)

if(OpenCV_FOUND)
    target_link_libraries(monica_vision_accel PRIVATE ${OpenCV_LIBS})
    target_compile_definitions(monica_vision_accel PRIVATE HAS_OPENCV=1)
    target_include_directories(monica_vision_accel PRIVATE ${OpenCV_INCLUDE_DIRS})
endif()

# SIMD optimizations
if(MSVC)
    target_compile_options(monica_vision_accel PRIVATE /O2 /arch:AVX2 /fp:fast)
else()
    target_compile_options(monica_vision_accel PRIVATE -O3 -mavx2 -mfma -ffast-math)
endif()

# Install target
install(TARGETS monica_vision_accel LIBRARY DESTINATION .)
