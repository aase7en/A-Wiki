// A-Wiki Dashboard build script (v8 foundation refactor).
// Concatenates src/*.js into a single minified app.min.js + sourcemap.
//
// The dashboard uses plain global-scope functions (no ES modules). We concat
// the source files in a specific order (app.js first for globals) and minify
// WITHOUT wrapping in IIFE — so global function declarations remain accessible
// to inline onclick handlers in the HTML markup.
//
// Usage:
//   node build.mjs           # one-shot build
//   node build.mjs --watch   # rebuild on file change (dev mode)
import * as esbuild from "esbuild";
import { readFileSync, existsSync } from "node:fs";

const SRC_DIR = "src";
const OUT_FILE = "app.min.js";

// Load order: app.js (globals + helpers + boot) must be FIRST.
// Rest are independent (they reference globals from app.js and each other).
const LOAD_ORDER = [
  "app.js",
  "sse.js",        // if exists (SSE handlers)
  "subagents.js",
  "modals.js",     // keyboard shortcuts, keybind, notif, workspace, palette, compare, sim
  "skills.js",
  "graph.js",
  "coverage.js",
  "analytics.js",
  "chat.js",
  "theme.js",
];

// Check if src/ exists yet
if (!existsSync(SRC_DIR + "/app.js")) {
  console.log("⚠️  src/app.js not found — run build after CHUNK C8 (JS extraction). Skipping.");
  process.exit(0);
}

// Read and concat all source files in order
let allCode = "// === A-Wiki Dashboard — bundled by esbuild (v8). See src/ for source files. Do not edit. ===\n";
for (const fname of LOAD_ORDER) {
  const fpath = SRC_DIR + "/" + fname;
  if (existsSync(fpath)) {
    const content = readFileSync(fpath, "utf-8");
    allCode += "\n// === FILE: " + fname + " ===\n" + content + "\n";
    console.log("  + " + fname + " (" + content.length + " bytes)");
  }
}

const isWatch = process.argv.includes("--watch");

if (isWatch) {
  const ctx = await esbuild.context({
    stdin: { contents: allCode, resolveDir: "." },
    minify: true,
    sourcemap: true,
    target: "es2020",
    outfile: OUT_FILE,
    logLevel: "info",
  });
  await ctx.watch();
  console.log("👀 Watching src/ for changes...");
} else {
  const result = await esbuild.transform(allCode, {
    minify: true,
    sourcemap: true,
    target: "es2020",
    loader: "js",
  });
  const { writeFileSync } = await import("node:fs");
  writeFileSync(OUT_FILE, result.code);
  writeFileSync(OUT_FILE + ".map", result.map);
  console.log("✅ " + OUT_FILE + " (" + (result.code.length / 1024).toFixed(1) + " KB)");
}
