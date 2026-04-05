from setuptools import find_packages, setup


setup(
    name="CuraFrame",
    version="2.4.1",
    description="Constraint-driven therapeutic design reasoning framework.",
    packages=find_packages(exclude=("tests", "docs", "apps")),
    python_requires=">=3.9",
)
