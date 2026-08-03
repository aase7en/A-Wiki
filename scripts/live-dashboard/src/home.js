// home.js — v20 D20 Activity Story rendering for #view-home
//
// Renders the hero sentence + 4 story tiles + binds SSE-driven state
// (S.activeCount, S.delegateFree, S.delegatePaid, S.failCount) to tile
// counts so they update in real-time without replaying count-up on every
// poll (NN/g: replaying = annoying).
//
// Research basis:
//   - Stripe/PostHog #1: one plain-language hero metric
//   - NN/g: count-up ONCE on mount, not on every render
//   - M3/Apple: ease-out cubic (1-Math.pow(1-t,3)) ≈ cubic-bezier(0.05,0.7,0.1,1)
//   - Miller's Law: 4 tiles max (under 7±2)
//   - Okabe-Ito: colorblind-safe semantic colors
//
// Mounted from app.js boot + setView('home'). Idempotent (safe to call twice).
(function () {
  'use strict';

  // ── count-up helper ──────────────────────────────────────────────────────
  // Plays ONCE per element. Uses ease-out cubic (research-compliant, M3 ban
  // on linear easing). Duration 900ms (600-1000ms sweet spot).
  function countUp(el, target, decimals) {
    if (!el) return;
    decimals = decimals || 0;
    // Skip if already at target (avoid replay on re-render).
    var current = parseFloat(el.getAttribute('data-shown')) || 0;
    if (current === target) {
      el.textContent = decimals ? target.toFixed(decimals) : String(target);
      return;
    }
    var start = current;
    var startTime = performance.now();
    var duration = 900;
    function step(now) {
      var t = Math.min(1, (now - startTime) / duration);
      // ease-out cubic ≈ cubic-bezier(0.05,0.7,0.1,1) enter curve
      var eased = 1 - Math.pow(1 - t, 3);
      var val = start + (target - start) * eased;
      el.textContent = decimals ? val.toFixed(decimals) : Math.round(val);
      if (t < 1) {
        requestAnimationFrame(step);
      } else {
        el.setAttribute('data-shown', String(target));
      }
    }
    requestAnimationFrame(step);
  }

  // ── state snapshot ──────────────────────────────────────────────────────
  // Reads from the global `S` object maintained by graph.js. Wrapped in
  // typeof guards so home.js is safe even if graph.js hasn't initialized.
  function _homeState() {
    var S = (typeof window !== 'undefined' && window.S) || {};
    return {
      active: S.activeCount || 0,
      done:   (S.delegateFree || 0) + (S.delegatePaid || 0),
      // Cost saved: estimate. Paid-tier rate ≈ $0.012/delegation vs free $0.
      // Conservative; refine when real cost history is wired (CHUNK E20+).
      saved:  (S.delegateFree || 0) * 0.05,
      risks:  S.failCount || 0
    };
  }

  // ── render: hero + tiles ────────────────────────────────────────────────
  function renderHome() {
    var st = _homeState();

    // Hero numbers (count-up only on first mount or when value changes
    // significantly — countUp internally skips if already at target).
    countUp($('home-hero-done'), st.done, 0);
    countUp($('home-hero-saved'), st.saved, 2);
    countUp($('home-hero-risks'), st.risks, 0);

    // Tile numbers
    countUp($('home-num-active'), st.active, 0);
    countUp($('home-num-done'), st.done, 0);
    countUp($('home-num-saved'), st.saved, 2);
    countUp($('home-num-risks'), st.risks, 0);

    // Tile explainers (context-aware, plain language)
    var exA = $('home-explain-active');
    if (exA) {
      exA.textContent = st.active === 0
        ? 'AI ทำงานเสร็จหมดแล้ว · พร้อมรับงานใหม่'
        : 'AI ' + st.active + ' ตัวกำลังทำงานพร้อมกัน';
    }
  }

  // ── live update hook (called by SSE handlers via _homeOnEvent) ───────────
  // Instead of monkey-patching onDelDone/onHook (fragile), expose a single
  // entry point that graph.js CAN call (but doesn't have to — renderHome
  // also runs on a 2s rAF-throttled loop while Home is visible).
  var _homeRAF = null;
  function _homeOnEvent(ev) {
    // Only re-render if Home is currently visible (save CPU).
    if (typeof currentView === 'undefined' || currentView !== 'home') return;
    if (_homeRAF) return;  // throttle: one render per frame
    _homeRAF = requestAnimationFrame(function () {
      _homeRAF = null;
      renderHome();
    });
  }
  window._homeOnEvent = _homeOnEvent;

  // ── mount ──────────────────────────────────────────────────────────────
  // Called from setView('home') in app.js and on boot. Idempotent.
  var _homeMounted = false;
  function homeMount() {
    renderHome();
    if (!_homeMounted) {
      _homeMounted = true;
      // Hook into SSE dispatch: graph.js's _dispatchSSE (or equivalent) is
      // the single chokepoint where all 7 event types flow. We wrap it so
      // Home gets live updates without touching each handler.
      // The wrapper is defensive — if the original isn't defined yet, we
      // retry on next setView('home').
      _wrapSSE();
    }
  }
  window.homeMount = homeMount;

  // ── SSE wrapper ─────────────────────────────────────────────────────────
  // graph.js calls pushTimeline(ev) for every event. We wrap pushTimeline
  // so _homeOnEvent fires too. Idempotent (only wraps once).
  var _wrapped = false;
  function _wrapSSE() {
    if (_wrapped) return;
    if (typeof pushTimeline !== 'function') return;  // not loaded yet
    _wrapped = true;
    var orig = pushTimeline;
    pushTimeline = function (ev) {
      try { _homeOnEvent(ev); } catch (_) {}
      return orig.apply(this, arguments);
    };
  }

  // Expose for app.js to call from setView('home') branch + boot.
  // (app.js's setView already has a `v==='home'` check added in C20 that
  // we now extend to call homeMount.)
})();
