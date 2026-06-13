#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$ProjectPath = "",
    [switch]$SkipInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectPath)) {
    if ($PSScriptRoot) { $ProjectPath = $PSScriptRoot } else { $ProjectPath = (Get-Location).Path }
}
$Root = (Resolve-Path $ProjectPath).Path
Set-Location $Root

function Find-Python310Plus {
    $candidates = @(
        @{ Exe = "py"; Args = @("-3") },
        @{ Exe = "python"; Args = @() },
        @{ Exe = "python3"; Args = @() }
    )
    foreach ($candidate in $candidates) {
        $exe = [string]$candidate.Exe
        $prefixArgs = [string[]]$candidate.Args
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) { continue }
        $args = @()
        $args += $prefixArgs
        $args += @("-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)")
        & $exe @args *> $null
        if ($LASTEXITCODE -eq 0) { return @{ Exe = $exe; Args = $prefixArgs } }
    }
    return $null
}

$pythonInfo = Find-Python310Plus
if (-not $pythonInfo) { throw "Python 3.10+ was not found." }

$pythonExe = [string]$pythonInfo.Exe
$pythonPrefixArgs = [string[]]$pythonInfo.Args
$venvDir = Join-Path $Root ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    $venvArgs = @()
    $venvArgs += $pythonPrefixArgs
    $venvArgs += @("-m", "venv", $venvDir)
    & $pythonExe @venvArgs
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment." }
}

if (-not $SkipInstall) {
    & $venvPython -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed." }
    & $venvPython -m pip install -e ((Join-Path $Root "local-llm-document-qa-rag") + "[dev]")
    if ($LASTEXITCODE -ne 0) { throw "Failed installing local RAG project." }
    & $venvPython -m pip install -e ((Join-Path $Root "ml-model-deployment-pipeline") + "[dev]")
    if ($LASTEXITCODE -ne 0) { throw "Failed installing ML deployment project." }
    & $venvPython -m pip install -e ((Join-Path $Root "real-time-security-log-detection-pipeline") + "[dev]")
    if ($LASTEXITCODE -ne 0) { throw "Failed installing security pipeline project." }
}

Write-Host "`n[1/3] Local RAG tests" -ForegroundColor Cyan
Push-Location (Join-Path $Root "local-llm-document-qa-rag")
& $venvPython -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) { throw "Local RAG tests failed." }
Pop-Location

Write-Host "`n[2/3] ML deployment tests" -ForegroundColor Cyan
Push-Location (Join-Path $Root "ml-model-deployment-pipeline")
& $venvPython -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "ML deployment tests failed." }
Pop-Location

Write-Host "`n[3/3] Security pipeline tests" -ForegroundColor Cyan
Push-Location (Join-Path $Root "real-time-security-log-detection-pipeline")
& $venvPython -m unittest discover -s tests
if ($LASTEXITCODE -ne 0) { throw "Security pipeline tests failed." }
Pop-Location

Write-Host "`nAll project tests completed successfully." -ForegroundColor Green
