#!/bin/bash
set -e

REPO_ROOT="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
APP_NAME="Tiny Screen.app"
APP_PATH="$REPO_ROOT/$APP_NAME"
CONTENTS="$APP_PATH/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

echo "🔨 Building $APP_NAME..."

# 1. Generate AppIcon.icns
echo "🎨 Generating AppIcon.icns..."
python3 "$REPO_ROOT/scripts/generate_app_icon.py"

# 2. Prepare bundle directories
mkdir -p "$MACOS" "$RESOURCES"

# 3. Copy Icon
cp "$REPO_ROOT/resources/AppIcon.icns" "$RESOURCES/AppIcon.icns"

# 4. Copy backend, emulator, and image resources for standalone portability
echo "📦 Bundling resources..."
mkdir -p "$RESOURCES/backend" "$RESOURCES/emulator" "$RESOURCES/img"
cp -R "$REPO_ROOT/backend/"* "$RESOURCES/backend/"
cp -R "$REPO_ROOT/emulator/"* "$RESOURCES/emulator/"
cp -R "$REPO_ROOT/img/"* "$RESOURCES/img/"

# 5. Set executable permissions
chmod +x "$MACOS/TinyScreen"
chmod +x "$REPO_ROOT/scripts/generate_app_icon.py"

# 6. Ad-hoc code sign for macOS Gatekeeper
if command -v codesign >/dev/null 2>&1; then
    echo "🔏 Signing application bundle (ad-hoc)..."
    codesign --force --deep --sign - "$APP_PATH" || true
fi

echo "✅ Successfully built: $APP_PATH"
echo "🚀 You can now launch '$APP_NAME' directly from Finder or move it to /Applications!"
