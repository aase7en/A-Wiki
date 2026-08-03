// plainlang.js — Plain-language translation layer (v20 A20)
//
// Translates every SSE event + tier code + hook name into a plain-Thai
// sentence for non-technical users. Research basis (Stripe/PostHog pattern #2,
// #9): every number gets a one-sentence plain-language wrapper; every block
// event gets an inline "action" affordance (data → insight → action).
//
// Exposed as window._plain(ev) -> {sentence, meta, action, tone}
//   - sentence: short Thai sentence (the headline of the row)
//   - meta:     secondary detail (duration, model, time)
//   - action:   optional "what the user can do" affordance (only for blocks)
//   - tone:     'success' | 'warn' | 'error' | 'info' | 'active' (for color)
//
// Field names mirror scripts/live-dashboard/event_logger.py:
//   session_start:   {}
//   hook_check:      {hook, tool, result, tier}
//   cost_declare:    {tier, task}
//   delegate_start:  {model, task}
//   delegate_done:   {model, duration_ms}
//   delegate_fail:   {model, reason}
//   route_plan:      {route, ...}
//   subagent_invoke: {model, task}
(function () {
  'use strict';

  // ── Tier code → plain Thai ──────────────────────────────────────────────
  // Cost-First Decision Pyramid tiers (AGENTS.md). Non-tech users do not
  // understand "tier L-1"; they understand "โมเดลฟรี".
  var TIER_LABELS = {
    'L-1': 'ค้นหาในเครื่อง',  // local FTS5/graph
    'L0':  'งานฟรี',           // hook + free model
    'L1':  'โมเดลฟรี',         // free-current roster
    'L2':  'โมเดลราคาประหยัด', // cheap-capable route
    'L3':  'โมเดลราคาประหยัด', // platform-low-scout
    'L4':  'โมเดลหลัก'         // platform-primary
  };

  function tierLabel(tier) {
    if (!tier) return 'โมเดล';
    return TIER_LABELS[tier] || tier;
  }

  // ── Hook rule name → plain Thai ─────────────────────────────────────────
  // Strip the "check_" prefix and translate the intent. Sourced from
  // scripts/hooks/*.py names actually in production.
  var HOOK_LABELS = {
    'skill_registry':       'ทะเบียน skill',
    'source_original_file': 'ไฟล์ต้นฉบับ',
    'harness_routing':      'ระบบกระจายงาน',
    'output_format':        'รูปแบบผลลัพธ์',
    'raw_immutable':        'ไฟล์ดิบ (ห้ามแก้)',
    'external_editor_drift':'การซิงค์เครื่องมือ',
    'secret_leak':          'การรั่วของความลับ',
    'bash_no_branch':       'การใช้ git branch',
    'cost_tier':            'ค่าใช้จ่ายเกินงบ',
    'agent_claim':          'การทำงานซ้อนทับ',
    'privacy':              'ข้อมูลส่วนตัว'
  };

  function hookLabel(hook) {
    if (!hook) return 'ระบบตรวจสอบ';
    var short = hook.replace('check_', '').replace(/_/g, '_');
    return HOOK_LABELS[short] || short.replace(/_/g, ' ');
  }

  // ── Model name → friendly short label ───────────────────────────────────
  // Reuses the same map as graph.js modelShort() but exposed here so plainlang
  // is self-contained (no load-order coupling).
  function modelShort(m) {
    if (!m) return 'AI';
    var id = String(m).toLowerCase();
    var map = [
      ['gemini-2.5-flash', 'Gemini 2.5 Flash'],
      ['gemini', 'Gemini'],
      ['deepseek-r1', 'DeepSeek R1'],
      ['deepseek', 'DeepSeek'],
      ['llama-3.3-70b', 'Llama 3.3 70B'],
      ['llama', 'Llama'],
      ['qwen3-235b', 'Qwen3 235B'],
      ['qwen', 'Qwen'],
      ['claude-haiku', 'Claude Haiku'],
      ['claude-sonnet', 'Claude Sonnet'],
      ['claude-opus', 'Claude Opus'],
      ['claude', 'Claude'],
      ['gpt-4o-mini', 'GPT-4o mini'],
      ['gpt-4o', 'GPT-4o'],
      ['glm', 'GLM']
    ];
    for (var i = 0; i < map.length; i++) {
      if (id.indexOf(map[i][0]) !== -1) return map[i][1];
    }
    // Free-tier suffix
    if (id.indexOf(':free') !== -1) {
      return m.split('/').pop().split(':')[0].slice(0, 18) + ' (ฟรี)';
    }
    return String(m).split('/').pop().slice(0, 18);
  }

  // ── Result classifier ───────────────────────────────────────────────────
  function resultTone(result) {
    if (result === 'block') return 'error';
    if (result === 'warn')  return 'warn';
    return 'success';
  }

  // ── Main entry: _plain(ev) ──────────────────────────────────────────────
  // ev = parsed SSE JSON object (see event_logger.py for shapes).
  function _plain(ev) {
    ev = ev || {};
    var type = ev.type || 'unknown';
    var model = modelShort(ev.model);
    var task  = ev.task || '';
    var tier  = tierLabel(ev.tier);
    var dur   = ev.duration_ms ? (ev.duration_ms / 1000).toFixed(1) + ' วินาที' : '';

    switch (type) {
      case 'session_start':
        return {
          sentence: 'เซสชันใหม่เริ่มต้น',
          meta: ev.agent ? ('โดย ' + ev.agent) : 'พร้อมทำงาน',
          action: null,
          tone: 'success'
        };

      case 'hook_check': {
        var result = ev.result || 'pass';
        var hookName = hookLabel(ev.hook);
        var tone = resultTone(result);
        var verb = result === 'block' ? 'บล็อก'
                 : result === 'warn'  ? 'ระวัง'
                 :                      'ผ่าน';
        var sentence;
        if (result === 'block') {
          sentence = 'ระบบตรวจสอบหยุดการกระทำที่ผิดกฎ (' + hookName + ')';
        } else if (result === 'warn') {
          sentence = 'ระบบตรวจสอบแจ้งระวัง: ' + hookName;
        } else {
          sentence = 'ระบบตรวจสอบ ' + verb + ': ' + hookName;
        }
        var meta = ev.tool ? ('เครื่องมือ: ' + ev.tool) : '';
        if (ev.tier) meta = (meta ? meta + ' · ' : '') + 'ระดับ: ' + tier;
        return {
          sentence: sentence,
          meta: meta,
          // PostHog/Stripe pattern: data → insight → ACTION. Only blocks get
          // an action because they are the only thing a user can act on.
          action: result === 'block' ? 'ตรวจสอบและอนุมัติ →' : null,
          tone: tone
        };
      }

      case 'cost_declare':
        return {
          sentence: 'ใช้' + tier + 'สำหรับ' + (task || 'งาน'),
          meta: 'เลือกตามหลักประหยัดก่อน',
          action: null,
          tone: 'info'
        };

      case 'delegate_start':
        return {
          sentence: model + ' เริ่มงาน' + (task ? ': ' + task : ''),
          meta: 'กำลังทำงาน · ใช้โมเดล' + (String(ev.model || '').indexOf(':free') !== -1 ? 'ฟรี' : ''),
          action: null,
          tone: 'active'
        };

      case 'delegate_done':
        return {
          sentence: model + ' ทำเสร็จ' + (dur ? ' · ' + dur : ''),
          meta: 'ส่งต่อผลลัพธ์กลับ',
          action: null,
          tone: 'success'
        };

      case 'delegate_fail':
        return {
          sentence: model + ' ทำไม่สำเร็จ' + (ev.reason ? ' — ' + ev.reason : ''),
          meta: 'ระบบจะลองใหม่หรือสลับโมเดล',
          action: 'ดูสาเหตุ →',
          tone: 'error'
        };

      case 'route_plan':
        return {
          sentence: 'วางแผนกระจายงาน' + (ev.route ? ' · ' + ev.route : ''),
          meta: 'เลือกโมเดลที่คุ้มที่สุด',
          action: null,
          tone: 'info'
        };

      case 'subagent_invoke':
        return {
          sentence: model + ' ถูกเรียก' + (task ? ' สำหรับ' + task : ''),
          meta: 'การทำงานซ้อนในขนาน',
          action: null,
          tone: 'active'
        };

      default:
        return {
          sentence: type.replace(/_/g, ' '),
          meta: '',
          action: null,
          tone: 'info'
        };
    }
  }

  // Export to global scope (no module system — bundle concatenates src/*.js).
  window._plain = _plain;
  // Expose helpers for testing / reuse by home.js
  window._plainTierLabel = tierLabel;
  window._plainHookLabel = hookLabel;
  window._plainModelShort = modelShort;
})();
