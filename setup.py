# Licensed under the PolyForm Noncommercial License 1.0.0
from setuptools import find_packages, setup


setup(
    name="CuraFrame",
    version="3.0.0",
    description="Constraint-driven therapeutic design reasoning framework.",
    packages=find_packages(exclude=("tests", "docs", "apps")),
    python_requires=">=3.9",
)
