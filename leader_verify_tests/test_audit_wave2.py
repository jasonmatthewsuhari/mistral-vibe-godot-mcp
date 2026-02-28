from __future__ import annotations

import unittest

from leader_verify.audit_wave2 import REQUIRED_TOOLS, build_report


class AuditWave2Tests(unittest.TestCase):
    def test_ok_when_server_and_contracts_match_required(self) -> None:
        tools = set(REQUIRED_TOOLS)
        report = build_report(tools, tools)
        self.assertTrue(report.ok)
        self.assertEqual(report.required_missing, [])

    def test_flags_missing_tools(self) -> None:
        server_tools = {"godot_get_version", "godot_list_projects"}
        contract_tools = set(REQUIRED_TOOLS)
        report = build_report(server_tools, contract_tools)
        self.assertFalse(report.ok)
        self.assertIn("scene_create", report.required_missing)
        self.assertIn("scene_create", report.missing_from_server)


if __name__ == "__main__":
    unittest.main()

