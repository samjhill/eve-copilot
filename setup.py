#!/usr/bin/env python3
"""
Setup script for EVE Copilot
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
install_requires = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        install_requires = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="eve-copilot",
    version="0.1.0",
    author="EVE Copilot Team",
    author_email="team@eve-copilot.com",
    description="Real-time EVE Online log monitoring with voice notifications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eve-copilot/eve-copilot",
    project_urls={
        "Bug Tracker": "https://github.com/eve-copilot/eve-copilot/issues",
        "Documentation": "https://github.com/eve-copilot/eve-copilot#readme",
        "Source Code": "https://github.com/eve-copilot/eve-copilot",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Games/Entertainment",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.11",
    install_requires=install_requires,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "eve-copilot=app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "evetalk": ["*.yml", "*.yaml"],
    },
    zip_safe=False,
    keywords="eve-online, gaming, voice, tts, monitoring, logs",
    platforms=["Windows", "macOS", "Linux"],
)
