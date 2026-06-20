---
name: code-simplification
description: Reduce unnecessary complexity while preserving exact behavior. Use when code works but is harder to read or maintain than it should be. Use when reviewing code and finding the complexity outweighs the problem being solved.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Code Simplification

## Overview

Complexity is a liability. Every abstraction, pattern, and indirection must earn its keep. This skill applies Chesterton's Fence ("understand it before removing it") and the Rule of 500 (extract when a module exceeds 500 lines) to reduce complexity safely.

## When to Use

- Code works but is harder to read than it should be
- A function or module is too long
- You see unnecessary abstraction (factory pattern for one call site)
- Design patterns are used where simple functions would do
- After implementation, before code review

**When NOT to use:** The code is correct and simple enough for its purpose. Over-simplification removes necessary clarity.

## The Process

### Step 1: Understand Before Removing (Chesterton's Fence)

Before removing ANY code, understand why it exists:
1. Read the git blame or history
2. Check if there's a related test that explains the behavior
3. If you can't figure it out in 2 minutes, ask or leave a comment

**Do not remove code you don't understand.** It exists for a reason, even if that reason is no longer valid.

### Step 2: Apply the Rule of 500

When a module exceeds 500 lines:
1. Identify the logical groupings within it
2. Extract each group into its own module
3. Keep the public API stable (don't change imports in other files)
4. Each extracted module should have a clear single responsibility

### Step 3: Reduce Layering

Identify layers that add no value:
- Translating between two identical representations
- Wrapper functions that don't add behavior
- Adapter patterns where the direct call works fine
- Factory functions with only one product type

### Step 4: Flatten Control Flow

Deeply nested conditionals hide the main path:
```
// Before
if (user) {
  if (user.isActive) {
    if (user.hasPermission('write')) {
      // main logic
    }
  }
}

// After
if (!user || !user.isActive || !user.hasPermission('write')) return;
// main logic
```

### Step 5: Replace Patterns with Primitives

Prefer the simplest construct that works:
- Generic event bus → function call (for 1-2 event types)
- Abstract factory → direct instantiation (for 1-2 variants)
- Strategy pattern → if/else or switch (for 2-3 strategies)
- Observable/RxJS → Promise or async/await (for single events)

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This abstraction anticipates future requirements" | You don't know what future requirements look like. Build for what exists, not what might exist. |
| "This pattern is more 'correct' architecturally" | Architecture serves readability, not the other way around. Boring code is better. |
| "The code is complicated because the problem is complicated" | Bad simplification is removing necessary complexity. Good simplification is removing unnecessary complexity. They are different. |
| "Let's keep it flexible" | Flexibility is also complexity. Every open extension point is a burden to understand. |

## Red Flags

- More than 500 lines in a single module
- Functions longer than 50 lines
- 3+ levels of nesting
- Patterns used for single-use abstractions
- Removing code you don't understand
- "We might need this later" justifications
- Unused exports or dead code paths

## Verification

- [ ] All existing tests still pass after simplification
- [ ] No code was removed without understanding its purpose
- [ ] Each module is under 500 lines (or justified)
- [ ] No unnecessary abstraction layers remain
- [ ] Control flow is flat (max 2 levels deep in any function)
- [ ] Dead code has been removed (not commented out)
