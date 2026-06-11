from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "game" / "normalize_pet_anims.py"
spec = importlib.util.spec_from_file_location("normalize_pet_anims", SCRIPT)
assert spec and spec.loader
normalize_pet_anims = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = normalize_pet_anims
spec.loader.exec_module(normalize_pet_anims)


def write_frame(gen_dir: Path, dog_id: str, action_slug: str, index: int, direction: str = "south") -> None:
    gen_dir.mkdir(parents=True, exist_ok=True)
    (gen_dir / f"dog-{dog_id}_animations_{action_slug}-abc123_{direction}_frame_{index:03d}.png").write_bytes(b"png")


def pet_root(tmp_path: Path) -> Path:
    return tmp_path / "pixel-wealth-quest"


def gen_dir_for(tmp_path: Path, dog_id: str) -> Path:
    return pet_root(tmp_path) / "public" / "assets" / "character" / "pets" / "gen" / dog_id


def ts_text(tmp_path: Path) -> str:
    return (pet_root(tmp_path) / "src" / "phaser" / "petAnims.ts").read_text(encoding="utf-8")


def test_normalize_keeps_existing_walk_sit_wag(tmp_path):
    for dog_id in ("black", "red", "cream"):
        gen = gen_dir_for(tmp_path, dog_id)
        for i in range(2):
            write_frame(gen, dog_id, "walking_legs_moving", i)
        write_frame(gen, dog_id, "sitting_down_calm", 0)

    summary = normalize_pet_anims.normalize_pet_frames(pet_root(tmp_path))

    assert summary["red"] == {"walk": 2, "sit": 1}
    ts = ts_text(tmp_path)
    assert "pwq_pet_red_walk_front" in ts
    assert "pwq_pet_red_sit_front" in ts


def test_normalize_maps_run_as_directional_looping_action(tmp_path):
    gen = gen_dir_for(tmp_path, "red")
    for direction in ("south", "east"):
        for i in range(4):
            write_frame(gen, "red", "running_fast_dash", i, direction=direction)

    summary = normalize_pet_anims.normalize_pet_frames(pet_root(tmp_path))

    assert summary["red"] == {"run": 8}
    ts = ts_text(tmp_path)
    # Run is a directional move action like walk, looping.
    assert 'PET_MOVE_ACTIONS = ["walk", "run"]' in ts
    assert "pwq_pet_red_run_front" in ts
    assert "pwq_pet_red_run_right" in ts


def test_normalize_maps_eat_sleep_bark_one_shots(tmp_path):
    gen = gen_dir_for(tmp_path, "cream")
    for slug in ("eating_food_from_bowl", "sleeping_curled_up", "barking_alert_woof"):
        for i in range(4):
            write_frame(gen, "cream", slug, i)

    summary = normalize_pet_anims.normalize_pet_frames(pet_root(tmp_path))

    assert summary["cream"] == {"eat": 4, "sleep": 4, "bark": 4}
    ts = ts_text(tmp_path)
    assert "pwq_pet_cream_eat_front" in ts
    assert "pwq_pet_cream_sleep_front" in ts
    assert "pwq_pet_cream_bark_front" in ts
    assert '"walk", "run", "sit", "wag", "eat", "sleep", "bark"' in ts
