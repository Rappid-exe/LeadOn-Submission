@echo off
echo ========================================
echo LeadOn CRM - Clean Submission Push
echo ========================================
echo.
echo This will create a fresh git repository without history
echo to avoid pushing any secrets that were in previous commits.
echo.
pause

echo.
echo Step 1: Removing old git history...
if exist .git (
    rmdir /s /q .git
    echo   Done: Removed .git folder
) else (
    echo   Skipped: No .git folder found
)

echo.
echo Step 2: Initializing fresh repository...
git init
echo   Done: Initialized new git repository

echo.
echo Step 3: Adding remote...
git remote add origin https://github.com/Rappid-exe/LeadOn-Submission.git
echo   Done: Added remote origin

echo.
echo Step 4: Adding files (respecting .gitignore)...
git add .
echo   Done: Staged files

echo.
echo Step 5: Creating initial commit...
git commit -m "Initial commit - LeadOn CRM hackathon submission"
echo   Done: Created commit

echo.
echo Step 6: Renaming branch to main...
git branch -M main
echo   Done: Branch renamed to main

echo.
echo Step 7: Pushing to GitHub...
echo   This will FORCE PUSH to overwrite any existing content
echo.
pause

git push -u origin main --force

echo.
echo ========================================
echo Push Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Visit: https://github.com/Rappid-exe/LeadOn-Submission
echo 2. Verify no sensitive files are visible
echo 3. Check that README.md displays correctly
echo 4. Review the submission checklist
echo.
pause
