import { mkdtempSync, rmSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createApp } from "../../ui/serve.js";

export function tempHome() {
  const dir = mkdtempSync(join(tmpdir(), "mmv-"));
  return { dir, cleanup: () => rmSync(dir, { recursive: true, force: true }) };
}

export async function startApp(homeDir) {
  const app = createApp(homeDir);
  await new Promise((resolve) => app.server.listen(0, "127.0.0.1", resolve));
  const { port } = app.server.address();
  return {
    base: `http://127.0.0.1:${port}`,
    close: () => new Promise((resolve) => app.server.close(resolve)),
  };
}

export function seedPersona(homeDir, id, { name = id, type = "self", voice = "# Voice\n", learned = "" } = {}) {
  const dir = join(homeDir, "profiles", id);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, "persona.json"), JSON.stringify({ name, type, created: "2026-09-20" }));
  writeFileSync(join(dir, "VOICE.md"), voice);
  writeFileSync(join(dir, "learned.md"), learned);
}
