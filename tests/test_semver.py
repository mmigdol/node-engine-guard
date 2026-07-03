import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from node_engine_guard.check import CheckResult
from node_engine_guard.cli import codex_hook_output, main
from node_engine_guard.semver import Version, parse_version, satisfies_range


class SemverTests(unittest.TestCase):
    def test_parse_version(self):
        self.assertEqual(parse_version("v22.22.2"), Version(22, 22, 2))
        self.assertEqual(parse_version("22.22.2"), Version(22, 22, 2))

    def test_exact_and_wildcard_ranges(self):
        self.assertTrue(satisfies_range(Version(22, 1, 0), "22"))
        self.assertTrue(satisfies_range(Version(22, 2, 3), "22.2"))
        self.assertFalse(satisfies_range(Version(23, 0, 0), "22"))
        self.assertFalse(satisfies_range(Version(22, 3, 0), "22.2"))

    def test_comparator_ranges(self):
        self.assertTrue(satisfies_range(Version(22, 22, 2), ">=22 <23"))
        self.assertFalse(satisfies_range(Version(21, 6, 2), ">=22 <23"))

    def test_caret_ranges(self):
        self.assertTrue(satisfies_range(Version(22, 22, 2), "^22.0.0"))
        self.assertFalse(satisfies_range(Version(23, 0, 0), "^22.0.0"))

    def test_tilde_ranges(self):
        self.assertTrue(satisfies_range(Version(22, 22, 2), "~22.22.0"))
        self.assertFalse(satisfies_range(Version(22, 23, 0), "~22.22.0"))

    def test_or_ranges(self):
        self.assertTrue(satisfies_range(Version(20, 19, 0), "^20.19.0 || >=22"))
        self.assertTrue(satisfies_range(Version(22, 0, 0), "^20.19.0 || >=22"))
        self.assertFalse(satisfies_range(Version(21, 6, 2), "^20.19.0 || >=22"))


class CodexHookOutputTests(unittest.TestCase):
    def test_warning_is_emitted_as_system_message_and_context(self):
        output = json.loads(codex_hook_output(CheckResult(False, "node is wrong")))

        self.assertEqual(output["systemMessage"], "WARNING: node is wrong")
        self.assertEqual(
            output["hookSpecificOutput"],
            {
                "hookEventName": "SessionStart",
                "additionalContext": "WARNING: node is wrong",
            },
        )

    def test_codex_hook_fails_by_default_on_mismatch(self):
        result = CheckResult(False, "node is wrong")
        stderr = io.StringIO()

        with (
            patch("node_engine_guard.cli.parse_hook_cwd", return_value=Path("/tmp/project")),
            patch("node_engine_guard.cli.check_node_engine", return_value=result),
            contextlib.redirect_stderr(stderr),
        ):
            code = main(["--codex-hook"])

        self.assertEqual(code, 1)
        self.assertIn("node-engine-guard: node is wrong", stderr.getvalue())

    def test_codex_hook_soft_mode_exits_zero_with_context(self):
        result = CheckResult(False, "node is wrong")
        stdout = io.StringIO()

        with (
            patch("node_engine_guard.cli.parse_hook_cwd", return_value=Path("/tmp/project")),
            patch("node_engine_guard.cli.check_node_engine", return_value=result),
            contextlib.redirect_stdout(stdout),
        ):
            code = main(["--codex-hook", "--soft"])

        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["systemMessage"], "WARNING: node is wrong")


if __name__ == "__main__":
    unittest.main()
