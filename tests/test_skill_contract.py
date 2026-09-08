"""Contract tests for the Match My Voice skill package.

Each test traces to a numbered behavioural check in
docs/superpowers/specs/2026-09-05-source-picker-design.md ("Verification").

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

    # Spec check 1: with no integrations, only core sources are offered.
    def test_learn_mode_routes_to_a_source_picker_split_into_core_and_conditional(self):
        skill = read("SKILL.md")
        self.assertIn("references/sources.md", skill)

        sources = read("references/sources.md")
        self.assertIn(
            "Where would you like to get examples of how you naturally communicate?",
            sources,
        )
        core_heading = "## Core sources"
        conditional_heading = "## Conditional sources"
        self.assertIn(core_heading, sources)
        self.assertIn(conditional_heading, sources)
        self.assertLess(
            sources.index(core_heading),
            sources.index(conditional_heading),
            "core sources must be presented before conditional ones",
        )

        core_block = sources[sources.index(core_heading):sources.index(conditional_heading)]
        for always_available in ("This conversation", "Paste text", "Answer a few simple questions"):
            self.assertIn(always_available, core_block, always_available)

        conditional_block = sources[sources.index(conditional_heading):]
        for gated in ("Upload documents", "local files", "connected service", "Speech transcript"):
            self.assertIn(gated, conditional_block, gated)

    # Spec check 3: an explicitly named source skips the menu.
    def test_an_explicitly_named_source_skips_the_menu(self):
        sources = read("references/sources.md")
        self.assertIn("skip the menu", flat(sources),
                      "sources.md must say an explicitly named source skips the menu")
        self.assertIn("one step at a time", flat(sources),
                      "sources.md must require one step at a time, not a questionnaire")

    # Spec check 5: a chosen source must narrow to user-selected items before analysis.
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

    # Spec check 6: an unavailable source produces a working fallback.
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

    # Spec check 2: a connected service is named without implying unrestricted access.
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

    # Spec check 4: only the person's own words become samples.
    def test_core_sources_filter_out_text_the_person_did_not_write(self):
        sources = flat(read("references/sources.md"))
        for excluded in ("assistant text", "quoted material", "copied templates",
                         "form questions", "other participants"):
            self.assertIn(excluded, sources, f"conversation samples must exclude: {excluded}")
        self.assertIn("substantially edited by another person or ai", sources,
                      "pasted text must be checked for outside editing")
        self.assertIn("provisional", sources,
                      "guided answers must be marked provisional")

    # Spec check 8: no raw sample or generated profile is tracked by the repository.
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
        for path in tracked:
            if path == self_path or not path.endswith((".md", ".yaml", ".py")):
                continue
            prose = url.sub(" ", read(path))
            self.assertNotIn("hunter", flat(prose), f"maintainer identity leaked into {path}")
            self.assertNotIn("曾尉庭", prose, f"maintainer identity leaked into {path}")

    # Spec scope: the README explains the new first-run behaviour.
    def test_readme_documents_the_source_picker(self):
        readme = read("README.md")
        first_run = readme[readme.index("## 第一次用"):readme.index("## 之後使用")]
        self.assertIn("你想從哪裡", first_run,
                      "README must show the one question the skill asks")
        for promise in ("讀得到", "跳過", "確認要分析哪些"):
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


if __name__ == "__main__":
    unittest.main()
