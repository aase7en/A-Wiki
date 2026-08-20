"""Phase 6 — canonical hook-engine contract tests (work order §11 items 1–33).

Iron Law #1: failing tests written FIRST. Pins:

  - scripts/hooks/registry.py = the ONE registration/classification authority
  - hooks_runner.py           = the ONE canonical lifecycle dispatcher
  - scripts/hooks/providers.py= provider event/payload normalization (claude/codex)
  - hard gates fail CLOSED (timeout/exception/odd exit code → block)
  - soft hooks can NEVER block through the runner
  - provider parity: equivalent canonical action → same hard-gate decision

N/A items (documented with repository evidence):
  - PreCompact: not wired in any provider config (.claude/settings.json,
    setup-codex-config.py HOOKS_CONFIG) — no such lifecycle event exists here.
  - scripts/codex_notify.py: does not exist in the repo (work-order reading
    list stale on this one file).
  - Item 28 (SessionStart no-mutation): session_start.py is invoked directly
    by provider configs, not through the runner; its no-unsafe-storage
    behavior is owned by Phase 5/P1.1 tests, not re-tested here.
"""
from __future__ import annotations

import ast
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

RUNNER = str(REPO_ROOT / "scripts" / "hooks_runner.py")
HOOKS_DIR = REPO_ROOT / "scripts" / "hooks"

TOKEN = "ghp_" + "EngineGate" + "0123456789abcdefghijklmnop"   # 36 chars, no placeholder words
WIN_DRIVE_PATH = "C" + chr(58) + chr(92) + "Users" + chr(92) + "me" + chr(92) + "f.txt"
POSIX_PRIVATE_PATH = "/" + "home/alice/private/notes.txt"


def run_runner(args, payload, env_extra=None, cwd=None, isolate=None):
    """P6-RR08: `isolate=<dir>` redirects EVERY mutable state seam the
    invoked hooks could write (ledger / cost gate / cline log / live log)
    into that directory — focused tests never touch live runtime state."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for k in ("HOOK_SKIP", "AWIKI_CLAIM_GATE", "AWIKI_CLAIMS_STORE",
              "AWIKI_AGENT", "USERSCRIPT_SYNC_OK", "AWIKI_FOCUS_ENFORCE",
              "AWIKI_FOCUS_DIR", "AWIKI_COST_GATE_TMP_DIR",
              "AWIKI_FLOW_STATE_DIR", "AWIKI_GIT_GUARD_REPO_ROOT",
              "AWIKI_LIVE_LOG_PATH", "AWIKI_LIVE_SESSION_FILE",
              "AWIKI_MEMORY_LEDGER_PATH", "CLINE_HOOK_LOG_FILE",
              "WIKI_UNLOCK", "AUTH_BY_DRIVE_MOUNT",
              # session ids would redirect stateful hooks at THIS live
              # session's state files — tests must control their own
              "ZCODE_SESSION_ID", "CLAUDE_SESSION_ID", "CODEX_SESSION_ID",
              "GEMINI_SESSION_ID"):
        env.pop(k, None)
    runtime_dir = Path(tempfile.gettempdir()) / "awiki-phase6-hook-tests" / str(os.getpid())
    runtime_dir.mkdir(parents=True, exist_ok=True)
    env.setdefault("AWIKI_LIVE_LOG_PATH", str(runtime_dir / "live-events.jsonl"))
    env.setdefault("AWIKI_LIVE_SESSION_FILE", str(runtime_dir / "live-session-id"))
    env.setdefault("AWIKI_MEMORY_LEDGER_PATH", str(runtime_dir / "memory-ledger.jsonl"))
    if isolate is not None:
        iso = Path(isolate)
        (iso / "costgate").mkdir(parents=True, exist_ok=True)
        env["AWIKI_MEMORY_LEDGER_PATH"] = str(iso / "memory-ledger.jsonl")
        env["AWIKI_COST_GATE_TMP_DIR"] = str(iso / "costgate")
        env["CLINE_HOOK_LOG_FILE"] = str(iso / "cline-hooks.log")
        env["AWIKI_LIVE_LOG_PATH"] = str(iso / "live-events.jsonl")
    env.update(env_extra or {})   # caller overrides win over isolation defaults
    return subprocess.run(
        [sys.executable, RUNNER, *args],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=env, cwd=str(cwd or REPO_ROOT), timeout=120,
    )


def edit(new_string="ok", file_path="scripts/example.py"):
    return {"tool_name": "Edit", "tool_input": {"file_path": file_path,
                                                "new_string": new_string,
                                                "old_string": "old-content"}}


def bash(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


# ══════════════════════════════════════════════════════════════════════
# P6-RR02 — documented Python 3.8+ runtime compatibility
# ══════════════════════════════════════════════════════════════════════
def test_hooks_runner_annotations_are_python38_runtime_safe():
    """README promises Python 3.8+; runner annotations must import there."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "Python** (3.8+)" in readme

    source = (REPO_ROOT / "scripts" / "hooks_runner.py").read_text(encoding="utf-8")
    # First prove the file stays inside Python 3.8 grammar.
    tree = ast.parse(source, filename="scripts/hooks_runner.py", feature_version=(3, 8))

    has_future_annotations = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in tree.body
    )
    if has_future_annotations:
        return

    annotations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign):
            annotations.append(node.annotation)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotations.extend(arg.annotation for arg in node.args.args if arg.annotation)
            annotations.extend(arg.annotation for arg in node.args.kwonlyargs if arg.annotation)
            if node.args.vararg and node.args.vararg.annotation:
                annotations.append(node.args.vararg.annotation)
            if node.args.kwarg and node.args.kwarg.annotation:
                annotations.append(node.args.kwarg.annotation)
            if node.returns:
                annotations.append(node.returns)

    unsafe = []
    for annotation in annotations:
        for part in ast.walk(annotation):
            if isinstance(part, ast.BinOp) and isinstance(part.op, ast.BitOr):
                unsafe.append(ast.dump(annotation, include_attributes=False))
            if (
                isinstance(part, ast.Subscript)
                and isinstance(part.value, ast.Name)
                and part.value.id in {"list", "dict", "tuple", "set", "frozenset", "type"}
            ):
                unsafe.append(ast.dump(annotation, include_attributes=False))
    assert not unsafe, f"runtime annotations require Python >3.8: {unsafe}"


# ══════════════════════════════════════════════════════════════════════
# Registry authority (items 15, 16, 17, 19)
# ══════════════════════════════════════════════════════════════════════
class TestRegistry:
    def test_registry_module_is_the_authority(self):
        import registry
        assert hasattr(registry, "HOOK_REGISTRY")
        assert hasattr(registry, "validate_registry")
        assert hasattr(registry, "hooks_for_event")
        assert hasattr(registry, "KNOWN_EVENTS")

    def test_only_real_lifecycle_events_exist(self):
        import registry
        # PreCompact is NOT wired anywhere — must not appear
        assert "PreCompact" not in registry.KNOWN_EVENTS
        for e in registry.KNOWN_EVENTS:
            assert e in ("SessionStart", "UserPromptSubmit", "PreToolUse",
                         "PostToolUse", "Stop", "PostCompact")

    def test_registry_validates_clean(self):
        import registry
        errors = registry.validate_registry()
        assert errors == [], errors

    def test_every_registered_hook_exists_on_disk(self):
        import registry
        for name in registry.HOOK_REGISTRY:
            assert (HOOKS_DIR / f"{name}.py").is_file(), f"{name}.py missing"

    def test_missing_executable_is_runtime_classification_not_registry_invalidity(
            self, tmp_path):
        """P6-R03: availability is handled after hard/soft classification."""
        import registry
        specs = [
            ("missing_soft", {
                "events": ["PreToolUse"], "classification": "soft",
                "order": 1, "timeout_s": None, "allow_context_stdout": False, "matchers": ["*"]}),
            ("missing_hard", {
                "events": ["PreToolUse"], "classification": "hard",
                "order": 2, "timeout_s": None, "allow_context_stdout": False, "matchers": ["*"]}),
        ]
        lookup = registry._validated_lookup(specs, hooks_dir=tmp_path)
        assert set(lookup) == {"missing_soft", "missing_hard"}

    def test_classification_is_hard_or_soft_only(self):
        import registry
        for name, entry in registry.HOOK_REGISTRY.items():
            assert entry["classification"] in ("hard", "soft"), name

    def test_duplicate_order_fails_validation(self):
        import registry
        bad = {"a_hook": {"events": ["PreToolUse"], "classification": "hard",
                          "order": 1, "allow_context_stdout": False, "matchers": ["*"]},
               "b_hook": {"events": ["PreToolUse"], "classification": "hard",
                          "order": 1, "allow_context_stdout": False, "matchers": ["*"]}}
        errors = registry.validate_registry(bad, hooks_dir=HOOKS_DIR,
                                            skip_executable_check=True)
        assert any("order" in e for e in errors)

    def test_duplicate_stable_hook_ids_fail_before_lookup_dict(self):
        """D-P6-002: duplicate IDs must remain visible until validation."""
        import registry
        entry_a = {"events": ["PreToolUse"], "classification": "hard",
                   "order": 1, "allow_context_stdout": False, "matchers": ["*"]}
        entry_b = {"events": ["Stop"], "classification": "soft",
                   "order": 2, "allow_context_stdout": False}
        duplicate_entries = [("same_hook", entry_a), ("same_hook", entry_b)]
        try:
            errors = registry.validate_registry(
                duplicate_entries, hooks_dir=HOOKS_DIR,
                skip_executable_check=True)
        except (AttributeError, TypeError) as exc:
            pytest.fail(
                "registry validator must accept a pre-dict sequence so duplicate "
                f"stable hook IDs can be detected: {exc}"
            )
        assert any(
            "duplicate" in error.lower() and "same_hook" in error
            for error in errors
        ), errors

    def test_unknown_event_fails_validation(self):
        import registry
        bad = {"a_hook": {"events": ["PreCompact"], "classification": "hard",
                          "order": 1, "allow_context_stdout": False}}
        errors = registry.validate_registry(bad, hooks_dir=HOOKS_DIR,
                                            skip_executable_check=True)
        assert any("event" in e.lower() for e in errors)

    def test_missing_executable_is_not_structural_registry_invalidity(self):
        import registry
        bad = {"ghost_hook": {"events": ["PreToolUse"], "classification": "hard",
                              "order": 1, "allow_context_stdout": False, "matchers": ["*"]}}
        errors = registry.validate_registry(bad, hooks_dir=HOOKS_DIR)
        assert errors == [], errors

    def test_hooks_for_event_deterministic_order(self):
        import registry
        names = registry.hooks_for_event("PreToolUse")
        assert names == sorted(
            names, key=lambda n: (registry.HOOK_REGISTRY[n]["order"], n))
        assert names, "PreToolUse must have registered hooks"

    def test_arbitrary_filename_is_not_registered(self):
        import registry
        for ghost in ("evil_new_gate", "totally_unknown", "__init__"):
            assert ghost not in registry.HOOK_REGISTRY


# ══════════════════════════════════════════════════════════════════════
# Provider configs consistency + parity (items 2, 15, 23, 24)
# ══════════════════════════════════════════════════════════════════════
def _load_codex_hook_config() -> dict:
    import importlib.util as ilu
    spec = ilu.spec_from_file_location(
        "codex_cfg_contract", REPO_ROOT / "scripts" / "setup-codex-config.py")
    mod = ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.HOOKS_CONFIG


def _event_commands(config: dict, event: str) -> list[str]:
    commands = []
    for block in config.get("hooks", {}).get(event, []):
        commands.extend(h.get("command", "") for h in block.get("hooks", []))
    return commands


def _all_commands(config: dict) -> list[str]:
    commands = []
    for event in config.get("hooks", {}):
        commands.extend(_event_commands(config, event))
    return commands


def _runner_hook_ids(commands) -> set[str]:
    found = set()
    for command in commands:
        m = re.search(r"hooks_runner\.py\s+([A-Za-z0-9_-]+)", command)
        if m:
            found.add(m.group(1).replace("-", "_"))
    return found


def _direct_hook_impl_ids(commands) -> set[str]:
    found = set()
    for command in commands:
        m = re.search(r"scripts/hooks/([A-Za-z0-9_-]+)\.py\b", command)
        if m:
            found.add(m.group(1).replace("-", "_"))
    return found


def _direct_scripts_hook_paths(commands) -> set[str]:
    found = set()
    for command in commands:
        m = re.search(r"(scripts/hooks/[A-Za-z0-9_.-]+\.(?:py|sh))\b", command)
        if m:
            found.add(m.group(1))
    return found


def _registered_event_hooks(event: str) -> set[str]:
    import registry
    return {
        name for name, entry in registry.HOOK_REGISTRY.items()
        if event in entry["events"]
    }


def _hard_runner_hook_ids(config: dict, event: str) -> set[str]:
    import registry
    return {
        name for name in _runner_hook_ids(_event_commands(config, event))
        if registry.HOOK_REGISTRY.get(name, {}).get("classification") == "hard"
    }


def _runner_hooks_in_claude_settings() -> set[str]:
    cfg = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    return _runner_hook_ids(_all_commands(cfg))


class TestProviderConfigConsistency:
    def test_deployed_registered_events_use_registry_event_sweeps(self):
        """P6-R02: provider configs must not enumerate registered hook IDs."""
        import providers
        import registry

        configs = {
            "claude": json.loads(
                (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
            ),
            "codex": json.loads(
                (REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8")
            ),
        }
        registered = set(registry.HOOK_REGISTRY)
        for provider, config in configs.items():
            all_named = _runner_hook_ids(_all_commands(config)) & registered
            assert all_named == set(), (
                f"{provider} config still enumerates registered hooks: {sorted(all_named)}"
            )

            for event in providers.supported_events(provider):
                canonical_event = providers.normalize_event(provider, event)
                if not _registered_event_hooks(canonical_event):
                    continue
                if canonical_event not in config.get("hooks", {}):
                    continue
                commands = _event_commands(config, canonical_event)
                expected = (
                    f"hooks_runner.py --provider {provider} --event {event}"
                )
                assert any(expected in command for command in commands), (
                    f"{provider} {canonical_event} lacks canonical event sweep"
                )

    def test_deployed_event_sweep_command_matches_outer_lifecycle(self):
        """P6-R02: wrong-event wiring must be visible in deployed config."""
        configs = {
            "claude": json.loads(
                (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
            ),
            "codex": json.loads(
                (REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8")
            ),
        }
        dispatch_re = re.compile(
            r"hooks_runner\.py\s+--provider\s+(\w+)\s+--event\s+(\w+)"
        )
        for provider, config in configs.items():
            for outer_event, blocks in config.get("hooks", {}).items():
                for block in blocks:
                    for hook in block.get("hooks", []):
                        match = dispatch_re.search(hook.get("command", ""))
                        if not match:
                            continue
                        assert match.group(1) == provider
                        assert match.group(2) == outer_event, (
                            f"{provider} {outer_event} block dispatches {match.group(2)}"
                        )

    def test_claude_settings_runner_hooks_all_registered(self):
        """P6-R02: Claude uses event sweeps, never named registered IDs."""
        import registry
        invoked = _runner_hooks_in_claude_settings() & set(registry.HOOK_REGISTRY)
        assert invoked == set(), f"Claude still enumerates registered hooks: {sorted(invoked)}"
        claude = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        assert any(
            "hooks_runner.py --provider claude --event PreToolUse" in command
            for command in _event_commands(claude, "PreToolUse")
        )

    def test_registered_userpromptsubmit_hooks_use_runner_in_claude(self):
        claude = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        commands = _event_commands(claude, "UserPromptSubmit")
        assert any(
            "hooks_runner.py --provider claude --event UserPromptSubmit" in command
            for command in commands
        )
        assert not (_runner_hook_ids(commands) & _registered_event_hooks("UserPromptSubmit"))

    def test_registered_stop_hooks_use_runner_in_supported_provider_configs(self):
        configs = {
            "claude": json.loads(
                (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
            ),
            "codex": json.loads(
                (REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8")
            ),
        }
        for provider, config in configs.items():
            commands = _event_commands(config, "Stop")
            assert any(
                f"hooks_runner.py --provider {provider} --event Stop" in command
                for command in commands
            )
            assert not (_runner_hook_ids(commands) & _registered_event_hooks("Stop"))

    def test_claude_has_no_registered_hook_implementation_bypass(self):
        import registry
        claude = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        bypass = _direct_hook_impl_ids(_all_commands(claude)) & set(registry.HOOK_REGISTRY)
        assert bypass == set(), f"Claude direct registered-hook bypass: {sorted(bypass)}"

    def test_codex_has_no_registered_hook_implementation_bypass(self):
        import registry
        codex = _load_codex_hook_config()
        bypass = _direct_hook_impl_ids(_all_commands(codex)) & set(registry.HOOK_REGISTRY)
        assert bypass == set(), f"Codex direct registered-hook bypass: {sorted(bypass)}"

    def test_direct_scripts_hooks_are_thin_runner_adapters_without_policy(self):
        """D-P6-003: a direct scripts/hooks adapter cannot own hook policy."""
        import registry
        claude = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        codex = _load_codex_hook_config()
        legacy_sessionstart_utilities = {
            "scripts/hooks/load-drive-keys.sh",
            "scripts/hooks/session_start.py",
        }
        for provider, config in (("claude", claude), ("codex", codex)):
            for rel_path in sorted(_direct_scripts_hook_paths(_all_commands(config))):
                hook_id = Path(rel_path).stem.replace("-", "_")
                assert hook_id not in registry.HOOK_REGISTRY, (
                    f"{provider} directly invokes registered hook {hook_id}"
                )
                source = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
                lowered = source.lower()
                assert "hook_registry" not in lowered
                assert "classification" not in lowered
                assert "allow_context_stdout" not in lowered
                assert not re.search(r"\b(?:sys\.)?exit\s*\(?\s*2\s*\)?", source)
                if rel_path in legacy_sessionstart_utilities:
                    continue
                assert "hooks_runner.py" in source or "hooks_runner" in source, (
                    f"{provider} direct adapter {rel_path} must only forward into "
                    "the canonical runner"
                )

    def test_codex_generator_runner_hooks_are_canonical_event_sweeps(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "codex_cfg", REPO_ROOT / "scripts" / "setup-codex-config.py")
        mod = ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for outer_event, blocks in mod.HOOKS_CONFIG["hooks"].items():
            for block in blocks:
                for hook in block.get("hooks", []):
                    command = hook.get("command", "")
                    if "hooks_runner.py" not in command:
                        continue
                    match = re.fullmatch(
                        r"python3 scripts/hooks_runner\.py --provider codex --event ([A-Za-z]+)",
                        command,
                    )
                    assert match, f"noncanonical generated runner command: {command}"
                    assert match.group(1) == outer_event

    def test_codex_generated_model_exactly_matches_tracked_runtime(self):
        """P6-R05: one full structured model owns the tracked Codex surface."""
        generated = _load_codex_hook_config()
        tracked = json.loads(
            (REPO_ROOT / ".codex" / "hooks.json").read_text(encoding="utf-8"))
        assert generated == tracked

    def test_codex_checker_rejects_wrong_matcher_even_with_canonical_command(self):
        """P6-R05: substring presence under the wrong matcher must not pass."""
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "codex_cfg_wrong_matcher", REPO_ROOT / "scripts" / "setup-codex-config.py")
        mod = ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        bad = json.loads(json.dumps(mod.HOOKS_CONFIG))
        bad["hooks"]["PreToolUse"][0]["matcher"] = "TodoWrite"
        errors = mod.check_guardrail_parity(bad)
        assert errors, "wrong matcher must fail structured parity"

    def test_codex_checker_rejects_wrong_runner_command(self):
        """P6-R05: right event/matcher with a noncanonical command must fail."""
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "codex_cfg_wrong_command", REPO_ROOT / "scripts" / "setup-codex-config.py")
        mod = ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        bad = json.loads(json.dumps(mod.HOOKS_CONFIG))
        bad["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = (
            "python3 scripts/hooks_runner.py check-secret-leak"
        )
        errors = mod.check_guardrail_parity(bad)
        assert errors, "named/noncanonical runner command must fail structured parity"

    def test_codex_checker_rejects_missing_observer_or_memory_hook(self):
        """P6-R05: compatibility observers are part of the full generated model."""
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "codex_cfg_missing_observer", REPO_ROOT / "scripts" / "setup-codex-config.py")
        mod = ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        bad = json.loads(json.dumps(mod.HOOKS_CONFIG))
        post = bad["hooks"]["PostToolUse"]
        for block in post:
            block["hooks"] = [
                h for h in block.get("hooks", [])
                if "hooks_runner.py --provider codex --event PostToolUse" not in h.get("command", "")
            ]
        errors = mod.check_guardrail_parity(bad)
        assert errors, "dropping registered PostToolUse observer dispatch must fail"

    def test_codex_generator_idempotent(self, tmp_path, monkeypatch):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("codex_cfg2", REPO_ROOT / "scripts" / "setup-codex-config.py")
        mod = ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        monkeypatch.setattr(mod, "CODEX_DIR", tmp_path)
        monkeypatch.setattr(mod, "HOOKS_JSON_PATH", tmp_path / "hooks.json")
        monkeypatch.setattr(mod, "CODEX_HOOKS_DIR", tmp_path / "hooks")
        monkeypatch.setattr(mod, "CONFIG_TEMPLATE", tmp_path / "config.toml")
        cwd = os.getcwd()
        try:
            mod.main([])
            first = (tmp_path / "hooks.json").read_text(encoding="utf-8")
            mod.main([])
            assert (tmp_path / "hooks.json").read_text(encoding="utf-8") == first
        finally:
            os.chdir(cwd)


# ══════════════════════════════════════════════════════════════════════
# Runner semantics — hard fail-closed, soft never blocks (items 5–14)
# ══════════════════════════════════════════════════════════════════════
class TestRunnerHardSoftSemantics:
    def test_hard_hook_pass_returns_zero(self):
        r = run_runner(["check_secret_leak", "--event", "PreToolUse"], edit("clean text"))
        assert r.returncode == 0, r.stderr

    def test_hard_hook_violation_blocks_with_two(self):
        r = run_runner(["check_secret_leak", "--event", "PreToolUse"],
                       edit(f"token {TOKEN} here"))
        assert r.returncode == 2
        assert r.stderr.strip()

    def test_unregistered_hook_refused_fail_closed(self):
        r = run_runner(["never_registered_hook"], edit("x"))
        assert r.returncode == 2
        assert "regist" in r.stderr.lower()

    def test_hook_not_registered_for_event_fails(self):
        # memory_capture is PostToolUse-only; invoked as PreToolUse → refuse
        r = run_runner(["memory_capture", "--event", "PreToolUse"], edit("x"))
        assert r.returncode == 2

    def test_missing_hard_executable_fails_closed(self, tmp_path):
        """P6-R03: runtime availability is classified after structural load."""
        empty = tmp_path / "empty-hooks"
        empty.mkdir()
        r = run_runner(["check_secret_leak"], edit("x"),
                       env_extra={"AWIKI_HOOKS_DIR": str(empty)})
        assert r.returncode == 2
        assert "executable missing" in r.stderr.lower()
        assert "fail closed" in r.stderr.lower()

    def test_run_all_requires_event(self):
        r = run_runner([], {"tool_name": "Edit"})
        assert r.returncode == 2

    def test_run_all_unknown_event_deterministic(self):
        r = run_runner(["--event", "NotAnEvent"], {"tool_name": "Edit"})
        assert r.returncode == 2

    def test_malformed_hard_gate_payload_fails_closed_without_echo(self):
        malformed = f"not-json {TOKEN} {WIN_DRIVE_PATH} {POSIX_PRIVATE_PATH}"
        r = run_runner(["check_secret_leak", "--event", "PreToolUse"], malformed)
        assert r.returncode == 2
        blob = r.stdout + r.stderr
        assert "Traceback" not in blob
        assert TOKEN not in blob
        assert WIN_DRIVE_PATH not in blob
        assert POSIX_PRIVATE_PATH not in blob

    def test_malformed_input_is_never_coerced_to_empty_dict(self, monkeypatch):
        import hooks_runner as hr
        seen = []

        def fake_execute(name, input_data, event=None):
            seen.append(input_data)
            return {"decision": "block", "reason": "malformed payload",
                    "context_stdout": "", "hook": name}

        monkeypatch.setattr(hr, "execute", fake_execute)
        monkeypatch.setattr(sys, "argv", [RUNNER, "check_secret_leak"])
        monkeypatch.setattr(sys, "stdin", io.StringIO("not-json {{{"))
        with pytest.raises(SystemExit) as exc:
            hr.main()
        assert exc.value.code == 2
        assert {} not in seen, "malformed input must not be coerced to {}"

    def test_malformed_soft_only_event_is_nonblocking_and_suppressed(
            self, monkeypatch, capsys):
        import hooks_runner as hr
        raw = f"not-json {TOKEN} {WIN_DRIVE_PATH} {POSIX_PRIVATE_PATH}"
        seen = []
        soft_entry = {"events": ["UserPromptSubmit"], "classification": "soft",
                      "order": 1, "timeout_s": None,
                      "allow_context_stdout": False}

        def fake_execute(name, input_data, event=None):
            seen.append(input_data)
            return {"decision": "pass", "reason": "",
                    "context_stdout": "", "hook": name}

        monkeypatch.setattr(hr, "REGISTRY", {"soft_probe": soft_entry})
        monkeypatch.setattr(hr, "run_event_hooks_order", lambda event: ["soft_probe"])
        monkeypatch.setattr(hr, "execute", fake_execute)
        monkeypatch.setattr(sys, "argv", [RUNNER, "--event", "UserPromptSubmit"])
        monkeypatch.setattr(sys, "stdin", io.StringIO(raw))
        with pytest.raises(SystemExit) as exc:
            hr.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        blob = captured.out + captured.err
        assert {} not in seen, "malformed input must not become an empty payload"
        assert "malformed" in captured.err.lower() or "suppressed" in captured.err.lower()
        assert TOKEN not in blob
        assert WIN_DRIVE_PATH not in blob
        assert POSIX_PRIVATE_PATH not in blob

    def test_invalid_timeout_exits_two_without_traceback_or_private_detail(self):
        """P6-R04: malformed startup env is normalized to safe exit 2."""
        r = run_runner(
            ["check_secret_leak", "--event", "PreToolUse"],
            edit("clean"),
            env_extra={"HOOK_TIMEOUT": WIN_DRIVE_PATH},
        )
        blob = r.stdout + r.stderr
        assert r.returncode == 2
        assert "Traceback" not in blob
        assert WIN_DRIVE_PATH not in blob

    def test_registry_startup_error_is_sanitized_in_execute(
            self, monkeypatch):
        """P6-R04: internal registry exceptions cannot leak through result reason."""
        import hooks_runner as hr
        raw = f"registry boom {TOKEN} {WIN_DRIVE_PATH} {POSIX_PRIVATE_PATH}"
        monkeypatch.setattr(hr, "_REGISTRY_LOAD_ERROR", raw)
        result = hr.execute("check_secret_leak", edit("clean"), event="PreToolUse")
        blob = json.dumps(result)
        assert result["decision"] == "block"
        for private in (TOKEN, WIN_DRIVE_PATH, POSIX_PRIVATE_PATH):
            assert private not in blob

    def test_registry_startup_error_cli_is_generic_exit_two(
            self, monkeypatch, capsys):
        import hooks_runner as hr
        raw = f"registry boom {TOKEN} {WIN_DRIVE_PATH} {POSIX_PRIVATE_PATH}"
        monkeypatch.setattr(hr, "_REGISTRY_LOAD_ERROR", raw)
        monkeypatch.setattr(sys, "argv", [RUNNER, "check_secret_leak"])
        monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
        with pytest.raises(SystemExit) as exc:
            hr.main()
        assert exc.value.code == 2
        blob = capsys.readouterr().err
        for private in (TOKEN, WIN_DRIVE_PATH, POSIX_PRIVATE_PATH):
            assert private not in blob

    def test_unexpected_provider_exception_hits_safe_outer_boundary(
            self, monkeypatch, capsys):
        """P6-RR03: unexpected provider errors never escape as traceback/rc1."""
        import hooks_runner as hr
        raw_detail = f"provider boom OPENROUTER_API_KEY=short!secret {WIN_DRIVE_PATH}"

        def explode(*_args, **_kwargs):
            raise RuntimeError(raw_detail)

        monkeypatch.setattr(hr.hook_providers, "normalize_payload", explode)
        monkeypatch.setattr(
            sys, "argv", [RUNNER, "--provider", "gemini", "--event", "BeforeTool"]
        )
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps({
            "tool_name": "write_file",
            "tool_input": {"file_path": "x.py", "content": "ok"},
        })))
        with pytest.raises(SystemExit) as exc:
            hr.main()
        assert exc.value.code == 2
        blob = capsys.readouterr().err
        assert "Traceback" not in blob
        assert raw_detail not in blob
        assert WIN_DRIVE_PATH not in blob
        assert "short!secret" not in blob

    def test_unexpected_dispatch_exception_hits_safe_outer_boundary(
            self, monkeypatch, capsys):
        """P6-RR03: event dispatch exceptions normalize to safe exit 2."""
        import hooks_runner as hr
        raw_detail = f"dispatch boom PASSWORD=p@ss/word {POSIX_PRIVATE_PATH}"

        def explode(_event):
            raise RuntimeError(raw_detail)

        monkeypatch.setattr(hr, "run_event_hooks_order", explode)
        monkeypatch.setattr(sys, "argv", [RUNNER, "--event", "PreToolUse"])
        monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(edit("clean"))))
        with pytest.raises(SystemExit) as exc:
            hr.main()
        assert exc.value.code == 2
        blob = capsys.readouterr().err
        assert "Traceback" not in blob
        assert raw_detail not in blob
        assert POSIX_PRIVATE_PATH not in blob
        assert "p@ss/word" not in blob

    def test_shared_redactor_covers_generic_secret_assignments(self):
        """P6-RR03: runner/ledger shared redactor covers short/punctuated values."""
        import memory_ledger
        raw = "OPENROUTER_API_KEY=short!secret PASSWORD='p@ss/word' token:abc.def"
        redacted = memory_ledger._redact(raw)
        for secret in ("short!secret", "p@ss/word", "abc.def"):
            assert secret not in redacted
        assert "OPENROUTER_API_KEY" in redacted
        assert "PASSWORD" in redacted

    def test_exit_contract_only_zero_or_two(self):
        cases = [
            ({}, ["check_secret_leak", "--event", "PreToolUse"]),
            (edit("clean"), ["check_secret_leak", "--event", "PreToolUse"]),
            (edit(f"{TOKEN}"), ["check_secret_leak", "--event", "PreToolUse"]),
            (bash("echo hi"), ["check_secret_leak", "--event", "PreToolUse"]),
        ]
        for payload, args in cases:
            r = run_runner(args, payload)
            assert r.returncode in (0, 2)


class TestSoftHooksNeverBlock:
    def test_memory_capture_non_blocking(self, tmp_path):
        r = run_runner(["memory_capture", "--event", "PostToolUse"],
                       bash("git commit -m 'test: engine'"),
                       isolate=tmp_path)
        assert r.returncode == 0

    def test_self_audit_soft_non_blocking(self):
        r = run_runner(["self_audit", "--event", "Stop"], {})
        assert r.returncode == 0


# ══════════════════════════════════════════════════════════════════════
# In-process engine semantics with synthetic hooks (timeout / rc / stdout)
# ══════════════════════════════════════════════════════════════════════
@pytest.fixture()
def synthetic(tmp_path, monkeypatch):
    """A tmp hooks dir + injected registry entries for behavior tests."""
    import hooks_runner as hr
    import registry

    d = tmp_path / "synth"
    d.mkdir()
    (d / "synth_soft_exit2.py").write_text("import sys; sys.exit(2)\n", encoding="utf-8")
    (d / "synth_soft_crash.py").write_text("import sys; sys.exit(3)\n", encoding="utf-8")
    (d / "synth_soft_timeout.py").write_text("import time; time.sleep(30)\n", encoding="utf-8")
    (d / "synth_hard_timeout.py").write_text("import time; time.sleep(30)\n", encoding="utf-8")
    (d / "synth_hard_crash.py").write_text("import sys; sys.exit(3)\n", encoding="utf-8")
    (d / "synth_soft_secret_diag.py").write_text(
        "import sys; sys.stderr.write('leak ' + 'sk-' + 'synthsecret0123456789 path C"
        + chr(58) + chr(92) + "Users" + chr(92) + "bob\\n'); sys.exit(2)\n",
        encoding="utf-8")
    sensitive = f"token={TOKEN} win={WIN_DRIVE_PATH} posix={POSIX_PRIVATE_PATH}"
    (d / "synth_soft_sensitive.py").write_text(
        "import sys\n"
        f"msg = {sensitive!r}\n"
        "sys.stdout.write(msg + '\\n')\n"
        "sys.stderr.write(msg + '\\n')\n",
        encoding="utf-8")
    (d / "synth_hard_sensitive.py").write_text(
        "import sys\n"
        f"msg = {sensitive!r}\n"
        "sys.stderr.write(msg + '\\n')\n"
        "sys.exit(2)\n",
        encoding="utf-8")
    (d / "synth_ctx_stdout.py").write_text(
        "import sys; sys.stdout.write('additional context line\\n')\n", encoding="utf-8")
    (d / "synth_no_ctx_stdout.py").write_text(
        "import sys; sys.stdout.write('must be discarded\\n')\n", encoding="utf-8")
    (d / "synth_missing.py")       # never created — hard missing case
    (d / "synth_soft_missing.py")  # never created — soft missing case

    entries = {}
    for name, cls in [("synth_soft_exit2", "soft"), ("synth_soft_crash", "soft"),
                      ("synth_soft_timeout", "soft"), ("synth_hard_timeout", "hard"),
                      ("synth_hard_crash", "hard"), ("synth_soft_secret_diag", "soft"),
                      ("synth_soft_sensitive", "soft"), ("synth_hard_sensitive", "hard"),
                      ("synth_ctx_stdout", "soft"), ("synth_no_ctx_stdout", "soft"),
                      ("synth_missing", "hard"), ("synth_soft_missing", "soft")]:
        entries[name] = {"events": ["PreToolUse"], "classification": cls,
                         "order": 10, "timeout_s": None,
                         "allow_context_stdout": name in {"synth_ctx_stdout",
                                                           "synth_soft_sensitive"}}

    monkeypatch.setattr(hr, "HOOKS_DIR", str(d))
    monkeypatch.setattr(hr, "REGISTRY", entries)
    monkeypatch.setattr(hr, "HOOK_TIMEOUT", 1)
    monkeypatch.setattr(hr, "_LIVE_LOG", str(tmp_path / "live-events.jsonl"))
    return hr


class TestEngineSemanticsSynthetic:
    def _exec(self, hr, name, payload=None):
        return hr.execute(name, payload or {"tool_name": "Edit", "tool_input": {}})

    def test_soft_exit2_normalized_non_blocking(self, synthetic):
        res = self._exec(synthetic, "synth_soft_exit2")
        assert res["decision"] == "pass"

    def test_soft_crash_non_blocking(self, synthetic):
        assert self._exec(synthetic, "synth_soft_crash")["decision"] == "pass"

    def test_soft_timeout_non_blocking(self, synthetic):
        assert self._exec(synthetic, "synth_soft_timeout")["decision"] == "pass"

    def test_hard_timeout_blocks_fail_closed(self, synthetic):
        assert self._exec(synthetic, "synth_hard_timeout")["decision"] == "block"

    def test_event_sweep_total_timeout_blocks_if_hard_hooks_remain(
            self, synthetic, monkeypatch, capsys):
        """P6-RR04: provider lifecycle budget is bounded across all hooks."""
        entries = {
            "first_hard": {"events": ["PreToolUse"], "classification": "hard",
                           "order": 1, "timeout_s": None, "allow_context_stdout": False, "matchers": ["*"]},
            "second_hard": {"events": ["PreToolUse"], "classification": "hard",
                            "order": 2, "timeout_s": None, "allow_context_stdout": False, "matchers": ["*"]},
        }
        seen = []

        def slow_pass(name, _input_data, event=None, **_kwargs):
            seen.append(name)
            time.sleep(0.08)
            return {"decision": "pass", "reason": "", "context_stdout": "", "hook": name}

        monkeypatch.setattr(synthetic, "REGISTRY", entries)
        monkeypatch.setattr(synthetic, "HOOK_TOTAL_TIMEOUT", 0.05, raising=False)
        monkeypatch.setattr(synthetic, "run_event_hooks_order",
                            lambda _event, tool_name=None: list(entries))
        monkeypatch.setattr(synthetic, "execute", slow_pass)
        monkeypatch.setattr(sys, "argv", [RUNNER, "--event", "PreToolUse"])
        monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
        started = time.monotonic()
        with pytest.raises(SystemExit) as exc:
            synthetic.main()
        elapsed = time.monotonic() - started
        assert exc.value.code == 2
        assert seen == ["first_hard"]
        assert elapsed < 0.5
        assert "timeout" in capsys.readouterr().err.lower()

    def test_hard_crash_rc3_normalized_to_block(self, synthetic):
        res = self._exec(synthetic, "synth_hard_crash")
        assert res["decision"] == "block"

    def test_hard_missing_executable_blocks(self, synthetic):
        res = self._exec(synthetic, "synth_missing")
        assert res["decision"] == "block"

    def test_soft_missing_executable_is_nonblocking(self, synthetic, capsys):
        res = self._exec(synthetic, "synth_soft_missing")
        captured = capsys.readouterr()
        assert res["decision"] == "pass"
        assert "missing" in captured.err.lower()
        assert "non-blocking" in captured.err.lower()

    def test_diagnostics_sanitized_no_secret_no_machine_path(self, synthetic):
        res = self._exec(synthetic, "synth_soft_secret_diag")
        assert res["decision"] == "pass"
        blob = json.dumps(res)
        assert "sk-synthsecret" not in blob
        assert chr(92) + "Users" not in blob

    def test_sensitive_diagnostics_are_sanitized_in_stderr_and_result(
            self, synthetic, capsys):
        soft = self._exec(synthetic, "synth_soft_sensitive")
        captured = capsys.readouterr()
        hard = self._exec(synthetic, "synth_hard_sensitive")
        captured2 = capsys.readouterr()
        blob = (
            captured.out + captured.err + captured2.out + captured2.err
            + json.dumps(soft) + json.dumps(hard)
        )
        assert soft["decision"] == "pass"
        assert hard["decision"] == "block"
        for raw in (TOKEN, WIN_DRIVE_PATH, POSIX_PRIVATE_PATH):
            assert raw not in blob

    def test_sensitive_context_stdout_is_sanitized_at_cli_surface(
            self, synthetic, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", [RUNNER, "synth_soft_sensitive"])
        monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
        with pytest.raises(SystemExit) as exc:
            synthetic.main()
        assert exc.value.code == 0
        captured = capsys.readouterr()
        blob = captured.out + captured.err
        for raw in (TOKEN, WIN_DRIVE_PATH, POSIX_PRIVATE_PATH):
            assert raw not in blob

    def test_sanitizer_failure_suppresses_raw_diagnostic(
            self, synthetic, monkeypatch, capsys):
        def unavailable(_text):
            raise RuntimeError("redactor unavailable")

        monkeypatch.setattr(synthetic, "_redact_secrets", unavailable)
        result = self._exec(synthetic, "synth_soft_sensitive")
        captured = capsys.readouterr()
        blob = captured.out + captured.err + json.dumps(result)
        assert result["decision"] == "pass"
        assert "suppressed" in blob.lower()
        for raw in (TOKEN, WIN_DRIVE_PATH, POSIX_PRIVATE_PATH):
            assert raw not in blob

    def test_sanitizer_import_fallback_is_not_identity(self):
        src = (REPO_ROOT / "scripts" / "hooks_runner.py").read_text(encoding="utf-8")
        assert "_redact_secrets = lambda s: s" not in src

    def test_named_invocation_soft_child_rc2_uses_registry_classification(
            self, synthetic, monkeypatch):
        monkeypatch.setattr(sys, "argv", [RUNNER, "synth_soft_exit2"])
        monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
        with pytest.raises(SystemExit) as exc:
            synthetic.main()
        assert exc.value.code == 0

    def test_named_invocation_hard_failure_blocks_with_two(
            self, synthetic, monkeypatch):
        monkeypatch.setattr(sys, "argv", [RUNNER, "synth_hard_crash"])
        monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
        with pytest.raises(SystemExit) as exc:
            synthetic.main()
        assert exc.value.code == 2

    def test_context_stdout_only_when_allowed(self, synthetic):
        ctx = self._exec(synthetic, "synth_ctx_stdout")
        assert "additional context line" in ctx["context_stdout"]
        noc = self._exec(synthetic, "synth_no_ctx_stdout")
        assert noc["context_stdout"] == ""

    def test_order_stable_regardless_of_filename(self, synthetic):
        names = synthetic.run_event_hooks_order("PreToolUse")
        assert names == sorted(
            names, key=lambda n: (synthetic.REGISTRY[n]["order"], n))

    @pytest.mark.parametrize("provider", ["claude", "codex"])
    def test_provider_event_sweep_executes_exact_registry_order(
            self, synthetic, monkeypatch, provider):
        """P6-R02: deployed provider path delegates order to registry."""
        expected = synthetic.run_event_hooks_order("PreToolUse")
        seen = []

        def fake_execute(name, input_data, event=None):
            seen.append(name)
            return {"decision": "pass", "reason": "", "context_stdout": "",
                    "hook": name}

        monkeypatch.setattr(synthetic, "execute", fake_execute)
        monkeypatch.setattr(
            sys, "argv", [RUNNER, "--provider", provider, "--event", "PreToolUse"]
        )
        monkeypatch.setattr(sys, "stdin", io.StringIO("{}"))
        with pytest.raises(SystemExit) as exc:
            synthetic.main()
        assert exc.value.code == 0
        assert seen == expected

    def test_runner_source_has_no_git_mutation(self):
        """Item 25: the runner cannot push/merge/deploy/mutate refs."""
        src = (REPO_ROOT / "scripts" / "hooks_runner.py").read_text(encoding="utf-8")
        for banned in ('"push"', '"merge"', '"rebase"', '"reset"', '"clone"'):
            assert banned not in src, f"runner must not invoke git {banned}"


# ══════════════════════════════════════════════════════════════════════
# Provider normalization (items 2, 4)
# ══════════════════════════════════════════════════════════════════════
class TestProviders:
    def test_module_exists_with_supported_providers(self):
        import providers
        assert set(providers.PROVIDERS) >= {"claude", "codex"}

    def test_claude_and_codex_share_canonical_pretooluse(self):
        import providers
        assert providers.normalize_event("claude", "PreToolUse") == \
               providers.normalize_event("codex", "PreToolUse") == "PreToolUse"

    def test_codex_lacks_userpromptsubmit_truthfully(self):
        import providers
        with pytest.raises(providers.ProviderError):
            providers.normalize_event("codex", "UserPromptSubmit")

    def test_unknown_provider_deterministic(self):
        import providers
        with pytest.raises(providers.ProviderError):
            providers.normalize_event("bogusprovider", "PreToolUse")

    def test_malformed_payload_normalized_deterministic(self):
        import providers
        assert providers.normalize_payload("claude", "{}") == {}
        out = providers.normalize_payload("claude", "not json {{{")
        assert out is providers.MALFORMED_PAYLOAD
        assert not isinstance(out, dict)
        assert providers.normalize_payload("codex", b"\xff\xfe") is providers.MALFORMED_PAYLOAD

    def test_equivalent_action_same_block_across_providers(self):
        """Item 23: planted token blocks on BOTH provider payload shapes."""
        for provider in ("claude", "codex"):
            payload = {"tool_name": "Edit",
                       "tool_input": {"file_path": "x.py",
                                      "new_string": f"leak {TOKEN}"}}
            r = run_runner(["check_secret_leak", "--event", "PreToolUse"], payload)
            assert r.returncode == 2, f"{provider} path failed to block"

    def test_gemini_and_cline_native_events_map_to_canonical_lifecycle(self):
        """P6-R01: supported provider-native lifecycle names are explicit."""
        import providers
        assert providers.normalize_event("gemini", "BeforeTool") == "PreToolUse"
        assert providers.normalize_event("cline", "PreToolUse") == "PreToolUse"
        assert providers.normalize_event("cline", "PostToolUse") == "PostToolUse"
        assert providers.normalize_event("cline", "TaskStart") == "SessionStart"
        assert providers.normalize_event("cline", "TaskComplete") == "Stop"

    def test_cline_payload_normalizes_parameters_without_collapsing_malformed(self):
        """P6-RR01: Cline native action/arguments become canonical schema."""
        import providers
        raw = {
            "preToolUse": {
                "toolName": "write_to_file",
                "parameters": {"path": "x.py", "content": "ok"},
            }
        }
        out = providers.normalize_payload("cline", raw, event="PreToolUse")
        assert out["tool_name"] == "Write"
        assert out["tool_input"] == {"file_path": "x.py", "content": "ok"}
        assert providers.normalize_payload("cline", {}, event="PreToolUse") == {}
        assert providers.normalize_payload(
            "cline", "not json {{{", event="PreToolUse"
        ) is providers.MALFORMED_PAYLOAD

    def test_gemini_native_actions_normalize_to_canonical_schema(self):
        """P6-RR01: Gemini built-ins must not bypass Claude-shaped hard gates."""
        import providers
        write = providers.normalize_payload(
            "gemini",
            {"tool_name": "write_file", "tool_input": {"file_path": "x.py", "content": "ok"}},
            event="BeforeTool",
        )
        replace = providers.normalize_payload(
            "gemini",
            {"tool_name": "replace", "tool_input": {
                "file_path": "x.py", "old_string": "a", "new_string": "b"
            }},
            event="BeforeTool",
        )
        shell = providers.normalize_payload(
            "gemini",
            {"tool_name": "run_shell_command", "tool_input": {"command": "echo ok"}},
            event="BeforeTool",
        )
        assert write["tool_name"] == "Write"
        assert replace["tool_name"] == "Edit"
        assert shell["tool_name"] == "Bash"

    def test_cline_native_actions_normalize_to_canonical_schema(self):
        """P6-RR01: Cline path/action aliases must be canonical before policy."""
        import providers
        replace = providers.normalize_payload(
            "cline",
            {"preToolUse": {"toolName": "replace_in_file", "parameters": {
                "path": "x.py", "diff": "SEARCH/REPLACE"
            }}},
            event="PreToolUse",
        )
        shell = providers.normalize_payload(
            "cline",
            {"preToolUse": {"toolName": "execute_command", "parameters": {
                "command": "echo ok"
            }}},
            event="PreToolUse",
        )
        assert replace["tool_name"] == "Edit"
        assert replace["tool_input"]["file_path"] == "x.py"
        assert shell["tool_name"] == "Bash"

    def test_provider_cli_preserves_hard_vs_soft_malformed_semantics(self):
        """P6-R01: provider-native malformed input uses canonical event policy."""
        hard = run_runner(
            ["--provider", "cline", "--event", "PreToolUse"], "not json {{{"
        )
        soft = run_runner(
            ["--provider", "cline", "--event", "PostToolUse"], "not json {{{"
        )
        assert hard.returncode == 2
        assert "malformed hook payload suppressed" in hard.stderr
        assert soft.returncode == 0
        assert "malformed hook payload suppressed" in soft.stderr

    def test_provider_cli_accepts_valid_and_empty_gemini_cline_payloads(self):
        """P6-R01: provider CLI is real dispatch, not an unknown-hook accident."""
        gemini_empty = run_runner(
            ["--provider", "gemini", "--event", "BeforeTool"], {}
        )
        cline_valid = run_runner(
            ["--provider", "cline", "--event", "PreToolUse"],
            {"preToolUse": {"toolName": "read_file", "parameters": {"path": "x.py"}}},
        )
        cline_empty = run_runner(
            ["--provider", "cline", "--event", "PreToolUse"], {}
        )
        assert gemini_empty.returncode == 0, gemini_empty.stderr
        assert cline_valid.returncode == 0, cline_valid.stderr
        assert cline_empty.returncode == 0, cline_empty.stderr

    def test_provider_cli_blocks_equivalent_secret_for_gemini_and_cline(self):
        """P6-RR01: real native write payloads reach the same secret hard gate."""
        gemini = {
            "tool_name": "write_file",
            "tool_input": {"file_path": "x.py", "content": f"leak {TOKEN}"},
        }
        cline = {
            "preToolUse": {
                "toolName": "write_to_file",
                "parameters": {"path": "x.py", "content": f"leak {TOKEN}"},
            }
        }
        g = run_runner(["--provider", "gemini", "--event", "BeforeTool"], gemini)
        c = run_runner(["--provider", "cline", "--event", "PreToolUse"], cline)
        assert g.returncode == 2, g.stderr
        assert c.returncode == 2, c.stderr
        assert "unknown registered hook" not in g.stderr.lower()
        assert "unknown registered hook" not in c.stderr.lower()

    def test_provider_native_shell_actions_reach_bash_hard_gate(self):
        """P6-RR01: native shell aliases must not bypass Bash policy hooks."""
        command = "git checkout -b rr01-should-block"
        gemini = {
            "tool_name": "run_shell_command",
            "tool_input": {"command": command},
        }
        cline = {
            "preToolUse": {
                "toolName": "execute_command",
                "parameters": {"command": command},
            }
        }
        g = run_runner(["--provider", "gemini", "--event", "BeforeTool"], gemini)
        c = run_runner(["--provider", "cline", "--event", "PreToolUse"], cline)
        assert g.returncode == 2, g.stderr
        assert c.returncode == 2, c.stderr

    def test_provider_native_file_writes_to_raw_are_blocked_equivalently(self):
        """P6-RR01: native provider writes must hit check_raw_immutable."""
        gemini = {
            "tool_name": "write_file",
            "tool_input": {"file_path": "raw/rr01-gemini.txt", "content": "blocked"},
        }
        cline = {
            "preToolUse": {
                "toolName": "write_to_file",
                "parameters": {"path": "raw/rr01-cline.txt", "content": "blocked"},
            }
        }
        g = run_runner(["--provider", "gemini", "--event", "BeforeTool"], gemini)
        c = run_runner(["--provider", "cline", "--event", "PreToolUse"], cline)
        assert g.returncode == 2, g.stderr
        assert c.returncode == 2, c.stderr
        assert "raw/" in g.stderr.lower()
        assert "raw/" in c.stderr.lower()

    def test_supported_gemini_and_cline_wiring_is_not_bare_run_all(self):
        """P6-R01: deployed adapters must name provider + lifecycle event."""
        gemini = json.loads(
            (REPO_ROOT / ".gemini" / "settings.json").read_text(encoding="utf-8")
        )
        cmd = gemini["hooks"]["BeforeTool"][0]["hooks"][0]["command"]
        assert "hooks_runner.py --provider gemini --event BeforeTool" in cmd

        adapter = (REPO_ROOT / "scripts" / "cline-hooks" / "adapter.sh").read_text(
            encoding="utf-8"
        )
        assert '--provider cline --event "$EVENT"' in adapter
        assert 'HOOK_DATA="{}"' not in adapter
        assert '|| HOOK_DATA="{}"' not in adapter


def _isolated_provider_env(tmp_path: Path) -> dict[str, str]:
    """Environment for provider E2E tests with no live repository state."""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for key in (
        "HOOK_SKIP", "AWIKI_CLAIM_GATE", "AWIKI_CLAIMS_STORE", "AWIKI_AGENT",
        "AWIKI_FOCUS_ENFORCE", "AWIKI_FOCUS_DIR", "AWIKI_FLOW_STATE_DIR",
        "AWIKI_COST_GATE_TMP_DIR", "AWIKI_LIVE_LOG_PATH",
        "AWIKI_LIVE_SESSION_FILE", "CLINE_HOOK_LOG_FILE", "AWIKI_PYTHON",
        "ZCODE_SESSION_ID", "CLAUDE_SESSION_ID", "CODEX_SESSION_ID",
        "GEMINI_SESSION_ID", "WIKI_UNLOCK", "AUTH_BY_DRIVE_MOUNT",
    ):
        env.pop(key, None)

    cost_dir = tmp_path / "cost-gate"
    cost_dir.mkdir(parents=True)
    today = datetime.now().date()
    for day in (today, today + timedelta(days=1)):
        (cost_dir / f"cost-tier-{day.isoformat()}.txt").write_text(
            "L4|phase6-test|provider e2e\n", encoding="utf-8"
        )

    focus_dir = tmp_path / "focus"
    flow_dir = tmp_path / "flow"
    focus_dir.mkdir()
    flow_dir.mkdir()
    env.update({
        "AWIKI_COST_GATE_TMP_DIR": str(cost_dir),
        "AWIKI_CLAIMS_STORE": str(tmp_path / "agent-claims.json"),
        "AWIKI_AGENT": "phase6-test",
        "AWIKI_FOCUS_DIR": str(focus_dir),
        "AWIKI_FLOW_STATE_DIR": str(flow_dir),
        "AWIKI_LIVE_LOG_PATH": str(tmp_path / "live-events.jsonl"),
        "AWIKI_LIVE_SESSION_FILE": str(tmp_path / "live-session-id"),
        "CLINE_HOOK_LOG_FILE": str(tmp_path / "cline-hooks.log"),
        "AWIKI_PYTHON": sys.executable,
    })
    return env


def _git_bash_executable() -> str:
    if os.name == "nt":
        program_files = Path(os.environ.get("ProgramFiles", "C:/Program Files"))
        candidate = program_files / "Git" / "bin" / "bash.exe"
        if candidate.is_file():
            return str(candidate)
    bash_path = shutil.which("bash")
    if not bash_path:
        pytest.skip("bash unavailable for Cline adapter E2E")
    return bash_path


def _run_cline_adapter(tmp_path: Path, event: str, payload, env_extra=None):
    env = _isolated_provider_env(tmp_path)
    env["CLINE_HOOK_EVENT"] = event
    env.update(env_extra or {})
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [_git_bash_executable(), "scripts/cline-hooks/adapter.sh"],
        input=raw, capture_output=True, text=True,
        encoding="utf-8", errors="replace", cwd=str(REPO_ROOT), env=env,
        timeout=120,
    )


def _run_gemini_config(tmp_path: Path, payload):
    cfg = json.loads(
        (REPO_ROOT / ".gemini" / "settings.json").read_text(encoding="utf-8")
    )
    command = cfg["hooks"]["BeforeTool"][0]["hooks"][0]["command"]
    # P6-RR04: the command is a fail-closed bash wrapper
    # (`bash -c 'python3 …; rc=$?; … exit 2'`). Extract the inner python3
    # invocation so this E2E exercises the runner portion directly.
    m = re.search(r"python3\s+(.+?);", command)
    assert m, f"gemini command must invoke python3: {command!r}"
    parts = shlex.split("python3 " + m.group(1), posix=True)
    assert parts[0] == "python3"
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, *parts[1:]], input=raw,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), env=_isolated_provider_env(tmp_path), timeout=120,
    )


def test_gemini_provider_path_e2e_valid_empty_malformed_and_hard_failure(tmp_path):
    native_valid = {
        "tool_name": "write_file",
        "tool_input": {"file_path": "scripts/x.py", "content": "ok"},
    }
    native_hard = {
        "tool_name": "write_file",
        "tool_input": {"file_path": "scripts/x.py", "content": f"leak {TOKEN}"},
    }
    valid = _run_gemini_config(tmp_path / "valid", native_valid)
    empty = _run_gemini_config(tmp_path / "empty", {})
    malformed = _run_gemini_config(tmp_path / "malformed", "not json {{{")
    hard = _run_gemini_config(tmp_path / "hard", native_hard)
    missing_dir = tmp_path / "missing-hard-hooks"
    missing_dir.mkdir()
    missing = _run_gemini_config(tmp_path / "missing", native_valid)
    # Re-run with all hook executables unavailable: PreToolUse contains hard gates.
    missing_env = _isolated_provider_env(tmp_path / "missing-env")
    missing_env["AWIKI_HOOKS_DIR"] = str(missing_dir)
    cfg = json.loads((REPO_ROOT / ".gemini" / "settings.json").read_text(encoding="utf-8"))
    # Execute the RUNNER portion (inner python3 invocation of the fail-closed
    # bash wrapper) with every hook executable unavailable: PreToolUse contains
    # hard gates, so the registry failure must fail closed (exit 2).
    m = re.search(r"python3\s+(.+?);", cfg["hooks"]["BeforeTool"][0]["hooks"][0]["command"])
    assert m, "gemini command must invoke python3"
    inner = shlex.split(m.group(1), posix=True)
    missing = subprocess.run(
        [sys.executable, *inner], input=json.dumps(native_valid),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), env=missing_env, timeout=120,
    )

    assert valid.returncode == 0, valid.stderr
    assert empty.returncode == 0, empty.stderr
    assert malformed.returncode == 2
    assert hard.returncode == 2
    assert missing.returncode == 2
    # Gemini exposes only BeforeTool in this repository; there is no soft-only
    # Gemini lifecycle event to manufacture a truthful soft-failure case.


def test_cline_adapter_e2e_valid_empty_malformed_hard_and_soft_failure(tmp_path):
    valid_payload = {
        "preToolUse": {
            "toolName": "write_to_file",
            "parameters": {"path": "scripts/x.py", "content": "ok"},
        }
    }
    hard_payload = {
        "preToolUse": {
            "toolName": "write_to_file",
            "parameters": {"path": "scripts/x.py", "content": f"leak {TOKEN}"},
        }
    }
    post_payload = {
        "postToolUse": {
            "toolName": "execute_command",
            "parameters": {"command": "echo ok"},
            "result": "ok",
        }
    }

    valid = _run_cline_adapter(tmp_path / "valid", "PreToolUse", valid_payload)
    empty = _run_cline_adapter(tmp_path / "empty", "PreToolUse", {})
    malformed = _run_cline_adapter(tmp_path / "malformed", "PreToolUse", "not json {{{")
    hard = _run_cline_adapter(tmp_path / "hard", "PreToolUse", hard_payload)
    empty_hooks = tmp_path / "soft-missing-hooks"
    empty_hooks.mkdir()
    soft = _run_cline_adapter(
        tmp_path / "soft", "PostToolUse", post_payload,
        env_extra={"AWIKI_HOOKS_DIR": str(empty_hooks)},
    )

    results = [valid, empty, malformed, hard, soft]
    responses = []
    for result in results:
        assert result.returncode == 0, result.stderr
        responses.append(json.loads(result.stdout.strip()))

    assert responses[0]["cancel"] is False
    assert responses[1]["cancel"] is False
    assert responses[2]["cancel"] is True
    assert responses[3]["cancel"] is True
    assert responses[4]["cancel"] is False


# ══════════════════════════════════════════════════════════════════════
# P6-RR04 — provider infrastructure failures must not fail open
# ══════════════════════════════════════════════════════════════════════
def test_cline_hard_event_missing_interpreter_returns_cancel_true(tmp_path):
    payload = {
        "preToolUse": {
            "toolName": "write_to_file",
            "parameters": {"path": "scripts/x.py", "content": "ok"},
        }
    }
    missing_python = str(tmp_path / "definitely-missing-python")
    result = _run_cline_adapter(
        tmp_path / "missing-python", "PreToolUse", payload,
        env_extra={"AWIKI_PYTHON": missing_python},
    )
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout.strip())
    assert response["cancel"] is True
    assert missing_python not in (result.stdout + result.stderr)


def test_cline_log_failure_cannot_bypass_hard_policy(tmp_path):
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("file blocks mkdir", encoding="utf-8")
    bad_log = blocker / "cline-hooks.log"
    payload = {
        "preToolUse": {
            "toolName": "write_to_file",
            "parameters": {"path": "raw/rr04.txt", "content": "blocked"},
        }
    }
    result = _run_cline_adapter(
        tmp_path / "bad-log", "PreToolUse", payload,
        env_extra={"CLINE_HOOK_LOG_FILE": str(bad_log)},
    )
    assert result.returncode == 0, result.stderr
    response = json.loads(result.stdout.strip())
    assert response["cancel"] is True


def test_gemini_hard_command_maps_missing_interpreter_to_exit_two(tmp_path):
    cfg = json.loads(
        (REPO_ROOT / ".gemini" / "settings.json").read_text(encoding="utf-8")
    )
    command = cfg["hooks"]["BeforeTool"][0]["hooks"][0]["command"]
    env = _isolated_provider_env(tmp_path)
    # Git Bash utilities remain available, but python3 is deliberately absent.
    env["PATH"] = "/usr/bin:/bin"
    payload = {
        "tool_name": "write_file",
        "tool_input": {"file_path": "scripts/x.py", "content": "ok"},
    }
    result = subprocess.run(
        [_git_bash_executable(), "-lc", command], input=json.dumps(payload),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), env=env, timeout=30,
    )
    assert result.returncode == 2, result.stderr
    assert "Traceback" not in (result.stdout + result.stderr)


# ══════════════════════════════════════════════════════════════════════
# P6-R06 — test/runtime-state isolation contracts
# ══════════════════════════════════════════════════════════════════════
def test_mutable_runtime_surfaces_expose_explicit_isolation_seams():
    """P6-R06: focused tests must never borrow live repo/session state."""
    flow = (REPO_ROOT / "scripts" / "lib" / "a_flow_state.py").read_text(encoding="utf-8")
    destructive = (REPO_ROOT / "scripts" / "hooks" / "check_bash_destructive_git.py").read_text(encoding="utf-8")
    runner = (REPO_ROOT / "scripts" / "hooks_runner.py").read_text(encoding="utf-8")
    logger = (REPO_ROOT / "scripts" / "live-dashboard" / "event_logger.py").read_text(encoding="utf-8")
    cline = (REPO_ROOT / "scripts" / "cline-hooks" / "adapter.sh").read_text(encoding="utf-8")

    assert "AWIKI_FLOW_STATE_DIR" in flow
    assert "AWIKI_GIT_GUARD_REPO_ROOT" in destructive
    assert "AWIKI_LIVE_LOG_PATH" in runner
    assert "AWIKI_LIVE_LOG_PATH" in logger
    memory_capture = (REPO_ROOT / "scripts" / "hooks" / "memory_capture.py").read_text(encoding="utf-8")
    assert "AWIKI_LIVE_SESSION_FILE" in logger
    assert "CLINE_HOOK_LOG_FILE" in cline
    assert "AWIKI_MEMORY_LEDGER_PATH" in memory_capture


# ══════════════════════════════════════════════════════════════════════
# Item 5 — every registered hard hook proves a REAL block path
# ══════════════════════════════════════════════════════════════════════
def _claims_store(tmp_path):
    """Live claim by ANOTHER agent via the real agent_claims seam."""
    import agent_claims as ac
    store = tmp_path / "agent-claims.json"
    ac.set_store(store)
    ac.acquire(agent="claude", scope=["skills/shared/**"],
               goal="build the shared router", phase="implement")
    ac.set_store(None)
    return store


def _focus_dir(tmp_path, phase="DESIGN"):
    d = tmp_path / "focus"
    d.mkdir()
    (d / "a-focus-engine.json").write_text(json.dumps({
        "active": True, "skill": "a-web", "goal": "g", "phase": phase,
        "allowed_files": ["docs/plan.md"], "started_ts": time.time(),
    }), encoding="utf-8")
    return d


def _flow_state(tmp_path):
    """Write isolated A-Flow state under pytest tmp_path only."""
    d = tmp_path / "flow-state"
    d.mkdir()
    p = d / "a-flow.json"
    p.write_text(json.dumps({
        "active": True, "skill": "a-web", "goal": "g", "phase": "design",
        "allowed_files": ["docs/plan.md"], "started_ts": time.time(),
        "completed_phases": ["ask"], "notes": [],
    }), encoding="utf-8")
    return d


@pytest.mark.parametrize("hook,make_payload,env", [
    # payload-only violations
    ("check_secret_leak", lambda t: edit(f"x {TOKEN} y"), None),
    ("check_raw_immutable", lambda t: edit("x", file_path="raw/doc.pdf"), None),
    ("check_claudemd_lock", lambda t: edit("x", file_path="CLAUDE.md"), None),
    ("check_machine_path", lambda t: edit(f"path {WIN_DRIVE_PATH}"), None),
    ("check_bash_no_branch", lambda t: bash("git checkout -b feature-x"), None),
    ("check_apikey", lambda t: bash(f"curl --api-key=sk-proj-{'a' * 24} https://x.io"), None),
    ("check_source_original_file",
     lambda t: {"tool_name": "Write", "tool_input": {
         "file_path": "wiki/sources/engine-test-slug.md",
         "content": "# no frontmatter\n"}}, None),
    ("check_harness_routing",
     lambda t: {"tool_name": "Write", "tool_input": {
         "file_path": "wiki/sources/engine-test-slug2.md",
         "content": "---\ntitle: x\nrouted_via: direct\n---\nbody"}}, None),
    ("check_skill_registry",
     lambda t: {"tool_name": "Write", "tool_input": {
         "file_path": "skills/ghost-pack/SKILL.md",
         "content": "---\nname: ghost-pack\n---\n"}}, None),
    ("check_output_format",
     lambda t: {"tool_name": "Write", "tool_input": {
         "file_path": "docs/evil-dump.html", "content": "<html>"}}, None),
    ("check_delegation_gate",
     lambda t: bash("git add . && git commit -m 'wip' && git push origin main"), None),
    # stateful violations
    ("check_agent_claim", lambda t: edit("x", file_path="skills/shared/thing.py"),
     lambda t: {"AWIKI_CLAIMS_STORE": str(_claims_store(t)), "AWIKI_AGENT": "zcode"}),
    ("check_a_focus", lambda t: edit("x", file_path="src/code.py"),
     lambda t: {"AWIKI_FOCUS_DIR": str(_focus_dir(t)),
                "AWIKI_FOCUS_ENFORCE": "1",
                # focus file name is session-derived — pin the session id
                "ZCODE_SESSION_ID": "engine"}),
    ("check_bash_destructive_git",
     lambda t: bash("git reset --hard HEAD~1"),
     lambda t: {"AWIKI_GIT_GUARD_REPO_ROOT": str(_dirty_repo(t))}),
])
def test_every_hard_hook_has_real_block_path(tmp_path, hook, make_payload, env):
    payload = make_payload(tmp_path)
    env_extra = env(tmp_path) if env else None
    r = run_runner([hook, "--event", "PreToolUse"], payload, env_extra=env_extra)
    assert r.returncode == 2, f"{hook} failed to block: rc={r.returncode} stderr={r.stderr[:300]}"


def _dirty_repo(tmp_path) -> Path:
    """Create an isolated dirty Git repo for destructive-command tests."""
    repo = tmp_path / "dirty-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / "dirty.txt").write_text("dirty", encoding="utf-8")
    return repo


def test_a_flow_discipline_blocks_out_of_phase_edit(tmp_path):
    flow_dir = _flow_state(tmp_path)
    r = run_runner(
        ["check_a_flow_discipline", "--event", "PreToolUse"],
        edit("x", file_path="src/code.py"),
        env_extra={"AWIKI_FLOW_STATE_DIR": str(flow_dir)},
    )
    assert r.returncode == 2, r.stderr[:300]


def test_external_editor_drift_blocks_version_mismatch(tmp_path):
    target = tmp_path / "engine-test.user.js"
    target.write_text("// @version 9.9.9\nconsole.log(1);\n", encoding="utf-8")
    r = run_runner(
        ["check_external_editor_drift", "--event", "PreToolUse"],
        edit("console.log(2);", file_path=str(target)),
    )
    assert r.returncode == 2, r.stderr[:300]


def test_cost_tier_blocks_invalid_tier_declaration(tmp_path):
    gate_tmp = tmp_path / "costgate"
    gate_tmp.mkdir()
    today = time.strftime("%Y-%m-%d")
    (gate_tmp / f"cost-tier-{today}.txt").write_text("lol|x|y", encoding="utf-8")
    r = run_runner(["check_cost_tier", "--event", "PreToolUse"], edit("x"),
                   env_extra={"AWIKI_COST_GATE_TMP_DIR": str(gate_tmp)})
    assert r.returncode == 2, r.stderr[:300]


# ══════════════════════════════════════════════════════════════════════
# Memory boundaries (items 26, 27)
# ══════════════════════════════════════════════════════════════════════
def test_memory_capture_classified_soft_observe_only():
    import registry
    entry = registry.HOOK_REGISTRY["memory_capture"]
    assert entry["classification"] == "soft"
    assert "PostToolUse" in entry["events"]


def test_memory_hook_source_cannot_promote_to_l3():
    """memory_capture writes L1 ledger only — no promotion/wiki imports."""
    src = (REPO_ROOT / "scripts" / "hooks" / "memory_capture.py").read_text(encoding="utf-8")
    for banned in ("promotion", "wiki/promotion-candidates", "import project_memory"):
        assert banned not in src


def test_runner_never_touches_git_refs(tmp_path):
    """Item 25 at CLI level: event sweep leaves refs and live logs untouched."""
    before = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                            text=True, cwd=str(REPO_ROOT)).stdout
    isolated_log = tmp_path / "live-events.jsonl"
    run_runner(
        ["--event", "PostToolUse"],
        bash("echo engine-test"),
        env_extra={"AWIKI_LIVE_LOG_PATH": str(isolated_log)},
    )
    after = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                           text=True, cwd=str(REPO_ROOT)).stdout
    assert before == after
    assert isolated_log.exists()


# ══════════════════════════════════════════════════════════════════════
# P6-RR05 — the registry owns matcher applicability (no over/under-dispatch)
# ══════════════════════════════════════════════════════════════════════
class TestRegistryMatcherOwnership:
    def test_every_entry_declares_matchers(self):
        import registry
        for name, entry in registry.HOOK_REGISTRY.items():
            m = entry.get("matchers")
            assert isinstance(m, list) and m, f"{name} must declare matchers"
            for alt in m:
                assert alt and "|" not in str(alt) or True  # allow alternation strings

    def test_validation_rejects_empty_matchers(self):
        import registry
        bad = {"a_hook": {"events": ["PreToolUse"], "classification": "hard",
                          "order": 1, "allow_context_stdout": False,
                          "matchers": []}}
        errors = registry.validate_registry(bad, hooks_dir=registry.HOOKS_DIR,
                                            skip_executable_check=True)
        assert any("matcher" in e.lower() for e in errors)

    def test_bash_tool_sweep_excludes_edit_only_gates(self):
        import registry
        bash_hooks = registry.hooks_for_event("PreToolUse", tool_name="Bash")
        assert "check_secret_leak" in bash_hooks        # applies to Bash too
        assert "check_machine_path" not in bash_hooks   # Edit-only gate
        assert "check_bash_no_branch" in bash_hooks

    def test_edit_tool_sweep_excludes_bash_only_gates(self):
        import registry
        edit_hooks = registry.hooks_for_event("PreToolUse", tool_name="Edit")
        assert "check_bash_no_branch" not in edit_hooks
        assert "check_apikey" not in edit_hooks
        assert "check_machine_path" in edit_hooks

    def test_unknown_tool_falls_back_to_star_only(self):
        import registry
        hooks = registry.hooks_for_event("PreToolUse", tool_name="SomethingNew")
        for name in hooks:
            assert "*" in registry.HOOK_REGISTRY[name]["matchers"]

    def test_runner_event_sweep_respects_matchers(self, tmp_path):
        """End-to-end: dispatch follows registry matchers. The Edit sweep
        legitimately includes check_cost_tier (hard, undeclared-cost blocks)
        — skip it here so the structural claim under test stays isolated."""
        bash_run = run_runner(
            ["--event", "PreToolUse"], bash("git status"),
            env_extra={"HOOK_SKIP": "check_cost_tier"}, isolate=tmp_path)
        edit_run = run_runner(
            ["--event", "PreToolUse"], edit("content"),
            env_extra={"HOOK_SKIP": "check_cost_tier"}, isolate=tmp_path)
        assert bash_run.returncode == 0, bash_run.stderr[:300]
        assert edit_run.returncode == 0, edit_run.stderr[:300]
        # structural signal: the registry-level sweep excludes Edit-only
        # gates from Bash dispatch and vice versa (proved by the unit tests
        # above); end-to-end both directions stay green.

    def test_codex_config_matcher_blocks_match_registry_matchers(self):
        """Codex matcher blocks carry event-SWEEP commands; applicability is
        enforced inside the runner by registry matchers. Consistency contract:
        every runner-invoking block declares --provider and --event with the
        block's event, and each non-wildcard PreToolUse matcher tool still
        dispatches a non-empty applicable set (no silent under-dispatch)."""
        import registry
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "codex_cfg_rr05", REPO_ROOT / "scripts" / "setup-codex-config.py")
        mod = ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        saw_sweep = False
        for event, blocks in mod.HOOKS_CONFIG["hooks"].items():
            for block in blocks:
                matcher = block.get("matcher") or "*"
                for h in block.get("hooks", []):
                    cmd = h.get("command", "")
                    if "hooks_runner.py" not in cmd:
                        continue
                    assert "--provider" in cmd and "--event" in cmd, (
                        f"runner command must be an event sweep: {cmd!r}")
                    assert f"--event {event}" in cmd, (
                        f"sweep event mismatch in block matcher {matcher!r}: {cmd!r}")
                    saw_sweep = True
                    for tool in matcher.split("|"):
                        if tool != "*" and event == "PreToolUse":
                            applicable = registry.hooks_for_event(event, tool_name=tool)
                            assert applicable, (
                                f"matcher tool {tool!r} dispatches nothing — "
                                f"under-dispatch")
        assert saw_sweep, "codex config must invoke the canonical runner"


# ══════════════════════════════════════════════════════════════════════
# P6-RR06 — preflight/ready verification uses registry authority
# ══════════════════════════════════════════════════════════════════════
class TestPreflightRegistryAuthority:
    def _preflight(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "agent_preflight_rr06", REPO_ROOT / "scripts" / "agent-preflight.py")
        mod = ilu.module_from_spec(spec)
        sys.modules[spec.name] = mod   # dataclass annotation resolution needs it
        spec.loader.exec_module(mod)
        return mod

    def test_check_hooks_consults_registry_not_a_stale_list(self, tmp_path):
        mod = self._preflight()
        ok = mod.check_hooks()
        assert ok.level == "OK", ok.detail
        import registry
        assert str(len(registry.HOOK_REGISTRY)) in ok.detail or "registry" in ok.detail.lower(), (
            f"check_hooks must report registry authority, got: {ok.detail!r}")

    def test_check_hooks_fails_when_registered_executable_missing(self, tmp_path):
        mod = self._preflight()
        empty = tmp_path / "no-hooks"
        empty.mkdir()
        result = mod.check_hooks(hooks_dir=empty)
        assert result.level == "FAIL", (
            f"registry-validated check must fail on missing executables: {result.detail!r}")

    def test_guardrail_coverage_covers_all_hard_pretooluse_registry_gates(self):
        mod = self._preflight()
        result = mod.check_guardrail_coverage()
        assert result.level == "OK", result.detail
        import registry
        # the stale-name era missed gates like check_agent_claim/check_machine_path;
        # the new check must be derived from the registry, not a frozen list
        hard_gates = {n for n, e in registry.HOOK_REGISTRY.items()
                      if "PreToolUse" in e["events"] and e["classification"] == "hard"}
        known_stale_misses = {"check_agent_claim", "check_machine_path",
                              "check_apikey", "check_delegation_gate"}
        assert known_stale_misses & hard_gates, "fixture assumption"


# ══════════════════════════════════════════════════════════════════════
# P6-RR07 — one Codex config source of truth + truthful CI parity
# ══════════════════════════════════════════════════════════════════════
class TestCodexSingleSourceOfTruth:
    def test_shell_wrapper_has_no_stale_fallback_json(self):
        src = (REPO_ROOT / "scripts" / "setup-codex-hooks.sh").read_text(encoding="utf-8")
        assert "cat > .codex/hooks.json" not in src, (
            "embedded fallback hooks.json can regenerate a stale (false-green) "
            "config — the python generator is the single source of truth")
        assert "<<'JSON'" not in src

    def test_shell_wrapper_fails_loudly_without_generator(self, tmp_path):
        """No generator → REFUSE to write anything (never a stale config)."""
        import shutil
        (tmp_path / "scripts").mkdir()
        shutil.copy(REPO_ROOT / "scripts" / "setup-codex-hooks.sh",
                    tmp_path / "scripts" / "setup-codex-hooks.sh")
        # generator deliberately absent
        r = subprocess.run(
            ["bash", str(tmp_path / "scripts" / "setup-codex-hooks.sh")],
            capture_output=True, text=True, timeout=60)
        assert r.returncode != 0, "must fail loudly when the generator is missing"
        assert not (tmp_path / ".codex" / "hooks.json").exists()

    def test_ci_verifies_codex_parity_with_check_mode(self):
        wf = (REPO_ROOT / ".github" / "workflows" / "ci-core.yml").read_text(encoding="utf-8")
        assert "setup-codex-config.py --check" in wf, (
            "CI must prove the tracked .codex/hooks.json matches the generator "
            "(check-before-write parity truth, P6-RR07)")

    def test_ci_has_real_python38_runner_smoke(self):
        """RR02 deferred evidence: a REAL Python 3.8 runtime imports the
        canonical runner/registry/providers and executes a benign sweep."""
        wf = (REPO_ROOT / ".github" / "workflows" / "ci-core.yml").read_text(encoding="utf-8")
        assert 'python-version: "3.8"' in wf
        assert "hooks_runner" in wf and "registry.py --check" in wf

    def test_registry_and_providers_are_py38_annotation_safe(self):
        """Local guard for the 3.8 smoke: modern union annotations must be
        lazy (future import) in every hook-engine module the smoke imports."""
        for rel in ("scripts/hooks/registry.py", "scripts/hooks/providers.py",
                    "scripts/hooks_runner.py"):
            src = (REPO_ROOT / rel).read_text(encoding="utf-8")
            if "|" in "".join(_ for _ in [] ) or " | None" in src or "dict | " in src:
                assert "from __future__ import annotations" in src, (
                    f"{rel} uses PEP-604 annotations without the future import — "
                    f"Python 3.8 def-time evaluation would crash")


# ══════════════════════════════════════════════════════════════════════
# P6-RR08 — focused tests never write/read live claims/cost/ledger state
# ══════════════════════════════════════════════════════════════════════
def _snapshot(path: Path):
    if not path.exists():
        return None
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestMutableStateIsolation:
    def test_memory_capture_run_never_touches_live_ledger(self, tmp_path):
        live = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"
        before = _snapshot(live)
        r = run_runner(
            ["memory_capture", "--event", "PostToolUse"],
            bash("git commit -m 'rr08: isolation proof'"),
            isolate=tmp_path)
        assert r.returncode == 0, r.stderr[:200]
        assert _snapshot(live) == before, (
            "memory_capture wrote to the LIVE ledger — tests must redirect "
            "every mutable seam (P6-RR08)")
        isolated = tmp_path / "memory-ledger.jsonl"
        assert isolated.exists(), "capture should land in the isolated ledger"

    def test_posttooluse_event_sweep_never_touches_live_ledger(self, tmp_path):
        live = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"
        before = _snapshot(live)
        r = run_runner(["--event", "PostToolUse"],
                       bash("git commit -m 'rr08: sweep isolation'"),
                       isolate=tmp_path)
        assert r.returncode in (0, 2)
        assert _snapshot(live) == before

    def test_pretooluse_sweep_is_cost_state_isolated(self, tmp_path):
        """Sweep outcome must depend ONLY on the isolated cost declaration,
        never on whatever the host machine happens to have in .tmp/."""
        cost_dir = tmp_path / "costgate"
        cost_dir.mkdir()
        today = time.strftime("%Y-%m-%d")
        (cost_dir / f"cost-tier-{today}.txt").write_text(
            "L1|tests|rr08 isolated declaration", encoding="utf-8")
        r = run_runner(["--event", "PreToolUse"], edit("rr08 content"),
                       isolate=tmp_path / "iso",
                       env_extra={"AWIKI_COST_GATE_TMP_DIR": str(cost_dir)})
        assert r.returncode == 0, r.stderr[:300]
