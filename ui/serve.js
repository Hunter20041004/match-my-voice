#!/usr/bin/env node
// Local management page for match-my-voice. Node built-ins only; no AI calls.
import { createServer } from "node:http";
import { readFileSync, existsSync, mkdirSync, readdirSync, writeFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
const ID_RE = /^[a-z0-9-]{1,40}$/;

export function defaultHome() {
  return process.env.MATCH_MY_VOICE_HOME || join(homedir(), ".config", "match-my-voice");
}

function readJson(path, fallback) {
  try { return JSON.parse(readFileSync(path, "utf8")); } catch { return fallback; }
}

function today() { return new Date().toISOString().slice(0, 10); }

export function ensureHome(home) {
  mkdirSync(join(home, "profiles"), { recursive: true });
  const cfgPath = join(home, "config.json");
  if (!existsSync(cfgPath)) writeFileSync(cfgPath, JSON.stringify({ active: null }, null, 2));
  // Migrate a pre-persona profiles/default/VOICE.md into a self persona.
  const def = join(home, "profiles", "default");
  if (existsSync(join(def, "VOICE.md"))) {
    if (!existsSync(join(def, "persona.json"))) {
      writeFileSync(join(def, "persona.json"), JSON.stringify({ name: "default", type: "self", created: today() }, null, 2));
    }
    if (!existsSync(join(def, "learned.md"))) writeFileSync(join(def, "learned.md"), "");
    const cfg = readJson(cfgPath, { active: null });
    if (!cfg.active) writeFileSync(cfgPath, JSON.stringify({ active: "default" }, null, 2));
  }
}

export function listPersonas(home) {
  ensureHome(home);
  const root = join(home, "profiles");
  const personas = readdirSync(root, { withFileTypes: true })
    .filter((d) => d.isDirectory() && ID_RE.test(d.name) && existsSync(join(root, d.name, "persona.json")))
    .map((d) => ({ id: d.name, ...readJson(join(root, d.name, "persona.json"), {}) }));
  const { active } = readJson(join(home, "config.json"), { active: null });
  return { active: active ?? null, personas };
}

function send(res, status, body, type = "application/json; charset=utf-8") {
  res.writeHead(status, { "content-type": type });
  res.end(typeof body === "string" ? body : JSON.stringify(body));
}

export function createApp(home) {
  const page = () => readFileSync(join(HERE, "index.html"), "utf8");
  const server = createServer(async (req, res) => {
    const url = new URL(req.url, "http://localhost");
    try {
      if (req.method === "GET" && url.pathname === "/") return send(res, 200, page(), "text/html; charset=utf-8");
      if (req.method === "GET" && url.pathname === "/api/personas") return send(res, 200, listPersonas(home));
      return send(res, 404, { error: "not found" });
    } catch (err) {
      return send(res, 500, { error: String(err.message || err) });
    }
  });
  return { server };
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const home = defaultHome();
  const { server } = createApp(home);
  const port = Number(process.env.MATCH_MY_VOICE_PORT) || 0;   // 0 = pick a free port
  server.listen(port, "127.0.0.1", () => {
    const { port: bound } = server.address();
    console.log(`match-my-voice UI → http://127.0.0.1:${bound}   (storage: ${home})`);
  });
}
