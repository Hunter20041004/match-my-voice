# Personas, Feedback Loop, and Local UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let one person keep several named voices (self and role), have the agent learn from the person's own edits to its drafts, and manage all of it in a local web page served from the skill folder.

**Architecture:** Three layers, all inside `~/.claude/skills/match-my-voice/`. (1) Skill documents (`SKILL.md`, `references/*.md`) teach the agent the persona model and the feedback loop — verified by contract tests as before. (2) Storage under `~/.config/match-my-voice/` is plain text the person can open in any editor; its layout is documented in the skill and read/written by the UI. (3) `ui/serve.js` is a Node server using only built-in modules that serves `ui/index.html` and a small JSON API over that storage — verified by `node --test` against a temporary home directory. This tool never calls an AI model.

**Tech Stack:** Markdown; Python 3 stdlib `unittest` (contract tests); Node ≥ 18 built-ins only (`node:http`, `node:fs`, `node:path`, `node:test`, global `fetch`); single-file HTML with Tailwind CDN and CSS variables.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-20-personas-and-feedback-design.md`. Acceptance check numbers below refer to its `## 驗收檢查`.
- Skill body documents are English. `README.md` is Traditional Chinese. UI text is Traditional Chinese.
- **No npm packages. No `package.json` dependencies. No build step.** `ui/serve.js` and its tests use Node built-ins only. `git clone` then `node ui/serve.js` must work.
- The tool never calls an AI API and never needs a key.
- Storage root is `~/.config/match-my-voice/`, overridable by env var `MATCH_MY_VOICE_HOME` (tests use a temp dir). Layout: `config.json` = `{"active": "<id>"}`; `profiles/<id>/persona.json` = `{"name": "...", "type": "self"|"role", "created": "<ISO date>"}`; `profiles/<id>/VOICE.md`; `profiles/<id>/learned.md`.
- Persona ids: lowercase ASCII letters, digits, hyphens; 1–40 chars; never `.` or `..`. Derived from the display name by the server; the display name lives in `persona.json`. The existing `default` id stays `default`.
- `learned.md` line format, one rule per line: `- [active|revoked] YYYY-MM-DD | <context label> | <rule> | source: <task>, <location>`. Revoking flips the status word in place; nothing is deleted.
- The agent reads `VOICE.md` plus the `[active]` lines of `learned.md`; `learned.md` is the source of truth for learned rules.
- `flat()` in the contract tests collapses whitespace and lowercases but keeps markdown punctuation. Keep asserted phrases unbroken on one line; never wrap `**` around part of one; blockquote `>` continuation markers land inside text.
- Contract tests: `cd ~/.claude/skills/match-my-voice && python3 -m unittest discover -s tests -q`. Server tests: `node --test tests/ui/`. Both must be green at each task's end.
- Branch `feat/personas-feedback-ui`, created in Task 0.
- Task 5 is a **gate held by the controller, not a subagent**: the visual direction must be chosen by the user before Task 11 starts (global frontend rule 硬規則三). Task 14 is the screenshot self-check (硬規則一); the branch is not complete until it passes.
- Product-owner teaching: before the full-suite run in Task 15 and before the merge, the controller pauses for a product-understanding checkpoint with the user.

---

### Task 0: Branch and baseline

**Files:** none modified.

- [ ] **Step 1: Create the branch and confirm baseline**

```bash
cd ~/.claude/skills/match-my-voice
git checkout -b feat/personas-feedback-ui
python3 -m unittest discover -s tests -q
node --version
```

Expected: `Ran 16 tests` … `OK`; Node prints `v18` or higher. If either fails, stop and report.

---

### Task 1: Persona model in the skill (check 1, part 8)

**Files:**
- Modify: `SKILL.md` — replace `## Find and separate personal profiles` body
- Modify: `references/profile-template.md` — add persona metadata line
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Produces: the terms `persona`, `active persona`, the file names `config.json`, `persona.json`, `learned.md`, and the `self`/`role` type words, used by every later task.

- [ ] **Step 1: Write the failing test**

Add a new class at the end of `tests/test_skill_contract.py`, before `if __name__ == "__main__":`:

```python
class PersonaContractTests(unittest.TestCase):
    """Traces to docs/superpowers/specs/2026-09-20-personas-and-feedback-design.md."""
    longMessage = False

    # Check 1: several personas; UI sets the active one; chat overrides once.
    def test_skill_defines_personas_and_active_persona_resolution(self):
        skill = flat(read("SKILL.md"))
        for term in ("persona", "config.json", "persona.json", "learned.md"):
            self.assertIn(term, skill, f"SKILL.md must introduce: {term}")
        self.assertIn('"active"', read("SKILL.md"), "config.json's active key must be named")
        self.assertIn("read the active persona from", skill,
                      "the default persona must come from config.json")
        self.assertIn("overrides it for this task only", skill,
                      "a chat-level persona choice must be one-off")
        self.assertIn("if only one persona exists, use it", skill,
                      "single persona needs no question")
        self.assertIn("ask once", skill, "several personas and no active one → one question")
        self.assertIn("personas never inherit from each other", skill,
                      "personas must be independent")

        template = flat(read("references/profile-template.md"))
        self.assertIn("persona.json", template)
        for t in ('"self"', '"role"'):
            self.assertIn(t, read("references/profile-template.md"), f"type value {t}")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.PersonaContractTests -v`
Expected: FAIL with `SKILL.md must introduce: persona`

- [ ] **Step 3: Write minimal implementation**

In `SKILL.md`, replace the three paragraphs under `## Find and separate personal profiles` (from `Use the user-provided profile or path first.` through `Saving locally does not mean the AI host processes the text offline.`) with:

```markdown
A **persona** is one complete voice profile with its own core habits, context modes, and coverage record. One person may keep several: their own voice (`"type": "self"`), and voices they write on behalf of — a club, a title, an organisation (`"type": "role"`). A formal version of the person is not a persona; it is a context mode inside their `self` persona. Personas never inherit from each other.

On a local filesystem the storage root is `~/.config/match-my-voice/`. Each persona lives in `profiles/<id>/` with three files: `persona.json` (display name, type, created date), `VOICE.md` (the profile, see [profile structure](references/profile-template.md)), and `learned.md` (rules learned from the person's edits, see [learning from edits](references/feedback.md)). `config.json` at the root holds `{"active": "<id>"}`.

To decide which persona a task uses: if the request names one — "use my own voice", "as the marketing lead" — that choice overrides it for this task only. Otherwise read the active persona from `config.json`. If there is no active entry and only one persona exists, use it. If several exist and none is active, ask once which to use, then continue. Do not derive file paths from unchecked names; ids are short lowercase slugs and the display name lives in `persona.json`. The existing `profiles/default/` is the person's own voice if no other `self` persona exists.

With no filesystem, provide a downloadable or copyable profile and explain that the user must supply it in future sessions. Do not promise automatic cross-session memory. Never put personas, profiles, or raw samples inside the installed skill folder or a shared repository. Saving locally does not mean the AI host processes the text offline.
```

In `references/profile-template.md`, insert after the line `Use only supported fields. This is a schema guide, not a completed person's profile.`:

```markdown

A profile belongs to one persona. The persona's `persona.json` beside it holds `"name"` (display name), `"type"` (`"self"` for the person's own voice, `"role"` for a voice they write on behalf of), and `"created"`. The profile below describes expression only.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_skill_contract.PersonaContractTests -v`
Expected: PASS. Then full suite: `python3 -m unittest discover -s tests -q` → `Ran 17 tests` … `OK`.

Note: `SKILL.md` now links `references/feedback.md`, which does not exist until Task 3. That is fine for the contract tests, but the final link check in Task 15 requires it. Do not create a stub.

- [ ] **Step 5: Commit**

```bash
git add SKILL.md references/profile-template.md tests/test_skill_contract.py
git commit -m "Introduce personas with self and role types"
```

---

### Task 2: Role personas confirm representativeness, not authorship (check 2)

**Files:**
- Modify: `references/sources.md` — `## Author confirmation`
- Test: `tests/test_skill_contract.py`

- [ ] **Step 1: Write the failing test**

Add to `PersonaContractTests`:

```python
    # Check 2: a role persona asks whether samples fit the role, not who wrote them.
    def test_role_personas_ask_about_representativeness(self):
        sources = read("references/sources.md")
        section = flat(sources[sources.index("## Author confirmation"):
                               sources.index("## Candidate review")])
        self.assertIn("for a self persona", section)
        self.assertIn("for a role persona", section)
        self.assertIn("is this what the role should sound like", section,
                      "the role question must be stated verbatim")
        self.assertIn("written by several people is expected", section,
                      "multiple authors are normal for a role")
        self.assertIn("did you write all of these yourself", section,
                      "the self question must survive")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.PersonaContractTests.test_role_personas_ask_about_representativeness -v`
Expected: FAIL with `'for a self persona' not found`

- [ ] **Step 3: Write minimal implementation**

In `references/sources.md`, replace the `## Author confirmation` section (heading through the paragraph ending `"When a source does not work" below.`) with:

```markdown
## Author confirmation

Every automatic filter above can be wrong, and only the person knows the answer.
**Ask it every time, before any analysis.** Which question depends on the
persona's type in `persona.json`.

For a self persona:

> Did you write all of these yourself?
> Was any of them heavily edited by someone else or by AI?

For a role persona, material written by several people is expected — a club
account has had several hands on it — so authorship is not the test. Ask instead:

> Is this what the role should sound like?
> Is any of it off-brand, or from a period you would rather not copy?

Their answer overrides every signal the skill inferred, and it is what fills in
the "likely author" line in the candidate review below. That review is for
correcting individual items, not for asking the question again. If the answer
is no, follow the Mixed authorship and Mostly AI-edited rules under "When a
source does not work" below; for a role persona, treat "off-brand" the way
those rules treat "not the person's own".
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 18 tests` … `OK`. (`test_author_confirmation_always_precedes_analysis` still asserts `did you write all of these yourself`, `heavily edited by someone else or by ai`, `ask it every time` — all survive.)

- [ ] **Step 5: Commit**

```bash
git add references/sources.md tests/test_skill_contract.py
git commit -m "Ask role personas about representativeness, not authorship"
```

---

### Task 3: The feedback loop reference (checks 3, 4)

**Files:**
- Create: `references/feedback.md`
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Produces: the `learned.md` line format that Task 10's server parses. The format is fixed by the Global Constraints; this document states it for the agent.

- [ ] **Step 1: Write the failing test**

Add to `PersonaContractTests`:

```python
    # Checks 3 and 4: learn only voice-class edits, and only after asking.
    def test_feedback_reference_learns_only_voice_edits_after_asking(self):
        fb = read("references/feedback.md")
        for heading in ("## Compare the two versions", "## Classify each change",
                        "## Propose, then ask", "## Record"):
            self.assertIn(heading, fb, f"feedback.md needs {heading}")
        f = flat(fb)
        self.assertIn("sentence by sentence", f, "comparison granularity must be stated")
        for cls in ("voice", "fact", "length", "structure", "other"):
            self.assertIn(cls, f, f"classification must include: {cls}")
        self.assertIn("only voice changes become candidate rules", f)
        self.assertIn("a corrected typo, number, name, or fact is never a voice rule", f)
        self.assertIn("never write a rule into learned.md without the person saying yes", f)
        self.assertIn("the sentences the person rewrote are their own original writing", f,
                      "edited sentences count as human corpus")
        self.assertIn("the sentences they left unchanged are accepted ai text", f)
        line_format = "- [active|revoked] YYYY-MM-DD | <context label> | <rule> | source: <task>, <location>"
        self.assertIn(line_format, fb, "the learned.md line format must be stated exactly")
        self.assertIn("revoking flips the status word in place", f)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.PersonaContractTests.test_feedback_reference_learns_only_voice_edits_after_asking -v`
Expected: FAIL — `FileNotFoundError` for `references/feedback.md`.

- [ ] **Step 3: Write the reference**

Create `references/feedback.md`:

```markdown
# Learning from the person's edits

Use this when the person pastes back a version of a draft they edited
themselves. The draft came from this skill; the edits came from them, made in
their own editor, without explanation. The edits are the lesson. Do not ask the
person to explain what they changed — read it.

## Compare the two versions

Align the draft you produced with the version they pasted back, sentence by
sentence. For Chinese, split on 。！？ and on paragraph breaks; do not apply
English tokenisation. When a paragraph was reordered or rewritten wholesale,
align by meaning, and say so in the summary rather than forcing a sentence map.

Produce a list of changes. Each change is: the original sentence, the replacement
(or "deleted" / "inserted"), and where it sits.

## Classify each change

Give every change exactly one class:

- **voice** — same meaning, different expression: word choice, sentence rhythm,
  stance, register, how an idea is opened or closed.
- **fact** — a number, name, date, claim, or detail was corrected or added.
- **length** — content was cut or expanded without changing how it is said.
- **structure** — order of paragraphs or points changed.
- **other** — typos, formatting, punctuation-only, or anything unclear.

Only voice changes become candidate rules. A corrected typo, number, name, or
fact is never a voice rule. A deletion is length, not voice, unless the replaced
text shows a different way of saying the same thing. When unsure between voice
and another class, choose the other class.

## Propose, then ask

For each voice change, state the rule you would record, in one line, with the
before and after as evidence. Group repeats: three edits of the same kind are one
rule with three pieces of evidence. Then ask, in the person's language:

> I noticed these changes. Should I keep any of them as rules for next time?

List the candidates with a number each. The person can accept some, reject some,
or say a change was one-off. Never write a rule into learned.md without the
person saying yes to that rule.

## Record

For each accepted rule, append one line to the active persona's `learned.md`:

```
- [active|revoked] YYYY-MM-DD | <context label> | <rule> | source: <task>, <location>
```

The context label is the one the writing task used (job application, work
email, social post, report or reflection, or the label the person gave). The
source names the task and where the evidence sat, not the full sentence. The
rule is written so it can be applied without the evidence.

Revoking flips the status word in place; nothing is deleted. The management page
does this; so can the person by editing the file. When writing, read `VOICE.md`
and then every `[active]` line of `learned.md`; skip `[revoked]` lines.

The sentences the person rewrote are their own original writing — treat them as
human corpus when updating patterns. The sentences they left unchanged are
accepted AI text — a reviewed example, not corpus, as the profile structure
already says.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 19 tests` … `OK`

- [ ] **Step 5: Commit**

```bash
git add references/feedback.md tests/test_skill_contract.py
git commit -m "Add the edit-based feedback reference"
```

---

### Task 4: Route Refine and Write through the feedback loop (checks 4, 5)

**Files:**
- Modify: `SKILL.md` — the `- **Refine:**` bullet, `## Write using the profile`, `## Learn from feedback`
- Test: `tests/test_skill_contract.py`

- [ ] **Step 1: Write the failing test**

Add to `PersonaContractTests`:

```python
    # Checks 4 and 5: writing applies active learned rules; refining follows feedback.md.
    def test_write_reads_learned_rules_and_refine_routes_to_feedback(self):
        skill = read("SKILL.md")
        self.assertIn("references/feedback.md", skill)
        f = flat(skill)
        self.assertIn("then every [active] line of learned.md", f,
                      "Write must apply active learned rules")
        self.assertIn("skip [revoked] lines", f)
        self.assertIn("pastes back an edited version", f,
                      "Refine must recognise the paste-back case")
        self.assertIn("follow [learning from edits](references/feedback.md)", f)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.PersonaContractTests.test_write_reads_learned_rules_and_refine_routes_to_feedback -v`
Expected: FAIL with `'then every [active] line of learned.md' not found`

- [ ] **Step 3: Write minimal implementation**

In `SKILL.md`:

Replace the `- **Refine:**` bullet with:

```markdown
- **Refine:** the user corrects a draft in the conversation, supplies new samples, or pastes back an edited version of a draft this skill produced. For the paste-back case follow [learning from edits](references/feedback.md). Otherwise apply the correction now and update only supported profile rules.
```

In `## Write using the profile`, replace the first paragraph (`Read the appropriate person's profile, language, context mode, and current instructions. Current explicit instructions override historical preferences.`) with:

```markdown
Read the active persona's `VOICE.md`, then every `[active]` line of `learned.md`; skip `[revoked]` lines. Learned rules are applied on top of the profile. Read the language, context mode, and current instructions. Current explicit instructions override historical preferences.
```

In `## Learn from feedback`, replace the first sentence `Apply edits immediately.` with:

```markdown
For edits made in the conversation, apply them immediately. For a pasted-back edited draft, the comparison, classification, and asking step live in [learning from edits](references/feedback.md); this section covers what to persist once the person has answered.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 20 tests` … `OK`

- [ ] **Step 5: Commit**

```bash
git add SKILL.md tests/test_skill_contract.py
git commit -m "Apply learned rules when writing; route paste-back edits to feedback.md"
```

---

### Task 5: Visual direction gate (controller only — no subagent)

**Files:** none. This task produces a decision, recorded in the progress ledger.

- [ ] **Step 1: Look up candidate directions**

Use the `ui-ux-pro-max` skill to pull 2–3 concrete style directions suited to a small local management page in Traditional Chinese: palette, typography pairing, layout skeleton, one reference product each.

- [ ] **Step 2: Present them to the user and wait**

Show the 2–3 directions with their concrete values. Do not start Task 11 until the user has picked one. Record the pick — palette tokens, font pairing, layout — in the ledger so Task 11's implementer receives exact values.

---

### Task 6: Server skeleton and persona listing (check 7, part 8)

**Files:**
- Create: `ui/serve.js`
- Create: `tests/ui/helpers.js`
- Create: `tests/ui/personas.test.js`

**Interfaces:**
- Produces: `createApp(homeDir)` returning `{ server }` where `server` is an unstarted `node:http` server (the caller listens and closes); `ensureHome(homeDir)` which creates the layout and migrates a bare `profiles/default/VOICE.md`. Later tasks add routes inside `createApp`.
- API: `GET /api/personas` → `{ "active": "<id>|null", "personas": [{ "id", "name", "type", "created" }] }`.

- [ ] **Step 1: Write the test helper**

Create `tests/ui/helpers.js`:

```js
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
```

- [ ] **Step 2: Write the failing test**

Create `tests/ui/personas.test.js`:

```js
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `node --test tests/ui/`
Expected: fails — `Cannot find module '../../ui/serve.js'`.

- [ ] **Step 4: Write the server**

Create `ui/serve.js`:

```js
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
```

Create a placeholder `ui/index.html` so `GET /` works (Task 11 replaces it):

```html
<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>match-my-voice</title></head>
<body><p>介面尚未建立。</p></body></html>
```

- [ ] **Step 5: Run test to verify it passes**

Run: `node --test tests/ui/`
Expected: `# pass 3`. Then `python3 -m unittest discover -s tests -q` → still `Ran 20 tests` … `OK`. If `test_python_build_artifacts_are_not_tracked` or the privacy scan complains, read the failure — `ui/` files are tracked on purpose.

- [ ] **Step 6: Commit**

```bash
git add ui/serve.js ui/index.html ui/package.json tests/ui/package.json tests/ui/helpers.js tests/ui/personas.test.js
git commit -m "Serve the management page and list personas from local storage"
```

`ui/serve.js` uses ES module syntax (`import`), and Node treats `.js` as CommonJS unless told otherwise. So before running the tests, create `ui/package.json` and `tests/ui/package.json`, each containing exactly `{"type": "module"}` and nothing else — no dependencies. They are module-type markers, not dependency manifests.

---

### Task 7: Create and delete personas

**Files:**
- Modify: `ui/serve.js` — add routes and `slugify`
- Test: `tests/ui/personas.test.js`

**Interfaces:**
- `POST /api/personas` body `{ "name": "...", "type": "self"|"role" }` → `201 { "id", "name", "type", "created" }`; `400` on empty name, bad type, or id collision; `slugify(name)` exported.
- `DELETE /api/personas/:id` → `204`; `404` if absent; if it was active, `config.json` active becomes `null`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/ui/personas.test.js`:

```js
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/ui/`
Expected: fails — `slugify` is not exported / `POST` returns 404.

- [ ] **Step 3: Implement**

In `ui/serve.js`, add after `ID_RE`:

```js
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
```

Add `rmSync` to the `node:fs` import. In the request handler, before the 404 line, add:

```js
      if (req.method === "POST" && url.pathname === "/api/personas") {
        const body = await readBody(req);
        return send(res, 201, createPersona(home, body));
      }
      const del = url.pathname.match(/^\/api\/personas\/([^/]+)$/);
      if (req.method === "DELETE" && del) {
        return deletePersona(home, decodeURIComponent(del[1])) ? send(res, 204, "") : send(res, 404, { error: "not found" });
      }
```

And change the `catch` to honour `err.status`:

```js
    } catch (err) {
      return send(res, err.status || 500, { error: String(err.message || err) });
    }
```

- [ ] **Step 4: Run tests**

Run: `node --test tests/ui/`
Expected: `# pass 6`.

- [ ] **Step 5: Commit**

```bash
git add ui/serve.js tests/ui/personas.test.js
git commit -m "Create and delete personas through the API"
```

---

### Task 8: Active persona (check 1)

**Files:**
- Modify: `ui/serve.js`
- Create: `tests/ui/config.test.js`

**Interfaces:** `GET /api/config` → `{ "active": "<id>|null" }`; `PUT /api/config` body `{ "active": "<id>" }` → `200` same shape; `404` if the id does not exist; `{ "active": null }` is allowed.

- [ ] **Step 1: Write the failing test**

Create `tests/ui/config.test.js`:

```js
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
```

- [ ] **Step 2: Run test to verify it fails** — `node --test tests/ui/` → `/api/config` returns 404.

- [ ] **Step 3: Implement**

In `ui/serve.js` add:

```js
export function getConfig(home) { ensureHome(home); return readJson(join(home, "config.json"), { active: null }); }

export function setActive(home, id) {
  ensureHome(home);
  if (id !== null && (!ID_RE.test(String(id)) || !existsSync(join(home, "profiles", id, "persona.json")))) {
    throw Object.assign(new Error("no such persona"), { status: 404 });
  }
  writeFileSync(join(home, "config.json"), JSON.stringify({ active: id }, null, 2));
  return { active: id };
}
```

Routes, before the 404:

```js
      if (url.pathname === "/api/config" && req.method === "GET") return send(res, 200, getConfig(home));
      if (url.pathname === "/api/config" && req.method === "PUT") return send(res, 200, setActive(home, (await readBody(req)).active ?? null));
```

- [ ] **Step 4: Run tests** — `node --test tests/ui/` → `# pass 7`.

- [ ] **Step 5: Commit**

```bash
git add ui/serve.js tests/ui/config.test.js
git commit -m "Get and set the active persona"
```

---

### Task 9: Read and write a persona's profile (check 6)

**Files:**
- Modify: `ui/serve.js`
- Create: `tests/ui/profile.test.js`

**Interfaces:** `GET /api/personas/:id/profile` → `200 text/markdown` body is `VOICE.md`; `PUT` with `text/plain` body replaces it; `404` unknown id.

- [ ] **Step 1: Write the failing test**

Create `tests/ui/profile.test.js`:

```js
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
```

- [ ] **Step 2: Run test to verify it fails** — 404 on `/profile`.

- [ ] **Step 3: Implement**

In `ui/serve.js`:

```js
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
```

Routes, before the 404 (and before the DELETE match, since this regex is more specific):

```js
      const prof = url.pathname.match(/^\/api\/personas\/([^/]+)\/profile$/);
      if (prof) {
        const dir = personaDir(home, decodeURIComponent(prof[1]));
        if (!dir) return send(res, 404, { error: "not found" });
        if (req.method === "GET") return send(res, 200, readFileSync(join(dir, "VOICE.md"), "utf8"), "text/markdown; charset=utf-8");
        if (req.method === "PUT") { writeFileSync(join(dir, "VOICE.md"), await readText(req)); return send(res, 200, { ok: true }); }
      }
```

- [ ] **Step 4: Run tests** — `node --test tests/ui/` → `# pass 8`.

- [ ] **Step 5: Commit**

```bash
git add ui/serve.js tests/ui/profile.test.js
git commit -m "Read and write a persona's profile as raw markdown"
```

---

### Task 10: Learned rules — parse, list, revoke, edit (check 5)

**Files:**
- Modify: `ui/serve.js`
- Create: `tests/ui/learned.test.js`

**Interfaces:** `parseLearned(text)` → `[{ index, status, date, context, rule, source }]`; `serializeLearned(entries)` → text in the exact line format. `GET /api/personas/:id/learned` → `{ "entries": [...] }`. `PATCH /api/personas/:id/learned/:index` body `{ "status": "active"|"revoked" }` or `{ "rule": "..." }` → `200 { "entries": [...] }`. Lines that do not match the format are preserved verbatim with `status: "unparsed"` and cannot be edited.

- [ ] **Step 1: Write the failing test**

Create `tests/ui/learned.test.js`:

```js
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
```

- [ ] **Step 2: Run test to verify it fails** — `parseLearned` not exported.

- [ ] **Step 3: Implement**

In `ui/serve.js`:

```js
const LINE_RE = /^- \[(active|revoked)\] (\d{4}-\d{2}-\d{2}) \| ([^|]*?) \| ([^|]*?) \| source: (.*)$/;

export function parseLearned(text) {
  const lines = text.split("\n");
  if (lines.length && lines[lines.length - 1] === "") lines.pop();
  return lines.map((line, index) => {
    const m = line.match(LINE_RE);
    if (!m) return { index, status: "unparsed", raw: line };
    return { index, status: m[1], date: m[2], context: m[3].trim(), rule: m[4].trim(), source: m[5].trim() };
  });
}

export function serializeLearned(entries) {
  const out = entries.map((e) => e.status === "unparsed" ? e.raw : `- [${e.status}] ${e.date} | ${e.context} | ${e.rule} | source: ${e.source}`);
  return out.join("\n") + "\n";
}

export function patchLearned(home, id, index, change) {
  const dir = personaDir(home, id);
  if (!dir) throw Object.assign(new Error("not found"), { status: 404 });
  const entries = parseLearned(readFileSync(join(dir, "learned.md"), "utf8"));
  const e = entries[index];
  if (!e) throw Object.assign(new Error("no such entry"), { status: 404 });
  if (e.status === "unparsed") throw Object.assign(new Error("line is not in the rule format"), { status: 400 });
  if ("status" in change) {
    if (change.status !== "active" && change.status !== "revoked") throw Object.assign(new Error("status must be active or revoked"), { status: 400 });
    e.status = change.status;
  }
  if ("rule" in change) {
    const r = String(change.rule).trim();
    if (!r || r.includes("|") || r.includes("\n")) throw Object.assign(new Error("rule must be one line without |"), { status: 400 });
    e.rule = r;
  }
  writeFileSync(join(dir, "learned.md"), serializeLearned(entries));
  return { entries };
}
```

Routes:

```js
      const learned = url.pathname.match(/^\/api\/personas\/([^/]+)\/learned(?:\/(\d+))?$/);
      if (learned) {
        const dir = personaDir(home, decodeURIComponent(learned[1]));
        if (!dir) return send(res, 404, { error: "not found" });
        if (req.method === "GET" && learned[2] === undefined) return send(res, 200, { entries: parseLearned(readFileSync(join(dir, "learned.md"), "utf8")) });
        if (req.method === "PATCH" && learned[2] !== undefined) return send(res, 200, patchLearned(home, decodeURIComponent(learned[1]), Number(learned[2]), await readBody(req)));
      }
```

Note the serializer's trailing-newline rule: `SAMPLE` ends with `"\n"` after an empty stray line; the parser pops one trailing empty string and the serializer adds one `"\n"`, so the round-trip is exact. Keep both behaviours.

- [ ] **Step 4: Run tests** — `node --test tests/ui/` → `# pass 10`. Contract suite still `Ran 20 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add ui/serve.js tests/ui/learned.test.js
git commit -m "List, revoke, and edit learned rules in place"
```

---

### Task 11: Page — persona list, switch, create, delete

**Files:**
- Replace: `ui/index.html`

**Interfaces:**
- Consumes: every API from Tasks 6–10, and the visual direction recorded in the ledger by Task 5 (palette tokens, font pairing, layout).
- Produces: a page with three panes — persona list (left), profile editor (centre, Task 12), learned rules (right, Task 13). Task 11 builds the shell and the left pane; the other two panes render placeholders.

- [ ] **Step 1: Write the page shell**

Replace `ui/index.html`. The exact colours and fonts come from the ledger — substitute them where marked `/* from ledger */`:

```html
<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>match-my-voice 口吻管理</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {
    /* from ledger — replace with the chosen direction's tokens */
    --bg: #faf9f6; --panel: #ffffff; --ink: #1c1b19; --muted: #6b6860;
    --accent: #2f5d50; --accent-ink: #ffffff; --line: #e6e3dc; --danger: #a33d2f;
    --radius: 10px; --gap: 16px;
    --font: "Noto Sans TC", system-ui, -apple-system, "PingFang TC", sans-serif;
    --mono: ui-monospace, SFMono-Regular, Menlo, monospace;
  }
  html { background: var(--bg); color: var(--ink); font-family: var(--font); }
  .panel { background: var(--panel); border: 1px solid var(--line); border-radius: var(--radius); }
  .btn { border-radius: 8px; padding: 6px 12px; font-weight: 500; transition: background .15s, transform .05s; }
  .btn:active { transform: translateY(1px); }
  .btn-primary { background: var(--accent); color: var(--accent-ink); }
  .btn-primary:hover { filter: brightness(1.08); }
  .btn-ghost { border: 1px solid var(--line); background: var(--panel); }
  .btn-ghost:hover { background: var(--bg); }
  .btn-danger { color: var(--danger); }
  .persona.active { border-color: var(--accent); box-shadow: inset 3px 0 0 var(--accent); }
  textarea, input { font-family: inherit; }
  textarea.mono { font-family: var(--mono); }
  :focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
</style>
</head>
<body class="min-h-screen">
<header class="px-6 py-4 border-b" style="border-color: var(--line)">
  <h1 class="text-xl font-bold tracking-tight">口吻管理</h1>
  <p class="text-sm" style="color: var(--muted)">Agent 寫東西時讀這裡。改了就生效。</p>
</header>

<main class="p-6 grid gap-4 lg:grid-cols-[280px_1fr_360px]">
  <!-- 角色 -->
  <section class="panel p-4" aria-labelledby="h-personas">
    <div class="flex items-center justify-between mb-3">
      <h2 id="h-personas" class="font-bold">角色</h2>
      <button id="new-persona" class="btn btn-primary text-sm">＋ 新增</button>
    </div>
    <ul id="persona-list" class="space-y-2" role="listbox" aria-label="角色清單"></ul>
    <p id="persona-empty" class="text-sm hidden" style="color: var(--muted)">還沒有角色。按「新增」建第一個。</p>
  </section>

  <!-- 口吻檔 -->
  <section class="panel p-4" aria-labelledby="h-profile">
    <h2 id="h-profile" class="font-bold mb-3">口吻檔 <span id="profile-name" class="font-normal" style="color: var(--muted)"></span></h2>
    <div id="profile-pane"><p class="text-sm" style="color: var(--muted)">選一個角色。</p></div>
  </section>

  <!-- 學到的規則 -->
  <section class="panel p-4" aria-labelledby="h-learned">
    <h2 id="h-learned" class="font-bold mb-3">學到的規則</h2>
    <div id="learned-pane"><p class="text-sm" style="color: var(--muted)">選一個角色。</p></div>
  </section>
</main>

<dialog id="new-dialog" class="panel p-5 w-[min(92vw,420px)]">
  <form method="dialog" id="new-form" class="space-y-3">
    <h3 class="font-bold">新增角色</h3>
    <label class="block text-sm">名稱<input name="name" required class="mt-1 w-full border rounded-md px-3 py-2" style="border-color: var(--line)" placeholder="例如：徵才月行銷長"></label>
    <fieldset class="text-sm">
      <legend class="mb-1">這是誰的口吻？</legend>
      <label class="block"><input type="radio" name="type" value="self" checked> 我自己（self）</label>
      <label class="block"><input type="radio" name="type" value="role"> 我代表的某個角色或組織（role）</label>
    </fieldset>
    <p id="new-error" class="text-sm hidden" style="color: var(--danger)"></p>
    <div class="flex justify-end gap-2">
      <button type="button" id="new-cancel" class="btn btn-ghost">取消</button>
      <button type="submit" class="btn btn-primary">建立</button>
    </div>
  </form>
</dialog>

<script>
const $ = (s) => document.querySelector(s);
const state = { active: null, personas: [], selected: null };

async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  const type = res.headers.get("content-type") || "";
  const body = type.includes("json") ? await res.json() : await res.text();
  if (!res.ok) throw new Error(body && body.error ? body.error : `HTTP ${res.status}`);
  return body;
}

async function loadPersonas() {
  const data = await api("/api/personas");
  state.active = data.active; state.personas = data.personas;
  if (!state.selected || !state.personas.some(p => p.id === state.selected)) state.selected = state.active || (state.personas[0] && state.personas[0].id) || null;
  renderPersonas();
  window.dispatchEvent(new CustomEvent("persona-selected", { detail: state.selected }));
}

function renderPersonas() {
  const ul = $("#persona-list"); ul.innerHTML = "";
  $("#persona-empty").classList.toggle("hidden", state.personas.length > 0);
  for (const p of state.personas) {
    const li = document.createElement("li");
    li.className = "persona panel p-3 flex items-center justify-between gap-2 cursor-pointer" + (p.id === state.selected ? " active" : "");
    li.setAttribute("role", "option"); li.setAttribute("aria-selected", p.id === state.selected);
    li.innerHTML = `
      <div class="min-w-0">
        <div class="font-medium truncate">${escapeHtml(p.name)}</div>
        <div class="text-xs" style="color: var(--muted)">${p.type === "role" ? "角色" : "本人"}${p.id === state.active ? " · 目前使用" : ""}</div>
      </div>
      <div class="flex gap-1 shrink-0">
        ${p.id === state.active ? "" : `<button class="btn btn-ghost text-xs" data-act="activate" data-id="${p.id}">設為目前</button>`}
        <button class="btn btn-ghost btn-danger text-xs" data-act="delete" data-id="${p.id}" aria-label="刪除 ${escapeHtml(p.name)}">刪除</button>
      </div>`;
    li.addEventListener("click", (e) => { if (!e.target.closest("button")) { state.selected = p.id; renderPersonas(); window.dispatchEvent(new CustomEvent("persona-selected", { detail: p.id })); } });
    ul.appendChild(li);
  }
}

function escapeHtml(s) { return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

$("#persona-list").addEventListener("click", async (e) => {
  const b = e.target.closest("button[data-act]"); if (!b) return;
  const id = b.dataset.id;
  if (b.dataset.act === "activate") { await api("/api/config", { method: "PUT", headers: { "content-type": "application/json" }, body: JSON.stringify({ active: id }) }); await loadPersonas(); }
  if (b.dataset.act === "delete") {
    const p = state.personas.find(x => x.id === id);
    if (confirm(`刪除「${p.name}」？口吻檔和學到的規則會一起刪，不能復原。`)) { await api(`/api/personas/${encodeURIComponent(id)}`, { method: "DELETE" }); await loadPersonas(); }
  }
});

$("#new-persona").addEventListener("click", () => { $("#new-form").reset(); $("#new-error").classList.add("hidden"); $("#new-dialog").showModal(); });
$("#new-cancel").addEventListener("click", () => $("#new-dialog").close());
$("#new-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  try {
    const created = await api("/api/personas", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ name: fd.get("name"), type: fd.get("type") }) });
    $("#new-dialog").close(); state.selected = created.id; await loadPersonas();
  } catch (err) { $("#new-error").textContent = err.message; $("#new-error").classList.remove("hidden"); }
});

loadPersonas().catch((err) => { $("#persona-empty").textContent = "讀取失敗：" + err.message; $("#persona-empty").classList.remove("hidden"); });
</script>
</body>
</html>
```

- [ ] **Step 2: Start the server and verify in the Browser pane**

Add a `.claude/launch.json` entry in the skill folder if none exists:

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "mmv-ui",
      "runtimeExecutable": "node",
      "runtimeArgs": ["ui/serve.js"],
      "port": 4747,
      "env": { "MATCH_MY_VOICE_PORT": "4747", "MATCH_MY_VOICE_HOME": "/tmp/mmv-scratch-home" }
    }
  ]
}
```

`MATCH_MY_VOICE_PORT` pins the port so the preview can open it; `MATCH_MY_VOICE_HOME` points at a scratch directory so real profiles are untouched during verification. Seed that scratch home with two personas (one `self`, one `role`) using the same three-file layout before opening the page.

In the Browser pane: `preview_start` → `read_page` to confirm the three panes; create a persona through the dialog; set it active; delete it; `read_console_messages` must show no errors.

- [ ] **Step 3: Run both suites** — `node --test tests/ui/` → `# pass 10`; contract suite `OK`.

- [ ] **Step 4: Commit**

```bash
git add ui/index.html .claude/launch.json
git commit -m "Management page: list, switch, create, and delete personas"
```

---

### Task 12: Page — profile editor (check 6)

**Files:**
- Modify: `ui/index.html` — fill `#profile-pane`

- [ ] **Step 1: Add the editor**

Inside the `<script>`, immediately **before** the final `loadPersonas().catch(...)` line, add:

```js
let profileDirty = false;
window.addEventListener("persona-selected", async (e) => {
  const id = e.detail; const pane = $("#profile-pane");
  if (!id) { pane.innerHTML = `<p class="text-sm" style="color: var(--muted)">選一個角色。</p>`; $("#profile-name").textContent = ""; return; }
  const p = state.personas.find(x => x.id === id); $("#profile-name").textContent = `— ${p.name}`;
  const text = await api(`/api/personas/${encodeURIComponent(id)}/profile`);
  pane.innerHTML = `
    <p class="text-xs mb-2" style="color: var(--muted)">你看到的就是 Agent 讀到的。直接改字，按儲存。</p>
    <textarea id="profile-text" class="mono w-full h-[60vh] border rounded-md p-3 text-sm leading-relaxed" style="border-color: var(--line)" spellcheck="false"></textarea>
    <div class="flex items-center justify-between mt-2">
      <span id="profile-status" class="text-xs" style="color: var(--muted)"></span>
      <button id="profile-save" class="btn btn-primary" disabled>儲存</button>
    </div>`;
  const ta = $("#profile-text"); ta.value = text; profileDirty = false;
  ta.addEventListener("input", () => { profileDirty = true; $("#profile-save").disabled = false; $("#profile-status").textContent = "未儲存"; });
  $("#profile-save").addEventListener("click", async () => {
    $("#profile-save").disabled = true; $("#profile-status").textContent = "儲存中…";
    try { await api(`/api/personas/${encodeURIComponent(id)}/profile`, { method: "PUT", headers: { "content-type": "text/plain; charset=utf-8" }, body: ta.value }); profileDirty = false; $("#profile-status").textContent = "已儲存 " + new Date().toLocaleTimeString("zh-TW"); }
    catch (err) { $("#profile-status").textContent = "儲存失敗：" + err.message; $("#profile-save").disabled = false; }
  });
});
window.addEventListener("beforeunload", (e) => { if (profileDirty) { e.preventDefault(); e.returnValue = ""; } });
```

- [ ] **Step 2: Verify in the Browser pane** — open a persona, edit a line, save, `read_page` shows "已儲存"; reload and the edit persists; `read_console_messages` clean.

- [ ] **Step 3: Run both suites** — unchanged counts, both green.

- [ ] **Step 4: Commit**

```bash
git add ui/index.html
git commit -m "Management page: edit a persona's profile in place"
```

---

### Task 13: Page — learned rules (check 5)

**Files:**
- Modify: `ui/index.html` — fill `#learned-pane`

- [ ] **Step 1: Add the learned list**

Inside the `<script>`, also before the final `loadPersonas().catch(...)` line, add:

```js
window.addEventListener("persona-selected", async (e) => {
  const id = e.detail; const pane = $("#learned-pane");
  if (!id) { pane.innerHTML = `<p class="text-sm" style="color: var(--muted)">選一個角色。</p>`; return; }
  await renderLearned(id);
});

async function renderLearned(id) {
  const pane = $("#learned-pane");
  const { entries } = await api(`/api/personas/${encodeURIComponent(id)}/learned`);
  const rules = entries.filter(x => x.status !== "unparsed");
  if (!rules.length) { pane.innerHTML = `<p class="text-sm" style="color: var(--muted)">還沒學到東西。把改好的草稿貼回給 Agent，它會問你要不要記下來。</p>`; return; }
  pane.innerHTML = `<ul class="space-y-2">${rules.map(x => `
    <li class="panel p-3 ${x.status === "revoked" ? "opacity-60" : ""}">
      <div class="text-xs mb-1" style="color: var(--muted)">${x.date} · ${escapeHtml(x.context)}${x.status === "revoked" ? " · 已撤銷" : ""}</div>
      <div class="text-sm" data-rule="${x.index}">${escapeHtml(x.rule)}</div>
      <div class="text-xs mt-1" style="color: var(--muted)">來源：${escapeHtml(x.source)}</div>
      <div class="flex gap-1 mt-2">
        <button class="btn btn-ghost text-xs" data-act="edit" data-i="${x.index}">改字</button>
        <button class="btn btn-ghost text-xs ${x.status === "active" ? "btn-danger" : ""}" data-act="toggle" data-i="${x.index}" data-next="${x.status === "active" ? "revoked" : "active"}">${x.status === "active" ? "撤銷" : "恢復"}</button>
      </div>
    </li>`).join("")}</ul>`;
  pane.onclick = async (ev) => {
    const b = ev.target.closest("button[data-act]"); if (!b) return;
    const i = Number(b.dataset.i);
    if (b.dataset.act === "toggle") { await api(`/api/personas/${encodeURIComponent(id)}/learned/${i}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ status: b.dataset.next }) }); await renderLearned(id); }
    if (b.dataset.act === "edit") {
      const cur = pane.querySelector(`[data-rule="${i}"]`).textContent;
      const next = prompt("改成：", cur); if (next === null || next.trim() === cur) return;
      try { await api(`/api/personas/${encodeURIComponent(id)}/learned/${i}`, { method: "PATCH", headers: { "content-type": "application/json" }, body: JSON.stringify({ rule: next }) }); await renderLearned(id); }
      catch (err) { alert("沒存成：" + err.message); }
    }
  };
}
```

- [ ] **Step 2: Verify in the Browser pane** — seed a `learned.md` in the scratch home with two lines in the format; open the persona; revoke one, restore it, edit one; `read_page` after each; `read_console_messages` clean.

- [ ] **Step 3: Run both suites** — both green.

- [ ] **Step 4: Commit**

```bash
git add ui/index.html
git commit -m "Management page: review, revoke, and edit learned rules"
```

---

### Task 14: Screenshot self-check (controller — global frontend rule 硬規則一, check 10)

**Files:** none modified unless the check fails.

- [ ] **Step 1: Round one**

With the server running on a scratch home seeded with two personas and three learned rules: take exactly two screenshots — desktop 1280×800 and mobile 375×812 (`resize_window` then `computer` screenshot; scale ≤ 1280 wide). Score all eight items: hierarchy, spacing rhythm, typography, palette (one accent, ≤ 3 colours, grey scale), alignment, responsive (no horizontal scroll at 375), states (hover/focus/empty/loading/error), motion (at least one micro-transition). Write down which items fail.

- [ ] **Step 2: Fix and round two**

Fix the failures in `ui/index.html`, re-screenshot both sizes, re-score. Repeat until all eight pass. Do not re-read old screenshots.

- [ ] **Step 3: Deliver evidence**

Send the final two screenshots to the user with `SendUserFile`. Commit any fixes:

```bash
git add ui/index.html
git commit -m "Management page: visual pass"
```

---

### Task 15: README, docs, finish, publish

**Files:**
- Modify: `README.md` — new `## 管理介面` section and a line in `## 之後使用`
- Modify: `tests/test_skill_contract.py` — docstring; README test
- Modify: `.gitignore` — nothing to add; verify
- Test: contract suite

- [ ] **Step 1: Write the failing README test**

Add to `PersonaContractTests`:

```python
    # README explains personas, the feedback loop, and how to open the page.
    def test_readme_documents_personas_feedback_and_ui(self):
        readme = read("README.md")
        self.assertIn("## 管理介面", readme)
        ui = readme[readme.index("## 管理介面"):]
        self.assertIn("node ui/serve.js", ui)
        self.assertIn("不會呼叫任何 AI", ui)
        for phrase in ("角色", "貼回", "要不要記下來", "撤銷"):
            self.assertIn(phrase, readme, f"README must mention: {phrase}")
```

- [ ] **Step 2: Run test to verify it fails** — `## 管理介面` absent.

- [ ] **Step 3: Update the README**

In `README.md`, after the `## 之後使用` section's last paragraph and before `## 幫忙測試`, insert:

```markdown
## 反哺：它從你的修改裡學

Agent 寫了第一版，你在自己的編輯器裡改到滿意，把改好的整份**貼回**給它。它會逐句比對你改了哪裡，只挑出跟口吻有關的改動（修錯字、改數字不算），列出來問你「這幾條**要不要記下來**」。你說好的才會寫進那個角色的 `learned.md`；下次寫東西就會套用。學錯了可以在管理介面**撤銷**。

## 角色

一個人可以有好幾種口吻：你自己（`self`），還有你代表的角色或組織，例如社團的行銷長（`role`）。每個**角色**一份口吻檔，互不影響。在管理介面設「目前角色」，Agent 預設用它；對話裡說「用我自己的口吻」可以臨時換一次。

## 管理介面

技能資料夾裡附一個本機網頁，看角色、切換、直接改口吻檔、看它學到什麼：

```bash
cd ~/.claude/skills/match-my-voice
node ui/serve.js
```

它會印出一個 `http://127.0.0.1:…` 的網址，用瀏覽器開。這個頁面**不會呼叫任何 AI**、不需要金鑰、沒有伺服器在我們這邊——它只是讀寫你電腦上 `~/.config/match-my-voice/` 裡的檔案。需要 Node 18 以上；Claude Code 和 Codex 本身就靠 Node，所以你已經有了。
```

- [ ] **Step 4: Update the test docstring**

Replace the first paragraph of the module docstring in `tests/test_skill_contract.py` with:

```python
Each test traces to a numbered acceptance check in one of:
docs/superpowers/specs/2026-09-08-sample-sourcing-design.md ("驗收檢查") for
SourcePickerContractTests, and
docs/superpowers/specs/2026-09-20-personas-and-feedback-design.md for
PersonaContractTests — except the package-hygiene tests, which guard the privacy
boundary described in docs/superpowers/specs/2026-09-05-source-picker-design.md.
The UI server has its own tests under tests/ui/ (node --test).
```

- [ ] **Step 5: Verify links, hygiene, both suites**

```bash
grep -o '](references/[^)]*)' SKILL.md | tr -d '](' | sed 's|)||' | while read f; do [ -f "$f" ] && echo "OK $f" || echo "BROKEN $f"; done
grep -rn -i "api key\|pip install\|npm install\|requirements.txt\|oauth\|client_secret" SKILL.md references/ README.md ui/ || echo clean
grep -rn '"dependencies"' ui/package.json tests/ui/package.json || echo "no deps"
python3 -m unittest discover -s tests -q
node --test tests/ui/
git status --porcelain   # nothing untracked that should be ignored; no scratch home committed
```

Expected: four `OK` links (sources, analysis, profile-template, feedback); `clean`; `no deps`; `Ran 21 tests` … `OK`; `# pass 10`.

- [ ] **Step 6: Product-understanding checkpoint (controller)**

Before merging, walk the user through: what a persona is, where the files live, how the feedback loop asks before writing, what the page does and does not do. Wait for their go.

- [ ] **Step 7: Merge, re-run on main, push, verify from outside**

```bash
git add README.md tests/test_skill_contract.py
git commit -m "Document personas, the feedback loop, and the management page"
git checkout main
git merge --no-ff feat/personas-feedback-ui -m "Merge feat/personas-feedback-ui"
python3 -m unittest discover -s tests -q
node --test tests/ui/
rm -rf tests/__pycache__
git branch -d feat/personas-feedback-ui
git push origin main
gh api "repos/{owner}/{repo}/contents/ui" --jq '.[].name'
gh api "repos/{owner}/{repo}/contents/references" --jq '.[] | "\(.name)  \(.size) bytes"'
```

Expected: both suites green on `main`; the remote lists `ui/serve.js`, `ui/index.html`, `ui/package.json`; `references/` lists four files including `feedback.md`.
