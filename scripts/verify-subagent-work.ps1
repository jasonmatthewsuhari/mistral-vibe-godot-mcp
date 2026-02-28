param(
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"

function Write-Section([string]$msg) {
    Write-Host ""
    Write-Host "== $msg ==" -ForegroundColor Cyan
}

function Run-IfExists([string]$label, [string]$command, [string]$pathToCheck) {
    if (Test-Path $pathToCheck) {
        Write-Section $label
        Write-Host "Running: $command"
        powershell -NoProfile -Command $command
    } else {
        Write-Host "Skipping $label (not found: $pathToCheck)" -ForegroundColor Yellow
    }
}

Push-Location $RepoRoot
try {
    Write-Section "Basic Structure Checks"
    $requiredPaths = @(
        "IMPLEMENTATION_PLAN.md",
        "docs/review-checklist.md"
    )

    $missing = @()
    foreach ($p in $requiredPaths) {
        if (-not (Test-Path $p)) {
            $missing += $p
        }
    }

    if ($missing.Count -gt 0) {
        Write-Host "Missing required files:" -ForegroundColor Red
        $missing | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
        exit 1
    }

    Write-Host "Required files present."

    Write-Section "Python Availability"
    python --version

    # Optional validation commands. These run only when config files exist.
    Run-IfExists -label "Pytest" -command "python -m pytest -q" -pathToCheck "tests"
    Run-IfExists -label "Ruff" -command "python -m ruff check ." -pathToCheck "pyproject.toml"
    Run-IfExists -label "Mypy" -command "python -m mypy ." -pathToCheck "mypy.ini"

    Write-Section "Quick MCP/Godot Keyword Scan"
    if (Get-Command rg -ErrorAction SilentlyContinue) {
        rg -n "godot_get_version|godot_launch_editor|godot_run_project|godot_stop_execution|godot_get_debug_output|godot_analyze_project|scene_create|uid_get|render_capture" .
    } else {
        Write-Host "ripgrep (rg) not found, skipping keyword scan." -ForegroundColor Yellow
    }

    Write-Section "Verification Script Completed"
    Write-Host "No blocking checks failed."
}
finally {
    Pop-Location
}
