from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mossy-manager",
    version="1.0.0",
    author="POINTYTHRUNDRA654",
    description="A manager tool for Mod Organizer 2 (MO2)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/POINTYTHRUNDRA654/Mossy-manager.",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "configparser>=5.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mossy-manager=mossy_manager.main:main",
        ],
    },
)
