import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { tempHome, startApp, seedPersona } from "./helpers.js";
import { parseLearned, serializeLearned } from "../../ui/serve.js";

const SAMPLE = [
  "- [active] 2026-09-20 | work email | 開頭直接講事情，不寒暄 | source: 實習求職信, 第1句",
  "- [revoked] 2026-09-18 | social post | 每段結尾加表情符號 | source: 徵才月貼文, 第3段",
  "some stray line",
  "",
].join("\n");

test("parseLearned reads the line format and keeps stray lines", () => {
  const e = parseLearned(SAMPLE);
  assert.equal(e.length, 3);
  assert.deepEqual(e[0], { index: 0, status: "active", date: "2026-09-20", context: "work email", rule: "開頭直接講事情，不寒暄", source: "實習求職信, 第1句" });
  assert.equal(e[1].status, "revoked");
  assert.equal(e[2].status, "unparsed");
  assert.equal(serializeLearned(e), SAMPLE);
});

test("PATCH revokes in place and edits rule text; unparsed lines are untouchable", async () => {
  const { dir, cleanup } = tempHome();
  try {
    seedPersona(dir, "me", { learned: SAMPLE });
    const app = await startApp(dir);
    try {
      const list = await (await fetch(`${app.base}/api/personas/me/learned`)).json();
      assert.equal(list.entries[0].status, "active");
      const patch = (i, body) => fetch(`${app.base}/api/personas/me/learned/${i}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
      assert.equal((await patch(0, { status: "revoked" })).status, 200);
      const text = readFileSync(join(dir, "profiles", "me", "learned.md"), "utf8");
      assert.match(text, /^- \[revoked\] 2026-09-20 \| work email/m);
      assert.equal((await patch(1, { rule: "每段結尾不加表情符號" })).status, 200);
      assert.match(readFileSync(join(dir, "profiles", "me", "learned.md"), "utf8"), /每段結尾不加表情符號/);
      assert.equal((await patch(2, { status: "active" })).status, 400);
      assert.equal((await patch(9, { status: "active" })).status, 404);
      assert.equal((await patch(0, { status: "maybe" })).status, 400);
    } finally { await app.close(); }
  } finally { cleanup(); }
});
