#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
APP_NAME="Tiny Screen.app"
APP_PATH="$REPO_ROOT/$APP_NAME"
CONTENTS="$APP_PATH/Contents"
MACOS="$CONTENTS/MacOS"
RESOURCES="$CONTENTS/Resources"

echo "🔨 Building $APP_NAME..."

# 1. Prepare clean bundle directories
rm -rf "$APP_PATH"
mkdir -p "$MACOS" "$RESOURCES"

# 2. Generate and copy AppIcon.icns
echo "🎨 Generating AppIcon.icns..."
python3 "$REPO_ROOT/scripts/generate_app_icon.py"
if [ -f "$REPO_ROOT/resources/AppIcon.icns" ]; then
    cp "$REPO_ROOT/resources/AppIcon.icns" "$RESOURCES/AppIcon.icns"
fi

# 3. Create Info.plist
cat <<'EOF' > "$CONTENTS/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleDisplayName</key>
    <string>Tiny Screen</string>
    <key>CFBundleExecutable</key>
    <string>TinyScreen</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleIdentifier</key>
    <string>com.kimishiba.tinyscreen</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Tiny Screen</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>0.5.0</string>
    <key>CFBundleVersion</key>
    <string>0.5.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13.0</string>
    <key>LSUIElement</key>
    <string>1</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
EOF

# 4. Create launcher executable
cat <<'EOF' > "$MACOS/TinyScreen"
#!/usr/bin/env bash
set -e

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
MACOS_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
CONTENTS_DIR="$( cd -P "$MACOS_DIR/.." >/dev/null 2>&1 && pwd )"
APP_DIR="$( cd -P "$CONTENTS_DIR/.." >/dev/null 2>&1 && pwd )"
REPO_DIR="$( cd -P "$APP_DIR/.." >/dev/null 2>&1 && pwd )"

if [ -f "$APP_DIR/backend/app.py" ]; then
    BACKEND_DIR="$APP_DIR/backend"
    WORK_DIR="$APP_DIR"
elif [ -f "$REPO_DIR/backend/app.py" ]; then
    BACKEND_DIR="$REPO_DIR/backend"
    WORK_DIR="$REPO_DIR"
elif [ -f "$CONTENTS_DIR/Resources/backend/app.py" ]; then
    BACKEND_DIR="$CONTENTS_DIR/Resources/backend"
    WORK_DIR="$CONTENTS_DIR/Resources"
else
    BACKEND_DIR="$PWD/backend"
    WORK_DIR="$PWD"
fi

cd "$WORK_DIR"

CANDIDATES=(
    "$VIRTUAL_ENV/bin/python3"
    "$WORK_DIR/.venv/bin/python3"
    "$HOME/.tiny_ai_screen/venv/bin/python3"
    "/opt/homebrew/bin/python3"
    "/usr/local/bin/python3"
    "$(command -v python3 2>/dev/null || true)"
    "/usr/bin/python3"
)

PYTHON_BIN=""

for CANDIDATE in "${CANDIDATES[@]}"; do
    if [ -n "$CANDIDATE" ] && [ -x "$CANDIDATE" ]; then
        USER_SITE="$("$CANDIDATE" -m site --user-site 2>/dev/null || true)"
        if [ -n "$USER_SITE" ] && [ -d "$USER_SITE" ]; then
            export PYTHONPATH="$USER_SITE:${PYTHONPATH:-}"
        fi
        if "$CANDIDATE" -c "import flask, requests, rumps, zeroconf" >/dev/null 2>&1; then
            PYTHON_BIN="$CANDIDATE"
            break
        fi
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    for CANDIDATE in "${CANDIDATES[@]}"; do
        if [ -n "$CANDIDATE" ] && [ -x "$CANDIDATE" ]; then
            PYTHON_BIN="$CANDIDATE"
            break
        fi
    done
fi

if [ -z "$PYTHON_BIN" ]; then
    osascript -e 'display alert "Tiny Screen Error" message "Python 3 could not be found on this system. Please install Python 3 to run the companion app." as critical'
    exit 1
fi

export PYTHONUNBUFFERED=1
exec "$PYTHON_BIN" "$BACKEND_DIR/app.py" "$@"
EOF

chmod +x "$MACOS/TinyScreen"

# 5. Copy backend, emulator, and image resources (excluding caches and git)
echo "📦 Bundling application resources..."
mkdir -p "$RESOURCES/backend" "$RESOURCES/emulator" "$RESOURCES/img"

if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='.pytest_cache' "$REPO_ROOT/backend/" "$RESOURCES/backend/"
    rsync -a "$REPO_ROOT/emulator/" "$RESOURCES/emulator/"
    rsync -a "$REPO_ROOT/img/" "$RESOURCES/img/"
else
    cp -R "$REPO_ROOT/backend/"* "$RESOURCES/backend/"
    cp -R "$REPO_ROOT/emulator/"* "$RESOURCES/emulator/"
    cp -R "$REPO_ROOT/img/"* "$RESOURCES/img/"
fi

# 6. Ad-hoc code sign for macOS Gatekeeper
if command -v codesign >/dev/null 2>&1; then
    echo "🔏 Signing application bundle (ad-hoc)..."
    codesign --force --deep --sign - "$APP_PATH" 2>/dev/null || true
fi

echo "✅ Successfully built: $APP_PATH"
echo "🚀 You can now launch '$APP_NAME' directly from Finder or move it to /Applications!"
