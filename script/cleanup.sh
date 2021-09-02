#!/usr/bin/env bash
# change working directory to project root
cd "$(dirname "$0")/.." || exit
# remove folders and files created by build and deploy scripts
echo "Removing 'dist', if it exists..."
rm -rf dist
echo "Removing 'sdist', if it exists..."
rm -rf sdist
echo "Removing 'build', if it exists..."
rm -rf build
echo "Removing any '.egg-info' folders, if they exist..."
rm -rf *.egg-info/
rm -rf **/*.egg-info/
echo "Removing any '__pycache__' folders, if they exist..."
rm -rf __pycache__/
rm -rf **/__pycache__/
