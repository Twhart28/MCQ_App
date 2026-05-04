param(
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Icon = Join-Path $Root "assets\mcq_tester_icon.ico"
$App = Join-Path $Root "mcq_qt_app.py"
$DistApp = Join-Path $Root "dist\MCQ Tester"
$ZipPath = Join-Path $Root "dist\MCQ_Tester_v$Version`_windows.zip"
$InstallerScript = Join-Path $Root "installer\MCQTester.iss"

if (-not (Test-Path $Python)) {
    throw "Missing venv Python at $Python"
}

& $Python -m pip install -r (Join-Path $Root "requirements.txt")

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --name "MCQ Tester" `
    --windowed `
    --icon $Icon `
    --add-data "$Root\assets;assets" `
    $App

if (Test-Path $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
Compress-Archive -Path "$DistApp\*" -DestinationPath $ZipPath -CompressionLevel Optimal

$Iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if ($Iscc) {
    $IsccPath = $Iscc.Source
} else {
    $CommonPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if (Test-Path $CommonPath) {
        $IsccPath = $CommonPath
    }
}
if (-not $IsccPath) {
    throw "Inno Setup compiler not found. Install Inno Setup 6 or add ISCC.exe to PATH."
}

& $IsccPath "/DMyAppVersion=$Version" $InstallerScript

Write-Host "Built release artifacts:"
Write-Host "  $ZipPath"
Write-Host "  $(Join-Path $Root "dist\installer\MCQ_Tester_Setup_v$Version.exe")"
