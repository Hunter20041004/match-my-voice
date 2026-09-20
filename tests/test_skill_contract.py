"""Contract tests for the Match My Voice skill package.

Each test traces to a numbered acceptance check in
docs/superpowers/specs/2026-09-08-sample-sourcing-design.md ("驗收檢查"),
except the package-hygiene tests, which guard the privacy boundary described
in docs/superpowers/specs/2026-09-05-source-picker-design.md.

These check that the skill *document* states the required behaviour. They
cannot prove an agent follows it — the multi-person blind test in
docs/first-pilot-zh-TW.md remains the product-level evaluation.
"""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


def flat(text):
    """Collapse whitespace so phrase assertions survive markdown line wrapping."""
    return " ".join(text.split()).casefold()


class SourcePickerContractTests(unittest.TestCase):
    longMessage = False

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

    # Checks 4 and 5 of docs/superpowers/specs/2026-09-08-sample-sourcing-design.md:
    # every candidate says what it is about; unpicked files stay unread.
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

    # Spec check 8: the profile has two layers and records which contexts it covers.
    def test_profile_template_has_core_modes_and_coverage(self):
        template = read("references/profile-template.md")
        for field in ("Core:", "Context modes:", "Context coverage:"):
            self.assertIn(field, template, f"profile template needs the field: {field}")
        flat_template = flat(template)
        self.assertIn("hold in every context", flat_template,
                      "the core layer must be defined as context-independent")
        self.assertIn("a formal version of the person is still that person",
                      flat_template,
                      "context modes must not be framed as conflicting with the voice")
        self.assertIn("which contexts this profile has actually been built from",
                      flat_template,
                      "coverage must record the contexts actually evidenced")

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

    # Spec check 10: profiles keep short excerpts as evidence, never whole sources.
    def test_profiles_keep_excerpts_not_whole_documents(self):
        skill = flat(read("SKILL.md"))
        self.assertIn("keep short excerpts as evidence", skill,
                      "SKILL.md must require excerpts as evidence")
        self.assertIn("never store the full text of a source document", skill,
                      "SKILL.md must forbid storing whole source documents")
        self.assertIn("a profile that cannot show its evidence cannot be argued with", skill,
                      "the reason for keeping excerpts must be recorded")

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

    # 2026-09-05 spec, Verification check 3: an explicitly named source skips the menu.
    def test_an_explicitly_named_source_skips_the_menu(self):
        sources = read("references/sources.md")
        self.assertIn("skip the path question below", flat(sources),
                      "an explicitly named source must skip the path question, not the context question")
        self.assertIn("one step at a time", flat(sources),
                      "sources.md must require one step at a time, not a questionnaire")

    # 2026-09-05 spec, Verification check 5: a chosen source must narrow to user-selected items before analysis.
    def test_candidates_are_selected_and_reviewed_before_analysis(self):
        sources = read("references/sources.md")
        self.assertIn("## Candidate review", sources,
                      "sources.md needs a candidate review section")
        review = sources[sources.index("## Candidate review"):]
        for required in (
            "selected items and source type",
            "likely author",
            "language and context",
            "excluded items",
            "where the resulting profile will be stored",
        ):
            self.assertIn(required, flat(review), f"review must summarise: {required}")
        self.assertIn("before analysis", flat(sources),
                      "sources.md must gate analysis behind the review")
        self.assertIn("do not copy full private passages", flat(review),
                      "review must not reproduce private passages")

    # 2026-09-05 spec, Verification check 6: an unavailable source produces a working fallback.
    def test_every_failure_mode_has_a_named_fallback(self):
        sources = read("references/sources.md")
        self.assertIn("## When a source does not work", sources,
                      "sources.md needs a fallback section")
        fallback = flat(sources[sources.index("## When a source does not work"):])
        for cue in (
            "unavailable source",
            "disconnected service",
            "no candidate items",
            "mixed authorship",
            "mostly ai-edited",
            "sensitive material",
            "profile path already belongs to another person",
        ):
            self.assertIn(cue, fallback, f"fallback section must cover: {cue}")
        self.assertIn("do not fabricate", fallback,
                      "a disconnected service must not produce invented results")
        self.assertIn("verify the search or path worked", fallback,
                      "empty results must be verified before concluding nothing exists")

    # 2026-09-05 spec, Verification check 2: a connected service is named without implying unrestricted access.
    def test_a_connected_service_is_scoped_and_read_only(self):
        sources = flat(read("references/sources.md"))
        self.assertIn("name only services with an available, connected tool", sources,
                      "only genuinely connected services may be named")
        self.assertIn("does not authorize edits, messages, uploads, or publication", sources,
                      "a service choice must stay read-only")
        self.assertIn("do not recursively read", sources,
                      "local browsing must not sweep whole trees")
        for never_swept in ("home directory", "downloads", "credentials"):
            self.assertIn(never_swept, sources, f"must exclude: {never_swept}")

    # 2026-09-05 spec, Verification check 4: only the person's own words become samples.
    def test_core_sources_filter_out_text_the_person_did_not_write(self):
        sources = flat(read("references/sources.md"))
        for excluded in ("assistant text", "quoted material", "copied templates",
                         "form questions", "other participants"):
            self.assertIn(excluded, sources, f"conversation samples must exclude: {excluded}")
        self.assertIn("substantially edited by another person or ai", sources,
                      "pasted text must be checked for outside editing")
        self.assertIn("provisional", sources,
                      "guided answers must be marked provisional")

    # 2026-09-05 spec, Verification check 8: no raw sample or generated profile is tracked by the repository.
    def test_no_personal_sample_or_profile_is_tracked(self):
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.split()

        for path in tracked:
            name = Path(path).name
            self.assertNotEqual(name, "VOICE.md", f"tracked personal profile: {path}")
            first = Path(path).parts[0]
            self.assertNotIn(first, ("profiles", "samples", "private"),
                             f"tracked private directory: {path}")

        ignored = read(".gitignore").split()
        for pattern in ("VOICE.md", "profiles/", "samples/", "private/"):
            self.assertIn(pattern, ignored, f".gitignore must exclude {pattern}")

        # The distributable package carries the method, never its author's voice.
        # Repository URLs legitimately contain the owner's account name, so strip
        # URLs before looking for the maintainer's identity in prose.
        url = re.compile(r"https?://\S+")
        # This file carries the search terms as literals, so it cannot scan itself.
        self_path = Path(__file__).resolve().relative_to(ROOT).as_posix()

        # The private terms themselves must never live in a tracked file, or this
        # test would repeat the exact leak it exists to catch. They are kept in a
        # gitignored local file instead; "hunter" is the public GitHub account
        # name, not private, so it is safe to keep as a built-in term.
        forbidden_terms = ["hunter"]
        forbidden_terms_path = ROOT / "private" / "forbidden-terms.txt"
        if forbidden_terms_path.exists():
            for line in forbidden_terms_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                forbidden_terms.append(line)

        for path in tracked:
            if path == self_path or not path.endswith((".md", ".yaml", ".py")):
                continue
            prose = flat(url.sub(" ", read(path)))
            for term in forbidden_terms:
                self.assertNotIn(term.casefold(), prose,
                                 f"maintainer identity leaked into {path}")

    # Spec scope: the README describes the task-driven first run.
    def test_readme_documents_the_task_driven_first_run(self):
        readme = read("README.md")
        first_run = readme[readme.index("## 第一次用"):readme.index("## 之後使用")]
        self.assertNotIn("你想從哪裡", first_run,
                         "the old open-ended source question must be gone from the README")
        for promise in ("你要寫什麼", "在講什麼", "沒勾的不會被讀",
                        "是你自己寫的嗎", "讀得到"):
            self.assertIn(promise, first_run, f"README first-run must mention: {promise}")

    # Package hygiene: build artifacts never ship inside a cloned skill.
    def test_python_build_artifacts_are_not_tracked(self):
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.split()
        for path in tracked:
            self.assertNotIn("__pycache__", path, f"tracked build artifact: {path}")
            self.assertFalse(path.endswith((".pyc", ".pyo")), f"tracked build artifact: {path}")

        ignored = read(".gitignore").split()
        for pattern in ("__pycache__/", "*.py[cod]"):
            self.assertIn(pattern, ignored, f".gitignore must exclude {pattern}")


class PersonaContractTests(unittest.TestCase):
    """Traces to docs/superpowers/specs/2026-09-20-personas-and-feedback-design.md."""
    longMessage = False

    # Check 1: several personas; UI sets the active one; chat overrides once.
    def test_skill_defines_personas_and_active_persona_resolution(self):
        skill = flat(read("SKILL.md"))
        self.assertIn("is one complete voice profile with its own core habits", skill,
                      "SKILL.md must define the term persona")
        for term in ("config.json", "persona.json", "learned.md"):
            self.assertIn(term, skill, f"SKILL.md must introduce: {term}")
        self.assertIn('"active"', read("SKILL.md"), "config.json's active key must be named")
        self.assertIn("read the active persona from", skill,
                      "the default persona must come from config.json")
        self.assertIn("overrides it for this task only", skill,
                      "a chat-level persona choice must be one-off")
        self.assertIn("only one persona exists, use it", skill,
                      "single persona needs no question")
        self.assertIn("ask once", skill, "several personas and no active one → one question")
        self.assertIn("personas never inherit from each other", skill,
                      "personas must be independent")

        template = flat(read("references/profile-template.md"))
        self.assertIn("persona.json", template)
        for t in ('"self"', '"role"'):
            self.assertIn(t, read("references/profile-template.md"), f"type value {t}")

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

    # Checks 4 and 5: writing applies active learned rules; refining follows feedback.md.
    def test_write_reads_learned_rules_and_refine_routes_to_feedback(self):
        skill = read("SKILL.md")
        self.assertIn("references/feedback.md", skill)
        f = flat(skill)
        self.assertIn("then every `[active]` line of `learned.md`", f,
                      "Write must apply active learned rules")
        self.assertIn("skip `[revoked]` lines", f)
        self.assertIn("pastes back an edited version", f,
                      "Refine must recognise the paste-back case")
        self.assertIn("follow [learning from edits](references/feedback.md)", f)


if __name__ == "__main__":
    unittest.main()
