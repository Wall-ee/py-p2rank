#!/usr/bin/env bash

#
# Creates binary distribution package for P2Rank Python implementation
#

set -e

echo "Building P2Rank Python distribution..."

# Get version from setup.py
VERSION=$(python3 -c "import setup; print(setup.setup.__dict__.get('version', '1.0.0'))" 2>/dev/null || echo "1.0.0")
DIRNAME="p2rank-python_${VERSION}"

# Clean previous builds
rm -rf build dist *.egg-info

# Create build directory
mkdir -p build

# Build wheel
echo "Building Python wheel..."
python3 -m build

# Create distribution directory
DISTRO_DIR="build/${DIRNAME}"
mkdir -p "$DISTRO_DIR"

# Copy package files
echo "Copying package files..."
cp -r p2rank "$DISTRO_DIR/"
cp -r config "$DISTRO_DIR/"
cp -r tests "$DISTRO_DIR/"
cp requirements.txt "$DISTRO_DIR/"
cp setup.py "$DISTRO_DIR/"
cp README.md "$DISTRO_DIR/"
cp p2rank_py.sh "$DISTRO_DIR/"

# Make launcher executable
chmod +x "$DISTRO_DIR/p2rank_py.sh"

# Create models directory (placeholder)
mkdir -p "$DISTRO_DIR/models"
echo "# Place trained models here" > "$DISTRO_DIR/models/README.md"

# Create test data directory (placeholder)
mkdir -p "$DISTRO_DIR/test_data"
echo "# Place test data files here" > "$DISTRO_DIR/test_data/README.md"

# Create tarball
cd build
echo "Creating distribution archive..."
tar czf "${DIRNAME}.tar.gz" "$DIRNAME"
cd ..

echo
echo "Distribution created: build/${DIRNAME}.tar.gz"
echo
echo "To install:"
echo "  tar xzf build/${DIRNAME}.tar.gz"
echo "  cd ${DIRNAME}"
echo "  pip install -r requirements.txt"
echo "  pip install -e ."
echo
echo "To run:"
echo "  ./p2rank_py.sh predict -i protein.pdb"
echo
echo "DONE" 