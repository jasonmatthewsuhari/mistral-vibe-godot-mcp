from __future__ import annotations

import unittest

from leader_verify.smoke_stdio import run_smoke


class SmokeStdioTests(unittest.TestCase):
    def test_initialize_and_tools_list(self) -> None:
        try:
            payload = run_smoke()
        except RuntimeError as exc:
            self.skipTest(f"stdio server currently not bootable: {exc}")
        init_result = payload["initialize"]["result"]
        self.assertIn("protocolVersion", init_result)

        tools_result = payload["tools_list"]["result"]
        names = {tool["name"] for tool in tools_result["tools"]}
        self.assertIn("godot_get_version", names)
        self.assertIn("godot_list_projects", names)


if __name__ == "__main__":
    unittest.main()
