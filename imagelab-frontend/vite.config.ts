// Using vitest/config (Vitest 2+ idiomatic pattern) for type-safe test options
// without requiring the older triple-slash reference hack.
import { createReadStream, readdirSync, readFileSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { defineConfig, type Plugin } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Path the app serves Blockly's media from. Keep in sync with BLOCKLY_MEDIA_PATH
// in src/blocklyMedia.ts.
const BLOCKLY_MEDIA_PATH = "blockly-media";

const MEDIA_TYPES: Record<string, string> = {
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".gif": "image/gif",
  ".mp3": "audio/mpeg",
  ".cur": "image/x-icon",
};

/**
 * Serves the media that ships with the installed blockly package (sprites.png
 * for the zoom and trash controls, and the click/delete sounds), so Blockly does
 * not fetch them from its default remote URL, which now returns 404.
 */
function blocklyMedia(): Plugin {
  const require = createRequire(import.meta.url);
  // blockly's "exports" hide package.json, but its entry point sits at the package root.
  const mediaDir = path.join(path.dirname(require.resolve("blockly")), "media");
  const prefix = `/${BLOCKLY_MEDIA_PATH}/`;

  return {
    name: "imagelab-blockly-media",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const url = req.url?.split("?")[0] ?? "";
        if (!url.startsWith(prefix)) return next();
        const name = path.basename(decodeURIComponent(url.slice(prefix.length)));
        const file = path.join(mediaDir, name);
        try {
          if (!statSync(file).isFile()) return next();
        } catch {
          return next();
        }
        res.setHeader(
          "Content-Type",
          MEDIA_TYPES[path.extname(name)] ?? "application/octet-stream",
        );
        createReadStream(file).pipe(res);
      });
    },
    generateBundle() {
      for (const name of readdirSync(mediaDir)) {
        this.emitFile({
          type: "asset",
          fileName: `${BLOCKLY_MEDIA_PATH}/${name}`,
          source: readFileSync(path.join(mediaDir, name)),
        });
      }
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), blocklyMedia()],
  server: { port: 3100 },
  test: {
    include: ["tests/**/*.test.{ts,tsx}", "src/**/*.test.{ts,tsx}"],
    clearMocks: true,
    environment: "node", // explicit; per-file override via @vitest-environment jsdom for React component tests
  },
});
