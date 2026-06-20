---
name: browser-testing-with-devtools
description: Chrome DevTools MCP for live runtime data — DOM inspection, console logs, network traces, performance profiling. Use when building or debugging anything that runs in a browser.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Browser Testing with DevTools

## Overview

The browser is the final environment for frontend code. Chrome DevTools gives you live access to DOM state, console logs, network activity, and performance data. This skill uses the DevTools protocol to debug, verify, and optimize browser-rendered code.

## When to Use

- Debugging visual layout issues
- Inspecting network requests and API calls
- Checking console errors or warnings
- Profiling performance (LCP, INP, CLS)
- Testing in-progress UI changes
- Verifying responsive design at different viewports

**When NOT to use:** Server-side logic, API-only changes, or non-browser environments.

## The Process

### Step 1: Navigate or Reload

Open the page that exhibits the behavior you're debugging. If the issue depends on a specific state, reproduce that state before collecting data.

### Step 2: Choose Your Tool

- **Console** — JS errors, warnings, logs. Check before and after the action.
- **Elements** — DOM structure, computed styles, accessibility tree.
- **Network** — API calls, timing, request/response payloads.
- **Performance** — LCP, INP, CLS, long tasks.
- **Application** — Storage, cookies, service workers, caches.
- **Lighthouse** — Full audit for a11y, perf, SEO, best practices.

### Step 3: Collect Evidence

Run the action that triggers the issue, then capture the evidence:
- Console output (errors, logs, warnings)
- Network waterfall (timing, status codes, payload sizes)
- DOM snapshot (current state after action)
- Performance trace (if applicable)

### Step 4: Diagnose

Compare actual behavior against expected behavior:
- Network: wrong URL? wrong method? unexpected status?
- DOM: element not rendering? wrong classes? missing content?
- Console: unhandled errors? unexpected state?
- Performance: long tasks? layout shifts? slow LCP element?

### Step 5: Fix and Verify

Apply the fix, then re-run the same DevTools check to confirm the issue is resolved.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The code looks correct, it must be a browser issue" | It's almost never a browser issue. Check the runtime state. |
| "I'll check the console if there's an error" | Check the console always. Silent failures are the hardest to debug. |
| "The layout renders fine in the code view" | The code view doesn't show runtime state. Render-blocking resources, async loading, and JS execution order only appear in the browser. |
| "Performance looks fine to me" | Your machine is not your user's machine. Use DevTools performance profiling and throttling. |

## Red Flags

- Debugging a browser issue without checking the console
- Relying on a code review to catch runtime errors
- Assuming the DOM is in a certain state without inspecting it
- Not checking the network tab for API errors or wrong endpoints
- Performance claims without DevTools measurements
- "It works on my machine" — test with CPU/network throttling

## Verification

- [ ] Console shows no errors (production mode)
- [ ] Network requests all return expected status codes
- [ ] DOM structure matches the component tree
- [ ] Accessibility tree shows all interactive elements
- [ ] Responsive design verified at mobile breakpoint
- [ ] Performance: LCP < 2.5s, no long tasks, no layout shift
