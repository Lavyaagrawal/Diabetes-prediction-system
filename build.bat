@echo off
REM Build script for Diabetes Prediction System Windows Executable

echo ============================================
echo Building Diabetes Prediction System
echo ============================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building executable using PyInstaller...
pyinstaller build.spec

if errorlevel 1 (
    echo.
    echo Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Build completed successfully!
echo ============================================
echo.
echo Your executable is located in: dist\DiabetesPredictionApp.exe
echo.
echo You can now distribute the entire 'dist' folder or just the .exe file
echo (Note: Make sure to include the model_data folder with the .exe)
echo.
pause
