#!/usr/bin/env node
// Local management page for match-my-voice. Node built-ins only; no AI calls.
import { createServer } from "node:http";
import { readFileSync, existsSync, mkdirSync, readdirSync, writeFileSync, rmSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { homedir } from "node:os";

const HERE = dirname(fileURLToPath(import.meta.url));
const ID_RE = /^[a-z0-9-]{1,40}$/;

export function slugify(name) {
  const s = String(name).toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 40).replace(/-+$/g, "");
  return s && s !== "." && s !== ".." ? s : "persona";
}

function uniqueId(home, base) {
  const root = join(home, "profiles");
  if (!existsSync(join(root, base))) return base;
  for (let n = 2; n < 1000; n += 1) {
    const candidate = `${base.slice(0, 40 - String(n).length - 1)}-${n}`;
    if (!existsSync(join(root, candidate))) return candidate;
  }
  throw new Error("could not allocate id");
}

async function readBody(req) {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  const raw = Buffer.concat(chunks).toString("utf8");
  return raw ? JSON.parse(raw) : {};
}

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

export function createPersona(home, { name, type }) {
  ensureHome(home);
  const cleanName = String(name ?? "").trim();
  if (!cleanName) throw Object.assign(new Error("name required"), { status: 400 });
  if (type !== "self" && type !== "role") throw Object.assign(new Error("type must be self or role"), { status: 400 });
  const id = uniqueId(home, slugify(cleanName));
  const dir = join(home, "profiles", id);
  mkdirSync(dir, { recursive: true });
  const meta = { name: cleanName, type, created: today() };
  writeFileSync(join(dir, "persona.json"), JSON.stringify(meta, null, 2));
  writeFileSync(join(dir, "VOICE.md"), `# ${cleanName}\n\n（尚未建立口吻檔。在對話裡請 Agent 用 match-my-voice 收集樣本。）\n`);
  writeFileSync(join(dir, "learned.md"), "");
  return { id, ...meta };
}

export function deletePersona(home, id) {
  ensureHome(home);
  if (!ID_RE.test(id)) return false;
  const dir = join(home, "profiles", id);
  if (!existsSync(join(dir, "persona.json"))) return false;
  rmSync(dir, { recursive: true, force: true });
  const cfgPath = join(home, "config.json");
  const cfg = readJson(cfgPath, { active: null });
  if (cfg.active === id) writeFileSync(cfgPath, JSON.stringify({ active: null }, null, 2));
  return true;
}

export function getConfig(home) { ensureHome(home); return readJson(join(home, "config.json"), { active: null }); }

export function setActive(home, id) {
  ensureHome(home);
  if (id !== null && (!ID_RE.test(String(id)) || !existsSync(join(home, "profiles", id, "persona.json")))) {
    throw Object.assign(new Error("no such persona"), { status: 404 });
  }
  writeFileSync(join(home, "config.json"), JSON.stringify({ active: id }, null, 2));
  return { active: id };
}

function personaDir(home, id) {
  if (!ID_RE.test(String(id))) return null;
  const dir = join(home, "profiles", id);
  return existsSync(join(dir, "persona.json")) ? dir : null;
}

async function readText(req) {
  const chunks = [];
  for await (const c of req) chunks.push(c);
  return Buffer.concat(chunks).toString("utf8");
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
      if (url.pathname === "/api/config" && req.method === "GET") return send(res, 200, getConfig(home));
      if (url.pathname === "/api/config" && req.method === "PUT") return send(res, 200, setActive(home, (await readBody(req)).active ?? null));
      if (req.method === "POST" && url.pathname === "/api/personas") {
        const body = await readBody(req);
        return send(res, 201, createPersona(home, body));
      }
      const prof = url.pathname.match(/^\/api\/personas\/([^/]+)\/profile$/);
      if (prof) {
        const dir = personaDir(home, decodeURIComponent(prof[1]));
        if (!dir) return send(res, 404, { error: "not found" });
        if (req.method === "GET") return send(res, 200, readFileSync(join(dir, "VOICE.md"), "utf8"), "text/markdown; charset=utf-8");
        if (req.method === "PUT") { writeFileSync(join(dir, "VOICE.md"), await readText(req)); return send(res, 200, { ok: true }); }
      }
      const del = url.pathname.match(/^\/api\/personas\/([^/]+)$/);
      if (req.method === "DELETE" && del) {
        return deletePersona(home, decodeURIComponent(del[1])) ? send(res, 204, "") : send(res, 404, { error: "not found" });
      }
      return send(res, 404, { error: "not found" });
    } catch (err) {
      return send(res, err.status || 500, { error: String(err.message || err) });
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
