"""Compatibility installer for Python/pip versions that do not read PEP 621 metadata."""

from pathlib import Path

from setuptools import find_packages, setup


ROOT = Path(__file__).resolve().parent

setup(
    name="make-com-skills",
    version=(ROOT / "VERSION").read_text(encoding="utf-8").strip(),
    description="A safe companion wizard and portable skill pack for the official Make CLI",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    python_requires=">=3.9",
    package_dir={"": "src"},
    packages=find_packages("src"),
    entry_points={"console_scripts": ["make-skills=make_skills.cli:main"]},
)
