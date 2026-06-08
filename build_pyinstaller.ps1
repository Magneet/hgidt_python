$ProgressPreference = 'SilentlyContinue'
$Version = "1.0.0"

.\.venv\scripts\activate

pyinstaller.exe .\horizon_golden_image_deployment_tool.py `
    --noconsole `
    --collect-all PySide6 `
    --hiddenimport requests `
    --hiddenimport horizon_functions `
    --hiddenimport horizon_app `
    --hiddenimport keyring `
    --hiddenimport loguru `
    --name "Horizon Golden Image Deployment Tool" `
    --noconfirm `
    --icon=logo.ico `
    --clean `
    --add-data "logo.ico;."

deactivate

# Package as ZIP
Write-Host "`nPackaging ZIP..."
New-Item -ItemType Directory -Force -Path installer | Out-Null
$zipPath = "installer\Horizon_Golden_Image_Deployment_Tool_v${Version}_Windows.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath }
Compress-Archive -Path "dist\Horizon Golden Image Deployment Tool" -DestinationPath $zipPath
Write-Host "ZIP written to $zipPath"
