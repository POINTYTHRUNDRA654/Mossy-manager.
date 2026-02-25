from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mossy-manager",
    version="1.0.0",
    author="POINTYTHRUNDRA654",
    description="MO2 Manager - Load Order Management, Conflict Resolution, and Patching Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/POINTYTHRUNDRA654/Mossy-manager.",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pyyaml>=6.0",
        "toml>=0.10.2",
        "configparser>=5.3.0",
        "click>=8.1.0",
        "colorama>=0.4.6",
        "tabulate>=0.9.0",
        "pydantic>=2.8.0",
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "scikit-learn>=1.3.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ],
        "build": [
            "pyinstaller>=5.13.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mossy=mossy_manager.cli.main:main",
            "mossy-manager=mossy_manager.main:main",
        ],
    },
)
