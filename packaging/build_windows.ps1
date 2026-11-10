# Build the Windows app and its installer (KD-packaging-pyinstaller, architecture section 7).
# Run from the repository root on 64-bit Windows, with requirements-build.txt installed in
# the active virtual environment and Inno Setup 6 installed. CI runs this same script.
#
# Output: dist\USPTO-Patent-Intelligence-<version>-x64-setup.exe
$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param([string] $Program, [string[]] $Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Program exited with code $LASTEXITCODE" }
}

$AppName = "USPTO Patent Intelligence"
$Version = (Select-String -Path "src/patent_intelligence/__init__.py" -Pattern '^__version__ = "([^"]+)"').Matches[0].Groups[1].Value
$AppFolder = "dist\$AppName"

# Inno Setup's compiler: on PATH, or in its default install folder.
$Iscc = (Get-Command iscc.exe -ErrorAction SilentlyContinue).Source
if (-not $Iscc) { $Iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" }
if (-not (Test-Path $Iscc)) { throw "Inno Setup 6 (ISCC.exe) was not found." }

Write-Host "== Building $AppName $Version"
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
Invoke-Checked pyinstaller @("--clean", "--noconfirm", "--distpath", "dist", "--workpath", "build", "packaging/patent-intelligence.spec")

Write-Host "== Starting the built app once"
Invoke-Checked python @("packaging/smoke_test.py", "$AppFolder\$AppName.exe")

Write-Host "== Making the installer"
Invoke-Checked $Iscc @("/Q", "/DAppVersion=$Version", "/DSourceDir=$((Resolve-Path $AppFolder).Path)", "packaging/windows-installer.iss")

Write-Host "== Done: dist\USPTO-Patent-Intelligence-$Version-x64-setup.exe"
