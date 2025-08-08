@echo off

rem
rem P2Rank Python Distribution Launcher
rem Windows startup script for P2Rank Python version
rem

setlocal enabledelayedexpansion

rem Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
rem Remove trailing backslash
if "%SCRIPT_DIR:~-1%"=="\" set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

rem Set Python path to include P2Rank modules
set "PYTHONPATH=%SCRIPT_DIR%;%PYTHONPATH%"

rem Default Python command (can be overridden with P2RANK_PYTHON env var)
if not defined P2RANK_PYTHON set "P2RANK_PYTHON=python"

rem Check if Python is available
where "%P2RANK_PYTHON%" >nul 2>nul
if errorlevel 1 (
    echo Error: Python not found. Please install Python 3.8+ or set P2RANK_PYTHON environment variable.
    echo Example: set P2RANK_PYTHON=C:\Python39\python.exe
    exit /b 1
)

rem Check Python version
for /f "tokens=*" %%i in ('"%P2RANK_PYTHON%" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set "python_version=%%i"

rem Simple version check (Python 3.8+)
if "%python_version:~0,2%" NEQ "3." (
    echo Error: Python 3.8+ is required. Found: Python %python_version%
    echo Please upgrade Python or set P2RANK_PYTHON to point to a newer version.
    exit /b 1
)

rem Extract minor version for more detailed check
for /f "tokens=2 delims=." %%a in ("%python_version%") do set "minor_version=%%a"
if %minor_version% LSS 8 (
    echo Error: Python 3.8+ is required. Found: Python %python_version%
    echo Please upgrade Python or set P2RANK_PYTHON to point to a newer version.
    exit /b 1
)

rem Check if required dependencies are installed
"%P2RANK_PYTHON%" -c "import numpy, scipy, sklearn" >nul 2>nul
if errorlevel 1 (
    echo Error: Required Python packages not found.
    echo Please install dependencies:
    echo   pip install -r requirements.txt
    echo or:
    echo   pip install numpy scipy scikit-learn pandas biopython
    exit /b 1
)

rem Set memory and performance options
set "PYTHONUNBUFFERED=1"
set "NUMBA_CACHE_DIR=%SCRIPT_DIR%\.numba_cache"

rem Create cache directory if it doesn't exist
if not exist "%NUMBA_CACHE_DIR%" mkdir "%NUMBA_CACHE_DIR%"

rem Set the install directory for the Python program
set "P2RANK_INSTALL_DIR=%SCRIPT_DIR%"

rem Show startup info in verbose mode
if "%1"=="-v" goto :show_info
if "%1"=="--verbose" goto :show_info
goto :run

:show_info
echo P2Rank Python Distribution
echo Python executable: %P2RANK_PYTHON%
echo Python version: %python_version%
echo Install directory: %SCRIPT_DIR%
echo Python path: %PYTHONPATH%
echo.

:run
rem Run the Python version of P2Rank
"%P2RANK_PYTHON%" "%SCRIPT_DIR%\p2rank_py.py" %* 