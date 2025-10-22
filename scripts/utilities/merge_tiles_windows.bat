@echo off
echo ========================================
echo Universal Raster Tile Merger for Windows
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

REM Check if rasterio is installed
python -c "import rasterio" >nul 2>&1
if errorlevel 1 (
    echo rasterio is not installed. Installing now...
    pip install rasterio
    if errorlevel 1 (
        echo.
        echo Failed to install rasterio. Try running:
        echo   pip install rasterio
        echo or
        echo   conda install -c conda-forge rasterio
        pause
        exit /b 1
    )
)

REM Get the directory path
set /p "input_dir=Enter the path to folder containing tiles (or drag folder here): "

REM Remove quotes if present
set input_dir=%input_dir:"=%

REM Check if directory exists
if not exist "%input_dir%" (
    echo ERROR: Directory does not exist: %input_dir%
    pause
    exit /b 1
)

echo.
echo Processing tiles in: %input_dir%
echo.

REM Run the merge script
python merge_raster_tiles.py "%input_dir%"

echo.
echo ========================================
echo Process complete! Check the 'merged' folder
echo ========================================
pause