import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { tempHome, startApp, seedPersona } from "./helpers.js";

test("profile round-trips as raw markdown", async () => {
  const { dir, cleanup } = tempHome();
  try {
    seedPersona(dir, "me", { voice: "# 我\n\n- 具體，不抽象\n" });
    const app = await startApp(dir);
    try {
      const get = await fetch(`${app.base}/api/personas/me/profile`);
      assert.equal(get.status, 200);
      assert.match(get.headers.get("content-type"), /text\/markdown/);
      assert.equal(await get.text(), "# 我\n\n- 具體，不抽象\n");
      const put = await fetch(`${app.base}/api/personas/me/profile`, { method: "PUT", headers: { "content-type": "text/plain; charset=utf-8" }, body: "# 我\n\n- 具體，不抽象\n- 先講結論\n" });
      assert.equal(put.status, 200);
      assert.equal(readFileSync(join(dir, "profiles", "me", "VOICE.md"), "utf8"), "# 我\n\n- 具體，不抽象\n- 先講結論\n");
      assert.equal((await fetch(`${app.base}/api/personas/nope/profile`)).status, 404);
    } finally { await app.close(); }
  } finally { cleanup(); }
});
