#!/usr/bin/env bash
set -e

REPO="tryroot1234/mindbase"
BINARY="mindbase"
INSTALL_DIR="${HOME}/.local/bin"

echo "Installing mindbase..."

# Detect OS and architecture
OS="$(uname -s)"
ARCH="$(uname -m)"

case "$OS" in
    Linux*)  PLATFORM="linux" ;;
    Darwin*) PLATFORM="macos" ;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM="windows" ;;
    *)       echo "Unsupported OS: $OS"; exit 1 ;;
esac

case "$ARCH" in
    x86_64|amd64)  ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    *)             echo "Unsupported architecture: $ARCH"; exit 1 ;;
esac

echo "Platform: $PLATFORM-$ARCH"

# Check Python version
check_python() {
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            version=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
                PYTHON="$cmd"
                return 0
            fi
        fi
    done
    return 1
}

if ! check_python; then
    echo "Error: Python 3.10+ is required but not found."
    echo "Please install Python 3.10 or later."
    exit 1
fi

echo "Using Python: $PYTHON ($($PYTHON --version))"

# Install via pip
echo ""
echo "Installing mindbase with pip..."
$PYTHON -m pip install --user --upgrade pip 2>/dev/null || true
$PYTHON -m pip install --user "git+https://github.com/${REPO}.git"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo "NOTE: Add ~/.local/bin to your PATH:"
    echo ""
    echo "  echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
    echo "  source ~/.bashrc"
    echo ""
fi

echo ""
echo "mindbase installed successfully!"
echo ""
echo "Usage:"
echo "  mindbase add \"My Note\" -c \"Hello world\" -t test"
echo "  mindbase list"
echo "  mindbase search \"keyword\""
echo ""
echo "For more information, run: mindbase --help"
