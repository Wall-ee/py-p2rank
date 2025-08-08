#!/usr/bin/env bash

#
# Main launcher script for P2Rank Python implementation
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set Python path to include the p2rank package
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Default Python command (can be overridden with P2RANK_PYTHON env var)
PYTHON_CMD="${P2RANK_PYTHON:-python3}"

# Check if Python is available
if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo "Error: Python not found. Please install Python 3.8+ or set P2RANK_PYTHON environment variable."
    exit 1
fi

# Check Python version
python_version=$($PYTHON_CMD -c "import sys; print(sys.version_info[:2])")
if [[ ! "$python_version" =~ \(3,\ [8-9]\)||(3,\ 1[0-9]) ]]; then
    echo "Error: Python 3.8+ is required. Found: $python_version"
    exit 1
fi

# Set up environment variables
export P2RANK_INSTALL_DIR="$SCRIPT_DIR"
export P2RANK_CONFIG_DIR="${P2RANK_INSTALL_DIR}/config"
export P2RANK_MODELS_DIR="${P2RANK_INSTALL_DIR}/models"

# Run P2Rank with all arguments passed through
exec "$PYTHON_CMD" -m p2rank.program.main "$@" 