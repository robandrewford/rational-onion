#!/bin/bash

# Create and activate virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3.10 -m venv .venv
fi
source .venv/bin/activate

# Ensure pip is installed and up to date
python -m ensurepip --upgrade
python -m pip install --upgrade pip

# Install numpy first to avoid compatibility issues
python -m pip install numpy==1.24.3

# Install dependencies
python -m pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_md 