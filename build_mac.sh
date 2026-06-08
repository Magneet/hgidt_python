#!/bin/bash
# build_mac.sh — Builds the macOS .app bundle for the Horizon Golden Image Deployment Tool.
#
# Requirements (run once):
#   python3 -m venv .venv
#   source .venv/bin/activate
#   pip install -r requirements.txt
#   pip install pyinstaller
#
# Output: dist/Horizon Golden Image Deployment Tool.app

set -e
VERSION="1.0.0"

source .venv/bin/activate

pyinstaller "Horizon Golden Image Deployment Tool-mac.spec" \
    --noconfirm \
    --clean

deactivate

APP="dist/Horizon Golden Image Deployment Tool.app"
DMG="installer/Horizon_Golden_Image_Deployment_Tool_v${VERSION}_macOS.dmg"
VOLUME="Horizon Golden Image Deployment Tool"

mkdir -p installer

echo ""
echo "Build complete: $APP"
echo "Creating DMG..."

# Detach any previously mounted volume with the same name
hdiutil detach "/Volumes/$VOLUME" -force -quiet 2>/dev/null || true

# Remove any previous DMG so hdiutil does not prompt
[ -f "$DMG" ] && rm "$DMG"

hdiutil create \
    -volname "$VOLUME" \
    -srcfolder "$APP" \
    -ov \
    -format UDZO \
    "$DMG"

echo "DMG written to $DMG"
