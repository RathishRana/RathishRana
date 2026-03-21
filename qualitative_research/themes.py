"""
Thematic Analysis
=================
Implements Braun & Clarke's (2006, 2019) six-phase reflexive thematic
analysis and supports Boyatzis' (1998) theory-driven approach.

Six Phases:
  1. FAMILIARISATION   — reading, initial note-taking (tracked via memos)
  2. GENERATING CODES  — see coding.py
  3. SEARCHING THEMES  — group codes into candidate themes
  4. REVIEWING THEMES  — check themes against data; split/merge/discard
  5. DEFINING THEMES   — name and write theme narratives
  6. REPORTING         — see report.py

Theme quality criteria (Braun & Clarke, 2006, p. 96):
  - Is the theme coherent, consistent, and distinctive?
  - Does it capture something important about the data?
  - Is the name concise, punchy, and immediately meaningful?

Negative case analysis:
  Each theme should be tested for disconfirming instances — segments
  that challenge or complicate the theme narrative.

Thematic map: a Theme can contain sub-themes for hierarchical structure.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterator

from .coding import CodeBook, Code


@dataclass
class Theme:
    """
    A meaningful pattern (theme) in the data, grounded in codes.

    Includes quality fields required by Braun & Clarke (2006):
    - central organizing concept
    - narrative description
    - supporting evidence (illustrative quotes)
    - negative/disconfirming cases
    """

    theme_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    central_concept: str = ""            # the core idea in one sentence
    narrative: str = ""                  # rich description of the theme
    code_ids: list[str] = field(default_factory=list)
    sub_themes: list["Theme"] = field(default_factory=list)
    illustrative_quotes: list[str] = field(default_factory=list)
    negative_cases: list[str] = field(default_factory=list)  # disconfirming evidence
    memos: list[str] = field(default_factory=list)
    phase: int = 3                       # Braun & Clarke phase (3–5)
    is_provisional: bool = True          # becomes False after phase 4 review
    created_by: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    revised_at: str | None = None

    # ------------------------------------------------------------------ #
    #  Modification                                                         #
    # ------------------------------------------------------------------ #

    def add_code(self, code_id: str) -> None:
        if code_id not in self.code_ids:
            self.code_ids.append(code_id)
            self._touch()

    def remove_code(self, code_id: str) -> None:
        self.code_ids = [c for c in self.code_ids if c != code_id]
        self._touch()

    def add_sub_theme(self, sub_theme: "Theme") -> None:
        self.sub_themes.append(sub_theme)
        self._touch()

    def add_quote(self, quote: str, participant: str | None = None) -> None:
        entry = f'"{quote}"' + (f" — {participant}" if participant else "")
        self.illustrative_quotes.append(entry)

    def add_negative_case(self, description: str) -> None:
        """
        Record a disconfirming instance — essential for credibility
        and analytic rigour (Lincoln & Guba, 1985).
        """
        self.negative_cases.append(description)
        self._touch()

    def add_memo(self, memo: str) -> None:
        self.memos.append(memo)

    def finalise(self, narrative: str = "", central_concept: str = "") -> None:
        """Mark theme as reviewed (phase 4 → 5 transition)."""
        if narrative:
            self.narrative = narrative
        if central_concept:
            self.central_concept = central_concept
        self.is_provisional = False
        self.phase = 5
        self._touch()

    def _touch(self) -> None:
        self.revised_at = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------ #
    #  Quality checks                                                       #
    # ------------------------------------------------------------------ #

    def quality_check(self) -> list[str]:
        """
        Return list of quality warnings based on Braun & Clarke (2006) criteria.
        An empty list means the theme passes all checks.
        """
        warnings = []
        if not self.name:
            warnings.append("Theme has no name.")
        if not self.central_concept:
            warnings.append("No central organizing concept defined.")
        if not self.narrative:
            warnings.append("No narrative description — required for Phase 5.")
        if len(self.code_ids) < 2:
            warnings.append(
                "Theme is grounded in fewer than 2 codes — may lack coherence."
            )
        if not self.illustrative_quotes:
            warnings.append(
                "No illustrative quotes added — required for thick description."
            )
        if not self.negative_cases:
            warnings.append(
                "No negative cases recorded — conduct negative case analysis "
                "before finalising (Lincoln & Guba, 1985)."
            )
        return warnings

    def __repr__(self) -> str:
        status = "provisional" if self.is_provisional else "final"
        return f"Theme('{self.name}', codes={len(self.code_ids)}, {status})"


class ThematicAnalyzer:
    """
    Orchestrates all six phases of Braun & Clarke thematic analysis.

    Maintains the thematic map and provides operations for reviewing,
    splitting, merging, and finalising themes.
    """

    def __init__(self, codebook: CodeBook, researcher: str = ""):
        self.codebook = codebook
        self.researcher = researcher
        self.themes: dict[str, Theme] = {}
        self.familiarisation_notes: list[str] = []
        self.thematic_map_memos: list[str] = []

    # ------------------------------------------------------------------ #
    #  Phase 1: Familiarisation                                             #
    # ------------------------------------------------------------------ #

    def add_familiarisation_note(self, note: str) -> None:
        """Phase 1: Record initial impressions, questions, ideas."""
        self.familiarisation_notes.append(
            f"[{datetime.now(timezone.utc).isoformat()}] {note}"
        )

    # ------------------------------------------------------------------ #
    #  Phase 3: Searching for themes                                        #
    # ------------------------------------------------------------------ #

    def create_theme(
        self,
        name: str,
        code_names: list[str],
        central_concept: str = "",
        narrative: str = "",
        researcher: str | None = None,
    ) -> Theme:
        """
        Phase 3: Create a candidate theme from a list of code names.
        Codes are looked up by name; missing codes are warned about.
        """
        code_ids = []
        missing = []
        for cn in code_names:
            code = self.codebook.find_by_name(cn)
            if code:
                code_ids.append(code.code_id)
            else:
                missing.append(cn)

        if missing:
            raise ValueError(
                f"Codes not found in codebook: {missing}. "
                "Create them first or check spelling."
            )

        theme = Theme(
            name=name,
            code_ids=code_ids,
            central_concept=central_concept,
            narrative=narrative,
            created_by=researcher or self.researcher,
        )
        self.themes[theme.theme_id] = theme
        return theme

    def create_theme_from_codes(
        self,
        name: str,
        codes: list[Code],
        **kwargs,
    ) -> Theme:
        return self.create_theme(name, [c.name for c in codes], **kwargs)

    # ------------------------------------------------------------------ #
    #  Phase 4: Reviewing themes                                            #
    # ------------------------------------------------------------------ #

    def merge_themes(
        self,
        theme_names: list[str],
        new_name: str,
        rationale: str = "",
        researcher: str | None = None,
    ) -> Theme:
        """Merge two or more themes into a new one (phase 4 review)."""
        to_merge = [self._find_by_name(n) for n in theme_names]
        merged_code_ids: list[str] = []
        merged_quotes: list[str] = []
        merged_negatives: list[str] = []

        for t in to_merge:
            merged_code_ids.extend(t.code_ids)
            merged_quotes.extend(t.illustrative_quotes)
            merged_negatives.extend(t.negative_cases)
            del self.themes[t.theme_id]

        new_theme = Theme(
            name=new_name,
            code_ids=list(dict.fromkeys(merged_code_ids)),  # dedup, preserve order
            illustrative_quotes=merged_quotes,
            negative_cases=merged_negatives,
            created_by=researcher or self.researcher,
            memos=[f"Merged from: {theme_names}. Rationale: {rationale}"],
        )
        self.themes[new_theme.theme_id] = new_theme
        return new_theme

    def split_theme(
        self,
        theme_name: str,
        split_a: dict,
        split_b: dict,
        rationale: str = "",
    ) -> tuple[Theme, Theme]:
        """
        Split one theme into two. split_a/split_b are dicts with keys:
        'name', 'code_names' (lists), optional 'central_concept'.
        """
        original = self._find_by_name(theme_name)
        del self.themes[original.theme_id]

        theme_a = self.create_theme(
            name=split_a["name"],
            code_names=split_a["code_names"],
            central_concept=split_a.get("central_concept", ""),
        )
        theme_b = self.create_theme(
            name=split_b["name"],
            code_names=split_b["code_names"],
            central_concept=split_b.get("central_concept", ""),
        )
        memo = f"Split from '{theme_name}'. Rationale: {rationale}"
        theme_a.add_memo(memo)
        theme_b.add_memo(memo)
        return theme_a, theme_b

    def discard_theme(self, theme_name: str, rationale: str = "") -> None:
        theme = self._find_by_name(theme_name)
        theme.add_memo(f"DISCARDED: {rationale}")
        del self.themes[theme.theme_id]

    # ------------------------------------------------------------------ #
    #  Phase 5: Defining themes                                             #
    # ------------------------------------------------------------------ #

    def finalise_theme(
        self,
        theme_name: str,
        narrative: str,
        central_concept: str,
    ) -> Theme:
        theme = self._find_by_name(theme_name)
        theme.finalise(narrative=narrative, central_concept=central_concept)
        return theme

    def add_quote_to_theme(
        self,
        theme_name: str,
        quote: str,
        participant: str | None = None,
    ) -> None:
        self._find_by_name(theme_name).add_quote(quote, participant)

    def add_negative_case(
        self, theme_name: str, description: str
    ) -> None:
        self._find_by_name(theme_name).add_negative_case(description)

    # ------------------------------------------------------------------ #
    #  Quality review                                                       #
    # ------------------------------------------------------------------ #

    def quality_report(self) -> dict[str, list[str]]:
        """
        Run quality checks on all themes.
        Returns {theme_name: [warnings]} — empty list = passes.
        """
        return {
            t.name: t.quality_check()
            for t in self.themes.values()
        }

    def all_warnings(self) -> list[str]:
        warnings = []
        for name, issues in self.quality_report().items():
            for issue in issues:
                warnings.append(f"[{name}] {issue}")
        return warnings

    # ------------------------------------------------------------------ #
    #  Coverage analysis                                                    #
    # ------------------------------------------------------------------ #

    def coverage(self) -> dict[str, dict]:
        """
        For each theme: how many segments does it cover?
        Uses code instances to map codes → segments.
        """
        result = {}
        for theme in self.themes.values():
            covered_segments: set[str] = set()
            covered_docs: set[str] = set()
            for code_id in theme.code_ids:
                for inst in self.codebook.instances_for_code(code_id):
                    covered_segments.add(inst.segment_id)
                    covered_docs.add(inst.document_id)
            result[theme.name] = {
                "segments": len(covered_segments),
                "documents": len(covered_docs),
                "codes": len(theme.code_ids),
            }
        return result

    def uncoded_code_names(self) -> list[str]:
        """Return active codes not yet assigned to any theme."""
        themed_ids = {cid for t in self.themes.values() for cid in t.code_ids}
        return [
            c.name
            for c in self.codebook.iter_active()
            if c.code_id not in themed_ids
        ]

    # ------------------------------------------------------------------ #
    #  Iteration                                                            #
    # ------------------------------------------------------------------ #

    def iter_themes(self) -> Iterator[Theme]:
        yield from self.themes.values()

    def provisional_themes(self) -> list[Theme]:
        return [t for t in self.themes.values() if t.is_provisional]

    def final_themes(self) -> list[Theme]:
        return [t for t in self.themes.values() if not t.is_provisional]

    def _find_by_name(self, name: str) -> Theme:
        for t in self.themes.values():
            if t.name.lower() == name.lower():
                return t
        raise KeyError(
            f"Theme '{name}' not found. Available: "
            + str([t.name for t in self.themes.values()])
        )

    def add_thematic_map_memo(self, memo: str) -> None:
        self.thematic_map_memos.append(
            f"[{datetime.now(timezone.utc).isoformat()}] {memo}"
        )

    def __repr__(self) -> str:
        final = len(self.final_themes())
        provisional = len(self.provisional_themes())
        return f"ThematicAnalyzer(final={final}, provisional={provisional})"
