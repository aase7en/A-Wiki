"""Unit tests for scripts/hooks/check_rabies_report.py (Layer 2 of v1.4.0).

Tests the JSON-output invariant validator in isolation by feeding synthetic
hook-event payloads via stdin. Each test asserts the hook returns the expected
exit code (0=pass, 2=block) for a given input.
"""
from __future__ import annotations
import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parent.parent / "scripts" / "hooks" / "check_rabies_report.py"


def _run_hook(payload: dict) -> tuple[int, str]:
    """Run the hook with the given stdin payload. Returns (exit_code, stderr)."""
    proc = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True, text=True, timeout=10,
    )
    return proc.returncode, proc.stderr


def _write_payload(content: str, file_path: str = "drive/test/rabiesvac_review_v6.json") -> dict:
    """Build a synthetic Write-tool hook payload."""
    return {
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": content},
    }


def _valid_report_json(n_cases: int = 5) -> str:
    """Build a valid rabies report JSON with n_cases."""
    return json.dumps({
        "report": {
            "complete_IM": 1, "complete_ID": 1,
            "sub5_IM": 1, "sub5_ID": 0,
            "incomplete_IM": 0, "incomplete_ID": 2,
            "erig": 1, "hrig": 0, "review": 0,
        },
        "cases": [
            {"hn_masked": "****0001", "cat": "complete", "route": "IM"},
            {"hn_masked": "****0002", "cat": "complete", "route": "ID"},
            {"hn_masked": "****0003", "cat": "sub5", "route": "IM"},
            {"hn_masked": "****0004", "cat": "incomplete", "route": "ID"},
            {"hn_masked": "****0005", "cat": "incomplete", "route": "ID"},
        ][:n_cases],
    })


class TestPathMatching(unittest.TestCase):
    """Hook should only fire on rabies-named JSON paths."""

    def test_non_rabies_json_passes(self):
        """Arbitrary JSON file (not rabies output) → exit 0 (skip)."""
        payload = _write_payload('{"foo": "bar"}', file_path="wiki/notes.json")
        code, _ = _run_hook(payload)
        self.assertEqual(code, 0)

    def test_rabiesvac_json_triggers(self):
        """rabiesvac_review_*.json → hook runs (will validate content)."""
        # Valid content → exit 0
        payload = _write_payload(_valid_report_json())
        code, _ = _run_hook(payload)
        self.assertEqual(code, 0)

    def test_non_json_extension_skipped(self):
        """rabiesvac.docx (not .json) → skip."""
        payload = _write_payload("binary", file_path="drive/x/rabiesvac_v6.docx")
        code, _ = _run_hook(payload)
        self.assertEqual(code, 0)


class TestNonWriteTools(unittest.TestCase):
    """Hook should pass through when tool is not Edit/Write/MultiEdit."""

    def test_bash_passes(self):
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        }
        code, _ = _run_hook(payload)
        self.assertEqual(code, 0)


class TestValidJson(unittest.TestCase):
    """Well-formed rabies report JSON passes."""

    def test_valid_5_case_report(self):
        payload = _write_payload(_valid_report_json(5))
        code, _ = _run_hook(payload)
        self.assertEqual(code, 0)

    def test_valid_with_review_case(self):
        """REVIEW category is valid."""
        content = json.dumps({
            "report": {
                "complete_IM": 0, "complete_ID": 0,
                "sub5_IM": 0, "sub5_ID": 0,
                "incomplete_IM": 0, "incomplete_ID": 0,
                "erig": 0, "hrig": 0, "review": 1,
            },
            "cases": [{"hn_masked": "****0001", "cat": "REVIEW", "route": "NONE"}],
        })
        payload = _write_payload(content)
        code, _ = _run_hook(payload)
        self.assertEqual(code, 0)


class TestBlockConditions(unittest.TestCase):
    """Each violation type must exit 2 with a clear reason."""

    def test_block_on_invalid_json(self):
        payload = _write_payload("{not valid json")
        code, err = _run_hook(payload)
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)

    def test_block_on_missing_report_key(self):
        content = json.dumps({"cases": []})
        payload = _write_payload(content)
        code, err = _run_hook(payload)
        self.assertEqual(code, 2)
        self.assertIn("missing required key 'report'", err)

    def test_block_on_missing_cases_key(self):
        content = json.dumps({"report": {"complete_IM": 1}})
        payload = _write_payload(content)
        code, err = _run_hook(payload)
        self.assertEqual(code, 2)
        self.assertIn("missing required key 'cases'", err)

    def test_block_on_empty_cases(self):
        """Empty cases array = silent date bug → BLOCK."""
        content = json.dumps({
            "report": {
                "complete_IM": 0, "complete_ID": 0,
                "sub5_IM": 0, "sub5_ID": 0,
                "incomplete_IM": 0, "incomplete_ID": 0,
                "erig": 0, "hrig": 0, "review": 0,
            },
            "cases": [],
        })
        payload = _write_payload(content)
        code, err = _run_hook(payload)
        self.assertEqual(code, 2)
        self.assertIn("'cases' is empty", err)

    def test_block_on_sum_mismatch(self):
        """9-cell sum != len(cases) → silent case drop → BLOCK."""
        content = json.dumps({
            "report": {
                "complete_IM": 5, "complete_ID": 5,  # claims 10 complete
                "sub5_IM": 0, "sub5_ID": 0,
                "incomplete_IM": 0, "incomplete_ID": 0,
                "erig": 0, "hrig": 0, "review": 0,
            },
            "cases": [{"hn_masked": "****0001", "cat": "complete", "route": "IM"}],  # actually 1
        })
        payload = _write_payload(content)
        code, err = _run_hook(payload)
        self.assertEqual(code, 2)
        self.assertIn("sum-of-cells invariant", err)

    def test_block_on_erig_overcount(self):
        """ERIG count > total cases → double-counting bug."""
        content = json.dumps({
            "report": {
                "complete_IM": 0, "complete_ID": 1,
                "sub5_IM": 0, "sub5_ID": 0,
                "incomplete_IM": 0, "incomplete_ID": 0,
                "erig": 5, "hrig": 0, "review": 0,  # erig=5 but only 1 case
            },
            "cases": [{"hn_masked": "****0001", "cat": "complete", "route": "ID"}],
        })
        payload = _write_payload(content)
        code, err = _run_hook(payload)
        self.assertEqual(code, 2)
        self.assertIn("ERIG count (5) > total cases (1)", err)

    def test_block_on_invalid_cat(self):
        """Unknown category like 'ig_only' → BLOCK (dead-code regression)."""
        content = json.dumps({
            "report": {
                "complete_IM": 0, "complete_ID": 0,
                "sub5_IM": 0, "sub5_ID": 0,
                "incomplete_IM": 0, "incomplete_ID": 0,
                "erig": 0, "hrig": 0, "review": 0,
            },
            "cases": [{"hn_masked": "****0001", "cat": "ig_only", "route": "ID"}],
        })
        payload = _write_payload(content)
        code, err = _run_hook(payload)
        self.assertEqual(code, 2)
        self.assertIn("cat='ig_only'", err)

    def test_block_on_typo_route(self):
        """Lowercase 'im' instead of 'IM' → BLOCK (case-sensitive enum)."""
        content = json.dumps({
            "report": {
                "complete_IM": 0, "complete_ID": 0,
                "sub5_IM": 0, "sub5_ID": 0,
                "incomplete_IM": 0, "incomplete_ID": 0,
                "erig": 0, "hrig": 0, "review": 0,
            },
            "cases": [{"hn_masked": "****0001", "cat": "incomplete", "route": "im"}],
        })
        payload = _write_payload(content)
        code, err = _run_hook(payload)
        self.assertEqual(code, 2)
        self.assertIn("route='im'", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
