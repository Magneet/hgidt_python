#!/bin/bash
# build_linux.sh — Builds the Linux distributable for the Horizon Golden Image Deployment Tool.
#
# Requirements (run once):
#   python3 -m venv .venv
#   source .venv/bin/activate
#   pip install -r requirements.txt
#   pip install pyinstaller

set -e
VERSION="1.0.0"

source .venv/bin/activate

pyinstaller "Horizon Golden Image Deployment Tool-linux.spec" \
    --noconfirm \
    --clean

deactivate

DIST_DIR="dist/Horizon Golden Image Deployment Tool"
ZIP="installer/Horizon_Golden_Image_Deployment_Tool_v${VERSION}_Linux.zip"

mkdir -p installer

echo ""
echo "Build complete: $DIST_DIR"
echo "Creating ZIP..."

[ -f "$ZIP" ] && rm "$ZIP"

zip -r "$ZIP" "$DIST_DIR"

echo "ZIP written to $ZIP"
