param(
    [string]$PythonExe = "python"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Mask-Token([string]$TokenValue) {
    if ([string]::IsNullOrWhiteSpace($TokenValue)) {
        return "(unset)"
    }
    if ($TokenValue.Length -le 4) {
        return ("*" * $TokenValue.Length)
    }
    return ("*" * ($TokenValue.Length - 4)) + $TokenValue.Substring($TokenValue.Length - 4)
}

Write-Output "== Release Diagnostics =="
Write-Output "Python:"
& $PythonExe --version

$godotPath = $env:GODOT_PATH
if ([string]::IsNullOrWhiteSpace($godotPath)) {
    Write-Output "GODOT_PATH: (unset)"
}
else {
    Write-Output "GODOT_PATH: $godotPath"
}

$bridgeUrl = $env:GODOT_BRIDGE_URL
if ([string]::IsNullOrWhiteSpace($bridgeUrl)) {
    $bridgeUrl = "http://127.0.0.1:19110 (default)"
}
Write-Output "GODOT_BRIDGE_URL: $bridgeUrl"
Write-Output "GODOT_BRIDGE_TOKEN: $(Mask-Token -TokenValue $env:GODOT_BRIDGE_TOKEN)"

$probeScript = @'
import json
import subprocess
import sys

def send(proc, payload):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    proc.stdin.write(header + body)
    proc.stdin.flush()

def recv(proc):
    headers = {}
    while True:
        line = proc.stdout.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, _, value = line.decode("utf-8").partition(":")
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = proc.stdout.read(length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))

proc = subprocess.Popen(
    [sys.executable, "-m", "mcp_server"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
result = {"initialize": None, "tools_list": None, "stderr": ""}
try:
    send(proc, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "release-diagnostics", "version": "1.0.0"}
        }
    })
    result["initialize"] = recv(proc)

    send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    result["tools_list"] = recv(proc)
finally:
    try:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=3)
    except Exception:
        proc.kill()
    result["stderr"] = proc.stderr.read().decode("utf-8", errors="replace")

print(json.dumps(result))
'@

$tmpProbe = Join-Path $env:TEMP "mcp_release_diagnostics_probe.py"
Set-Content -Path $tmpProbe -Value $probeScript -Encoding UTF8
try {
    $probeRaw = & $PythonExe $tmpProbe
}
finally {
    Remove-Item -Force $tmpProbe -ErrorAction SilentlyContinue
}
$probe = $probeRaw | ConvertFrom-Json

Write-Output "MCP Tools:"
$toolNames = @()
if ($null -ne $probe.tools_list -and $null -ne $probe.tools_list.result -and $null -ne $probe.tools_list.result.tools) {
    $toolNames = @($probe.tools_list.result.tools | ForEach-Object { $_.name })
}
if ($toolNames.Count -eq 0) {
    Write-Output "- (none or unavailable)"
}
else {
    foreach ($toolName in $toolNames) {
        Write-Output "- $toolName"
    }
}

if ([string]::IsNullOrWhiteSpace($probe.stderr) -eq $false) {
    Write-Output "MCP Server stderr:"
    Write-Output $probe.stderr.Trim()
}
