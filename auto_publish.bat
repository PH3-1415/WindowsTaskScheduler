@echo off
echo ========================================
echo Windows Task Scheduler - Final Fixed Tool
echo ========================================
echo.
echo Press any key to start...
pause >nul

echo.
echo Step 1: Checking Git...
git --version
if errorlevel 1 (
    echo ERROR: Git not found!
    pause
    exit /b 1
)
echo OK: Git found
echo.
pause

echo.
echo Step 2: Checking current directory...
cd
echo Current directory: %cd%
echo.
pause

echo.
echo Step 3: Checking files...
if not exist main.py (
    echo ERROR: main.py not found!
    pause
    exit /b 1
)
echo OK: main.py found
echo.
pause

echo.
echo Step 4: Cleaning and reinitializing Git...
if exist .git (
    echo Removing old Git repository...
    rmdir /s /q .git
)
echo Initializing new Git repository...
git init
echo OK: Git initialized
echo.
pause

echo.
echo Step 5: Configuring Git user info...
echo.
echo IMPORTANT: Git needs your name and email for commits
echo.
echo Enter your name (anything is fine, e.g., "Your Name"):
set /p GIT_NAME="Name: "
echo.
echo Enter your email (anything is fine, e.g., "your@email.com"):
set /p GIT_EMAIL="Email: "
echo.
git config user.name "%GIT_NAME%"
git config user.email "%GIT_EMAIL%"
echo OK: Git configured
git config user.name
git config user.email
echo.
pause

echo.
echo Step 6: Adding all files...
git add -A
echo OK: Files added
echo.
pause

echo.
echo Step 7: Committing...
git commit -m "Initial commit: Windows Task Scheduler v1.0.0"
if errorlevel 1 (
    echo ERROR: git commit failed
    echo Showing git status:
    git status
    pause
    exit /b 1
)
echo OK: Commit successful
echo.
pause

echo.
echo Step 8: Setting branch to main...
git branch -M main
echo OK: Branch set to main
echo.
pause

echo.
echo Step 9: Setting up GitHub...
echo.
echo IMPORTANT: Create repository first!
echo 1. Visit: https://github.com/new
echo 2. Repository name: WindowsTaskScheduler
echo 3. Do NOT check "Add a README file"
echo 4. Click "Create repository"
echo.
echo Press any key after creating the repository...
pause >nul
echo.
echo Enter your GitHub username:
set /p GITHUB_USER="Username: "
echo.
echo Your username: %GITHUB_USER%
echo.
pause

echo.
echo Step 10: Adding remote...
git remote remove origin 2>nul
git remote add origin https://github.com/%GITHUB_USER%/WindowsTaskScheduler.git
echo OK: Remote added
echo.
pause

echo.
echo Step 11: Checking status...
git status
echo.
pause

echo.
echo Step 12: Pushing to GitHub...
echo.
echo ========================================
echo AUTHENTICATION INFO
echo ========================================
echo.
echo You will be asked for:
echo 1. Username: Enter your GitHub username
echo 2. Password: Use Personal Access Token (NOT your GitHub password!)
echo.
echo How to create token:
echo 1. Visit: https://github.com/settings/tokens/new
echo 2. Note: "Windows Task Scheduler"
echo 3. Expiration: No expiration
echo 4. Select scopes: Check "repo" (full control)
echo 5. Click "Generate token"
echo 6. Copy the token (you won't see it again!)
echo 7. Use this token as password
echo.
echo ========================================
echo.
pause
git push -u origin main
if errorlevel 1 (
    echo.
    echo ========================================
    echo ERROR: Push failed!
    echo ========================================
    echo.
    echo Common issues:
    echo 1. Repository not created: https://github.com/new
    echo 2. Use Personal Access Token as password
    echo 3. Check username is correct
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS!
echo ========================================
echo.
echo Code pushed to GitHub successfully!
echo.
echo Next steps:
echo 1. Wait 5-10 minutes for build to complete
echo 2. Visit: https://github.com/%GITHUB_USER%/WindowsTaskScheduler/actions
echo 3. Download EXE from: https://github.com/%GITHUB_USER%/WindowsTaskScheduler/releases
echo.
pause