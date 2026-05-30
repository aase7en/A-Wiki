from pathlib import Path


def test_sync_smoke_script_is_temp_repo_only():
    text = (Path(__file__).resolve().parents[1] / "scripts" / "sync-smoke.py").read_text(encoding="utf-8")

    assert "tempfile.mkdtemp" in text
    assert "sync.sync_now" in text
    assert "shutil.rmtree" in text

