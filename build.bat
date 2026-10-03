@echo off
rem Build dist\AlgorithmStudy.exe with PyInstaller (Windows).
rem Usage: double-click build.bat, or run it from a terminal in the project folder.
setlocal
cd /d "%~dp0"

echo.
echo === Algorithm Study - Windows build ===
echo.

rem 1. Python environment: use .venv if it exists, otherwise create it.
set "PY=.venv\Scripts\python.exe"
if exist "%PY%" goto :have_venv
echo Creating a virtual environment in .venv ...
where py >nul 2>nul
if errorlevel 1 (
    python -m venv .venv
) else (
    py -3 -m venv .venv
)
if not exist "%PY%" (
    echo ERROR: could not create .venv. Install Python 3.10 or newer from python.org and try again.
    goto :fail
)
:have_venv
"%PY%" --version
if errorlevel 1 goto :fail

rem 2. Dependencies: install them only if something is missing.
"%PY%" -c "import flask, sympy, waitress, dotenv, PyInstaller" >nul 2>nul
if errorlevel 1 (
    echo Installing build dependencies from requirements-build.txt ...
    "%PY%" -m pip install --disable-pip-version-check -r requirements-build.txt
    if errorlevel 1 goto :fail
)
"%PY%" -c "import flask, sympy, waitress, dotenv, PyInstaller; print('Dependencies OK - PyInstaller', PyInstaller.__version__)"
if errorlevel 1 goto :fail

rem 3. Clean previous build output.
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

rem 4. Build.
echo.
echo Building - this takes a minute or two ...
"%PY%" -m PyInstaller --noconfirm --clean AlgorithmStudy.spec
if errorlevel 1 goto :fail
if not exist "dist\AlgorithmStudy.exe" (
    echo ERROR: PyInstaller finished but dist\AlgorithmStudy.exe was not created.
    goto :fail
)

rem 5. Report.
echo.
echo === Build succeeded ===
echo Executable: %CD%\dist\AlgorithmStudy.exe
echo Double-click it to start the app. Your progress is stored in %LOCALAPPDATA%\AlgorithmStudy
echo.
if not defined CI pause
exit /b 0

:fail
echo.
echo === Build FAILED (see the messages above) ===
if not defined CI pause
exit /b 1
