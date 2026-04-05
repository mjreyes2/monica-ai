"""
Build script for monica_vision_accel C++ extension.

Usage:
    pip install pybind11
    python setup.py build_ext --inplace
    # Then copy monica_vision_accel.*.pyd to src/ or site-packages
"""
import os
import sys
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

class BuildExt(build_ext):
    """Custom build extension for C++17 + AVX2."""
    def build_extensions(self):
        if self.compiler.compiler_type == 'msvc':
            for ext in self.extensions:
                ext.extra_compile_args = ['/O2', '/std:c++17', '/arch:AVX2', '/fp:fast']
        else:
            for ext in self.extensions:
                ext.extra_compile_args = ['-O3', '-std=c++17', '-mavx2', '-mfma', '-ffast-math']
        super().build_extensions()

# Find pybind11 include path
try:
    import pybind11
    pybind11_include = pybind11.get_include()
except ImportError:
    print("ERROR: pybind11 not found. Install with: pip install pybind11")
    sys.exit(1)

ext_modules = [
    Extension(
        'monica_vision_accel',
        sources=[
            'src/vision_accel.cpp',
            'src/frame_ops.cpp',
            'src/skeleton_draw.cpp',
            'src/globe_math.cpp',
        ],
        include_dirs=[
            pybind11_include,
            'src/',
        ],
        language='c++',
    ),
]

setup(
    name='monica_vision_accel',
    version='1.0.0',
    author='Monica AI',
    description='C++ accelerated vision primitives for Monica AI',
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExt},
    python_requires='>=3.8',
)
