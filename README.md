# Diabetes Prediction System

A KivyMD-based desktop application for diabetes prediction and health assistance.

## Requirements

- Python 3.8 or higher
- OpenRouter API Key (for chatbot functionality)

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Option 1: Using Python directly

```bash
python main.py
```

### Option 2: Using Python module

```bash
python -m main
```

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up OpenRouter API Key (Optional for chatbot):**
   
   The application uses OpenRouter API for the chatbot feature. You can set it up in one of two ways:
   
   **Option A: Environment Variable (Recommended)**
   ```bash
   # On Windows (PowerShell)
   $env:OPENROUTER_API_KEY="your-api-key-here"
   
   # On Windows (Command Prompt)
   set OPENROUTER_API_KEY=your-api-key-here
   
   # On Linux/Mac
   export OPENROUTER_API_KEY=your-api-key-here
   ```
   
   **Option B: Hardcode (Not Recommended for Production)**
   - Edit `main.py` and replace the API key on line 758 (if needed)

3. **Run the application:**
   ```bash
   python main.py
   ```

## Features

- User authentication (Login/Signup)
- Diabetes symptom assessment
- AI-powered health chatbot
- Health data tracking
- Welcome screen with terms & conditions

## Deployment / Making the App Live

### Creating a Standalone Executable (Windows)

To create a standalone executable that users can run without installing Python:

1. **Install build dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Build the executable:**
   
   **On Windows:**
   ```bash
   build.bat
   ```
   
   **On Linux/Mac:**
   ```bash
   chmod +x build.sh
   ./build.sh
   ```
   
   **Or manually with PyInstaller:**
   ```bash
   pyinstaller build.spec
   ```

3. **Find your executable:**
   - The executable will be created in the `dist` folder
   - Windows: `dist\DiabetesPredictionApp.exe`
   - Linux/Mac: `dist/DiabetesPredictionApp`

4. **Distribute the application:**
   - Copy the entire `dist` folder contents, OR
   - Copy just the `.exe` file along with the `model_data` folder
   - Users can run the executable directly without Python installed

### Alternative: Cloud Deployment

If you want to deploy as a web application, you have these options:

1. **Convert to Kivy Web** (using KivyMD2Web or similar tools)
2. **Use Docker** to containerize the application
3. **Use cloud platforms** like:
   - Heroku (for web apps)
   - AWS EC2 / Google Cloud / Azure (for hosting)
   - GitHub Releases (for distributing executables)

### Distribution Options

1. **Direct Download:**
   - Upload the executable to Google Drive, Dropbox, or your website
   - Share the download link

2. **GitHub Releases:**
   - Create a GitHub repository
   - Use GitHub Releases to distribute the executable

3. **App Stores:**
   - Microsoft Store (Windows)
   - Mac App Store (macOS)
   - Requires app signing and store submission process

## Troubleshooting

### Build Issues
- **Import errors:** Make sure all dependencies are installed: `pip install -r requirements.txt`
- **PyInstaller errors:** Try: `pip install --upgrade pyinstaller`
- **Missing files:** Ensure all `.kv` files and `logo.png` are in the project root

### Runtime Issues
- **API errors:** Ensure your OpenRouter API key is set correctly
- **Window size issues:** The app is configured for mobile-like dimensions (360x640)
- **Missing model data:** Ensure `model_data` folder is included with the executable