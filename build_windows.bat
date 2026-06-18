@echo off
REM Build the Horizon Golden Image Deployment Tool .exe for Windows.
REM Run from the project root directory.

SET VENV=.venv
SET SPEC=Horizon Golden Image Deployment Tool-windows.spec
SET DIST=dist
SET VERSION=1.0.0

echo === Horizon Golden Image Deployment Tool - Windows build ===

REM Create venv if it doesn't exist
IF NOT EXIST "%VENV%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv %VENV%
)

echo Installing / upgrading dependencies...
%VENV%\Scripts\pip.exe install --upgrade pip --quiet
%VENV%\Scripts\pip.exe install -r requirements.txt --quiet
%VENV%\Scripts\pip.exe install pyinstaller --quiet

echo Running PyInstaller...
%VENV%\Scripts\pyinstaller.exe "%SPEC%" --clean --noconfirm

echo.
echo Build complete. Output: %DIST%\Horizon Golden Image Deployment Tool\

echo Packaging ZIP...
IF NOT EXIST installer mkdir installer
SET ZIP=installer\Horizon_Golden_Image_Deployment_Tool_v%VERSION%_Windows.zip
IF EXIST "%ZIP%" DEL "%ZIP%"
powershell -NoProfile -Command "Compress-Archive -Path '%DIST%\Horizon Golden Image Deployment Tool' -DestinationPath '%ZIP%'"
echo ZIP written to %ZIP%

echo.
echo To run:  %DIST%\Horizon Golden Image Deployment Tool\Horizon Golden Image Deployment Tool.exe
pause