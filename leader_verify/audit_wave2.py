from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass


REQUIRED_TOOLS = {
    "godot_get_version",
    "godot_list_projects",
    "godot_launch_editor",
    "godot_run_project",
    "godot_stop_execution",
    "godot_get_debug_output",
    "godot_analyze_project",
    "scene_create",
    "scene_add_node",
    "scene_load_sprite",
    "scene_export_mesh_library",
    "scene_save",
    "uid_get",
    "uid_refresh_references",
    "render_capture",
    "render_interact",
}


@dataclass
class AuditReport:
    missing_from_server: list[str]
    missing_from_contracts: list[str]
    required_missing: list[str]
    server_only: list[str]
    contracts_only: list[str]

    @property
    def ok(self) -> bool:
        return not any(
            [
                self.missing_from_server,
                self.missing_from_contracts,
                self.required_missing,
            ]
        )


def build_report(server_tools: set[str], contract_tools: set[str]) -> AuditReport:
    missing_from_server = sorted(contract_tools - server_tools)
    missing_from_contracts = sorted(server_tools - contract_tools)
    required_missing = sorted(REQUIRED_TOOLS - server_tools)
    server_only = sorted(server_tools - REQUIRED_TOOLS)
    contracts_only = sorted(contract_tools - REQUIRED_TOOLS)
    return AuditReport(
        missing_from_server=missing_from_server,
        missing_from_contracts=missing_from_contracts,
        required_missing=required_missing,
        server_only=server_only,
        contracts_only=contracts_only,
    )


def collect_current_tool_sets() -> tuple[set[str], set[str]]:
    from mcp_server.stdio_server import StdioMCPServer
    from mcp_server.tool_contracts import TOOL_SCHEMAS

    server_tools = set(StdioMCPServer().tools.keys())
    contract_tools = set(TOOL_SCHEMAS.keys())
    return server_tools, contract_tools


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit MCP Wave 2 tool parity.")
    parser.add_argument("--json", action="store_true", help="Print report as JSON.")
    args = parser.parse_args()

    server_tools, contract_tools = collect_current_tool_sets()
    report = build_report(server_tools, contract_tools)

    payload = {"ok": report.ok, **asdict(report)}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Wave 2 parity audit")
        print(f"ok: {report.ok}")
        print(f"missing_from_server: {report.missing_from_server}")
        print(f"missing_from_contracts: {report.missing_from_contracts}")
        print(f"required_missing: {report.required_missing}")
        print(f"server_only: {report.server_only}")
        print(f"contracts_only: {report.contracts_only}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

