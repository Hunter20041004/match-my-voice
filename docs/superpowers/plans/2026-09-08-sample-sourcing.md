# Sample Sourcing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the "where do you want samples from?" menu with sourcing driven by what the person is about to write, and split the voice profile into a core layer plus per-context modes.

**Architecture:** This package is a set of markdown instruction documents read by an AI agent, not executable code. `SKILL.md` is the entry point; `references/*.md` are loaded on demand. Behaviour is verified by contract tests that assert the documents state the required rules — `tests/test_skill_contract.py`, Python `unittest`, no third-party dependencies.

**Tech Stack:** Markdown, Python 3 standard library (`unittest`, `subprocess`, `re`, `pathlib`), git.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-09-08-sample-sourcing-design.md`. Every acceptance check number below refers to its "驗收檢查" list.
- Skill body documents (`SKILL.md`, `references/*.md`) are written in English. `README.md` is written in Traditional Chinese. Do not switch either.
- No service-specific API instructions, no new dependencies, no third-party Python packages.
- Never add a real person's name, sample text, or voice profile to a tracked file. `test_no_personal_sample_or_profile_is_tracked` enforces this.
- Candidate list cap: **15** items per batch.
- Run tests with `cd ~/.claude/skills/match-my-voice && python3 -m unittest discover -s tests -q`.
- Work on branch `feat/task-driven-sourcing`, created in Task 0.
- The phrase-matching helper `flat()` collapses whitespace, so assertions survive markdown line wrapping. Use `flat()` for any multi-word phrase assertion; use raw text only for headings and exact single tokens.

---

### Task 0: Branch and baseline

**Files:**
- None modified.

**Interfaces:**
- Consumes: nothing.
- Produces: branch `feat/task-driven-sourcing` with a known-green baseline.

- [ ] **Step 1: Create the branch**

```bash
cd ~/.claude/skills/match-my-voice
git checkout -b feat/task-driven-sourcing
```

- [ ] **Step 2: Confirm the baseline is green**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 9 tests` … `OK`

If it is not green, stop and report. Do not start on a red baseline.

---

### Task 1: The writing task drives sourcing (checks 2 and 3)

Replaces the old opening question. When the person says what they are writing, that is the filter. When they do not, ask one context question first.

**Files:**
- Modify: `references/sources.md:1-18` (replace the intro and "## The one question" section)
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: nothing.
- Produces: heading `## Start from the writing task` and heading `## When there is no task yet` in `references/sources.md`. Tasks 2 and 3 insert their sections after these.

- [ ] **Step 1: Update the existing skip test**

This task deletes the phrase "skip the menu", which `test_an_explicitly_named_source_skips_the_menu` asserts. There is no menu any more, so the test moves with the wording. In that method, replace:

```python
        self.assertIn("skip the menu", flat(sources),
                      "sources.md must say an explicitly named source skips the menu")
```

with:

```python
        self.assertIn("skip the questions below", flat(sources),
                      "an explicitly named source must skip the remaining questions")
```

- [ ] **Step 2: Write the failing test**

Add this method to `SourcePickerContractTests` in `tests/test_skill_contract.py`, immediately after `test_learn_mode_routes_to_a_source_picker_split_into_core_and_conditional`:

```python
    # Spec checks 2 and 3: the writing task is the filter; no task means ask context first.
    def test_sourcing_starts_from_the_writing_task(self):
        sources = read("references/sources.md")
        self.assertIn("## Start from the writing task", sources,
                      "sources.md must lead with the writing task")
        self.assertIn("## When there is no task yet", sources,
                      "sources.md must handle a request with no stated task")

        flat_sources = flat(sources)
        self.assertNotIn(
            "where would you like to get examples of how you naturally communicate?",
            flat_sources,
            "the old open-ended source question must be gone",
        )
        self.assertIn("use what they are about to write as the filter", flat_sources,
                      "the task must be stated as the filter")
        self.assertIn("ask one context question", flat_sources,
                      "a missing task must trigger exactly one context question")
        for offered in ("job application", "work email", "social post", "report"):
            self.assertIn(offered, flat_sources, f"context options must include: {offered}")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.SourcePickerContractTests.test_sourcing_starts_from_the_writing_task -v`
Expected: FAIL with `sources.md must lead with the writing task`

- [ ] **Step 4: Write minimal implementation**

In `references/sources.md`, replace lines 1–18 (everything from `# Choosing sample sources` down to and including the `one step at a time: ask about a source, then about the items, never both at once.` paragraph) with:

```markdown
# Choosing sample sources

Use this when a voice profile is needed and the person has not already supplied
usable samples. Do not open with a menu of places to look.

## Start from the writing task

Someone reaches this skill because they have something to write. Use what they
are about to write as the filter for which samples to gather. This keeps the
search small, and it guarantees the samples come from the same context as the
piece being written — a profile built from application forms will not match a
work email.

When the request already names a source — pasted passages, an attached file, a
named folder or service — use that source and skip the questions below. Work one
step at a time: settle the source, then the items, never both at once.

## When there is no task yet

If the person asks to learn their voice with nothing to write, ask one context
question before looking for anything:

> Which kind of writing do you want this for?

Offer: job application, work email, social post, report or reflection. Accept
anything else they name. One question only — do not run a setup questionnaire.
```

- [ ] **Step 5: Run both tests to verify they pass**

Run: `python3 -m unittest tests.test_skill_contract.SourcePickerContractTests.test_sourcing_starts_from_the_writing_task tests.test_skill_contract.SourcePickerContractTests.test_an_explicitly_named_source_skips_the_menu -v`
Expected: `Ran 2 tests` … `OK`

- [ ] **Step 6: Commit**

```bash
git add references/sources.md tests/test_skill_contract.py
git commit -m "Drive sample sourcing from the writing task"
```

Note: the suite as a whole is red after this task — `test_learn_mode_routes_to_a_source_picker_split_into_core_and_conditional` still asserts the deleted question. Task 2 replaces that test. Do not run the full suite as a gate until Task 2 is done.

---

### Task 2: Two paths, and silence when there is no connector (check 1)

**Files:**
- Modify: `references/sources.md` (replace `## Core sources` and `## Conditional sources`)
- Modify: `tests/test_skill_contract.py:31-56` (rewrite the existing test)

**Interfaces:**
- Consumes: `## When there is no task yet` from Task 1.
- Produces: headings `## Capability detection`, `## Two paths`, `### Path A — from a connected service`, `### Path B — supplied by the person`.

- [ ] **Step 1: Rewrite the failing test**

Replace the whole of `test_learn_mode_routes_to_a_source_picker_split_into_core_and_conditional` (lines 30–56, including its `# Spec check 1` comment) with:

```python
    # Spec check 1: with no connector, no service is offered or mentioned.
    def test_two_paths_and_no_service_talk_without_a_connector(self):
        skill = read("SKILL.md")
        self.assertIn("references/sources.md", skill)

        sources = read("references/sources.md")
        for heading in ("## Capability detection", "## Two paths",
                        "### Path A — from a connected service",
                        "### Path B — supplied by the person"):
            self.assertIn(heading, sources, f"sources.md needs {heading}")

        flat_sources = flat(sources)
        self.assertIn("do not mention path a, and do not ask about it", flat_sources,
                      "with no connector the service path must not be raised at all")
        self.assertIn("ask which of the two paths", flat_sources,
                      "with a connector, offer the two paths once")
        for supplied in ("paste text", "upload", "this conversation",
                         "answer a few simple questions"):
            self.assertIn(supplied, flat_sources, f"path B must offer: {supplied}")

        # The spec asks for one worked example, generic rules everywhere else.
        self.assertIn("### Worked example — Google Drive", sources,
                      "Path A needs one concrete worked example")
        example = flat(sources[sources.index("### Worked example — Google Drive"):])
        self.assertIn("google docs", example, "the example must name the document type")
        self.assertIn("this is an example, not a requirement", example,
                      "the example must not read as a hard dependency")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.SourcePickerContractTests.test_two_paths_and_no_service_talk_without_a_connector -v`
Expected: FAIL with `sources.md needs ## Two paths`

- [ ] **Step 3: Write minimal implementation**

In `references/sources.md`, replace the `## Core sources` section and the `## Conditional sources` section (both headings and all their list items, up to but not including `## Per-source rules`) with:

```markdown
## Capability detection

Check which tools, attachments, and connectors exist in this environment before
offering anything. Capability detection is like a power strip that exposes only
the sockets actually wired up: it stops the skill promising access it does not
have.

If detection is uncertain, treat the capability as absent.

## Two paths

**With no connected service available: do not mention Path A, and do not ask
about it.** Go straight to Path B. Naming a service the host cannot reach only
teaches the person to expect something that will not work.

**With a connected service available:** ask which of the two paths they want.
Ask once.

### Path A — from a connected service

Search the connected service using the writing task as the query, then build the
candidate list described below. Name the specific service, never "your cloud".

### Worked example — Google Drive

This is an example, not a requirement: every rule here is generic, and any
connected service follows the same shape.

With a Drive connector, search Drive for the writing task, keep Google Docs and
uploaded text documents, and drop Sheets, Slides, and images. Where the
connector exposes it, restrict to files the person owns. Show each candidate as
title, modified date, and what it is about.

Two things to say out loud rather than assume. A Drive connector reads through
the Drive API, so it can reach Google Docs content that a synced desktop folder
cannot — a synced `.gdoc` file on disk is only a pointer, not the text. And a
Drive that has never been tidied will return badly named files, which is exactly
why the candidate list carries an "about" line instead of trusting names.

### Path B — supplied by the person

Four ways in, all available without any integration:

- **Paste text** — they paste passages directly.
- **Upload documents** — when the host accepts attachments and can extract text.
- **This conversation** — their own messages in this thread.
- **Answer a few simple questions** — guided questions when no writing exists.

Local files and speech transcripts also belong here when the host supports them.
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 10 tests` … `OK`

If `test_a_connected_service_is_scoped_and_read_only` fails, its assertions rely on `## Per-source rules → ### Connected service`, which this task did not touch — re-check that you deleted only the two list sections.

- [ ] **Step 5: Commit**

```bash
git add references/sources.md tests/test_skill_contract.py
git commit -m "Replace the source menu with two paths"
```

---

### Task 3: The candidate list (checks 4 and 5)

**Files:**
- Modify: `references/sources.md` (replace `## Narrowing to specific items`)
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: `### Path A — from a connected service` from Task 2.
- Produces: heading `## The candidate list`.

- [ ] **Step 1: Write the failing test**

Add after `test_two_paths_and_no_service_talk_without_a_connector`:

```python
    # Spec checks 4 and 5: every candidate says what it is about; unpicked files stay unread.
    def test_candidate_list_shows_what_each_item_is_about(self):
        sources = read("references/sources.md")
        self.assertIn("## The candidate list", sources,
                      "sources.md needs a candidate list section")
        listing = flat(sources[sources.index("## The candidate list"):])

        self.assertIn("what this one is about", listing,
                      "each candidate must say what it is about")
        self.assertIn("do not show a fixed number", listing,
                      "the list length must follow the search, not a constant")
        self.assertIn("15", listing, "a default per-batch cap of 15 must be stated")
        self.assertIn("do not silently truncate", listing,
                      "an over-long list must be disclosed, not cut quietly")
        self.assertIn("snippet the search already returned", listing,
                      "summaries must reuse search snippets first")
        self.assertIn("read only the opening of that item", listing,
                      "falling back to reading must be limited to the opening")
        self.assertIn("items the person did not pick are not read", listing,
                      "unpicked items must never be read in full")
        for dropped in ("spreadsheets", "slide decks", "images"):
            self.assertIn(dropped, listing, f"candidate list must exclude: {dropped}")
        self.assertIn("ownedbyme", listing.replace(" ", ""),
                      "owner filtering must be used when the field exists")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.SourcePickerContractTests.test_candidate_list_shows_what_each_item_is_about -v`
Expected: FAIL with `sources.md needs a candidate list section`

- [ ] **Step 3: Write minimal implementation**

Replace the whole `## Narrowing to specific items` section in `references/sources.md` with:

```markdown
## The candidate list

Choosing a path authorizes the discovery needed to show candidates. It does not
authorize analysing an entire account, drive, or folder.

**Do not show a fixed number.** The search decides how many there are. When
results run long, order by relevance and show at most 15 in one batch, then say
how many more there are and offer either the next batch or a narrower
description. Do not silently truncate.

Show three things per row: **title**, **date**, and **what this one is about**.

The "about" line comes from the cheapest source that works:

1. The snippet the search already returned — use it when present, at no extra cost.
2. Only when no snippet exists, read only the opening of that item.

This line replaces "who wrote it" as the thing the person judges by. Someone
seeing "this one is about your internship motivation" knows immediately whether
it is theirs and whether it fits.

Keep out spreadsheets, slide decks, and images. Documents only.

When the service exposes an owner field such as `ownedByMe`, list only items the
person created. When it does not, list them anyway and rely on the "about" line
plus the author confirmation below. Do not claim the filter was applied when it
was not.

The person then picks 3–5 items. **Items the person did not pick are not read.**
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 11 tests` … `OK`

- [ ] **Step 5: Commit**

```bash
git add references/sources.md tests/test_skill_contract.py
git commit -m "Describe the candidate list and its about line"
```

---

### Task 4: Author confirmation before analysis (check 6)

**Files:**
- Modify: `references/sources.md` (`## Candidate review` section)
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: `## The candidate list` from Task 3.
- Produces: heading `## Author confirmation` placed before `## Candidate review`.

- [ ] **Step 1: Write the failing test**

Add after `test_candidate_list_shows_what_each_item_is_about`:

```python
    # Spec check 6: one explicit author confirmation always precedes analysis.
    def test_author_confirmation_always_precedes_analysis(self):
        sources = read("references/sources.md")
        self.assertIn("## Author confirmation", sources,
                      "sources.md needs an author confirmation section")
        self.assertLess(
            sources.index("## Author confirmation"),
            sources.index("## Candidate review"),
            "author confirmation comes before the review summary",
        )
        confirm = flat(sources[sources.index("## Author confirmation"):
                               sources.index("## Candidate review")])
        self.assertIn("did you write all of these yourself", confirm,
                      "the confirmation question must be stated verbatim")
        self.assertIn("heavily edited by someone else or by ai", confirm,
                      "the confirmation must ask about outside editing")
        self.assertIn("ask it every time", confirm,
                      "the confirmation is not skippable")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.SourcePickerContractTests.test_author_confirmation_always_precedes_analysis -v`
Expected: FAIL with `sources.md needs an author confirmation section`

- [ ] **Step 3: Write minimal implementation**

Insert this section in `references/sources.md` immediately before `## Candidate review`:

```markdown
## Author confirmation

Every automatic filter above can be wrong. Only the person knows. So before any
analysis, ask exactly this, and ask it every time:

> Did you write all of these yourself? Was any of them heavily edited by someone
> else or by AI?

Their answer overrides every signal the skill inferred.
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 12 tests` … `OK`

- [ ] **Step 5: Commit**

```bash
git add references/sources.md tests/test_skill_contract.py
git commit -m "Require an author confirmation before analysis"
```

---

### Task 5: Thin samples still produce a profile (check 7)

**Files:**
- Modify: `references/sources.md` (add before `## When a source does not work`)
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: `## Author confirmation` from Task 4.
- Produces: heading `## When the samples are thin`.

- [ ] **Step 1: Write the failing test**

Add after `test_author_confirmation_always_precedes_analysis`:

```python
    # Spec check 7: thin samples still yield a profile, marked provisional with its gap.
    def test_thin_samples_still_produce_a_marked_provisional_profile(self):
        sources = read("references/sources.md")
        self.assertIn("## When the samples are thin", sources,
                      "sources.md needs a thin-samples section")
        thin = flat(sources[sources.index("## When the samples are thin"):])
        self.assertIn("do not block the person", thin,
                      "thin samples must not stop the person from getting a profile")
        self.assertIn("mark the profile provisional", thin,
                      "a thin profile must be marked provisional")
        self.assertIn("name the gap", thin,
                      "the specific gap must be stated, not just the label")
        self.assertIn("requiring more samples before producing anything is the barrier", thin,
                      "the rationale for not blocking must be recorded")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.SourcePickerContractTests.test_thin_samples_still_produce_a_marked_provisional_profile -v`
Expected: FAIL with `sources.md needs a thin-samples section`

- [ ] **Step 3: Write minimal implementation**

Insert immediately before `## When a source does not work` in `references/sources.md`:

```markdown
## When the samples are thin

The picked items may turn out to be short, tabular, or mostly written by someone
else. **Do not block the person.** Requiring more samples before producing
anything is the barrier that makes people abandon the setup and never return.

Instead: produce the profile, mark the profile provisional, and name the gap in
plain words.

> This one only holds up for short pieces — long writing may not match yet.

Say what is missing. Do not claim coverage the samples do not support.
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 13 tests` … `OK`

- [ ] **Step 5: Commit**

```bash
git add references/sources.md tests/test_skill_contract.py
git commit -m "Produce a marked provisional profile from thin samples"
```

---

### Task 6: Core layer, context modes, and coverage record (check 8)

**Files:**
- Modify: `references/profile-template.md`
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: the profile field names `Core`, `Context modes`, and `Context coverage`, which Task 7 relies on by name.

- [ ] **Step 1: Write the failing test**

Add after `test_thin_samples_still_produce_a_marked_provisional_profile`:

```python
    # Spec check 8: the profile has two layers and records which contexts it covers.
    def test_profile_template_has_core_modes_and_coverage(self):
        template = read("references/profile-template.md")
        for field in ("Core:", "Context modes:", "Context coverage:"):
            self.assertIn(field, template, f"profile template needs the field: {field}")
        flat_template = flat(template)
        self.assertIn("holds in every context", flat_template,
                      "the core layer must be defined as context-independent")
        self.assertIn("a formal version of the person is still that person",
                      flat_template,
                      "context modes must not be framed as conflicting with the voice")
        self.assertIn("which contexts this profile has actually been built from",
                      flat_template,
                      "coverage must record the contexts actually evidenced")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.SourcePickerContractTests.test_profile_template_has_core_modes_and_coverage -v`
Expected: FAIL with `profile template needs the field: Core:`

- [ ] **Step 3: Write minimal implementation**

In `references/profile-template.md`, replace the single bullet reading
`- Context modes: what changes for different audiences; omit if unsupported.`
with these three bullets:

```markdown
- Core: the habits that hold in every context — what to keep no matter the audience.
- Context modes: what changes per context (job application, work email, social post, report). A formal version of the person is still that person, so a mode is not a conflict with the core; it is the same person in a different room.
- Context coverage: which contexts this profile has actually been built from, and which are untested. Later sessions read this to decide whether new samples are needed.
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 14 tests` … `OK`

- [ ] **Step 5: Commit**

```bash
git add references/profile-template.md tests/test_skill_contract.py
git commit -m "Split the profile into a core layer and context modes"
```

---

### Task 7: Second use reads coverage before searching again (check 9)

**Files:**
- Modify: `SKILL.md` (the `## Gather enough evidence without a long interview` section, and the `- **Write:**` bullet under `## Choose the task`)
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: the field name `Context coverage` from Task 6.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing test**

Add after `test_profile_template_has_core_modes_and_coverage`:

```python
    # Spec check 9: a covered context skips re-sourcing; an uncovered one is narrow.
    def test_second_use_checks_coverage_before_searching_again(self):
        skill = flat(read("SKILL.md"))
        self.assertIn("read its context coverage", skill,
                      "SKILL.md must check coverage on a returning session")
        self.assertIn("do not look for new samples", skill,
                      "a covered context must not trigger a new search")
        self.assertIn("only for that context", skill,
                      "an uncovered context must trigger a narrow search, not a full redo")
        self.assertIn("no samples exist for that context", skill,
                      "the no-samples case must be handled explicitly")
        self.assertIn("say so plainly rather than guessing silently", skill,
                      "guessing at an uncovered context must be disclosed")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.SourcePickerContractTests.test_second_use_checks_coverage_before_searching_again -v`
Expected: FAIL with `SKILL.md must check coverage on a returning session`

- [ ] **Step 3: Write minimal implementation**

In `SKILL.md`, replace this paragraph:

```
When Learn mode starts and no usable samples have been supplied, follow [choosing sample sources](references/sources.md): ask once where the person wants to draw material from, list only sources this host can actually reach, and have them select the exact items before analysis.
```

with:

```
When samples are needed, follow [choosing sample sources](references/sources.md): use what the person is about to write as the filter, offer only what this host can reach, and have them select the exact items before analysis.

When a profile already exists, read its context coverage first. If it covers the context being written now, do not look for new samples — write. If it does not, search only for that context and keep the core layer as it is. If no samples exist for that context, write using the core layer plus ordinary conventions for that kind of writing, and say so plainly rather than guessing silently:

> You have no samples of this kind of writing, so I used ordinary conventions for it and kept only your core habits. Tell me what does not sound like you and I will record it.
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 15 tests` … `OK`

- [ ] **Step 5: Commit**

```bash
git add SKILL.md tests/test_skill_contract.py
git commit -m "Check context coverage before re-sourcing samples"
```

---

### Task 8: Excerpts only, never full source text (check 10)

**Files:**
- Modify: `SKILL.md` (the `## Calibrate with the person` section, the paragraph beginning `Save using [profile structure]`)
- Test: `tests/test_skill_contract.py`

**Interfaces:**
- Consumes: nothing.
- Produces: nothing.

- [ ] **Step 1: Write the failing test**

Add after `test_second_use_checks_coverage_before_searching_again`:

```python
    # Spec check 10: profiles keep short excerpts as evidence, never whole sources.
    def test_profiles_keep_excerpts_not_whole_documents(self):
        skill = flat(read("SKILL.md"))
        self.assertIn("keep short excerpts as evidence", skill,
                      "SKILL.md must require excerpts as evidence")
        self.assertIn("never store the full text of a source document", skill,
                      "SKILL.md must forbid storing whole source documents")
        self.assertIn("a profile that cannot show its evidence cannot be argued with", skill,
                      "the reason for keeping excerpts must be recorded")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.SourcePickerContractTests.test_profiles_keep_excerpts_not_whole_documents -v`
Expected: FAIL with `SKILL.md must require excerpts as evidence`

- [ ] **Step 3: Write minimal implementation**

In `SKILL.md`, replace this sentence inside the `## Calibrate with the person` section:

```
Keep only necessary style evidence; do not copy private documents, contacts, credentials, or unrelated life history into the profile.
```

with:

```
Keep short excerpts as evidence — a few representative lines per sample — because a profile that cannot show its evidence cannot be argued with or corrected. Never store the full text of a source document, and do not copy contacts, credentials, or unrelated life history into the profile.
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 16 tests` … `OK`

- [ ] **Step 5: Commit**

```bash
git add SKILL.md tests/test_skill_contract.py
git commit -m "Keep excerpts as evidence, never whole source documents"
```

---

### Task 9: README first-run section

The existing README test asserts the old question. It must be rewritten, not extended.

**Files:**
- Modify: `README.md` (the `## 第一次用` section)
- Modify: `tests/test_skill_contract.py` (rewrite `test_readme_documents_the_source_picker`)

**Interfaces:**
- Consumes: the behaviour settled in Tasks 1–8.
- Produces: nothing.

- [ ] **Step 1: Rewrite the failing test**

Replace the whole of `test_readme_documents_the_source_picker`, including its `# Spec scope` comment, with:

```python
    # Spec scope: the README describes the task-driven first run.
    def test_readme_documents_the_task_driven_first_run(self):
        readme = read("README.md")
        first_run = readme[readme.index("## 第一次用"):readme.index("## 之後使用")]
        self.assertNotIn("你想從哪裡", first_run,
                         "the old open-ended source question must be gone from the README")
        for promise in ("你要寫什麼", "在講什麼", "沒勾的不會被讀",
                        "是你自己寫的嗎", "讀得到"):
            self.assertIn(promise, first_run, f"README first-run must mention: {promise}")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_skill_contract.SourcePickerContractTests.test_readme_documents_the_task_driven_first_run -v`
Expected: FAIL with `the old open-ended source question must be gone from the README`

- [ ] **Step 3: Write minimal implementation**

In `README.md`, replace everything between the `## 第一次用` heading and the line beginning `它會整理習慣、試寫一小段供你修正` with:

```markdown
直接說你要寫什麼就好，例如「幫我寫一封實習求職信」。

**它用你要寫的東西去找素材**，不會反過來先問你「要從哪裡拿」。這樣找到的樣本跟你要寫的東西屬於同一個場合，寫出來才會準。

如果你只是想先建口吻檔、還沒有要寫的東西，它會問一句場合（求職申請／工作信件／社群貼文／報告心得），然後才開始找。

接下來分兩條路：

- **從已連接的服務找**（例如 Google 雲端硬碟）——它會列出候選文件，每一份都標示標題、日期、**在講什麼**，你勾 3～5 份。**沒勾的不會被讀。**
- **自己提供**——貼上文字、上傳檔案、用這段對話，或是「我沒有樣本，你問我」。

你的 AI 工具沒有連接任何服務時，第一條路不會出現，也不會問你要不要接。**只列讀得到的東西。**

分析之前它會問一次：「這幾份都是你自己寫的嗎？有沒有哪份是別人或 AI 幫你改很多的？」——前面所有自動判斷都可能猜錯，這句只有你答得出來。
```

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 16 tests` … `OK`

- [ ] **Step 5: Commit**

```bash
git add README.md tests/test_skill_contract.py
git commit -m "Document the task-driven first run in the README"
```

---

### Task 10: Finish and publish

**Files:**
- Modify: `tests/test_skill_contract.py` (module docstring only)

**Interfaces:**
- Consumes: everything.
- Produces: `main` updated and pushed.

- [ ] **Step 1: Point the docstring at the current spec**

In `tests/test_skill_contract.py`, replace:

```python
Each test traces to a numbered behavioural check in
docs/superpowers/specs/2026-09-05-source-picker-design.md ("Verification").
```

with:

```python
Each test traces to a numbered acceptance check in
docs/superpowers/specs/2026-09-08-sample-sourcing-design.md ("驗收檢查"),
except the package-hygiene tests, which guard the privacy boundary described
in docs/superpowers/specs/2026-09-05-source-picker-design.md.
```

- [ ] **Step 2: Verify no broken reference links**

```bash
grep -o '](references/[^)]*)' SKILL.md | tr -d '](' | sed 's|)||' | while read f; do
  [ -f "$f" ] && echo "OK   $f" || echo "BROKEN $f"
done
```

Expected: three `OK` lines, no `BROKEN`.

- [ ] **Step 3: Verify no dependencies crept in**

```bash
grep -rn -i "api key\|pip install\|npm install\|requirements.txt\|oauth\|client_secret" SKILL.md references/ README.md || echo "clean"
```

Expected: `clean`

- [ ] **Step 4: Run the full suite**

Run: `python3 -m unittest discover -s tests -q`
Expected: `Ran 16 tests` … `OK`

- [ ] **Step 5: Merge to main and re-run there**

```bash
git add tests/test_skill_contract.py
git commit -m "Point contract tests at the current spec"
git checkout main
git merge --no-ff feat/task-driven-sourcing -m "Merge feat/task-driven-sourcing"
python3 -m unittest discover -s tests -q
```

Expected: `Ran 16 tests` … `OK`

The privacy scan only sees files that `git ls-files` reports, so a file becomes
visible to it at commit time, not before. If a test that passed on the branch
fails here, that is why — read the failure, do not re-run and hope.

- [ ] **Step 6: Push and verify from outside**

```bash
rm -rf tests/__pycache__
git branch -d feat/task-driven-sourcing
git push origin main
gh api repos/Hunter20041004/match-my-voice/contents/references --jq '.[] | "\(.name)  \(.size) bytes"'
```

Expected: `sources.md` listed with a size larger than its previous 5,867 bytes.
