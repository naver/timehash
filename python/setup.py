# Timehash
# Copyright (c) 2026-present NAVER Corp.
# Apache-2.0

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="timehash",
    version="1.0.0",
    author="Naver",
    description="Hierarchical time indexing for efficient business hours search",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/naver/timehash",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
)
