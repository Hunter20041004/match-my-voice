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
