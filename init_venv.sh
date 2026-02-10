#!/bin/bash

read -p "ATTENTION - overwrite existing .venv? (y/n)? " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    exit 0
fi

echo
echo Create an empty .venv
if [ -d ".venv" ]; then
    rm -rf .venv
fi
python -m venv .venv

source activate

echo
echo Upgrade pip
python -m pip install --upgrade pip

echo
echo Install dependencies from pyproject.toml
pip install --group test .
