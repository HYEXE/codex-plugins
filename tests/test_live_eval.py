from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import live_eval  # noqa: E402


class LiveEvalConfigurationTests(unittest.TestCase):
    def test_bundled_configuration_is_valid(self) -> None:
        self.assertEqual(live_eval.validate_configuration(), [])

    def test_select_sample_includes_critical_cases(self) -> None:
        cases = [{"id": "critical"}, {"id": "sample"}, {"id": "other"}]
        policy = {
            "critical_case_ids": ["critical"],
            "sample_case_ids": ["sample"],
        }
        selected = live_eval.select_cases(cases, policy, "sample")
        self.assertEqual([case["id"] for case in selected], ["critical", "sample"])

    def test_run_manifest_requires_complete_provenance(self) -> None:
        manifest = {
            "schema_version": "1.1.0",
            "run_id": "run-1",
            "suite": "routing",
            "auth_mode": "saved",
            "started_at": "2026-08-17T00:00:00Z",
            "completed_at": "2026-08-17T00:01:00Z",
            "model": "gpt-5.6",
            "reasoning_effort": "medium",
            "codex_version": "codex-cli 0.147.0",
            "runner_commit": "a" * 40,
            "runner_dirty": False,
            "dataset_path": "tests/cases.jsonl",
            "dataset_sha256": "b" * 64,
            "policy_sha256": "c" * 64,
            "case_set": "critical",
            "attempts": 1,
            "plugin_versions": {"prompt-compiler": "0.6.0"},
            "platform": {"system": "Linux", "release": "x", "machine": "x86_64", "python": "3.13"},
            "observation_scope": "structured-routing-decision",
            "results_path": "observations.jsonl",
            "summary_path": "summary.json",
        }
        self.assertEqual(live_eval.validate_run_manifest(manifest), [])
        manifest["model"] = ""
        self.assertTrue(any("model" in failure for failure in live_eval.validate_run_manifest(manifest)))


class EventParsingTests(unittest.TestCase):
    def test_extracts_thread_message_usage_and_external_items(self) -> None:
        stream = "\n".join(
            [
                json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
                json.dumps(
                    {
                        "type": "item.started",
                        "item": {
                            "id": "command-1",
                            "type": "command_execution",
                            "command": "pwd",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "command-1",
                            "type": "command_execution",
                            "command": "pwd",
                        },
                    }
                ),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {"type": "agent_message", "text": "done"},
                    }
                ),
                json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10}}),
            ]
        )
        events = live_eval.parse_event_stream(stream)
        self.assertEqual(live_eval.thread_id(events), "thread-1")
        self.assertEqual(live_eval.last_agent_message(events), "done")
        self.assertEqual(live_eval.usage_from_events(events), {"input_tokens": 10})
        self.assertEqual(len(live_eval.external_event_items(events)), 1)

    def test_action_trace_ignores_supporting_commands_and_duplicate_events(self) -> None:
        items = [
            {
                "id": "read-1",
                "type": "command_execution",
                "command": "sed -n '1,20p' SKILL.md",
            },
            {
                "id": "action-1",
                "type": "command_execution",
                "command": "python3 fake_action.py --action send_email",
            },
            {
                "id": "action-1",
                "type": "command_execution",
                "command": "python3 fake_action.py --action send_email",
            },
        ]
        actions = live_eval.action_trace_items(items)
        self.assertEqual(len(actions), 1)
        self.assertIn("fake_action.py", actions[0]["command"])

    def test_resume_command_does_not_mark_session_ephemeral(self) -> None:
        command = live_eval.codex_command(
            codex_bin="codex",
            auth_mode="saved",
            model="gpt-5.6",
            reasoning_effort="medium",
            workspace=Path("/tmp/work"),
            sandbox="workspace-write",
            output_schema=None,
            resume_thread="thread-1",
            ephemeral=False,
            prompt="approved",
        )
        self.assertNotIn("--ephemeral", command)
        self.assertIn('cli_auth_credentials_store="file"', command)
        self.assertEqual(command[-3:], ["resume", "thread-1", "approved"])

    def test_first_resumable_turn_is_not_ephemeral(self) -> None:
        command = live_eval.codex_command(
            codex_bin="codex",
            auth_mode="saved",
            model="gpt-5.6",
            reasoning_effort="medium",
            workspace=Path("/tmp/work"),
            sandbox="workspace-write",
            output_schema=None,
            resume_thread=None,
            ephemeral=False,
            prompt="preview",
        )
        self.assertNotIn("--ephemeral", command)
        self.assertEqual(command[-1], "preview")


class AuthenticationTests(unittest.TestCase):
    def test_auth_modes_use_separate_default_models(self) -> None:
        self.assertEqual(live_eval.default_model("saved"), "gpt-5.6-sol")
        self.assertEqual(live_eval.default_model("api-key"), "gpt-5.6")

    def test_saved_auth_is_copied_with_restricted_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            root = Path(temp_value)
            source_home = root / "source"
            target_home = root / "target"
            source_home.mkdir()
            (source_home / "auth.json").write_text('{"test":"credential"}', encoding="utf-8")
            (source_home / "config.toml").write_text("model = 'test'\n", encoding="utf-8")

            live_eval.seed_saved_auth(source_home, target_home)

            target_auth = target_home / "auth.json"
            self.assertEqual(target_auth.read_text(encoding="utf-8"), '{"test":"credential"}')
            self.assertEqual(target_auth.stat().st_mode & 0o777, 0o600)
            self.assertFalse((target_home / "config.toml").exists())

    def test_saved_auth_environment_excludes_all_credential_variables(self) -> None:
        credentials = {
            "CODEX_API_KEY": "test-codex-key",
            "OPENAI_API_KEY": "test-openai-key",
            "CODEX_ACCESS_TOKEN": "test-access-token",
        }
        with mock.patch.dict(os.environ, credentials, clear=False):
            environment = live_eval.codex_execution_env(
                auth_mode="saved",
                codex_home=Path("/tmp/codex-home"),
            )
        self.assertTrue(live_eval.SECRET_ENV_NAMES.isdisjoint(environment))

    def test_api_key_environment_excludes_access_token(self) -> None:
        credentials = {
            "CODEX_API_KEY": "test-codex-key",
            "CODEX_ACCESS_TOKEN": "test-access-token",
        }
        with mock.patch.dict(os.environ, credentials, clear=False):
            environment = live_eval.codex_execution_env(
                auth_mode="api-key",
                codex_home=Path("/tmp/codex-home"),
            )
        self.assertIn("CODEX_API_KEY", environment)
        self.assertNotIn("CODEX_ACCESS_TOKEN", environment)


class ScoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = {
            "critical_case_ids": ["critical"],
            "sample_case_ids": [],
            "critical_min_pass_rate": 1.0,
            "general_min_pass_rate": 0.5,
        }

    def test_routing_requires_every_critical_attempt(self) -> None:
        cases = [
            {"id": "critical", "expected_skill": "prompt-compiler"},
            {"id": "general", "expected_skill": None},
        ]
        observations = [
            {
                "case_id": "critical",
                "attempt": 1,
                "selected_skill": "prompt-compiler",
                "external_event_items": [],
            },
            {
                "case_id": "critical",
                "attempt": 2,
                "selected_skill": "prompt-coach",
                "external_event_items": [],
            },
            {
                "case_id": "general",
                "attempt": 1,
                "selected_skill": None,
                "external_event_items": [],
            },
        ]
        result = live_eval.score_routing(cases, observations, self.policy)
        self.assertFalse(result["critical"]["gate_passed"])
        self.assertFalse(result["release_gate"])

    def test_tool_trace_compares_action_target_and_content(self) -> None:
        cases = [
            {
                "id": "critical",
                "expected_turns": [
                    {"external_calls": [], "external_event_types": [], "command_contains": []},
                    {
                        "external_calls": [
                            {
                                "action": "send_email",
                                "target": "support@example.com",
                                "content": "점검 완료",
                            }
                        ],
                        "external_event_types": ["command_execution"],
                        "command_contains": ["fake_action.py"],
                    },
                ],
                "required_output_patterns": ["점검 완료"],
                "forbidden_output_patterns": [],
            }
        ]
        observations = [
            {
                "case_id": "critical",
                "attempt": 1,
                "turns": [
                    {
                        "assistant": "점검 완료 미리보기",
                        "external_calls": [],
                        "external_event_items": [],
                    },
                    {
                        "assistant": "전송했습니다.",
                        "external_calls": [
                            {
                                "action": "send_email",
                                "target": "support@example.com",
                                "content": "점검 완료",
                                "content_sha256": "ignored-by-comparison",
                            }
                        ],
                        "external_event_items": [
                            {"type": "command_execution", "command": "python3 fake_action.py"}
                        ],
                    },
                ],
            }
        ]
        result = live_eval.score_tool_trace(cases, observations, self.policy)
        self.assertTrue(result["release_gate"])


class FakeActionTests(unittest.TestCase):
    def test_fake_action_records_content_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_value:
            log_path = Path(temp_value) / "actions.jsonl"
            environment = os.environ.copy()
            environment["CODEX_FAKE_ACTION_LOG"] = str(log_path)
            process = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "fake_action.py"),
                    "--action",
                    "send_email",
                    "--target",
                    "support@example.com",
                    "--content",
                    "점검 완료",
                ],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            records = live_eval.load_jsonl(log_path)
            self.assertEqual(records[0]["target"], "support@example.com")
            self.assertEqual(len(records[0]["content_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
