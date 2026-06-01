---
type: synthesis
title: "PixelLab API Endpoint Matrix"
slug: pixellab-api-endpoint-matrix
tags: [pixellab, api, endpoint-catalog, pixel-art, game-assets, animation, tileset]
sources: [pixellab-api-v2-openapi-2026-06-01]
created: 2026-06-01
updated: 2026-06-01
quality_score: 9/10
domain: ai-tools
---

# PixelLab API Endpoint Matrix

## Purpose

[verified 2026-06-01] หน้านี้เป็น operational catalog ของ PixelLab API v2 สำหรับใช้ค้นเร็วว่า endpoint ไหนทำอะไร, คืนค่าอะไร, เป็น async หรือไม่, และควรต่อด้วย endpoint ไหนใน workflow จริง. ให้ใช้หน้านี้คู่กับ [[sources/pixellab-api-v2-openapi-2026-06-01]] และ [[synthesis/synth-pixellab-api-v2-openapi-2026-06-01]].

**Coverage status**
- `direct` = เดิมมี path นี้ถูกอ้างตรงๆ อยู่แล้วใน A-Wiki
- `concept-only` = เดิมมีสรุป capability แต่ยังไม่ได้ระบุ path ตรง
- `newly-added` = ช่องว่างที่รอบนี้เติมใหม่ให้ครบ

## Create Image

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/generate-image-v2` | Generate image (Pro) | Create Image | async | prompt, image_size, optional refs/style | `background_job_id`, image grid later | poll `/background-jobs/{job_id}` | batch concept sprites or item sheets | direct |
| POST | `/generate-with-style-v2` | Generate with style (Pro) | Create Image | async | prompt, style image, optional subject refs | `background_job_id` | poll `/background-jobs/{job_id}` | lock one approved art style before NPC batch runs | newly-added |
| POST | `/generate-ui-v2` | Generate UI (Pro) | Create Image | async | prompt, image_size, optional palette/concept image | `background_job_id` | poll `/background-jobs/{job_id}` | HUD buttons, status bars, panel parts | direct |
| POST | `/create-image-pixflux` | Create image (pixflux) | Create Image | sync | prompt, image_size, optional transparent bg | image payload | inspect or pass into edit endpoints | fast one-off sprite ideation | direct |
| POST | `/create-image-pixen` | Create image (pixen) | Create Image | sync | prompt, image_size, optional detail controls | image payload | inspect or enhance prompt first | cleaner prompt-driven pixel art base | direct |
| POST | `/create-image-bitforge` | Create image (bitforge) | Create Image | sync | prompt, image_size, optional style refs | image payload | inspect or send to edit/inpaint | style-driven item or portrait experiments | direct |

## Image Operations

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/image-to-pixelart` | Convert image to pixel art | Image Operations | sync | source image, size/style hints | converted image | resize, remove background, or edit | turn a rough sketch or photo ref into pixel base | newly-added |
| POST | `/resize` | Resize pixel art image | Image Operations | sync | source image, target size | resized image | inspect in Phaser or continue cleanup | normalize mixed asset sizes without blur | direct |
| POST | `/remove-background` | Remove background | Image Operations | sync | source image | transparent PNG | import to game or edit further | clean portrait/object outputs for spritesheets | direct |

## Animate

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/edit-animation-v2` | Edit animation (Pro) | Animate | async | existing frames, text edit | edited frames job | poll `/background-jobs/{job_id}` | fix outfit/motion wording across all frames | direct |
| POST | `/interpolation-v2` | Interpolate (Pro) | Animate | async | start frame, end frame, action context | in-between frame job | poll `/background-jobs/{job_id}` | smooth missing motion between key poses | direct |
| POST | `/transfer-outfit-v2` | Transfer outfit (Pro) | Animate | async | animation frames, outfit reference | edited frames job | poll `/background-jobs/{job_id}` | keep one approved costume across multiple animations | concept-only |
| POST | `/animate-with-skeleton` | Animate with skeleton | Animate | sync | image, skeleton/keypoints, animation spec | animation frames | refine with edit/interpolation if needed | deterministic animation after manual pose planning | direct |
| POST | `/animate-with-text` | Animate with text | Animate | sync | prompt/action, reference frame, size | animation frames | inspect or upscale workflow | quick movement ideation | direct |
| POST | `/animate-with-text-v2` | Animate with text (pro) | Animate | async | prompt/action, reference frame | `background_job_id` | poll `/background-jobs/{job_id}` | higher quality motion when base model fails | newly-added |
| POST | `/animate-with-text-v3` | Animate with text v3 | Animate | async | reference frame, detailed action prompt | `background_job_id` | poll `/background-jobs/{job_id}` | best default for polished action loops | direct |
| POST | `/estimate-skeleton` | Estimate skeleton | Animate | sync | character image | keypoint list | feed into `/animate-with-skeleton` | bootstrap skeleton poses from existing sprite | newly-added |

## Rotate

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/generate-8-rotations-v2` | Generate 8 rotations (Pro) | Rotate | async | source image, direction settings | `background_job_id` | poll `/background-jobs/{job_id}` | legacy high-quality rotation path for character/object refs | concept-only |
| POST | `/generate-8-rotations-v3` | Generate 8 rotations v3 | Rotate | async | south-facing reference frame | `background_job_id` | poll `/background-jobs/{job_id}` | preferred ref-to-8-directions flow when v3 is available | concept-only |
| POST | `/rotate` | Rotate character or object | Rotate | sync | source image, target direction | rotated image | inspect or promote into object/character workflow | one-off turn without full persistent character flow | newly-added |

## Inpaint/Edit

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/inpaint-v3` | Inpaint image (Pro) | Inpaint/Edit | async | image, mask, text edit | `background_job_id` | poll `/background-jobs/{job_id}` | fix hands, edges, props, or holes without redrawing | newly-added |
| POST | `/inpaint` | Inpaint image | Inpaint/Edit | sync | image, mask, text edit | edited image | inspect or continue cleanup | small sprite repairs on one frame | direct |
| POST | `/edit-images-v2` | Edit images (Pro) | Inpaint/Edit | async | multiple images, text or ref image | `background_job_id` | poll `/background-jobs/{job_id}` | apply one art-direction change to a batch consistently | newly-added |
| POST | `/edit-image` | Edit image | Inpaint/Edit | sync | image, text edit | edited image | inspect or chain to resize/remove bg | fast single-frame revision | direct |

## Create Map

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/tilesets` | Create a tileset asynchronously | Create Map | async | prompt, tile size, transition config | `background_job_id`, `tileset_id` | poll `/background-jobs/{job_id}` or fetch `/tilesets/{tileset_id}` | Wang-style terrain packs with explicit retrieval path | concept-only |
| POST | `/create-tileset` | Create top-down tileset (async processing) | Create Map | async | prompt, tile size, theme | `background_job_id` | poll `/background-jobs/{job_id}` | top-down ocean, island, deck transitions | direct |
| GET | `/tilesets/{tileset_id}` | Get generated tileset by ID | Create Map | sync | `tileset_id` | completed tileset payload | export or import into game atlas | retrieve async result directly by resource id | concept-only |
| POST | `/tilesets-sidescroller` | Create a sidescroller tileset asynchronously | Create Map | async | prompt, tile size | `background_job_id`, `tileset_id` | poll job or fetch `/tilesets/{tileset_id}` | future platformer-style environments | concept-only |
| POST | `/create-tileset-sidescroller` | Create sidescroller tileset (async processing) | Create Map | async | prompt, tile size, theme | `background_job_id` | poll `/background-jobs/{job_id}` | alternative entrypoint for platform tiles | concept-only |
| POST | `/create-isometric-tile` | Create isometric tile (async processing) | Create Map | async | prompt, tile shape, size | `background_job_id`, tile ref | poll job or fetch tile | ship deck props in iso experiments | direct |
| GET | `/isometric-tiles/{tile_id}` | Get generated isometric tile by ID | Create Map | sync | `tile_id` | tile payload | import into asset pack | retrieve completed isometric output | concept-only |
| GET | `/isometric-tiles` | List user's isometric tiles | Create Map | sync | auth only | tile list | inspect ids and fetch specific tile | audit reusable iso assets | concept-only |
| POST | `/create-tiles-pro` | Create tiles pro (async processing) | Create Map | async | prompt, tile specs, style hints | `background_job_id`, tile ref | poll job or fetch `/tiles-pro/{tile_id}` | advanced tile variants when basic tileset is not enough | direct |
| GET | `/tiles-pro/{tile_id}` | Get generated tiles pro by ID | Create Map | sync | `tile_id` | tile payload | import/export | retrieve pro tile output by id | concept-only |
| POST | `/map-objects` | Create map object | Create Map | async | prompt, object type, transparency | `background_job_id` or object payload | poll job if needed, then manage object | cannon, barrel, mast, treasure chest | direct |

## Character from Template

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/create-character-with-4-directions` | Create character with 4 directions | Character from Template | async | prompt or ref image, 4-dir choice | `background_job_id`, character ref | poll job then inspect in `/characters/{character_id}` | NPCs that only need cardinal movement | direct |
| POST | `/create-character-with-8-directions` | Create character with 8 directions | Character from Template | async | prompt or ref image, 8-dir choice | `background_job_id`, character ref | poll job then inspect/export | richer RPG movement set | direct |
| POST | `/create-character-pro` | Create character with Pro mode (8 directions) | Character from Template | async | prompt or ref image, pro mode | `background_job_id`, character ref | poll job then inspect/export | use when consistency matters more than credit cost | concept-only |
| POST | `/create-character-v3` | Create character with v3 model (8 rotations) | Character from Template | async | south-facing ref or prompt, 8-dir target | `background_job_id`, character ref | poll job then animate/export | preferred first pass for hero character | direct |
| POST | `/characters/animations` | Create Character Animation | Character from Template | async | `character_id`, animation prompt/config | `background_job_id` | poll job then inspect character | background animation queue for persistent characters | concept-only |
| POST | `/animate-character` | Animate character | Character from Template | async | `character_id`, action, frame count | `background_job_id` | poll job then export ZIP | idle/walk/action loops for captain or crew | direct |
| POST | `/create-character-state` | Create a state of an existing character | Character from Template | async | `character_id`, text edit for new state | `background_job_id`, new grouped character | poll job then tag/export | profit, worried, tired, resting variants | direct |

## Character Management

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/characters` | List user's characters | Character Management | sync | auth only | character list | inspect id, tags, previews | inventory of reusable cast assets | direct |
| GET | `/characters/{character_id}` | Get character details | Character Management | sync | `character_id` | rotations, metadata, previews | animate, tag, or export ZIP | inspect one asset before spending more generations | concept-only |
| GET | `/characters/{character_id}/zip` | Export character as ZIP | Character Management | sync | `character_id` | downloadable archive | unpack into Phaser asset folder | final delivery step for accepted character | concept-only |
| PATCH | `/characters/{character_id}/tags` | Update character tags | Character Management | sync | `character_id`, tag list | updated metadata | re-list `/characters` or export | classify crew roles, factions, or project ownership | concept-only |

## Objects

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/create-1-direction-object` | Create a 1-direction object | Objects | async | prompt, size, object description | `background_job_id`, `object_id` | poll `/objects/{object_id}` | static props that do not need rotation | newly-added |
| POST | `/create-8-direction-object` | Create an 8-direction object | Objects | async | prompt or ref image, 8-dir object spec | `background_job_id`, `object_id` | poll `/objects/{object_id}` | ships or vehicles visible from multiple angles | newly-added |
| POST | `/objects/{object_id}/animations` | Add an animation to an existing object | Objects | async | `object_id`, action, mode, frame count | `background_job_id` | poll `/objects/{object_id}` | animate ship sails, flags, cannons, machines | newly-added |
| POST | `/objects/{object_id}/states` | Create a state of an existing object | Objects | async | `object_id`, text edit | `background_job_id`, grouped object | poll `/objects/{object_id}` | damaged, glowing, open, closed variants | newly-added |
| POST | `/objects/{object_id}/select-frames` | Promote selected frames of a review object to completed objects | Objects | sync | `object_id`, selected review frames | completed object entries | tag/list/fetch promoted objects | curate only the frames worth keeping from review output | newly-added |
| POST | `/objects/{object_id}/dismiss-review` | Dismiss a review object without saving any frames | Objects | sync | `object_id` | dismissal confirmation | retry generation or abandon branch | reject noisy review results cleanly | newly-added |

## Object Management

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/objects` | List user's objects | Object Management | sync | auth only | object list | inspect ids, previews, states | audit reusable object library | direct |
| GET | `/objects/{object_id}` | Get object details | Object Management | sync | `object_id` | status, frames, metadata | animate, state-edit, select frames, tag | central polling point for object jobs | newly-added |
| PATCH | `/objects/{object_id}/tags` | Update object tags | Object Management | sync | `object_id`, tag list | updated metadata | re-list or fetch object | classify prop families and review outcomes | newly-added |

## Prompt Enhancement

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| POST | `/enhance-pixen-prompt` | Enhance pixen prompt | Prompt Enhancement | sync | short image description | expanded prompt | send to `/create-image-pixen` | upgrade rough art direction before generation | direct |
| POST | `/enhance-character-v3-prompt` | Enhance character v3 prompt | Prompt Enhancement | sync | short character brief | expanded character prompt | send to `/create-character-v3` | tighten silhouette/clothing/lore in one pass | direct |
| POST | `/enhance-animation-v3-prompt` | Enhance animation v3 prompt | Prompt Enhancement | sync | short action description | expanded motion prompt | send to `/animate-with-text-v3` | better movement language for idle/walk/action loops | direct |

## Infra / Docs

| method | path | summary | category | mode | key inputs | returns | next step | A-Wiki use case | coverage status |
|---|---|---|---|---|---|---|---|---|---|
| GET | `/background-jobs/{job_id}` | Get background job status | Infra / Docs | sync | `job_id` | job status, last response, errors | fetch asset/resource endpoint when complete | universal polling endpoint for async jobs | direct |
| GET | `/balance` | Get balance | Infra / Docs | sync | auth only | credits + subscription generations | decide whether to use pro/v2/v3 modes | cost guard before large batches | direct |
| GET | `/llms.txt` | Get LLM-friendly API documentation | Infra / Docs | sync | none | LLM-oriented endpoint index | quick skim before prompting an agent | fastest human/agent refresher layer | direct |

## Workflow blocks

### Style-guided generation flow

1. Use `/generate-with-style-v2` when you already have one approved reference style.
2. Poll `/background-jobs/{job_id}` until completed.
3. If the style is good but one frame is wrong, use `/edit-image` or `/edit-images-v2`.
4. If you need transparency, finish with `/remove-background`.

**Why:** ล็อก visual identity ก่อน batch generation จะลดงาน cleanup และลด prompt drift.

### Image-to-pixel cleanup flow

1. Start with `/image-to-pixelart` from a sketch, photo, or painted concept.
2. Normalize dimensions with `/resize`.
3. Clean silhouette or remove scene leftovers with `/remove-background`.
4. If some areas still break, patch with `/inpaint` or `/inpaint-v3`.

**Why:** เหมาะกับการแปลง idea จากนอก PixelLab ให้เข้า asset pipeline โดยไม่ต้อง redraw ทุกอย่างใหม่.

### Character creation and export flow

1. Expand the brief with `/enhance-character-v3-prompt` if the prompt is short.
2. Generate the base hero with `/create-character-v3`.
3. Add motion using `/animate-character` or `/characters/animations`.
4. Add mood/outfit variants with `/create-character-state`.
5. Inspect `/characters/{character_id}`, tag with `/characters/{character_id}/tags`, then export `/characters/{character_id}/zip`.

**Why:** แยก base character, animation, state, และ export ออกจากกัน ทำให้ reuse ง่ายและคุม credit ได้ดี.

### Object review and frame promotion flow

1. Create the prop with `/create-1-direction-object` หรือ `/create-8-direction-object`.
2. Poll `/objects/{object_id}` until the object leaves processing status.
3. If the object is a review object, inspect the candidate frames in `/objects/{object_id}`.
4. Keep only the good outputs with `/objects/{object_id}/select-frames` หรือทิ้งทั้งชุดด้วย `/objects/{object_id}/dismiss-review`.
5. Add animation/state/tag later through `/objects/{object_id}/animations`, `/objects/{object_id}/states`, `/objects/{object_id}/tags`.

**Why:** review object เป็น buffer stage สำหรับคัดเฟรมก่อน promote เข้า asset library จริง ลดการเก็บของเสียลงระบบ.

### Async map/tiles polling flow

1. Submit `/tilesets`, `/create-tileset`, `/tilesets-sidescroller`, `/create-tileset-sidescroller`, `/create-isometric-tile`, or `/create-tiles-pro`.
2. Poll `/background-jobs/{job_id}` when the endpoint returns a job id.
3. Fetch the final resource from `/tilesets/{tileset_id}`, `/isometric-tiles/{tile_id}`, or `/tiles-pro/{tile_id}` when a resource id exists.
4. Store the approved result in the game asset folder and reuse the id for later updates.

**Why:** map endpoints มีทั้ง job-oriented และ resource-oriented retrieval; ถ้าไม่แยกสองชั้นนี้จะสับสนว่าควร poll ที่ไหนต่อ.

## Decision notes

- `/create-character-v3` และ `/animate-with-text-v3` เป็นตัวเลือกเริ่มต้นที่ดีเมื่ออยากได้คุณภาพสูงกว่า base model โดยไม่ต้องกระโดดไป pro ทุกครั้ง
- ใช้ `pro` เมื่อคุณมี style target ชัดและงานเสียจากการ regenerate หนักกว่าค่า credit ที่เพิ่ม
- ใช้ base/sync endpoints (`/create-image-pixflux`, `/edit-image`, `/inpaint`) สำหรับลองเร็วหรือแก้เฉพาะจุด
- object endpoints เป็นคนละ lifecycle กับ map object endpoint; `/map-objects` เน้น transparent prop generation ส่วน `/objects/*` เน้น persistent object management, review, states, tags, and animations

## Related pages

- [[sources/pixellab-api-v2-openapi-2026-06-01]]
- [[synthesis/synth-pixellab-api-v2-openapi-2026-06-01]]
- [[synthesis/pixellab-asset-pipeline-for-trading-rpg]]
