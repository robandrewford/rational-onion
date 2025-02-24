from setuptools import setup, find_packages

setup(
    name="rational-onion",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.95.1",
        "pytest>=7.3.1",
        "pytest-asyncio>=0.21.0",
        "coverage>=7.2.6",
    ]
) 