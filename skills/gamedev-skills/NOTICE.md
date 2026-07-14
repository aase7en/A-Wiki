# Vendored subset from gamedev-skills/awesome-gamedev-agent-skills

- Source: https://github.com/gamedev-skills/awesome-gamedev-agent-skills
- License: Apache-2.0 (see upstream LICENSE + NOTICE files)
- Vendored subpath: `skills/web-engines/*` — only the 6 web-engine skills below,
  cherry-picked from the upstream repo's full 66-skill catalog (Godot/Unity/Unreal/
  other-engines/genres/disciplines/workflows not vendored):
  phaser-arcade-physics, phaser-core, pixijs-rendering, threejs-gltf-loading,
  threejs-materials-lighting, threejs-scene-setup
- Vendored on: 2026-07-14
- Refresh: `bash scripts/refresh-gamedev-skills.sh`
- Related: `skills/awiki/game-phaser-pipeline/` (A-Wiki's own route/convention/safety
  skill) links to `phaser-core`/`phaser-arcade-physics` here for engine-API depth.

Each SKILL.md is kept byte-identical to upstream. A-Wiki-specific metadata lives in
`skills-registry.json`, not in these files.
