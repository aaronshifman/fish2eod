#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Setup script. Imports description from readme."""

import re

import setuptools

verstrline = open("fish2eod/__init__.py", "rt").read()
mo = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", verstrline, re.M)

if mo:
    version = mo.group(1)
else:
    raise RuntimeError("Unable to find version fish2eod version")

with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="fish2eod",
    version=version,
    author="Aaron R. Shifman",
    author_email="aaronrshifman@gmail.com",
    description="Automated simulation and inference of electric fields from weakly electric fish",
    long_description=long_description,
    long_description_content_type="text/rst",
    url="https://github.com/aaronshifman/fish2eod",
    packages=setuptools.find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
    ],
)
