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
