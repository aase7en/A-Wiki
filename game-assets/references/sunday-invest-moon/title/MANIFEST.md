# title/ — moved assets manifest

The large reference splash images that used to live in this directory were
moved out of git tracking (public-safe repo policy — Iron Law #6, large
binary game-dev references belong in the private data layer, not the
tracked repo).

| File | New location |
|------|---------------|
| `splash-v001.png` | `drive/game-assets/sunday-invest-moon/title/splash-v001.png` |
| `splash-v002.png` | `drive/game-assets/sunday-invest-moon/title/splash-v002.png` |

`logo-v001.png` stays tracked here (small, non-sensitive).

If `drive/` is not linked on your machine, run `bash scripts/setup-cloud-link.sh --auto`
first (see root `CLAUDE.md` → External Data Layer).
