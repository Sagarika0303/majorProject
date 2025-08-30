@echo off
:: Batch file to add a dependency, commit, and push

if "%~1"=="" (
    echo ⚠️  Please provide a dependency name. Example:
    echo     add_dep.bat matplotlib
    exit /b 1
)

set dep=%~1

:: Step 1: Append dependency to root requirements.txt
echo %dep%>> requirements.txt

:: Step 2: Add file to git
git add requirements.txt

:: Step 3: Commit with dependency name
git commit -m "Added dependency: %dep%"

:: Step 4: Push to main branch
git push origin main

echo.
echo ✅ Dependency "%dep%" added, committed, and pushed successfully!
pause
