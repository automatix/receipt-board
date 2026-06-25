// Bundles the TypeScript GUI with esbuild and copies the static HTML/CSS into the
// Python package (src/receipt_board/gui/static), which the local server serves at /app.
import { build } from "esbuild";
import { copyFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = resolve(here, "../src/receipt_board/gui/static");

await mkdir(outDir, { recursive: true });

await build({
  entryPoints: [resolve(here, "src/main.ts")],
  bundle: true,
  format: "iife",
  target: ["es2020"],
  outfile: resolve(outDir, "app.js"),
  minify: true,
  sourcemap: false,
  logLevel: "info",
});

await copyFile(resolve(here, "index.html"), resolve(outDir, "index.html"));
await copyFile(resolve(here, "src/styles.css"), resolve(outDir, "styles.css"));

console.log(`GUI bundled -> ${outDir}`);
