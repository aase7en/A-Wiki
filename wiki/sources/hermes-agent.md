---
type: source
title: "คู่มือ คำสั่งที่ใช้บ่อย น้องเฮอมีส Hermes Agent"
slug: hermes-agent
date_ingested: 2026-05-24
original_file: raw/คู่มือ Hermes Agent.md
---

```yaml
---
title: "คู่มือ คำสั่งที่ใช้บ่อย น้องเฮอมีส Hermes Agent"
source: "https://www.sanookai.com/articles/hermes-agent-doc?fbclid=IwY2xjawRRBEtleHRuA2FlbQIxMABicmlkETFxd1ZtMTRQblBJenlPczFac3J0YwZhcHBfaWQQMjIyMDM5MTc4ODIwMDg5MgABHo4Hg0Pk-Kde64ImrT8h22RV9JsHEUavVuGsG7fLelsIgBs2bVNwkNUJEHdQ_aem_dLwP5lhz1kaVlvki3TY11A"
author: ""
published: ""
created: "2026-04-19"
description: "คู่มือภาษาไทย น้อง เฮอมีส ai"
tags: ""
---
```

คู่มือภาษาไทย น้อง เฮอมีส ai

## ติดตั้งแบบง่ายที่สุด บน mac

Hermes Agent รองรับ Linux, macOS, WSL2 และ Android/Termux; ส่วน Windows แบบ native ยังไม่รองรับและเอกสารแนะนำให้ใช้ WSL2 แทน ตัวติดตั้งแบบ one-line ต้องการแค่ git และจะจัดการ dependency หลักให้เอง เช่น Python 3.11, Node.js, ripgrep, ffmpeg, การ clone repo, virtual environment และคำสั่ง hermes แบบ global ให้เลย

```plain
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
source ~/.bashrc   # หรือ source ~/.zshrc
hermes
```

หลังติดตั้งแล้ว ถ้าจะตั้งค่าเพิ่มภายหลัง ใช้ hermes model เพื่อเลือก provider/model, ใช้ hermes tools เพื่อเปิด/ปิด tools, ใช้ hermes gateway setup เพื่อตั้งค่า Telegram/Discord/Slack/WhatsApp ฯลฯ, หรือใช้ hermes setup เพื่อเข้าตัวช่วยตั้งค่ารวมทั้งระบบ

\---

Ai หลังบ้าน สามารถใช้ chatgpt plus ได้ครับ ถ้าหากไม่มี แนะนำ minimax เริ่มต้น เดือนละ 10$

.

**ส่วนลด ai minimax 10%**

🎁 MiniMax Token Plan New Year Mega Offer! Invite friends and earn rewards for both!

Exclusive 10% OFF for friends. \*\* โปร 20$ คุ้ม สร้างภาพ สร้างเพลงได้

👉 Get your referral link: [https://platform.minimax.io/subscribe/token-plan?code=5rtzDiiXd1&source=link](https://platform.minimax.io/subscribe/token-plan?code=5rtzDiiXd1&source=link)

\---

วิธีติดตั้งบน windows [https://hermes-install-guide.netlify.app/](https://hermes-install-guide.netlify.app/)

\---

## ติดตั้งแบบ manual เผื่อ installer ใช้ไม่ได้

เอกสารมีเส้นทาง manual install ชัดเจน โดยให้ clone repo พร้อม submodules, สร้าง venv ด้วย Python 3.11 ผ่าน uv, ติดตั้งแพ็กเกจ, สร้างโฟลเดอร์ config และใส่ API key อย่างน้อย 1 ตัว เช่น OPENROUTER\_API\_KEY ก่อนเริ่มใช้งาน

```plain
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv venv --python 3.11
export VIRTUAL_ENV="$(pwd)/venv"

uv pip install -e ".[all]"

mkdir -p ~/.hermes/{cron,sessions,logs,memories,skills,pairing,hooks,image_cache,audio_cache,whatsapp/session}
cp cli-config.yaml.example ~/.hermes/config.yaml
touch ~/.hermes/.env
echo 'OPENROUTER_API_KEY=sk-or-v1-your-key' >> ~/.hermes/.env

mkdir -p ~/.local/bin
ln -sf "$(pwd)/venv/bin/hermes" ~/.local/bin/hermes

hermes doctor
hermes
```

ถ้าต้องการติดตั้งแบบเบากว่า เอกสารระบุว่าใช้ uv pip install -e "." ได้สำหรับ core agent แบบไม่เอา messaging/cron extras ทั้งหมด

## ลำดับเริ่มใช้งานหลังติดตั้ง

ใช้งานจริงแบบสั้นที่สุดมักเป็นลำดับนี้: เปิด hermes, เลือกโมเดลด้วย hermes model, ตรวจสุขภาพด้วย hermes doctor หรือ hermes status, แล้วค่อยเพิ่ม tools / gateway ตามต้องการ

```plain
hermes
hermes model
hermes doctor
hermes status
```

## ชีตสรุปคำสั่ง shell (hermes...)

### 1) เริ่มคุย / ยิงคำสั่งแบบ one-shot / กลับเข้า session

- hermes หรือ hermes chat ใช้เปิดแชตแบบ interactive กับ agent; ถ้าจะยิง prompt ครั้งเดียวใช้ hermes chat -q "..." ได้เลย ส่วน options ที่ใช้บ่อยคือ --model, --provider, --toolsets, --skills, --image, --worktree, --checkpoints, --continue, --resume และ --verbose
- hermes -c หรือ hermes --continue ใช้กลับเข้า session ล่าสุด, hermes -r  หรือ --resume ใช้ระบุ session/ชื่อ session ที่ต้องการ, hermes -p  ใช้สลับ profile สำหรับคำสั่งนั้น ๆ, และ hermes -w หรือ --worktree ใช้เปิด isolated git worktree สำหรับงานคู่ขนาน

ตัวอย่างที่ใช้บ่อย:

```plain
hermes
hermes chat -q "สรุป PR ล่าสุด"
hermes -c
hermes -r my-session
hermes -p work chat -q "hello"
hermes chat --worktree -q "review repo นี้แล้วเปิด PR"
```

### 2) ตั้งค่า model / provider / config / tools

- hermes model คือ wizard หลักสำหรับเพิ่ม provider ใหม่, ใส่ API key, ทำ OAuth และเลือก default model; เอกสารแยกชัดว่าอันนี้เป็นคำสั่งระดับ shell ไม่ใช่ slash command ในแชต
- hermes setup \[model|terminal|gateway|tools|agent\] คือ setup wizard แบบรวม หรือจะเข้าเฉพาะ section ก็ได้; มี --non-interactive และ --reset ให้ใช้ด้วย
- hermes tools ใช้ตั้งค่าเครื่องมือที่เปิดใช้ในแต่ละ platform; ถ้าอยากดูสรุปเร็ว ๆ ใช้ hermes tools --summary
- hermes config show|edit|set|path|env-path|check|migrate ใช้ดู/แก้ config, ตรวจ config ที่ขาด, หรือ migrate option ใหม่ ๆ หลังอัปเดต
- hermes auth, hermes auth list, hermes auth add, hermes auth remove, hermes auth reset ใช้จัดการ credential pool และ OAuth credential ของ provider ต่าง ๆ
- hermes status \[--all\] \[--deep\] ใช้ดูสถานะรวมของ agent, auth, และ platform ที่ตั้งไว้

ตัวอย่างที่ใช้บ่อย:

```plain
hermes model
hermes setup
hermes setup gateway
hermes tools
hermes tools --summary
hermes config show
hermes config set OPENROUTER_API_KEY sk-or-v1-your-key
hermes config check
hermes config migrate
hermes auth list
hermes status --deep
```

ตั้งค่า terminal backend ที่ใช้บ่อยจาก quickstart:

```plain
hermes config set terminal.backend docker
hermes config set terminal.backend ssh
```

คำสั่งสองบรรทัดนี้เป็นตัวอย่างจาก quickstart สำหรับทำ sandbox ด้วย Docker หรือย้ายไปใช้ remote server ผ่าน SSH

### 3) Messaging gateway / WhatsApp / pairing

- hermes gateway setup ใช้ตั้งค่า Telegram, Discord, Slack, WhatsApp, Signal, Email, Home Assistant ฯลฯ แบบ interactive
- hermes gateway run|start|stop|restart|status|install|uninstall ใช้รัน gateway แบบ foreground หรือแบบ service; เอกสารระบุว่าใน WSL, Docker และ Termux แนะนำ hermes gateway run มากกว่า start
- hermes whatsapp ใช้เข้า flow สำหรับจับคู่และตั้งค่า WhatsApp bridge
- hermes pairing list|approve|revoke|clear-pending ใช้อนุมัติหรือเพิกถอน pairing code ของผู้ใช้บน messaging platform ต่าง ๆ

ตัวอย่าง:

```plain
hermes gateway setup
hermes gateway run
hermes gateway install
hermes gateway start
hermes whatsapp
hermes pairing list
```

### 4) Sessions / logs / backup / diagnostics / maintenance

- hermes sessions list|browse|export|delete|prune|stats|rename ใช้ดู session ล่าสุด, ค้นหาแล้ว resume, export เป็น JSONL, ลบ session เก่า หรือเปลี่ยนชื่อ session
- hermes logs ใช้ดู log; รองรับ agent, errors, gateway, list และ options ที่ใช้บ่อยคือ -n, -f, --level, --session, --since, --component
- hermes backup สำรอง Hermes home เป็น zip; --quick ทำ snapshot เฉพาะไฟล์สำคัญ; hermes import  ใช้กู้คืน backup กลับมา
- hermes doctor \[--fix\] ใช้วินิจฉัยปัญหาและพยายามซ่อมอัตโนมัติบางอย่างได้, hermes dump \[--show-keys\] ใช้สรุป environment แบบพร้อมส่งให้คนช่วยดู, hermes debug share ใช้อัปโหลด debug report พร้อม log และ system info
- hermes version, hermes update, hermes uninstall \[--full\] \[--yes\] คือกลุ่ม maintenance พื้นฐาน
- hermes insights \[--days N\] \[--source platform\] ใช้ดูสถิติการใช้งาน, token/cost/activity ตามช่วงเวลาและ platform

ตัวอย่าง:

```plain
hermes sessions list
hermes sessions browse
hermes sessions rename 20250305_091523_a1b2c3d4 "my project"
hermes logs
hermes logs gateway -n 100
hermes logs --level WARNING --since 1h
hermes backup --quick --label "pre-upgrade"
hermes import ~/hermes-backup.zip -f
hermes doctor --fix
hermes dump
hermes debug share --local
hermes update
```

### 5) Skills / cron / webhook / automation

- hermes skills browse|search|install|inspect|list|check|update|audit|uninstall|publish|snapshot|tap|config คือชุดคำสั่งสำหรับ skills ทั้งหมด ตั้งแต่ค้นหา ติดตั้ง อัปเดต audit ไปจนถึง publish และ config per-platform
- ตัวอย่างจาก docs ได้แก่ hermes skills browse --source official, hermes skills search react --source skills-sh, hermes skills search https://mintlify.com/docs --source well-known, hermes skills install... --force โดย --force override ได้เฉพาะ non-dangerous policy block แต่ไม่ override verdict แบบ dangerous
- hermes cron list|create|edit|pause|resume|run|remove|status|tick ใช้ตั้ง scheduled task และควบคุม scheduler
- hermes webhook subscribe|list|remove|test ใช้สร้าง webhook route ให้ agent ถูกเรียกจาก event ภายนอก พร้อมตั้ง prompt, event type, skill ที่จะโหลด และ target การส่งผลลัพธ์กลับ

ตัวอย่าง:

```plain
hermes skills browse
hermes skills search react --source skills-sh
hermes skills inspect official/security/1password
hermes skills install official/migration/openclaw-migration
hermes skills check
hermes skills update
hermes skills config

hermes cron list
hermes cron create
hermes cron status

hermes webhook list
hermes webhook subscribe github-pr --events pull_request
```

### 6) คำสั่งขั้นสูง / เสริม

- hermes memory setup|status|off ใช้เลือกและจัดการ external memory provider; docs ระบุ provider ที่รองรับเช่น honcho, mem0, hindsight, holographic, retaindb, byterover, supermemory ฯลฯ โดย built-in memory ยังทำงานเสมอ
- hermes honcho... เป็นคำสั่งเฉพาะเมื่อเลือก memory provider เป็น Honcho เช่น status, peers, sessions, map, peer, mode, tokens, identity, enable, disable, sync, migrate
- hermes acp ใช้รัน Hermes เป็น ACP server สำหรับ editor integration และ docs ระบุว่าต้องติดตั้ง support เพิ่มด้วย pip install -e '.\[acp\]' ก่อน
- hermes mcp serve|add|remove|list|test|configure ใช้จัดการ MCP server และรัน Hermes เป็น MCP server เอง
- hermes plugins, install, update, remove, enable, disable, list ใช้จัดการ plugin; ส่วน hermes dashboard เปิด web dashboard แต่ต้องติดตั้ง hermes-agent\[web\] ก่อน
- hermes profile list|use|create|delete|show|alias|rename|export|import ใช้ทำหลาย profile แยกกัน, hermes completion \[bash|zsh\] สร้าง shell completion, และ hermes claw migrate... ใช้ย้ายข้อมูลมาจาก OpenClaw

ตัวอย่าง:

```plain
hermes memory setup
hermes honcho status --all
hermes acp
hermes mcp list
hermes plugins list
hermes dashboard --port 8080 --no-open
hermes profile create work --clone
hermes completion zsh >> ~/.zshrc
hermes claw migrate --dry-run
```

## ชีตสรุป slash commands ในแชต (/...)

Hermes มี 2 พื้นที่สำหรับ slash commands คือใน CLI interactive และใน messaging gateway; นอกจากนี้ skill ที่ติดตั้งไว้ก็สามารถถูกเรียกเป็น / ได้ด้วยทั้งสองฝั่ง

### คำสั่งหลักใน CLI chat

- จัดการ session: /new, /reset, /clear, /history, /save, /retry, /undo, /title, /compress, /rollback, /snapshot, /stop, /queue, /resume, /status, /background, /btw, /plan, /branch
- ตั้งค่า/พฤติกรรม: /config, /model, /provider, /personality, /verbose, /fast, /reasoning, /skin, /statusbar, /voice, /yolo
- tools และ skills: /tools, /toolsets, /browser, /skills, /cron, /reload-mcp, /reload, /plugins
- ข้อมูลและ utility: /help, /usage, /insights, /platforms, /paste, /image, /debug, /profile
- ออกจาก CLI: /quit หรือ /exit
- เรียก skill โดยตรง: / เช่น /plan หรือ skill ที่ติดตั้งเอง

### คำสั่งหลักใน messaging chat

- ใช้ร่วมกับ CLI ได้หลายตัว เช่น /new, /reset, /status, /stop, /model, /provider, /personality, /fast, /retry, /undo, /compress, /title, /resume, /usage, /insights, /reasoning, /voice, /rollback, /snapshot, /background, /plan, /reload-mcp, /reload, /yolo, /debug, /help, และ /
- ที่เป็น messaging-only ตาม docs คือ /sethome, /commands, /approve, /deny, /update, /restart โดย /sethome ใช้ตั้ง chat นี้เป็น home channel ของ platform สำหรับรับผลลัพธ์จาก cron/jobs, และ /approve//deny ใช้ตอบรับหรือปฏิเสธ dangerous command ที่รออนุมัติอยู่

### คำสั่งที่ควรจำเป็นพิเศษ

```plain
/new        เริ่มบทสนทนาใหม่
/retry      ให้ลองตอบ/ทำงานรอบล่าสุดใหม่
/undo       ลบ exchange ล่าสุด
/title      ตั้งชื่อ session
/compress   ย่อ context เมื่อคุยนานมาก
/usage      ดู token/cost/session duration
/background รันงานแยกเบื้องหลัง
/plan       ให้เขียนแผนแทนลงมือทำทันที
/skills     จัดการ skills
/voice on   เปิด voice mode
```

สรุปนี้อิงจากหน้า Slash Commands Reference โดยตรง และ quickstart ก็ย้ำคำสั่งหลักอย่าง /help, /tools, /model, /personality, /save รวมถึง /voice on สำหรับ voice mode เช่นกัน

## คำสั่งเสริมที่ควรรู้เพิ่ม

ต้องการ voice mode ใน CLI หรือ messaging ให้ติดตั้ง extra voice ก่อน แล้วเปิดด้วย /voice on; quickstart ระบุคำสั่งติดตั้งเป็น pip install "hermes-agent\[voice\]"

```plain
pip install "hermes-agent[voice]"
```

ต้องการใช้ Hermes ใน editor แบบ ACP:

```plain
pip install -e '.[acp]'
hermes acp
```

ส่วน web dashboard ต้องมี extra web ก่อนถึงจะใช้ hermes dashboard ได้

## ข้อสังเกตสำคัญก่อนใช้งานจริง

- hermes model กับ /model ไม่เหมือนกัน: ตัวแรกเป็น wizard ระดับ shell สำหรับเพิ่ม provider, ใส่ API key/OAuth และตั้ง default model; ส่วน /model ตาม docs ใช้สลับระหว่าง provider/model ที่ “ตั้งค่าไว้แล้ว” ระหว่างคุยอยู่ใน session ได้ และใส่ --global เพื่อบันทึกเป็นค่า default ได้
- แต่มี issue ล่าสุดในรีโปที่รายงานว่า /model ใน chat บางเวอร์ชันยังมีอาการ docs ไม่ตรงกับ runtime หรือทำงานไม่ครบ ดังนั้นถ้าพิมพ์ /model แล้วไม่เกิดอะไรขึ้น ให้ใช้ hermes model จาก shell แทนจะชัวร์กว่า
- หน้า slash commands ระบุว่า /verbose ใช้ได้ แต่ก็มีรายงานเปิดค้างอยู่ว่าบาง build ยังไม่ expose คำสั่งนี้จริง; ถ้าต้องการโหมด verbose แบบแน่นอน ใช้ hermes chat --verbose หรือ -v ตอนเปิด session จะตรงกับ CLI reference ชัดที่สุด
- docs ระบุเองว่า alias /q ของ /queue ไปชนกับ /quit; ในทางปฏิบัติให้ใช้ /queue แบบพิมพ์เต็ม จะไม่สับสน

[กลับไปบทความทั้งหมด](https://www.sanookai.com/articles)

แชร์:
