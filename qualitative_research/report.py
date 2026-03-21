"""
Report Generator
================
Produces comprehensive, publication-ready research reports covering:

  EXECUTIVE SUMMARY    — key findings, participant overview
  METHODOLOGY          — sampling rationale, saturation evidence
  CODEBOOK             — full code definitions, frequencies, hierarchy
  RELIABILITY          — κ, α, % agreement tables with interpretations
  SATURATION           — code emergence curve and judgement
  THEMES               — per-theme narrative, quotes, negative cases
  AUDIT TRAIL SUMMARY  — decision log counts and key milestones
  REFLEXIVITY          — researcher positionality statements
  RECOMMENDATIONS      — next steps, limitations

Outputs to plain text (always), with hooks for Markdown and JSON.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from dataclasses import asdict
from typing import Any

from .coding import CodeBook
from .corpus import Corpus
from .themes import ThematicAnalyzer
from .reliability import ReliabilityReport, ReliabilityCalculator
from .saturation import SaturationResult
from .audit import AuditTrail


# ─────────────────────────────────────────────────────────────────────────────

DIVIDER = "=" * 78
SECTION = "-" * 78


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


class ReportGenerator:
    """
    Assembles a full qualitative research report from project components.
    """

    def __init__(
        self,
        project_name: str,
        corpus: Corpus,
        codebook: CodeBook,
        analyzer: ThematicAnalyzer,
        audit: AuditTrail | None = None,
    ):
        self.project_name = project_name
        self.corpus = corpus
        self.codebook = codebook
        self.analyzer = analyzer
        self.audit = audit

    # ------------------------------------------------------------------ #
    #  Public entry points                                                  #
    # ------------------------------------------------------------------ #

    def generate_text(
        self,
        reliability_report: ReliabilityReport | None = None,
        saturation_result: SaturationResult | None = None,
        coders: list | None = None,
    ) -> str:
        sections = [
            self._header(),
            self._executive_summary(),
            self._corpus_description(),
            self._methodology_section(),
            self._codebook_section(),
            self._reliability_section(reliability_report),
            self._saturation_section(saturation_result),
            self._themes_section(),
            self._audit_section(),
            self._reflexivity_section(coders),
            self._quality_section(),
            self._footer(),
        ]
        return "\n\n".join(s for s in sections if s)

    def generate_markdown(
        self,
        reliability_report: ReliabilityReport | None = None,
        saturation_result: SaturationResult | None = None,
        coders: list | None = None,
    ) -> str:
        text = self.generate_text(reliability_report, saturation_result, coders)
        # Minimal conversion: section headers
        md = text.replace(DIVIDER, "---").replace(SECTION, "")
        return md

    def generate_json(
        self,
        reliability_report: ReliabilityReport | None = None,
        saturation_result: SaturationResult | None = None,
        coders: list | None = None,
    ) -> str:
        data: dict[str, Any] = {
            "project": self.project_name,
            "generated_at": _now(),
            "corpus": self.corpus.stats(),
            "codebook": self.codebook.export_codebook(),
            "themes": [
                {
                    "name": t.name,
                    "central_concept": t.central_concept,
                    "narrative": t.narrative,
                    "code_count": len(t.code_ids),
                    "quotes": t.illustrative_quotes,
                    "negative_cases": t.negative_cases,
                    "is_provisional": t.is_provisional,
                    "quality_warnings": t.quality_check(),
                }
                for t in self.analyzer.iter_themes()
            ],
        }
        if reliability_report:
            data["reliability"] = {
                "krippendorffs_alpha": reliability_report.krippendorffs_alpha,
                "overall_percent_agreement": reliability_report.overall_percent_agreement,
                "pairwise": [p._asdict() for p in reliability_report.pairwise],
                "recommendation": reliability_report.recommendation,
            }
        if saturation_result:
            data["saturation"] = {
                "reached": saturation_result.saturation_reached,
                "at_document": saturation_result.saturation_document_index,
                "total_unique_codes": saturation_result.total_unique_codes,
                "recommendation": saturation_result.recommendation,
            }
        if self.audit:
            data["audit_summary"] = self.audit.summary()

        return json.dumps(data, indent=2, ensure_ascii=False)

    def save(
        self,
        path: str,
        fmt: str = "text",
        **kwargs,
    ) -> None:
        if fmt == "text":
            content = self.generate_text(**kwargs)
        elif fmt == "markdown":
            content = self.generate_markdown(**kwargs)
        elif fmt == "json":
            content = self.generate_json(**kwargs)
        else:
            raise ValueError(f"Unknown format: {fmt}. Choose text/markdown/json.")

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Report saved to: {path}")

    # ------------------------------------------------------------------ #
    #  Section builders                                                     #
    # ------------------------------------------------------------------ #

    def _header(self) -> str:
        return "\n".join([
            DIVIDER,
            f"  QUALITATIVE RESEARCH REPORT",
            f"  Project: {self.project_name}",
            f"  Generated: {_now()}",
            DIVIDER,
        ])

    def _executive_summary(self) -> str:
        stats = self.corpus.stats()
        themes = list(self.analyzer.iter_themes())
        final_themes = [t for t in themes if not t.is_provisional]
        freq = self.codebook.code_frequency()
        top_codes = list(freq.items())[:5]

        lines = [
            "EXECUTIVE SUMMARY",
            SECTION,
            f"Data corpus:    {stats['document_count']} documents, "
            f"{stats['total_words']:,} words, {stats['total_segments']:,} segments",
            f"Codes generated: {sum(1 for _ in self.codebook.iter_active())} active codes",
            f"Themes identified: {len(themes)} total ({len(final_themes)} finalised)",
            "",
            "Top 5 codes by frequency:",
        ]
        for name, count in top_codes:
            lines.append(f"  {name:<40} {count:>4} applications")

        if final_themes:
            lines += ["", "Final themes:"]
            for t in final_themes:
                lines.append(f"  • {t.name}: {t.central_concept}")

        return "\n".join(lines)

    def _corpus_description(self) -> str:
        stats = self.corpus.stats()
        lines = [
            "CORPUS DESCRIPTION",
            SECTION,
            f"Total documents:  {stats['document_count']}",
            f"Total words:      {stats['total_words']:,}",
            f"Total segments:   {stats['total_segments']:,}",
            "",
            "Source types:",
        ]
        for stype, count in stats["source_types"].items():
            lines.append(f"  {stype:<30} {count} document(s)")

        if self.corpus.sampling_notes:
            lines += ["", "Purposive sampling rationale:"]
            for note in self.corpus.sampling_notes:
                lines.append(f"  • {note}")

        lines += ["", "Documents:"]
        for doc in self.corpus.iter_documents():
            lines.append(
                f"  [{doc.source_type}] {doc.title}"
                + (f" — {doc.participant_id}" if doc.participant_id else "")
                + (f" ({doc.collection_date})" if doc.collection_date else "")
            )
            if doc.context:
                lines.append(f"    Context: {doc.context}")

        return "\n".join(lines)

    def _methodology_section(self) -> str:
        return "\n".join([
            "METHODOLOGY",
            SECTION,
            "Analytic approach: Reflexive Thematic Analysis (Braun & Clarke, 2006, 2019)",
            "Trustworthiness criteria: Lincoln & Guba (1985)",
            "  • Credibility — triangulation, member checking, negative case analysis",
            "  • Transferability — thick description, purposive sampling records",
            "  • Dependability — full audit trail (see Audit Trail section)",
            "  • Confirmability — reflexivity journal, inter-rater reliability",
            "",
            "Coding approach: Multi-paradigm (Saldaña, 2021)",
            "  Paradigms used: Descriptive, In-Vivo, Process, Axial, Theoretical",
            "",
            "Inter-rater reliability: Cohen's κ and Krippendorff's α",
            "  Threshold: κ ≥ 0.80, α ≥ 0.80 (Landis & Koch, 1977; Krippendorff, 2004)",
            "",
            "Saturation criterion: Theoretical saturation (Glaser & Strauss, 1967)",
            "  Operationalised as: ≤5% new codes per document over 3+ consecutive documents",
        ])

    def _codebook_section(self) -> str:
        codes = self.codebook.export_codebook()
        lines = [
            "CODEBOOK",
            SECTION,
            f"Total active codes: {len(codes)}",
            "",
        ]
        for entry in codes:
            lines += [
                f"CODE: {entry['name']}",
                f"  Paradigm:   {entry['paradigm']}",
                f"  Frequency:  {entry['frequency']} application(s)",
            ]
            if entry["definition"]:
                lines.append(f"  Definition: {entry['definition']}")
            if entry["inclusion_criteria"]:
                lines.append(f"  Include:    {entry['inclusion_criteria']}")
            if entry["exclusion_criteria"]:
                lines.append(f"  Exclude:    {entry['exclusion_criteria']}")
            if entry["example_anchor"]:
                lines.append(f"  Example:    \"{entry['example_anchor']}\"")
            if entry["child_codes"]:
                lines.append(f"  Sub-codes:  {', '.join(entry['child_codes'])}")
            if entry["memos"]:
                for memo in entry["memos"]:
                    lines.append(f"  Memo:       {memo}")
            lines.append("")

        return "\n".join(lines)

    def _reliability_section(self, report: ReliabilityReport | None) -> str:
        if not report:
            return ""

        lines = [
            "INTER-RATER RELIABILITY",
            SECTION,
            f"Krippendorff's Alpha (α): {report.krippendorffs_alpha:.4f}",
            f"Overall % Agreement:      {report.overall_percent_agreement:.1%}",
            "",
            "Pairwise Results:",
        ]

        for p in report.pairwise:
            lines += [
                f"  {p.rater_a} vs {p.rater_b}:",
                f"    Cohen's κ:      {p.cohens_kappa:.4f}  ({p.interpretation})",
                f"    Scott's π:      {p.scotts_pi:.4f}",
                f"    % Agreement:    {p.percent_agreement:.1%}",
                f"    Segments:       {p.n_segments} ({p.n_agreed} agreed)",
                "",
            ]

        lines += [
            "Assessment:",
            f"  {report.recommendation}",
        ]

        if report.discrepancies:
            lines += ["", f"Discrepancies requiring review: {len(report.discrepancies)}"]
            for d in report.discrepancies[:5]:  # show top 5
                lines.append(f"  Segment {d['segment_id'][:8]}…")
                for rater, codes in d["codings"].items():
                    lines.append(f"    {rater}: {codes or ['(no code)']}")

        return "\n".join(lines)

    def _saturation_section(self, result: SaturationResult | None) -> str:
        if not result:
            return ""

        detector_cls = SaturationResult  # for type hint only
        lines = [
            "THEORETICAL SATURATION",
            SECTION,
            f"Total unique codes:   {result.total_unique_codes}",
            f"Saturation reached:   {result.saturation_reached}",
            f"Window size:          {result.window_size} documents",
            f"Threshold:            {result.threshold:.0%} new codes per document",
            "",
            "Code emergence by document:",
        ]

        for pt in result.curve:
            bar = "█" * min(int(pt.new_code_rate * 100), 40)
            sat = " ← SAT" if pt.document_index == result.saturation_document_index else ""
            lines.append(
                f"  Doc {pt.document_index + 1:02d} |{bar:<40}| "
                f"{pt.new_code_rate:.0%} ({pt.new_codes} new codes){sat}"
            )

        lines += ["", "Assessment:", f"  {result.recommendation}"]
        return "\n".join(lines)

    def _themes_section(self) -> str:
        themes = list(self.analyzer.iter_themes())
        if not themes:
            return ""

        coverage = self.analyzer.coverage()
        lines = ["THEMES", SECTION, f"Total themes: {len(themes)}", ""]

        for theme in themes:
            status = "PROVISIONAL" if theme.is_provisional else "FINAL"
            cov = coverage.get(theme.name, {})
            lines += [
                f"THEME: {theme.name}  [{status}]",
                f"  Central concept: {theme.central_concept or '(not yet defined)'}",
                f"  Coverage: {cov.get('segments', 0)} segments across "
                f"{cov.get('documents', 0)} documents",
                f"  Grounding codes ({cov.get('codes', 0)}): "
                + ", ".join(
                    self.codebook.codes[cid].name
                    for cid in theme.code_ids
                    if cid in self.codebook.codes
                ),
            ]

            if theme.narrative:
                lines += ["", f"  Narrative:", f"    {theme.narrative}"]

            if theme.illustrative_quotes:
                lines += ["", "  Illustrative quotes:"]
                for q in theme.illustrative_quotes:
                    lines.append(f"    {q}")

            if theme.negative_cases:
                lines += ["", "  Negative/disconfirming cases:"]
                for nc in theme.negative_cases:
                    lines.append(f"    • {nc}")

            if theme.sub_themes:
                lines += ["", "  Sub-themes:"]
                for st in theme.sub_themes:
                    lines.append(f"    – {st.name}: {st.central_concept}")

            if theme.memos:
                lines += ["", "  Analytic memos:"]
                for m in theme.memos:
                    lines.append(f"    [{m}]")

            lines.append("")

        # Unthemed codes
        unthemed = self.analyzer.uncoded_code_names()
        if unthemed:
            lines += [
                "Codes not yet assigned to a theme:",
                "  " + ", ".join(unthemed),
            ]

        return "\n".join(lines)

    def _audit_section(self) -> str:
        if not self.audit:
            return ""

        summary = self.audit.summary()
        lines = [
            "AUDIT TRAIL SUMMARY",
            SECTION,
            "Decision log entry counts by type:",
        ]
        for entry_type, count in sorted(summary.items()):
            lines.append(f"  {entry_type:<35} {count:>4}")

        total = sum(summary.values())
        lines += ["", f"  Total entries: {total}"]
        return "\n".join(lines)

    def _reflexivity_section(self, coders: list | None) -> str:
        if not coders:
            return ""

        lines = ["RESEARCHER REFLEXIVITY", SECTION]
        for coder in coders:
            lines.append(f"Researcher: {coder.name} ({coder.role})")
            if coder.reflexivity_notes:
                for note in coder.reflexivity_notes:
                    lines.append(f"  {note}")
            else:
                lines.append(
                    "  [No reflexivity notes recorded. Use coder.add_reflexivity_note()]"
                )
            lines.append("")

        return "\n".join(lines)

    def _quality_section(self) -> str:
        warnings = self.analyzer.all_warnings()
        lines = ["QUALITY & CREDIBILITY CHECK", SECTION]

        if not warnings:
            lines.append(
                "All themes pass quality criteria (Braun & Clarke, 2006)."
            )
        else:
            lines.append(f"{len(warnings)} quality issue(s) require attention:")
            for w in warnings:
                lines.append(f"  ⚠  {w}")

        return "\n".join(lines)

    def _footer(self) -> str:
        return "\n".join([
            DIVIDER,
            "References",
            SECTION,
            "Braun, V. & Clarke, V. (2006). Using thematic analysis in psychology.",
            "  Qualitative Research in Psychology, 3(2), 77–101.",
            "Braun, V. & Clarke, V. (2019). Reflecting on reflexive thematic analysis.",
            "  Qualitative Research in Sport, Exercise and Health, 11(4), 589–597.",
            "Cohen, J. (1960). A coefficient of agreement for nominal scales.",
            "  Educational and Psychological Measurement, 20(1), 37–46.",
            "Glaser, B. & Strauss, A. (1967). The Discovery of Grounded Theory.",
            "Krippendorff, K. (2004). Content Analysis (2nd ed.).",
            "Landis, J. & Koch, G. (1977). The measurement of observer agreement.",
            "  Biometrics, 33(1), 159–174.",
            "Lincoln, Y. & Guba, E. (1985). Naturalistic Inquiry.",
            "O'Connor, C. & Joffe, H. (2020). Intercoder reliability in qualitative research.",
            "  International Journal of Qualitative Methods, 19.",
            "Saldaña, J. (2021). The Coding Manual for Qualitative Researchers (4th ed.).",
            "Saunders, B. et al. (2018). Saturation in qualitative research.",
            "  Quality & Quantity, 52, 1893–1907.",
            DIVIDER,
        ])
