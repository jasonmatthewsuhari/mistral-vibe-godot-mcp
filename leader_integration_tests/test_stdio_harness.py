from __future__ import annotations

import unittest

from leader_integration.stdio_client import MCPStdioClient


class StdioHarnessTests(unittest.TestCase):
    def test_initialize_and_list_tools(self) -> None:
        client = MCPStdioClient.start()
        try:
            init_resp = client.initialize()
            self.assertIn("result", init_resp)
            self.assertIn("protocolVersion", init_resp["result"])

            tools_resp = client.list_tools()
            self.assertIn("result", tools_resp)
            tool_names = {tool["name"] for tool in tools_resp["result"]["tools"]}
            self.assertIn("godot_get_version", tool_names)
            self.assertIn("render_capture", tool_names)
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()

