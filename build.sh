#!/bin/bash
# Build script for Diabetes Prediction System (Linux/Mac)

echo "============================================"
echo "Building Diabetes Prediction System"
echo "============================================"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

echo ""
echo "Cleaning previous builds..."
rm -rf build dist

echo ""
echo "Building executable using PyInstaller..."
pyinstaller build.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "Build failed! Check the error messages above."
    exit 1
fi

echo ""
echo "============================================"
echo "Build completed successfully!"
echo "============================================"
echo ""
echo "Your executable is located in: dist/"
echo ""
echo "You can now distribute the executable from the dist folder"
echo ""
