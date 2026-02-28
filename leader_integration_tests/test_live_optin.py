from __future__ import annotations

import os
from pathlib import Path
import unittest

from leader_integration.stdio_client import MCPStdioClient


def _enabled() -> bool:
    return os.getenv("ENABLE_LEADER_GODOT_INTEGRATION", "0") == "1"


@unittest.skipUnless(_enabled(), "Set ENABLE_LEADER_GODOT_INTEGRATION=1 to run live Godot integration tests.")
class LiveGodotOptInTests(unittest.TestCase):
    def test_core_live_calls(self) -> None:
        fixture_project = (
            Path(__file__).resolve().parents[1]
            / "leader_integration"
            / "fixtures"
            / "minimal_project"
        )
        client = MCPStdioClient.start()
        try:
            _ = client.initialize()
            version = client.call_tool("godot_get_version", {}, req_id=10)
            self.assertIn("result", version)

            projects = client.call_tool(
                "godot_list_projects",
                {"root_path": str(fixture_project.parent)},
                req_id=11,
            )
            self.assertIn("result", projects)
            structured = projects["result"]["structuredContent"]
            self.assertTrue(structured["projects"])

            analysis = client.call_tool(
                "godot_analyze_project",
                {"project_path": str(fixture_project)},
                req_id=12,
            )
            self.assertIn("result", analysis)
            a = analysis["result"]["structuredContent"]
            self.assertIn("scenes/main.tscn", a["scenes"])
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()

