"""Issue #74: opt-in fail-closed claims without changing lenient consumers."""
import subprocess

import pytest

from conductor import state


HEADER = "| Chunk/WO | Agent | Claimed | Scope | Branch / PR |\n|---|---|---|---|---|\n"
ROW = "| WO-P1-551 | owner | 2026-11-06 | conductor/** | main |\n"


@pytest.fixture
def repo(tmp_path):
    def git(*args):
        return subprocess.run(
            ["git", "-c", "user.name=Test", "-c", "user.email=noreply",
             *args], cwd=tmp_path, check=True, capture_output=True, text=True,
        ).stdout.strip()

    git("init", "-b", "main")
    (tmp_path / "COLLAB.md").write_text(HEADER + ROW, encoding="utf-8")
    git("add", "COLLAB.md")
    git("commit", "-m", "seed claim")
    return tmp_path


def test_happy_path_matches_legacy_canonical_record(repo):
    expected = state.read_canonical_claim(repo, "WO-P1-551")
    assert state.read_canonical_claim_strict(repo, "WO-P1-551") == expected
    assert expected["generation"] == 1


@pytest.mark.parametrize("bad", [
    "| WO-P1-551 | foreign-owner |",
    "| unrelated | foreign-owner |",
    "| unrelated | foreign-owner | date | scope | branch | extra |",
    "| _placeholder |",
    "|---|---|",
    "| WO-P1-551 | foreign-owner | date | scope | main ||",
])
def test_malformed_row_anywhere_in_claim_region_refuses(repo, bad):
    (repo / "COLLAB.md").write_text(HEADER + ROW + "\n" + bad + "\n", encoding="utf-8")
    with pytest.raises(state.ClaimLookupError, match="CLAIM_TABLE_MALFORMED"):
        state.read_canonical_claim_strict(repo, "WO-P1-551")


@pytest.mark.parametrize("conflict", [False, True])
@pytest.mark.parametrize("reader", ["parser", "canonical"])
def test_short_lane_row_cannot_hide_claims(repo, conflict, reader):
    row = ROW.replace("WO-P1-551", "TASK-X")
    text = HEADER + row + "| Lane | someone |\n"
    if conflict:
        text += row.replace("| owner |", "| conflicting-owner |")
    (repo / "COLLAB.md").write_text(text, encoding="utf-8")
    with pytest.raises(state.ClaimLookupError, match="CLAIM_TABLE_MALFORMED"):
        if reader == "parser":
            state.parse_claims_strict(repo / "COLLAB.md")
        else:
            state.read_canonical_claim_strict(repo, "TASK-X")


def test_legacy_malformed_conflict_still_skips(repo):
    (repo / "COLLAB.md").write_text(
        HEADER + ROW + "| WO-P1-551 | foreign-owner |\n", encoding="utf-8")
    assert state.read_canonical_claim(repo, "WO-P1-551")["agent"] == "owner"


def test_ambiguity_refuses(repo):
    (repo / "COLLAB.md").write_text(HEADER + ROW + ROW, encoding="utf-8")
    with pytest.raises(state.ClaimLookupError, match="CLAIM_AMBIGUOUS"):
        state.read_canonical_claim_strict(repo, "WO-P1-551")


@pytest.mark.parametrize("encoding,newline", [
    ("utf-8", "\r\n"), ("utf-8-sig", "\n"), ("utf-8-sig", "\r\n"),
])
def test_windows_bom_and_crlf_tolerance(repo, encoding, newline):
    # BOM directly before the header also exercises header recognition.
    (repo / "COLLAB.md").write_bytes((HEADER + ROW).replace("\n", newline).encode(encoding))
    result = state.read_canonical_claim_strict(repo, "WO-P1-551")
    assert result["agent"] == "owner"
    assert result["scope"] == ["conductor/**"]


@pytest.mark.parametrize("command", ["rev-parse", "log", "diff"])
def test_git_history_unavailable_is_typed_error(repo, monkeypatch, command):
    original = state._git

    def unavailable(root, *args):
        if args[0] == command:
            raise state.ClaimLookupError("GIT_UNAVAILABLE: injected " + command)
        return original(root, *args)

    monkeypatch.setattr(state, "_git", unavailable)
    with pytest.raises(state.ClaimLookupError, match="GIT_UNAVAILABLE"):
        state.read_canonical_claim_strict(repo, "WO-P1-551")


def test_legacy_git_history_failure_still_defaults_to_one(repo, monkeypatch):
    def unavailable(*args):
        raise state.ClaimLookupError("GIT_UNAVAILABLE: injected")

    monkeypatch.setattr(state, "_git", unavailable)
    assert state.claim_generation(repo, "WO-P1-551") == 1


def test_strict_generation_rejects_shallow_history(repo, monkeypatch):
    monkeypatch.setattr(state, "_git", lambda *args: "true")
    with pytest.raises(state.ClaimLookupError, match="GIT_HISTORY_SHALLOW"):
        state.claim_generation_strict(repo, "WO-P1-551")


def test_strict_generation_counts_pending_replacement(repo):
    (repo / "COLLAB.md").write_text(
        HEADER + ROW.replace("| owner |", "| replacement |"), encoding="utf-8")
    assert state.claim_generation_strict(repo, "WO-P1-551") == 2


def test_parser_region_excludes_other_tables_and_prose(tmp_path):
    collab = tmp_path / "COLLAB.md"
    collab.write_text(
        "| Lane | Description |\n|---|---|\n| malformed |\n\n" + HEADER + ROW
        + "\n| Lane | Description |\n|---|---|\n| malformed |\n"
        + "prose ends table\n| malformed |\n", encoding="utf-8")
    claims = state.parse_claims_strict(collab)
    assert claims == state.parse_claims(collab)
    assert [claim["chunk"] for claim in claims] == ["WO-P1-551"]


def test_empty_branch_cell_is_not_stripped_away(tmp_path):
    collab = tmp_path / "COLLAB.md"
    collab.write_text(HEADER + ROW.replace("main |", "|"), encoding="utf-8")
    assert state.parse_claims_strict(collab)[0]["branch"] == ""


@pytest.mark.parametrize("task,error", [("", "TASK_ID_REQUIRED"), ("missing", "CLAIM_NOT_FOUND")])
def test_exact_task_required(repo, task, error):
    with pytest.raises(state.ClaimLookupError, match=error):
        state.read_canonical_claim_strict(repo, task)


def test_file_read_failure_uses_existing_error_type(tmp_path):
    with pytest.raises(state.ClaimLookupError, match="CLAIM_TABLE_UNAVAILABLE"):
        state.parse_claims_strict(tmp_path / "absent.md")


@pytest.mark.parametrize("failure", [OSError("no git"), subprocess.TimeoutExpired("git", 15)])
def test_git_process_exceptions_are_typed(repo, monkeypatch, failure):
    def unavailable(*args, **kwargs):
        raise failure

    monkeypatch.setattr(state.subprocess, "run", unavailable)
    with pytest.raises(state.ClaimLookupError, match="GIT_UNAVAILABLE"):
        state.claim_generation_strict(repo, "WO-P1-551")


def test_git_nonzero_exit_is_typed(repo, monkeypatch):
    monkeypatch.setattr(state.subprocess, "run", lambda *args, **kwargs:
                        subprocess.CompletedProcess(args, 1, "", "history unavailable"))
    with pytest.raises(state.ClaimLookupError, match="GIT_UNAVAILABLE"):
        state.claim_generation_strict(repo, "WO-P1-551")


def test_invalid_shallow_probe_is_not_complete_history(repo, monkeypatch):
    monkeypatch.setattr(state, "_git", lambda *args: "")
    with pytest.raises(state.ClaimLookupError, match="GIT_UNAVAILABLE"):
        state.claim_generation_strict(repo, "WO-P1-551")


@pytest.mark.parametrize("header", ["| Chunk/WO | Agent |\n", HEADER + "| Chunk/WO | Agent |\n"])
def test_malformed_header_refuses(tmp_path, header):
    collab = tmp_path / "COLLAB.md"
    collab.write_text(header + ROW, encoding="utf-8")
    with pytest.raises(state.ClaimLookupError, match="CLAIM_TABLE_MALFORMED"):
        state.parse_claims_strict(collab)


@pytest.mark.parametrize("old,new,error", [
    ("| owner |", "| unknown |", "OWNER_UNBOUND"),
    ("conductor/**", "/private/**", "SCOPE_UNSAFE"),
    ("| main |", "| |", "BRANCH_UNBOUND"),
    ("| main |", "| main@{1} |", "BRANCH_INVALID"),
])
def test_strict_reader_keeps_existing_validation(repo, old, new, error):
    (repo / "COLLAB.md").write_text(HEADER + ROW.replace(old, new), encoding="utf-8")
    with pytest.raises(state.ClaimLookupError, match=error):
        state.read_canonical_claim_strict(repo, "WO-P1-551")
