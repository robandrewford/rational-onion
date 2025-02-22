from setuptools import setup, find_packages

setup(
    name="rational-onion",
    packages=find_packages(),
    install_requires=[
        "pytest>=7.3.1",
        "pytest-asyncio>=0.21.0",
    ]
) 