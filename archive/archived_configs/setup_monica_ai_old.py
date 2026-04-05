"""
Setup script for Monica AI.
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="monica-ai",
    version="1.0.0",
    author="Monica AI Team",
    description="Monica AI - Your Intelligent AI Assistant with Voice and Vision",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/monica-ai/monica",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "opencv-python>=4.5.0",
        "pillow>=9.0.0",
        "sounddevice>=0.4.6",
        "pyaudio>=0.2.13",
    ],
    extras_require={
        "full": [
            "torch>=2.0.0",
            "torchaudio>=2.0.0",
            "openai-whisper>=20231117",
            "piper-tts>=2.0.0",
            "ollama>=0.1.0",
            "pygame>=2.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "monica-ai=src.app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["resources/*", "resources/**/*"],
    },
)
