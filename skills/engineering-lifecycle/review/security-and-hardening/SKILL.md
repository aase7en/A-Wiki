---
name: security-and-hardening
description: OWASP Top 10 prevention, authentication patterns, secrets management, dependency auditing, and input validation. Use when handling user input, authentication, data storage, or external integrations.
source: addyosmani/agent-skills@v0.6.2
adapted_for: A-Wiki
---

# Security and Hardening

## Overview

Security is not a feature — it's a property of the entire system. Every input boundary, every data store, every external integration is an attack surface. This skill applies the principle of least privilege, defense in depth, and the OWASP Top 10 to code changes.

## When to Use

- Writing code that handles user input
- Implementing authentication or authorization
- Storing or transmitting sensitive data
- Adding external integrations (APIs, webhooks, third-party libraries)
- Reviewing code with security implications
- Configuring CORS, CSP, or other security headers

**When NOT to use:** Pure algorithmic code with no inputs or outputs.

## The Three-Boundary System

### Boundary 1: Input (API, Form, File)

All external input must be validated before use:
- **Allowlist validation**: define what's allowed, reject everything else
- **Length limits**: constrain string lengths (min/max)
- **Type checking**: confirm the value is the expected type
- **Format validation**: email, URL, phone patterns with well-tested libraries
- **File uploads**: verify MIME type, scan contents, limit size

### Boundary 2: Storage (Database, Cache, Filesystem)

All data written to storage must be:
- Sanitized of injection vectors (parameterized queries, not string interpolation)
- Encrypted if sensitive (PII, credentials, financial data)
- Backed up with retention policy

### Boundary 3: Output (API Response, HTML, Log)

All output must be:
- Encoded to prevent XSS (use framework auto-escaping, not manual escaping)
- Minimized in data returned (don't return internal IDs, hashes, or full DB records)
- Free of secrets in logs (no passwords, tokens, PII)

## Authentication Patterns

### Password-based
- Hash with bcrypt (≥12 rounds), scrypt, or argon2
- Rate-limit login attempts (≤10 per 15 minutes)
- Session cookies: `httpOnly`, `secure`, `sameSite: 'lax'`
- Token expiry: short-lived access tokens, long-lived refresh tokens

### OAuth / Social Login
- Validate the `id_token` signature and issuer
- Use PKCE for mobile/SPA flows
- Never log the access token
- Scope tokens to minimum necessary permissions

### API Keys
- Keys should be random, high-entropy strings
- Store as hash (like passwords) — never store the raw key
- Scope keys to specific permissions
- Allow key rotation and revocation

## Secrets Management

- **Never** hardcode secrets in source code (even in tests)
- Use environment variables or a secrets manager
- Store secrets in `drive/.secrets` (A-Wiki) or `.env` (project-specific)
- `.env.example` in version control, `.env` in `.gitignore`
- Audit secrets in git history if leaked (rotate immediately)

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This endpoint is internal, no one will find it" | Internal endpoints are discovered through SSRF, leaked configs, or social engineering. Every endpoint needs auth. |
| "I'll add input validation later" | Input validation is not optional. Missing validation is the #1 root cause of security incidents. |
| "It's just a demo / MVP" | MVPs become production systems. Security debt compounds with interest. |
| "The framework handles security automatically" | Frameworks handle XSS and CSRF. They don't handle business logic vulnerabilities (IDOR, mass assignment, rate limiting). |

## Red Flags

- String concatenation in SQL queries
- Storing passwords in plain text
- No rate limiting on auth endpoints
- CORS `origin: '*'` in production
- Private keys or secrets in source code
- `console.log` of request bodies or tokens
- Disabling security features "just for now"
- Missing CSRF tokens on state-changing endpoints

## Verification

- [ ] Input validation at every external boundary
- [ ] Parameterized queries for all database operations
- [ ] Authentication checked on every protected endpoint
- [ ] Authorization checked (user can access this specific resource)
- [ ] Secrets management reviewed (no secrets in code)
- [ ] Security headers configured (CSP, HSTS, CORS)
- [ ] All dependencies audited (`npm audit` or equivalent)
- [ ] OWASP Top 10 reviewed against the change
