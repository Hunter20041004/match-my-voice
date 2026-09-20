import { test } from "node:test";
import assert from "node:assert/strict";
import { tempHome, startApp, seedPersona } from "./helpers.js";

test("PUT /api/config sets the active persona and rejects unknown ids", async () => {
  const { dir, cleanup } = tempHome();
  try {
    seedPersona(dir, "me"); seedPersona(dir, "cmo", { type: "role" });
    const app = await startApp(dir);
    try {
      assert.equal((await (await fetch(`${app.base}/api/config`)).json()).active, null);
      const put = (active) => fetch(`${app.base}/api/config`, { method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ active }) });
      assert.equal((await put("cmo")).status, 200);
      assert.equal((await (await fetch(`${app.base}/api/config`)).json()).active, "cmo");
      assert.equal((await put("nope")).status, 404);
      assert.equal((await (await fetch(`${app.base}/api/config`)).json()).active, "cmo");
      assert.equal((await put(null)).status, 200);
      assert.equal((await (await fetch(`${app.base}/api/config`)).json()).active, null);
    } finally { await app.close(); }
  } finally { cleanup(); }
});
