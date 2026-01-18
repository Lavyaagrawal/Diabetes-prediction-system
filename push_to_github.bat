@echo off
REM Script to push to GitHub and create a release

echo ============================================
echo Push to GitHub Repository
echo ============================================
echo.

REM Check if remote exists
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo No remote repository configured.
    echo.
    echo Please provide your GitHub repository URL:
    echo Example: https://github.com/username/repo-name.git
    echo.
    set /p REPO_URL="Enter your GitHub repository URL: "
    
    if "%REPO_URL%"=="" (
        echo Error: Repository URL is required!
        pause
        exit /b 1
    )
    
    git remote add origin %REPO_URL%
    echo.
    echo Remote repository added: %REPO_URL%
    echo.
)

REM Show current remote
echo Current remote repository:
git remote -v
echo.

REM Push to GitHub
echo Pushing to GitHub...
git branch -M main
git push -u origin main

if errorlevel 1 (
    echo.
    echo Push failed! Please check:
    echo 1. Your GitHub repository URL is correct
    echo 2. You have access to the repository
    echo 3. You're authenticated (use: git config --global user.name "Your Name")
    echo 4. You're authenticated (use: git config --global user.email "your.email@example.com")
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Successfully pushed to GitHub!
echo ============================================
echo.
echo Next steps to create a release:
echo 1. Go to your GitHub repository
echo 2. Click on "Releases" in the right sidebar
echo 3. Click "Create a new release"
echo 4. Choose a tag (e.g., v1.0.0)
echo 5. Add release title and description
echo 6. Upload dist\DiabetesPredictionApp.exe as a release asset
echo 7. Click "Publish release"
echo.
pause
