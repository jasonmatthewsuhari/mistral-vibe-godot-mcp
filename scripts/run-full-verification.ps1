param(
    [switch]$IncludeIntegration
)

$ErrorActionPreference = "Stop"

function Step([string]$name, [string]$cmd) {
    Write-Host ""
    Write-Host "== $name ==" -ForegroundColor Cyan
    Write-Host $cmd
    powershell -NoProfile -Command $cmd
}

Step "Pytest" "python -m pytest -q"
Step "Wave2 parity audit" "python -m leader_verify.audit_wave2 --json"
Step "Stdio smoke" "python -m leader_verify.smoke_stdio"

if ($IncludeIntegration) {
    Step "Product integration tests (opt-in marker)" "python -m pytest -q tests_integration -m godot_integration"
    Step "Leader integration harness tests" "python -m unittest discover -s leader_integration_tests -v"
}

Write-Host ""
Write-Host "Verification completed." -ForegroundColor Green
