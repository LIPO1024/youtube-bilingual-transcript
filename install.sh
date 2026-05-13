#!/usr/bin/env bash
# Install youtube-bilingual-transcript skill for Claude Code
# Usage: curl -fsSL https://raw.githubusercontent.com/LIPO1024/youtube-bilingual-transcript/main/install.sh | bash

set -e

REPO_URL="https://github.com/LIPO1024/youtube-bilingual-transcript.git"
SKILL_NAME="youtube-bilingual-transcript"
SKILLS_DIR="${HOME}/.claude/skills"
TARGET_DIR="${SKILLS_DIR}/${SKILL_NAME}"

echo "Installing youtube-bilingual-transcript skill for Claude Code..."

# Ensure skills directory exists
mkdir -p "$SKILLS_DIR"

# Remove existing skill if present
if [ -d "$TARGET_DIR" ]; then
    echo "Removing existing installation at $TARGET_DIR ..."
    rm -rf "$TARGET_DIR"
fi

# Clone
git clone "$REPO_URL" "$TARGET_DIR"

echo ""
echo "Installation complete!"
echo "Skill installed to: $TARGET_DIR"
echo ""
echo "Next steps:"
echo "  1. Open Claude Code in your Obsidian vault directory"
echo "  2. Type: /youtube-bilingual-transcript"
echo "  3. Or say: 处理这个YouTube转录稿，生成双语笔记"
