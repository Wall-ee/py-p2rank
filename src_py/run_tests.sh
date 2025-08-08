#!/usr/bin/env bash

#
# Run test suite for P2Rank Python implementation
#

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Running P2Rank Python test suite..."

# Set Python path
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Run different types of tests
echo
echo "=== Running unit tests ==="
python3 -m pytest tests/ -v

echo
echo "=== Running integration tests ==="
python3 -m unittest discover -s tests -p "test_*.py" -v

echo
echo "=== Testing CLI interface ==="
python3 -m p2rank.program.main help

echo
echo "=== Testing version info ==="
python3 -m p2rank.program.main version

echo
echo "All tests completed successfully!" 