#!/usr/bin/env python3
"""
Pushup Rep Counter - Setup Script
For packaging and distribution
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="pushup-rep-counter",
    version="1.0.0",
    author="Your Team Name",
    description="Real-time pushup rep counter using MediaPipe and Streamlit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
    python_requires=">=3.8",
    install_requires=[
        "streamlit>=1.42.2",
        "mediapipe>=0.10.5",
        "opencv-python>=4.8.1",
        "numpy>=1.24.3",
        "scipy>=1.11.2",
        "Pillow>=10.0.0",
    ],
)
