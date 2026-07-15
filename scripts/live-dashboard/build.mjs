// A-Wiki Dashboard build script (v8 foundation refactor).
// Bundles all src/*.js into a single minified app.min.js + sourcemap.
//
// The dashboard uses plain global-scope functions (no ES modules). esbuild
// concatenates the source files in alphabetical order and minifies — globals
// remain global, inline onclick handlers keep working.
//
// Usage:
//   node build.mjs           # one-shot build
//   node build.mjs --watch   # rebuild on file change (dev mode)
import * as esbuild from "esbuild";
import { glob } from "node:fs/promises";
import { existsSync } from "node:fs";

const SRC_DIR = "src";
const OUT_FILE = "app.min.js";

// Collect source files — app.js first (it has globals + boot), rest alphabetical.
const entryFile = `${SRC_DIR}/app.js`;
if (!existsSync(entryFile)) {
  // src/ doesn't exist yet (pre-C8). Exit gracefully — build is a no-op until JS is extracted.
  console.log("⚠️  src/app.js not found — run build after CHUNK C8 (JS extraction). Skipping.");
  process.exit(0);
}

const ctx = await esbuild.context({
  entryPoints: [entryFile],
  bundle: true,           // follow imports (none in plain-globals mode, but safe)
  minify: true,
  sourcemap: true,
  target: "es2020",
  format: "iife",         // wrap in IIFE — but globals declared WITHOUT var/let at top level stay global
  outfile: OUT_FILE,
  logLevel: "info",
  banner: {
    js: "// A-Wiki Dashboard — bundled by esbuild (v8). See src/ for source files. Do not edit directly.",
  },
});

const isWatch = process.argv.includes("--watch");
if (isWatch) {
  await ctx.watch();
  console.log("👀 Watching src/ for changes...");
} else {
  await ctx.rebuild();
  await ctx.dispose();
}
