from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "skill-quality-report.py"
spec = importlib.util.spec_from_file_location("skill_quality_report", SCRIPT)
assert spec and spec.loader
skill_quality_report = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = skill_quality_report
spec.loader.exec_module(skill_quality_report)


def test_discovers_local_skills_but_skips_upstream(monkeypatch, tmp_path):
    local = tmp_path / "skills" / "claude-code" / "demo" / "SKILL.md"
    local.parent.mkdir(parents=True)
    local.write_text("---\nname: demo\ndescription: Demo skill.\n---\n# Demo\n", encoding="utf-8")
    upstream = tmp_path / "skills" / "_upstream" / "demo" / "SKILL.md"
    upstream.parent.mkdir(parents=True)
    upstream.write_text("# Upstream\n", encoding="utf-8")

    monkeypatch.setattr(skill_quality_report, "REPO_ROOT", tmp_path)
    skills = skill_quality_report.discover_skill_files()

    assert local in skills
    assert upstream not in skills


def test_analyze_skill_reports_missing_frontmatter_and_eval_coverage(tmp_path):
    skill = tmp_path / "skills" / "claude-code" / "demo" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# Demo\n\nUse local search.\n", encoding="utf-8")

    result = skill_quality_report.analyze_skill(skill, eval_covered=set())

    assert "missing-frontmatter" in result.issues
    assert "no-eval-coverage" in result.issues
    assert result.level == "WARN"


def test_analyze_skill_flags_iron_law_violations(tmp_path):
    skill = tmp_path / "skills" / "claude-code" / "danger" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: danger\ndescription: Dangerous skill.\n---\n"
        "# Danger\n\nRun git reset --hard and git push --force.\n",
        encoding="utf-8",
    )

    result = skill_quality_report.analyze_skill(skill, eval_covered={skill})

    assert "dangerous-git-pattern" in result.issues
    assert result.level == "FAIL"


def test_eval_coverage_reads_awiki_suites(monkeypatch, tmp_path):
    skill = tmp_path / "skills" / "claude-code" / "demo" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: demo\ndescription: Demo.\n---\n# Demo\n", encoding="utf-8")
    suite = tmp_path / "evals" / "awiki" / "demo.json"
    suite.parent.mkdir(parents=True)
    suite.write_text(json.dumps({"cases": [{"skill": "skills/claude-code/demo/SKILL.md"}]}), encoding="utf-8")

    monkeypatch.setattr(skill_quality_report, "REPO_ROOT", tmp_path)
    covered = skill_quality_report.discover_eval_coverage()

    assert skill in covered


def test_script_mentions_core_skill_roots():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "skills/claude-code" in text
    assert "skills/claude-thai" in text
    assert "agent-skills/engineering" in text
