from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "wiki" / "build-capability-map.py"
spec = importlib.util.spec_from_file_location("build_capability_map", SCRIPT)
assert spec and spec.loader
build_capability_map = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = build_capability_map
spec.loader.exec_module(build_capability_map)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_fixture_repo(root: Path) -> None:
    write(
        root / "skills" / "claude-code" / "foo-skill" / "SKILL.md",
        """---
name: foo-skill
description: Use when foo capability is needed.
---

# Foo Skill
""",
    )
    write(
        root / "agent-skills" / "engineering" / "debug-mantra" / "SKILL.md",
        """---
name: debug-mantra
description: Root-cause debugging workflow.
---

# Debug Mantra
""",
    )
    write(
        root / "skills" / "_upstream" / "vendor" / "ignored" / "SKILL.md",
        """---
name: ignored
description: Should not appear.
---

# Ignored
""",
    )
    write(root / "scripts" / "wiki" / "search-wiki.py", "#!/usr/bin/env python3\n")
    write(root / "scripts" / "wiki" / "query-graph.py", "#!/usr/bin/env python3\n")
    write(root / "scripts" / "game" / "report_phaser_asset_pack.py", "#!/usr/bin/env python3\n")
    write(root / "scripts" / "agent-preflight.py", "#!/usr/bin/env python3\n")
    write(root / "docs" / "protocols" / "brain-improvement-gate.md", "# Brain Gate\n")
    write(root / "docs" / "runbooks" / "setup-new-machine.md", "# Setup\n")
    write(
        root / "skills" / "render-html" / "registry.json",
        json.dumps(
            {
                "surfaces": {
                    "health": {"title": "Health", "description": "Wiki health dashboard"},
                    "skills": {"title": "Skills", "description": "Skill quality dashboard"},
                }
            }
        ),
    )
    write(
        root / "wiki" / "context" / "wiki-overview.md",
        """# Wiki Overview

| ENTITIES | 2 |
| CONCEPTS | 1 |
| SYNTHESIS | 3 |
| SOURCES | 4 |
| **Total** | **10 pages** |
""",
    )
    write(
        root / ".wiki-graph.json",
        json.dumps(
            {
                "stats": {
                    "nodes": 4,
                    "edges": 4,
                    "broken_links": 2,
                    "orphans": 1,
                    "orphans_list": ["wiki/context/now.md"],
                    "hubs": [],
                },
                "edges": [
                    {
                        "from": "wiki/synthesis/demo.md",
                        "to": "wiki/entities/ai-tools/missing.md",
                        "type": "wikilink",
                        "broken": True,
                        "external": False,
                    },
                    {
                        "from": "wiki/concepts/iot/demo.md",
                        "to": "wiki/concepts/iot/missing.md",
                        "type": "wikilink",
                        "broken": True,
                        "external": False,
                    },
                ],
            }
        ),
    )


def test_build_capability_map_discovers_owned_surfaces(tmp_path):
    make_fixture_repo(tmp_path)

    data = build_capability_map.build_capability_map(tmp_path)

    assert data["summary"]["owned_skill_count"] == 2
    assert data["summary"]["script_count"] == 4
    assert data["summary"]["protocol_count"] == 2
    assert data["summary"]["render_surface_count"] == 2
    skill_names = {skill["name"] for skill in data["skills"]}
    assert {"foo-skill", "debug-mantra"} <= skill_names
    assert "ignored" not in skill_names
    assert any(item["capability"] == "Local Search" for item in data["capabilities"])
    assert any(item["capability"] == "Asset Pack Reporting" for item in data["capabilities"])
    assert {lane["id"] for lane in data["strategic_lanes"]} == {
        "design-web",
        "game-lightweight-highend",
        "revenue-engine",
        "premium-auto-trading",
    }
    assert data["graph_hygiene"]["broken_links"] == 2
    assert data["graph_hygiene"]["orphans"] == 1
    assert data["graph_hygiene"]["broken_by_domain"]["synthesis"] == 1
    assert data["graph_hygiene"]["broken_by_domain"]["iot"] == 1


def test_build_capability_map_counts_wiki_files_without_stale_overview(tmp_path):
    make_fixture_repo(tmp_path)
    write(tmp_path / "wiki" / "entities" / "iot" / "esp32.md", "# ESP32\n")
    write(tmp_path / "wiki" / "concepts" / "iot" / "mqtt.md", "# MQTT\n")
    write(tmp_path / "wiki" / "synthesis" / "model-switching.md", "# Model Switching\n")
    write(tmp_path / "wiki" / "sources" / "source-one.md", "# Source One\n")

    data = build_capability_map.build_capability_map(tmp_path)

    assert data["wiki_stats"] == {
        "entities": 1,
        "concepts": 1,
        "synthesis": 1,
        "sources": 1,
        "total_pages": 4,
    }
    assert data["summary"]["wiki_page_count"] == 4


def test_format_markdown_includes_routing_tables(tmp_path):
    make_fixture_repo(tmp_path)
    data = build_capability_map.build_capability_map(tmp_path)

    text = build_capability_map.format_markdown(data)

    assert "# Wiki Capability Map" in text
    assert "## Strategic Capability Lanes" in text
    assert "| `design-web` |" in text
    assert "## Capability Upgrade Matrix" in text
    assert "| Website design |" in text
    assert "## Knowledge Graph Hygiene" in text
    assert "| Broken links | 2 |" in text
    assert "## MCP Allowlist" in text
    assert "| `awiki` | Keep |" in text
    assert "## Capability Routing" in text
    assert "`python3 scripts/wiki/search-wiki.py \"query\"`" in text
    assert "| `foo-skill` |" in text
    assert "| `health` | Health |" in text


def test_cli_writes_output_file(tmp_path):
    make_fixture_repo(tmp_path)
    out = tmp_path / "wiki" / "context" / "wiki-capability-map.md"

    subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--out", str(out)],
        check=True,
        capture_output=True,
        text=True,
    )

    text = out.read_text(encoding="utf-8")
    assert "Generated by `scripts/wiki/build-capability-map.py`" in text
    assert "foo capability is needed" in text
