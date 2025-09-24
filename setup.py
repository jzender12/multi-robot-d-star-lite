#!/usr/bin/env python3
"""Setup script for Multi-Robot D* Lite Path Planning System."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="multi-robot-d-star-lite",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Multi-Robot D* Lite Path Planning System with collision detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/multi-robot-d-star-lite",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.24.0",
        "pygame>=2.5.0",
        "colorama>=0.4.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.0.0",
            "pytest-timeout>=2.1.0",
            "tox>=4.0.0",
        ],
        "dev": [
            "black>=23.0.0",
            "flake8>=6.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "multi-robot-demo=multi_robot_d_star_lite.__main__:main",
        ],
    },
)