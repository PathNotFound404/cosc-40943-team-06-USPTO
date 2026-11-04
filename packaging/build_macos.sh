#!/bin/sh
# Build the macOS app and its DMG (KD-packaging-pyinstaller, architecture section 7).
# Run from the repository root on an Apple silicon Mac, with requirements-build.txt
# installed in the active virtual environment. CI runs this same script.
#
# Output: dist/USPTO-Patent-Intelligence-<version>-arm64.dmg
set -eu

APP_NAME="USPTO Patent Intelligence"
VERSION=$(python -c 'import re; print(re.search(r"__version__ = \"([^\"]+)\"", open("src/patent_intelligence/__init__.py").read()).group(1))')
APP="dist/$APP_NAME.app"
DMG="dist/USPTO-Patent-Intelligence-$VERSION-arm64.dmg"

echo "== Building $APP_NAME $VERSION"
rm -rf build dist
pyinstaller --clean --noconfirm --distpath dist --workpath build packaging/patent-intelligence.spec

echo "== Checking the ad-hoc signature"
codesign --verify --deep --strict --verbose=2 "$APP"

echo "== Starting the built app once"
python packaging/smoke_test.py "$APP/Contents/MacOS/$APP_NAME"

echo "== Making the DMG"
STAGING="build/dmg"
mkdir -p "$STAGING"
cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING" -fs HFS+ -format UDZO -ov "$DMG"

echo "== Done: $DMG"
