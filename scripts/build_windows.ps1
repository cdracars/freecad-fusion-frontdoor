$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

$WorkingTree = & git status --porcelain --untracked-files=all
if ($LASTEXITCODE -ne 0) { throw "Could not inspect the source revision." }
if ($WorkingTree) {
    throw "Commit or remove source changes before building so BUILD-INFO identifies the exact packaged revision."
}

if ($env:OS -ne "Windows_NT") {
    throw "The Windows package must be built on Windows."
}

$PythonVersion = & py -3.13 -c "import platform, sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} {platform.architecture()[0]}')"
if ($LASTEXITCODE -ne 0 -or $PythonVersion.Trim() -ne "3.13.17 64bit") {
    throw "Python 3.13.17 x64 is required for the pinned Windows package build. Install it for this Windows user, then retry."
}

$Venv = Join-Path $RepoRoot ".venv-windows-build"
if (-not (Test-Path (Join-Path $Venv "Scripts\python.exe"))) {
    & py -3.13 -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create the isolated package-build virtual environment." }
}
$Python = Join-Path $Venv "Scripts\python.exe"
$Deploy = Join-Path $Venv "Scripts\pyside6-deploy.exe"
$BuildPythonVersion = & $Python -c "import platform, sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} {platform.architecture()[0]}')"
if ($LASTEXITCODE -ne 0 -or $BuildPythonVersion.Trim() -ne "3.13.17 64bit") {
    throw "The existing build virtual environment does not use the required Python 3.13.17 x64. Remove only .venv-windows-build and rerun this script."
}
& $Python -m pip install --disable-pip-version-check --requirement "requirements\windows-build.txt"
if ($LASTEXITCODE -ne 0) { throw "Could not install the pinned Windows package-build requirements." }

& $Python "scripts\build_frontdoor_payload.py"
if ($LASTEXITCODE -ne 0) { throw "Could not prepare the Frontdoor workbench resource archive." }

$VsWhere = Join-Path ${env:ProgramFiles(x86)} "Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path $VsWhere)) {
    throw "Visual Studio Build Tools 2022 are required for pyside6-deploy (dumpbin). Install them, or use an already provisioned Windows build host."
}
$VsRoot = & $VsWhere -latest -products "*" -property installationPath
if ($LASTEXITCODE -ne 0 -or -not $VsRoot) { throw "Could not locate Visual Studio Build Tools." }
$VcVars = Join-Path $VsRoot "VC\Auxiliary\Build\vcvars64.bat"
if (-not (Test-Path $VcVars)) { throw "The Visual Studio x64 developer environment was not found: $VcVars" }

$BuildRoot = Join-Path $RepoRoot "build\windows"
$Ownership = Join-Path $BuildRoot ".frontdoor-build.json"
if (Test-Path $BuildRoot) {
    if (-not (Test-Path $Ownership)) {
        throw "Refusing to replace an unowned build directory: $BuildRoot"
    }
    $BuildRecord = Get-Content -Raw $Ownership | ConvertFrom-Json
    if ($BuildRecord.product -ne "FreeCAD Fusion Frontdoor Windows package") {
        throw "Refusing to replace a build directory owned by another product: $BuildRoot"
    }
    Remove-Item -LiteralPath $BuildRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $BuildRoot | Out-Null
@{ product = "FreeCAD Fusion Frontdoor Windows package" } |
    ConvertTo-Json | Set-Content -Encoding utf8 $Ownership

$env:PYTHONPATH = Join-Path $RepoRoot "src"
$VsEnvironment = & $env:ComSpec /d /c "call `"$VcVars`" >nul && set"
if ($LASTEXITCODE -ne 0) { throw "Could not activate the Visual Studio x64 build environment." }
foreach ($Line in $VsEnvironment) {
    $Separator = $Line.IndexOf("=")
    if ($Separator -gt 0) {
        $Name = $Line.Substring(0, $Separator)
        $Value = $Line.Substring($Separator + 1)
        [Environment]::SetEnvironmentVariable($Name, $Value, "Process")
    }
}

$env:PYTHONPATH = Join-Path $RepoRoot "src"
& $Deploy --force --no-install --no-warn --mode standalone "scripts\frontdoor_entry.py"
if ($LASTEXITCODE -ne 0) { throw "pyside6-deploy failed with exit code $LASTEXITCODE." }
if (-not (Test-Path "pysidedeploy.spec")) { throw "pyside6-deploy did not produce its deployment specification." }
Copy-Item -LiteralPath "pysidedeploy.spec" -Destination (Join-Path $BuildRoot "pysidedeploy.spec")

$AppFolders = @(Get-ChildItem -LiteralPath $BuildRoot -Directory -Filter "*.dist")
if ($AppFolders.Count -ne 1) {
    throw "Expected exactly one standalone .dist folder in $BuildRoot; found $($AppFolders.Count)."
}
$AppExe = Get-ChildItem -LiteralPath $AppFolders[0].FullName -Filter "*.exe" -File -Recurse |
    Where-Object { $_.BaseName -eq "frontdoor_entry" } | Select-Object -First 1
if (-not $AppExe) { throw "The standalone Frontdoor executable was not found in $($AppFolders[0].FullName)." }

$Version = (& $Python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])").Trim()
$Revision = (& git rev-parse --short HEAD).Trim()
$Stage = Join-Path $BuildRoot "candidate"
New-Item -ItemType Directory -Path $Stage | Out-Null
$StagedApp = Join-Path $Stage $AppFolders[0].Name
Copy-Item -LiteralPath $AppFolders[0].FullName -Destination $StagedApp -Recurse
Copy-Item -LiteralPath "docs\portable-windows-preview.txt" -Destination (Join-Path $Stage "README.txt")
Copy-Item -LiteralPath "LICENSE" -Destination (Join-Path $Stage "LICENSE.txt")
Copy-Item -LiteralPath "THIRD_PARTY_NOTICES.md" -Destination (Join-Path $Stage "THIRD_PARTY_NOTICES.txt")
@(
    "Product: FreeCAD Fusion Frontdoor"
    "Version: $Version"
    "Source revision: $Revision"
    "Python build version: $PythonVersion"
    "PySide6: 6.12.0"
    "Nuitka: 4.3.4"
    "ordered-set: 4.1.0"
    "zstandard: 0.25.0"
    "Signing: unsigned review candidate"
) | Set-Content -Encoding utf8 (Join-Path $Stage "BUILD-INFO.txt")

$Dist = Join-Path $RepoRoot "dist"
New-Item -ItemType Directory -Path $Dist -Force | Out-Null
$Archive = Join-Path $Dist "FreeCAD-Fusion-Frontdoor-$Version-windows-x64-$Revision.zip"
if ((Test-Path -LiteralPath $Archive) -or (Test-Path -LiteralPath "$Archive.sha256")) {
    throw "Refusing to overwrite an existing candidate: $Archive"
}
Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $Archive -CompressionLevel Optimal
$Hash = (Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash.ToLowerInvariant()
Set-Content -Encoding ascii -NoNewline -Path "$Archive.sha256" -Value "$Hash  $(Split-Path -Leaf $Archive)"

Write-Host "Unsigned candidate: $Archive"
Write-Host "SHA-256: $Hash"
