#!/bin/bash
set -e

# Exit immediately if a command exits with a non-zero status.
# set -e

# branch from parameter
if [ -z "$1" ]; then
    echo "Error: Branch parameter is empty. Please provide a valid branch name."
    exit 1
fi
BRANCH="$1"

if [ "$BRANCH" = "local" ]; then
    # For local branch, use the files
    echo "Using local dev files in /git/agent-zero"
    # List all files recursively in the target directory
    # echo "All files in /git/agent-zero (recursive):"
    # find "/git/agent-zero" -type f | sort
else
    # For other branches, clone from GitHub
    echo "Cloning repository from branch $BRANCH..."
    git clone -b "$BRANCH" "https://github.com/agent0ai/agent-zero" "/git/agent-zero" || {
        echo "CRITICAL ERROR: Failed to clone repository. Branch: $BRANCH"
        exit 1
    }
fi

. "/ins/setup_venv.sh" "$@"

# moved to base image
# # Ensure the virtual environment and pip setup
# pip install --upgrade pip ipython requests
# # Install some packages in specific variants
# pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install Python development headers for compiling native extensions
apt-get update && apt-get install -y python3-dev python3.13-dev

# Install remaining A0 python packages from pyproject.toml into active venv (/opt/venv-a0)
cd /git/agent-zero
uv sync --no-dev --active

# Install pip into the active venv for compatibility with Agent Zero's code execution
# (must be after uv sync to avoid being removed)
uv pip install pip

# install playwright
bash /ins/install_playwright.sh "$@"

# Preload A0 (venv is active from setup_venv.sh)
python preload.py --dockerized=true
