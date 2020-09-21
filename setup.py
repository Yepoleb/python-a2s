#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as readme:
    long_description = readme.read()

setuptools.setup(
    name="python-a2s",
    version="1.2.1",
    author="Gabriel Huber",
    author_email="mail@gabrielhuber.at",
    description="Query Source and GoldSource servers for name, map, players and more.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Yepoleb/python-a2s",
    packages=["a2s"],
    license="MIT License",
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment"
    ],
    python_requires=">=3.7"
)
