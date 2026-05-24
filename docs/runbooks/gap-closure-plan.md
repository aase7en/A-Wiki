# Gap Closure Plan — A-Wiki Improvement Roadmap

> **โจทย์**: ปิด 4 Gap จาก Scoring Matrix (Cross-Device, Hooks, Cost Opt, Code Quality)  
> **หลักการ**: ไม่สมองล้า — ทีละ step, dependency-aware, ไม่มี loop ไม่รู้จบ  
> **Priority**: Effort/Impact ratio + dependency order

---

## ภาพรวม Gap

| # | Gap | Current | Target | Effort | Impact | Dependency |
|---|-----|:-------:|:------:|:------:|:------:|:-----------|
| 1 | 🟡 Hooks | 7→10 | 3 hooks เพิ่ม | เล็ก | สูง | — |
| 2 | 🟡 Cost Opt | 7→10 | delegate.sh upgrade | ปานกลาง | สูง | — |
| 3 | 🔴 Cross-Device | 5→10 | sync.py polish | เล็ก | ปานกลาง | — |
| 4 | 🟡 Code Quality | 7→10 | test coverage | ปานกลาง | ปานกลาง | แก้ไขใน scripts ที่ test ครอบคลุม |

**ลำดับการทำ**: 1 → 2 → 3 → 4 (เรียงตาม dependency — ทำ parallel ไม่ได้เพราะต้อง merge ทีละชุด)

---

## Gap 1: Hooks (7→10)

### Current State
| Hook ที่มีแล้ว | Function |
|----------------|----------|
| `check_bash_destructive_git.py` | ✅ Block destructive git commands |
| `check_bash_no_branch.py` | ✅ Block branch operations (main-only) |
| `check_claudemd_lock.py` | ✅ Prevent CLAUDE.md edit without permission |
| `check_raw_immutable.py` | ✅ Protect raw/ from modification |
| `check_secret_leak.py` | ✅ Scan staged diff for secrets |
| `session_start.py` | ✅ Session start hook |
| `hooks_runner.py` | ✅ Orchestrator (รัน ALL หรือ specific) |

### 3 Hooks ที่ต้องเพิ่ม

| # | Hook | File | Logic | Why Missing |
|---|------|------|-------|-------------|
| H1 | **apikey-check** | `scripts/hooks/check_apikey.py` | ✋ Block ถ้า bash command มี API key literal ใน `--api-key`, `--token` flags | ป้องกัน API key leak ใน Claude Code logs |
| H2 | **post-wiki-edit-gen-index** | `scripts/hooks/post_wiki_edit.py` | ⚡ Auto-run `gen-index.py` หลัง `write_to_file` บน path `wiki/**/*.md` | Index ตก — ทำให้ search ไม่เจอหน้าล่าสุด |
| H3 | **delegation-gate** | `scripts/hooks/check_delegation_gate.py` | ✋ Block ถ้า tool call = `Bash` + `git push` โดยไม่ผ่าน `session_end` checklist | ป้องกัน push โดยไม่บันทึก log/session-memory |

### Implementation Detail (H2)

```python
# post_wiki_edit.py — Minimal, safe auto-index
# 1. รับ input JSON (tool_name, tool_input)
# 2. ถ้า tool_name == "WriteToFile" หรือ "ReplaceInFile" 
#    และ path ขึ้นต้นด้วย "wiki/" หรือ "index-" 
#    → รัน subprocess gen-index.py แบบ async (ไม่ block)
# 3. จับ stderr/log ไว้ report ใน next response
```

> **Safety**: ไม่ block (exit 0 เสมอ) — แค่ log ถ้า gen-index ล้มเหลว  
> **Performance**: gen-index ใช้ <2s → ไม่กระทบ session flow

### Files to Create/Modify
- CREATE: `scripts/hooks/check_apikey.py` (~50 lines)
- CREATE: `scripts/hooks/post_wiki_edit.py` (~40 lines)
- CREATE: `scripts/hooks/check_delegation_gate.py` (~45 lines)
- NO CHANGE: `hooks_runner.py` (auto-discovers new hooks)

**Effort**: 3 ไฟล์ ไฟล์ละ ~15 นาที รวม ~1 ชม.

---

## Gap 2: Cost Optimization (7→10)

### Current State
- CLAUDE.md มี Cost Pyramid text (Level -1 ถึง 4) ✅
- `scripts/delegate.sh` มี basic tiering ✅
- `scripts/wiki/ask-notebooklm.py` ใช้ Gemini free ✅
- **ขาด**: direct API calls (Gemini, Groq, DeepSeek), race mode, auto-roster-scout

### 3 Improvements

| # | Item | File | Logic |
|---|------|------|-------|
| C1 | **delegate.sh upgrade** | `scripts/delegate.sh` | เพิ่ม direct call ไป Gemini API + Groq + DeepSeek (ไม่ผ่าน OpenRouter) |
| C2 | **race mode** | `scripts/delegate.sh` | Parallel query 3 models → first complete wins |
| C3 | **cost annotation** | `scripts/delegate.sh` | ต่อท้าย command output ด้วย cost estimate (tokens × rate) |

### Implementation Detail (C1)

```bash
# ใน delegate.sh — เพิ่มหลัง OpenRouter block
delegate_gemini() {
    # Gemini Flash — ฟรี tier (60 req/min)
    local prompt="$1"
    local api_key="${GEMINI_API_KEY:-}"
    [ -z "$api_key" ] && { echo "GEMINI_API_KEY not set"; return 1; }
    
    curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$api_key" \
        -H "Content-Type: application/json" \
        -d "{\"contents\":[{\"parts\":[{\"text\":$(echo "$prompt" | jq -Rs .)}]}]}"
}
```

### Dependency
- C1 ต้องมี `GEMINI_API_KEY`, `GROQ_API_KEY`, `DEEPSEEK_API_KEY` ใน .env
- C2 ต้องใช้ `bash` job control (`&`, `wait -n`)
- C3 pure addition — ไม่มี dependency

### Files to Create/Modify
- MODIFY: `scripts/delegate.sh` (~+80 lines, insert 3 functions)
- CREATE (optional): `scripts/update-model-roster.sh` (ถ้ายังไม่มี — ดูจาก file list มีแล้ว)
- MODIFY: `.env.example` (เพิ่ม API key placeholders)

**Effort**: ~2 ชม. รวม test

---

## Gap 3: Cross-Device (5→10)

### Current State
- ✅ `scripts/sync.py` มีอยู่แล้ว (202 lines) — daemon mode, debounce, auto-commit/push/pull
- ✅ `.gitignore` มี raw/ symlink rule
- ✅ GitHub remote configured
- **สิ่งที่มีแต่ยังไม่สมบูรณ์**: SYNC_PATHS ไม่รวมไฟล์ใหม่ๆ (index-ai-tools.md, index-env.md), ไม่มี device detection ใน CLAUDE.md

### 3 Improvements

| # | Item | File | Logic |
|---|------|------|-------|
| X1 | **Update SYNC_PATHS** | `scripts/sync.py` | เพิ่ม `index-*.md` pattern, `.clinerules`, `decisions/`, `docs/` |
| X2 | **Device ID protocol** | `CLAUDE.md` | เพิ่มข้อความ: "ถ้าทำงานข้าม device → รัน `python3 scripts/sync.py --daemon` ก่อนเริ่ม session" |
| X3 | **Conflict docs** | `docs/runbooks/recover-drive-conflict.md` | มีอยู่แล้ว — แค่ update ให้ตรงกับ sync.py จริง |

### Implementation Detail (X1)

```python
# ปรับ SYNC_PATHS ให้ dynamic
SYNC_PATTERNS = ["wiki/", "index-*.md", "index.md", "log.md", 
                 "session-memory.md", "CLAUDE.md", "AGENTS.md",
                 "brain-map.canvas", "decisions/"]
```

**Effort**: ~30 นาที — trivial changes

---

## Gap 4: Code Quality (7→10)

### Current State
- ❌ `test-zone/` มีแค่ `greet.py` + `test_greet.py` (ตัวอย่างเท่านั้น)
- ❌ `scripts/` (26 ไฟล์) — ไม่มี test เลย
- ✅ `scripts/review-check.py` — health checker ที่ใช้ได้จริง
- ✅ `scripts/hooks/` — all 7 hooks มี exit code discipline

### 3 Test Suites (เลือกเฉพาะ high-ROI)

| # | Suite | Scripts to Test | Approach |
|---|-------|-----------------|----------|
| T1 | **gen-index** | `scripts/gen-index.py` | สร้าง wiki temp, gen-index, assert FTS5 table มี rows |
| T2 | **hooks** | `scripts/hooks/check_*.py` | Mock stdin input, assert exit 0 vs 2 |
| T3 | **sync** | `scripts/sync.py` | Mock git commands, assert output format |

> **หลักการ**: ไม่ cover ทุกอย่าง — เลือก scripts ที่ failure แล้วมี impact สูง  
> **อย่าเขียน test สำหรับ**: agent-skills/ (markdown), skills/ (markdown), wiki/ (content ไม่ deterministic)

### Implementation Detail (T1)

```python
# test-zone/test_gen_index.py
import tempfile, os, sqlite3, subprocess

WIKI_SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "scripts")

def test_gen_index_creates_fts():
    with tempfile.TemporaryDirectory() as tmpdir:
        wiki_dir = os.path.join(tmpdir, "wiki", "entities")
        os.makedirs(wiki_dir)
        # เขียนไฟล์ตัวอย่าง
        with open(os.path.join(wiki_dir, "test-entity.md"), "w") as f:
            f.write("# Test Entity\nSome content here.")
        
        # รัน gen-index
        result = subprocess.run(
            ["python3", f"{WIKI_SCRIPTS}/gen-index.py"], 
            cwd=tmpdir, capture_output=True, text=True
        )
        assert result.returncode == 0
        
        # ตรวจสอบ FTS5 index
        db_path = os.path.join(tmpdir, ".wiki-index.db")
        assert os.path.exists(db_path), "FTS5 index should exist"
        
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT COUNT(*) FROM wiki_index").fetchone()[0]
        assert rows > 0, f"Expected >0 rows, got {rows}"
```

### Files to Create/Modify
- CREATE: `test-zone/test_gen_index.py` (~50 lines)
- CREATE: `test-zone/test_hooks.py` (~80 lines)
- CREATE: `test-zone/test_sync.py` (~60 lines)
- MODIFY: `test-zone/__init__.py` (ถ้ายังไม่มี — สร้างเปล่า)
- MODIFY: `CLAUDE.md` — เพิ่ม `/test` command ใน Quick Commands

**Effort**: ~2.5 ชม.

---

## Execution Timeline

```
Phase 1: Hooks          (1 ชม.) → merge → push
Phase 2: Cost Opt       (2 ชม.) → merge → push
Phase 3: Cross-Device   (30 นาที) → merge → push
Phase 4: Code Quality   (2.5 ชม.) → merge → push
Total: ~6 ชม.
```

### กฎการ merge
- **แต่ละ Phase = 1 commit** — ไม่รวมกัน
- **Commit format**: `feat(gap-<name>): <description>` — เช่น `feat(gap-hooks): add apikey-check, post-wiki-edit, delegation-gate`
- **Push ทันที** → ไม่มี worktree/branch
- **หลังจาก push แต่ละ Phase**: รัน `python3 scripts/gen-index.py` เพื่อรีเฟรช index

### ถ้าเกิดสมองล้า/loop
1. **หยุดทันที** — ถ้าเห็น scope creep (เช่น เริ่มอยาก refactor ไฟล์อื่นที่ไม่ได้อยู่ใน plan) → revert commit, พัก
2. **ปรึกษาก่อน** — ถ้างานเกิน ~6 ชม. หรือกระทบ >5 ไฟล์ → ถามก่อน
3. **ไม่ต้อง perfect** — 80/20 rule: ส่งของที่ useable ก่อน, polish ทีหลัง

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|:-----------:|:------:|------------|
| API key leak ใน delegate.sh | ต่ำ | สูง | .gitignore + ก่อน commit ต้อง check_secret_leak |
| hooks block การทำงานปกติ | ต่ำ | กลาง | ทุก hook ใหม่ต้อง test ก่อน deploy: exit 0 เมื่อ irrelevant |
| sync conflict เมื่อ 2 devices push พร้อมกัน | กลาง | ต่ำ | `--theirs` strategy + conflict doc |
| test flaky (network dependent) | ต่ำ | ต่ำ | Mock external calls ใน test |

---

*Plan ver 1.0 — 2026-05-25 — 6 ชม. รวม 4 Phases*