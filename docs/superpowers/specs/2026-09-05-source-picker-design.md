# Sample Source Picker Design

## Goal

Make first-time voice setup understandable without requiring users to know what counts as a useful writing sample. The skill asks where the user wants to get material, shows only sources the current AI environment can actually access, and lets the user choose specific content before analysis.

The picker changes onboarding and source handling. It does not add universal access to Google Drive, Gmail, Notion, Slack, local files, or audio transcription. Each option depends on capabilities already available and authorized in the current host.

## User experience

When Learn mode starts and no usable samples have already been supplied, ask one question:

> Where would you like to get examples of how you naturally communicate?

Show only available choices, using plain language:

1. This conversation
2. Paste text
3. Upload documents
4. Choose local files or a folder
5. Choose from a connected service, naming each available service
6. Answer a few simple questions

The skill accepts an explicit source already named in the request and skips the menu. It asks one step at a time; it does not present a long setup questionnaire.

After a source is chosen, the skill displays or describes the candidate items and asks the user to select the specific material. Choosing a service authorizes discovery needed to present candidates, not unrestricted analysis of the entire account. The skill states what will be read before it analyzes the material.

## Capability detection

The source picker has two layers:

- Core sources work without external integrations: current conversation, pasted text, and guided questions.
- Conditional sources appear only when supported: uploaded files, local filesystem, audio transcription, or installed and connected services.

Capability detection means checking which tools, attachments, and connectors exist in the current environment. It is similar to a power strip that exposes only sockets that are actually connected. This prevents the skill from promising Google Drive or local-file access when the host cannot provide it.

If detection is uncertain, the skill does not claim the source is available. It offers a core fallback, such as pasting the text or exporting the selected documents.

## Source flows

### Current conversation

Use only the user's own messages in the relevant conversation. Exclude assistant text, quoted material, copied templates, form questions, and other participants unless authorship is explicitly established. Ask whether the conversation represents the writing context the user wants to reproduce when that difference matters.

### Pasted text

Treat pasted content as candidate material. Ask whether it is entirely the user's work and whether it was substantially edited by another person or AI. Separate multiple samples by label when possible.

### Uploaded documents

List the supplied files and let the user include or exclude each one. Extract text using the host's supported document tools. Do not treat document ownership as proof of authorship. Do not change the source files.

### Local files or folder

Let the user choose or name a narrow path. First list plausible files and ask which ones to analyze. Do not recursively read an entire home directory, cloud mirror, repository collection, or downloads folder. Ignore credentials, hidden configuration, unrelated files, and version-control metadata.

### Connected service

Name only services with an available, connected tool. Search within the user's stated scope, return a small candidate list with title, type, and date when available, and let the user select exact items. A service choice does not authorize edits, messages, uploads, or publication. If the connector cannot limit discovery safely, use export or paste as the fallback.

### Guided questions

Ask one simple, open question at a time and use only the user's answers. Start with a topic they can explain naturally. Build a provisional profile as soon as there is enough evidence for a trial; ask another question only to resolve a meaningful gap. Mark the result provisional because prompted conversation may differ from natural writing.

### Speech transcript

Offer audio only when transcription is supported. Explain that the skill learns expression in text, not vocal identity. Separate transcript artifacts, fillers, and spoken rhythm from intentional written preferences. Without transcription capability, ask the user to provide a transcript.

## Candidate review

Before analysis, summarize:

- selected items and source type;
- likely author and any uncertainty;
- intended language and context;
- excluded items and why;
- where the resulting personal profile will be stored.

The review should be compact. The user can remove an item or correct authorship. Do not copy full private passages into the review when a title or user-provided label is enough.

## Data flow and separation

```text
Available host capabilities
          ↓
Visible source choices
          ↓
User-selected source and scope
          ↓
Small candidate list
          ↓
User-selected samples
          ↓
Authorship and context filtering
          ↓
Private personal VOICE.md
```

The distributable skill stores only the workflow and empty schema. Raw samples and generated profiles remain outside the repository. Each person's profile has a separate location and identifier. Current explicit instructions override profile history.

## Error and fallback behavior

- Unavailable source: explain briefly and offer paste, upload, or guided questions.
- Disconnected service: tell the user the connection is unavailable; do not fabricate results or repeatedly retry authorization.
- No candidate items: verify the search or path worked before concluding nothing exists, then offer another source.
- Mixed authorship: exclude uncertain passages or keep them labeled as weak evidence.
- Mostly AI-edited samples: use them for facts only or ask for a natural alternative.
- Sensitive material detected: stop before adding it to the profile and ask for a safer sample or redacted version.
- Profile path already belongs to another person: do not overwrite or merge it; select a different profile.

## Verification

Behavioral checks should cover one scenario at a time:

1. With no integrations, only core sources are offered.
2. With a connected service, its name appears without implying unrestricted access.
3. An explicitly pasted sample skips the source menu.
4. Assistant and quoted text are excluded from current-conversation samples.
5. Selecting a service requires selection of exact candidate items before analysis.
6. An unavailable source produces a working fallback.
7. Different users create separate profiles.
8. No raw sample or generated profile enters tracked repository files.

The existing multi-person blind test remains the product-level evaluation. Passing onboarding checks proves the flow behaves as designed; it does not prove that generated writing matches the person.

## Alternatives considered

### Always request pasted samples

This is simplest and works across hosts, but it makes users decide what to collect and copy. Keep it as the universal fallback.

### Automatically scan every connected source

This reduces user effort but creates unclear authorization, authorship, and privacy boundaries. It also makes results depend heavily on host integrations. Do not use this approach.

### Recommended: capability-aware source picker

This gives beginners a clear first step while preserving control over exact samples. It adds conditional branches, but each branch ends in the same reviewed sample set, so the downstream voice analysis remains consistent.

## Scope for the next implementation

Update Learn mode in `SKILL.md`, add a focused source-selection reference, and update the README examples. Do not add service-specific API instructions or dependencies. Validate the package, run the behavioral scenarios that can be checked locally, inspect the public repository for private data, and publish the update to the existing `main` branch only after those checks pass.
