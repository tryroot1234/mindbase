# mindbase installer for Windows
# Usage: iwr -useb https://raw.githubusercontent.com/tryroot1234/mindbase/main/install.ps1 | iex

$ErrorActionPreference = "Continue"

Write-Host "Installing mindbase..." -ForegroundColor Cyan

# Check Python version
function Get-Python {
    $commands = @("python3", "python", "py -3")
    foreach ($cmd in $commands) {
        try {
            $version = & $cmd --version 2>&1 | Out-String
            if ($version -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                if ($major -ge 3 -and $minor -ge 10) {
                    return $cmd
                }
            }
        } catch {
            continue
        }
    }
    return $null
}

$python = Get-Python
if (-not $python) {
    Write-Host "Error: Python 3.10+ is required but not found." -ForegroundColor Red
    Write-Host "Please install Python 3.10 or later from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "Using Python: $python" -ForegroundColor Green

# Install via pip
Write-Host ""
Write-Host "Installing mindbase with pip..." -ForegroundColor Cyan
& $python -m pip install --user --upgrade pip 2>&1 | Out-Null
& $python -m pip install --user "git+https://github.com/tryroot1234/mindbase.git"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Installation failed." -ForegroundColor Red
    exit 1
}

# Check if Scripts directory is in PATH
$scriptsDir = & $python -c "import site; print(site.USER_BASE + '\\Scripts')" 2>&1 | Out-String
$scriptsDir = $scriptsDir.Trim()
if ($scriptsDir -and $env:PATH -notlike "*$scriptsDir*") {
    Write-Host ""
    Write-Host "NOTE: Add the following to your PATH:" -ForegroundColor Yellow
    Write-Host "  $scriptsDir" -ForegroundColor White
    Write-Host ""
    Write-Host "Run this to add it permanently:" -ForegroundColor Yellow
    Write-Host "  [Environment]::SetEnvironmentVariable('Path', `$env:PATH + ';$scriptsDir', 'User')" -ForegroundColor White
}

Write-Host ""
Write-Host "mindbase installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Usage:" -ForegroundColor Cyan
Write-Host '  mindbase add "My Note" -c "Hello world" -t test'
Write-Host '  mindbase list'
Write-Host '  mindbase search "keyword"'
Write-Host ""
Write-Host "For more information, run: mindbase --help" -ForegroundColor Cyan
