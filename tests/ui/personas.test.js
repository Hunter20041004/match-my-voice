import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { tempHome, startApp, seedPersona } from "./helpers.js";

test("GET /api/personas lists personas with metadata and the active id", async () => {
  const { dir, cleanup } = tempHome();
  try {
    seedPersona(dir, "me", { name: "我", type: "self" });
    seedPersona(dir, "cmo", { name: "徵才月行銷長", type: "role" });
    writeFileSync(join(dir, "config.json"), JSON.stringify({ active: "me" }));
    const app = await startApp(dir);
    try {
      const res = await fetch(`${app.base}/api/personas`);
      assert.equal(res.status, 200);
      const body = await res.json();
      assert.equal(body.active, "me");
      const ids = body.personas.map((p) => p.id).sort();
      assert.deepEqual(ids, ["cmo", "me"]);
      const cmo = body.personas.find((p) => p.id === "cmo");
      assert.equal(cmo.name, "徵才月行銷長");
      assert.equal(cmo.type, "role");
    } finally { await app.close(); }
  } finally { cleanup(); }
});

test("a bare profiles/default/VOICE.md is migrated into a self persona on first listing", async () => {
  const { dir, cleanup } = tempHome();
  try {
    mkdirSync(join(dir, "profiles", "default"), { recursive: true });
    writeFileSync(join(dir, "profiles", "default", "VOICE.md"), "# existing\n");
    const app = await startApp(dir);
    try {
      const body = await (await fetch(`${app.base}/api/personas`)).json();
      assert.equal(body.personas.length, 1);
      assert.equal(body.personas[0].id, "default");
      assert.equal(body.personas[0].type, "self");
      assert.equal(body.active, "default");
      assert.ok(existsSync(join(dir, "profiles", "default", "persona.json")));
      assert.ok(existsSync(join(dir, "profiles", "default", "learned.md")));
      assert.equal(readFileSync(join(dir, "profiles", "default", "VOICE.md"), "utf8"), "# existing\n");
    } finally { await app.close(); }
  } finally { cleanup(); }
});

test("GET / serves the page", async () => {
  const { dir, cleanup } = tempHome();
  try {
    const app = await startApp(dir);
    try {
      const res = await fetch(`${app.base}/`);
      assert.equal(res.status, 200);
      assert.match(res.headers.get("content-type"), /text\/html/);
    } finally { await app.close(); }
  } finally { cleanup(); }
});

import { slugify } from "../../ui/serve.js";

test("slugify makes safe ids and never a path segment", () => {
  assert.equal(slugify("徵才月行銷長"), "persona");
  assert.equal(slugify("Marketing Lead 2026"), "marketing-lead-2026");
  assert.equal(slugify("  ..  "), "persona");
  assert.equal(slugify("a".repeat(60)).length, 40);
});

test("POST /api/personas creates the folder set and rejects bad input", async () => {
  const { dir, cleanup } = tempHome();
  try {
    const app = await startApp(dir);
    try {
      const ok = await fetch(`${app.base}/api/personas`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "徵才月行銷長", type: "role" }) });
      assert.equal(ok.status, 201);
      const created = await ok.json();
      assert.equal(created.type, "role");
      assert.equal(created.name, "徵才月行銷長");
      const p = join(dir, "profiles", created.id);
      for (const f of ["persona.json", "VOICE.md", "learned.md"]) assert.ok(existsSync(join(p, f)), f);

      const dup = await fetch(`${app.base}/api/personas`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "徵才月行銷長", type: "role" }) });
      assert.equal(dup.status, 201, "same display name gets a distinct id");
      assert.notEqual((await dup.json()).id, created.id);

      const badType = await fetch(`${app.base}/api/personas`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "x", type: "brand" }) });
      assert.equal(badType.status, 400);
      const empty = await fetch(`${app.base}/api/personas`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: "   ", type: "self" }) });
      assert.equal(empty.status, 400);
    } finally { await app.close(); }
  } finally { cleanup(); }
});

test("DELETE /api/personas/:id removes it and clears active if needed", async () => {
  const { dir, cleanup } = tempHome();
  try {
    seedPersona(dir, "me");
    writeFileSync(join(dir, "config.json"), JSON.stringify({ active: "me" }));
    const app = await startApp(dir);
    try {
      assert.equal((await fetch(`${app.base}/api/personas/me`, { method: "DELETE" })).status, 204);
      assert.ok(!existsSync(join(dir, "profiles", "me")));
      assert.equal(JSON.parse(readFileSync(join(dir, "config.json"), "utf8")).active, null);
      assert.equal((await fetch(`${app.base}/api/personas/me`, { method: "DELETE" })).status, 404);
      assert.equal((await fetch(`${app.base}/api/personas/..`, { method: "DELETE" })).status, 404);
    } finally { await app.close(); }
  } finally { cleanup(); }
});
