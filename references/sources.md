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
named folder or service — use that source and skip the path question below. If
no task has been stated yet, still ask the context question first. Work one
step at a time: settle the source, then the items, never both at once.

## When there is no task yet

If the person asks to learn their voice with nothing to write, ask one context
question before looking for anything:

> Which kind of writing do you want this for?

Offer: job application, work email, social post, report or reflection. Accept
anything else they name. One question only — do not run a setup questionnaire.

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

Four ways in, all available without a connected service:

- **Paste text** — they paste passages directly.
- **Upload documents** — when the host accepts attachments and can extract text.
- **This conversation** — their own messages in this thread.
- **Answer a few simple questions** — guided questions when no writing exists.

Local files and speech transcripts also belong here when the host supports them.

## Per-source rules

### This conversation

Use only the person's own messages. Exclude assistant text, quoted material,
copied templates, form questions, and other participants unless authorship is
explicitly established. When it matters, ask whether this conversation reflects
the writing context they actually want to reproduce.

### Pasted text

Treat pasted content as candidate material, not settled evidence. Ask whether it
is entirely their own work and whether it was substantially edited by another
person or AI. Label multiple samples separately where possible.

### Guided questions

Ask one open question at a time, starting with something they can explain
naturally, and use only their answers. Build a provisional profile as soon as
there is enough for a trial; ask again only to close a real gap. Keep the result
marked provisional — prompted conversation can differ from natural writing.

### Uploaded documents

List the supplied files and let the person include or exclude each one. Extract
text with the host's document tools. Owning a document is not proof of writing
it. Never modify the source files.

### Local files or a folder

Ask for one narrow path. List plausible files first and ask which to analyse.
Do not recursively read a home directory, cloud mirror, repository collection,
or downloads folder. Skip credentials, hidden configuration, version-control
metadata, and unrelated files.

### Connected service

Name only services with an available, connected tool — the specific service, not
"your cloud". Search within the scope the person states, return a short candidate
list with title, date, and what it is about, and let them select exact items.
A service choice does not authorize edits, messages, uploads, or publication. If
discovery cannot be limited safely, use export or paste instead.

### Speech transcript

Offer audio only where transcription exists; otherwise ask for a transcript.
Say plainly that this learns expression in text, not vocal identity. Keep
transcription artifacts, fillers, and spoken rhythm separate from deliberate
written preferences.

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

This opening peek happens before anything is picked, and it is bounded by what
the about-line needs — a few opening lines, nothing more. It is not a licence
to read further, and it ends the moment the about-line is written.

This line replaces "who wrote it" as the thing the person judges by. Someone
seeing "this one is about your internship motivation" knows immediately whether
it is theirs and whether it fits.

Keep out spreadsheets, slide decks, and images. Documents only.

When the service exposes an owner field such as `ownedByMe`, list only items the
person created. When it does not, list them anyway and rely on the "about" line
plus the author confirmation below. Do not claim the filter was applied when it
was not.

The person then picks 3–5 items. Do not open, fetch, or read an item the person
did not pick. **Items the person did not pick are not read.**

## Author confirmation

Every automatic filter above can be wrong, and only the person knows the answer.
**Ask it every time, before any analysis.**

> Did you write all of these yourself?
> Was any of them heavily edited by someone else or by AI?

Their answer overrides every signal the skill inferred, and it is what fills in
the "likely author" line in the candidate review below. That review is for
correcting individual items, not for asking the authorship question again. If
the answer is no, follow the Mixed authorship and Mostly AI-edited rules under
"When a source does not work" below.

## Candidate review

Summarise compactly before analysis:

- selected items and source type;
- likely author, and any uncertainty about authorship;
- intended language and context;
- excluded items, and why;
- where the resulting profile will be stored.

The person can remove an item or correct authorship here. Do not copy full
private passages into the review when a title or their own label is enough.

## When the samples are thin

Authorship problems are resolved first, under the Mixed authorship and Mostly
AI-edited rules below; thinness is then judged on whatever material survives
that pass.

The picked items may turn out to be short, tabular — a document that is mostly
table or form content, not a spreadsheet file — or mostly written by someone
else. **Do not block the person.** Requiring more samples before producing
anything is the barrier that makes people abandon the setup and never return.

Instead: produce the profile, mark the profile provisional, and name the gap in
plain words.

> This one only holds up for short pieces — long writing may not match yet.

Say what is missing. Do not claim coverage the samples do not support.

## When a source does not work

Every failure ends in a working alternative, never a dead end.

- **Unavailable source** — explain briefly, then offer paste, upload, or guided questions.
- **Disconnected service** — say the connection is unavailable. Do not fabricate results and do not repeatedly retry authorization.
- **No candidate items** — verify the search or path worked before concluding nothing exists, then offer another source.
- **Mixed authorship** — exclude the uncertain passages, or keep them labelled as weak evidence.
- **Mostly AI-edited samples** — use them for facts only, or ask for a more natural alternative.
- **Sensitive material** — stop before it reaches the profile and ask for a safer or redacted sample.
- **Profile path already belongs to another person** — never overwrite or merge; select a different profile.
