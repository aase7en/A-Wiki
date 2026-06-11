from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "game" / "normalize_pwq_anims.py"
spec = importlib.util.spec_from_file_location("normalize_pwq_anims", SCRIPT)
assert spec and spec.loader
normalize_pwq_anims = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = normalize_pwq_anims
spec.loader.exec_module(normalize_pwq_anims)


def write_frame(anim_dir: Path, action_slug: str, index: int, direction: str = "south") -> None:
    anim_dir.mkdir(parents=True, exist_ok=True)
    (anim_dir / f"nong-sunday_animations_{action_slug}-abc123_{direction}_frame_{index:03d}.png").write_bytes(b"png")


def test_normalize_animation_frames_creates_clean_files_and_ts_module(tmp_path):
    pwq_root = tmp_path / "pixel-wealth-quest"
    anim_dir = pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim"
    for i in range(2):
      write_frame(anim_dir, "standing_still_gentle_idle_breathing", i)
    for i in range(3):
      write_frame(anim_dir, "walking_moving_arms_and_legs", i)

    result = normalize_pwq_anims.normalize_animation_frames(pwq_root)

    assert result == {"idle": 2, "walk": 3}
    assert (pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim_clean" / "idle_south_000.png").exists()
    assert (pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim_clean" / "walk_south_002.png").exists()
    ts = (pwq_root / "src" / "phaser" / "playerAnims.ts").read_text(encoding="utf-8")
    assert "export const PLAYER_ANIM_ACTIONS" in ts
    assert "idle_south_000.png" in ts
    assert "walk_south_002.png" in ts


def test_normalize_maps_farm_tool_one_shots(tmp_path):
    pwq_root = tmp_path / "pixel-wealth-quest"
    anim_dir = pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim"
    for slug in ("watering_plants", "hoeing_soil", "harvesting_crop"):
        for i in range(8):
            write_frame(anim_dir, slug, i)

    result = normalize_pwq_anims.normalize_animation_frames(pwq_root)

    assert result == {"water": 8, "hoe": 8, "harvest": 8}
    clean_dir = pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim_clean"
    assert (clean_dir / "water_south_007.png").exists()
    assert (clean_dir / "hoe_south_000.png").exists()
    assert (clean_dir / "harvest_south_000.png").exists()
    ts = (pwq_root / "src" / "phaser" / "playerAnims.ts").read_text(encoding="utf-8")
    # Tool swings are one-shots: present in the registry but never looping.
    assert "'pwq_player_water_front'" in ts
    assert "'pwq_player_hoe_front'" in ts
    assert "'pwq_player_harvest_front'" in ts


def test_normalize_animation_frames_keeps_walk_frames_per_direction(tmp_path):
    pwq_root = tmp_path / "pixel-wealth-quest"
    anim_dir = pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim"
    for direction in ("south", "north-east"):
        for i in range(2):
            write_frame(anim_dir, "walking_moving_arms_and_legs", i, direction=direction)

    result = normalize_pwq_anims.normalize_animation_frames(pwq_root)

    assert result == {"walk": 4}
    clean_dir = pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim_clean"
    assert (clean_dir / "walk_south_001.png").exists()
    assert (clean_dir / "walk_north-east_001.png").exists()
    ts = (pwq_root / "src" / "phaser" / "playerAnims.ts").read_text(encoding="utf-8")
    assert "PLAYER_MOVE_ANIMS" in ts
    assert "pwq_player_walk_front" in ts
    assert "pwq_player_walk_back_right" in ts


def test_normalize_prefers_walk_export_with_more_directions(tmp_path):
    pwq_root = tmp_path / "pixel-wealth-quest"
    anim_dir = pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim"
    for i in range(3):
        write_frame(anim_dir, "walking_moving_old", i, direction="south")
    for direction in ("south", "east", "west"):
        for i in range(2):
            write_frame(anim_dir, "walking_moving_new", i, direction=direction)

    result = normalize_pwq_anims.normalize_animation_frames(pwq_root)

    assert result == {"walk": 6}
    clean_dir = pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim_clean"
    assert (clean_dir / "walk_south_001.png").exists()
    assert not (clean_dir / "walk_south_002.png").exists()


def test_normalize_maps_walk_left_to_south_west_art(tmp_path):
    pwq_root = tmp_path / "pixel-wealth-quest"
    anim_dir = pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim"
    for direction in ("south", "west", "south-west"):
        for i in range(2):
            write_frame(anim_dir, "walking_moving_arms_and_legs", i, direction=direction)

    normalize_pwq_anims.normalize_animation_frames(pwq_root)

    ts = (pwq_root / "src" / "phaser" / "playerAnims.ts").read_text(encoding="utf-8")
    left_line = next(line for line in ts.splitlines() if line.strip().startswith("left:"))
    assert "walk_south-west_000.png" in left_line
    assert "walk_west_000.png" not in left_line


def test_normalize_builds_directional_run_fallbacks_from_walk_art(tmp_path):
    pwq_root = tmp_path / "pixel-wealth-quest"
    anim_dir = pwq_root / "public" / "assets" / "character" / "nong-sunday" / "anim"
    for direction in ("south", "east"):
        for i in range(2):
            write_frame(anim_dir, "walking_moving_arms_and_legs", i, direction=direction)
    for i in range(2):
        write_frame(anim_dir, "running_fast_arms_and_legs_pumping", i)

    normalize_pwq_anims.normalize_animation_frames(pwq_root)

    ts = (pwq_root / "src" / "phaser" / "playerAnims.ts").read_text(encoding="utf-8")
    assert 'export const PLAYER_MOVE_ACTIONS = ["walk", "run"] as const' in ts
    run_section = ts.split("  run: {", maxsplit=2)[-1].split("  },", maxsplit=1)[0]
    front_line = next(line for line in run_section.splitlines() if line.strip().startswith("front:"))
    right_line = next(line for line in run_section.splitlines() if line.strip().startswith("right:"))
    assert "run_south_000.png" in front_line
    assert "walk_east_000.png" in right_line
