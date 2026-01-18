# GitHub Release Guide

## Step 1: Push to GitHub

Run the script to push your code:
```bash
push_to_github.bat
```

Or manually:
```bash
# Add your GitHub repository as remote (replace with your URL)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 2: Create a Release on GitHub

### Option A: Using GitHub Web Interface (Recommended)

1. **Go to your repository** on GitHub
   - Navigate to: `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME`

2. **Click on "Releases"**
   - Located on the right sidebar, or go to: `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/releases`

3. **Click "Create a new release"**
   - Or "Draft a new release"

4. **Fill in release details:**
   - **Tag version:** `v1.0.0` (or your version number)
   - **Release title:** `Diabetes Prediction System v1.0.0`
   - **Description:** 
     ```
     ## First Release 🎉
     
     ### Features
     - User authentication (Login/Signup)
     - Diabetes symptom assessment
     - AI-powered health chatbot
     - Health data tracking
     - Standalone Windows executable
     
     ### Installation
     1. Download `DiabetesPredictionApp.exe` from the assets below
     2. Run the executable (no Python installation required)
     3. Sign up or login to start using the application
     
     ### Requirements
     - Windows 10/11
     - OpenRouter API Key (optional, for chatbot features)
     ```

5. **Upload the executable:**
   - Scroll down to "Attach binaries"
   - Drag and drop `dist\DiabetesPredictionApp.exe`
   - Or click "selecting them" and browse to `dist\DiabetesPredictionApp.exe`

6. **Click "Publish release"**

### Option B: Using GitHub CLI

If you have GitHub CLI installed:

```bash
# Install GitHub CLI if needed: winget install GitHub.cli

# Create release with executable
gh release create v1.0.0 dist\DiabetesPredictionApp.exe \
  --title "Diabetes Prediction System v1.0.0" \
  --notes "First release with standalone Windows executable"
```

## Step 3: Share Your Release

After publishing, you can share:
- **Release URL:** `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/releases/tag/v1.0.0`
- **Direct download:** Users can download the `.exe` file directly from the release page

## Release Notes Template

```markdown
## 🎉 Diabetes Prediction System v1.0.0

### ✨ Features
- **User Authentication:** Secure login and signup with password recovery
- **Symptom Assessment:** AI-powered diabetes risk prediction
- **Health Chatbot:** Interactive AI assistant for diabetes information
- **Health Tracking:** Monitor and track your health data
- **Standalone Application:** No Python installation required

### 📦 Installation
1. Download `DiabetesPredictionApp.exe` from the assets below
2. Double-click to run (Windows 10/11)
3. Create an account or login
4. Start using the application!

### 🔧 Requirements
- Windows 10 or Windows 11
- Internet connection (for chatbot features)
- OpenRouter API Key (optional, for full chatbot functionality)

### 🐛 Known Issues
- None at this time

### 📝 Notes
- The application stores user data locally
- Chatbot requires OpenRouter API key for full functionality
- All health predictions are for informational purposes only

### 🙏 Thank You
Thank you for using Diabetes Prediction System!
```

## Future Releases

For future updates:
1. Make your changes
2. Commit: `git commit -m "Description of changes"`
3. Push: `git push`
4. Create new release with incremented version (v1.1.0, v1.2.0, etc.)
5. Upload new executable
