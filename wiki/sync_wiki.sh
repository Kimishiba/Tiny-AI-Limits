#!/usr/bin/env bash
# ==============================================================================
# Tiny AI Limits - GitHub Wiki Sync Utility
# ==============================================================================
# This script clones the GitHub Wiki repository (or pulls latest), copies all
# markdown files from the local wiki/ directory, and pushes them to GitHub.
# ==============================================================================

set -e

WIKI_REPO_URL="https://github.com/Kimishiba/Tiny-AI-Limits.wiki.git"
TEMP_DIR="/tmp/tiny-ai-limits-wiki-sync"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Syncing Tiny AI Limits documentation to GitHub Wiki..."

# Clean up any previous temp directory
rm -rf "$TEMP_DIR"

# Clone the GitHub Wiki repository
echo "📥 Cloning GitHub Wiki repository..."
if git clone "$WIKI_REPO_URL" "$TEMP_DIR"; then
    echo "✅ Wiki repository cloned successfully."
else
    echo "⚠️ Note: If the wiki repository was not found, ensure you have clicked 'Create the first page' on GitHub Wiki first to initialize the wiki repository."
    exit 1
fi

# Copy all markdown files
echo "📋 Copying wiki documentation files..."
cp -v "$SCRIPT_DIR"/*.md "$TEMP_DIR/"

# Navigate to temp repo and commit
cd "$TEMP_DIR"
git add .

if git diff --staged --quiet; then
    echo "✨ GitHub Wiki is already up-to-date. No changes to push."
else
    git commit -m "docs: update wiki documentation from main repository" \
               -m "Co-Authored-By: Google Antigravity <google-antigravity@users.noreply.github.com>"
    echo "📤 Pushing updates to GitHub Wiki..."
    git push origin master || git push origin main
    echo "🎉 Wiki documentation successfully published to GitHub Wiki!"
fi

# Clean up
rm -rf "$TEMP_DIR"
