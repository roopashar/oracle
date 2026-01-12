"""
Setup script for Oracle Test Library
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="oracle-test-lib",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive testing library for Oracle database clients",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/oracle-test-lib",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Database",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "oracledb>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "viz": [
            "matplotlib>=3.7.0",
            "pandas>=2.0.0",
            "numpy>=1.24.0",
            "scipy>=1.10.0",
        ],
        "all": [
            "faker>=20.0.0",
            "jsonschema>=4.17.0",
            "tqdm>=4.65.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "oracle-test=oracle_test_lib:main",
        ],
    },
)
