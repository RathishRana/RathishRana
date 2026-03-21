"""
Project
=======
Top-level façade that wires all components together.
This is the main entry point for researchers.

Workflow:
  project = Project("My Study")

  # Add data
  doc = project.add_interview("transcript.txt", participant_id="P1")

  # Code
  coder = project.add_coder("Dr Smith")
  coder.code(project.codebook, "financial stress", doc.segments[0].segment_id, ...)

  # Double-code for reliability
  coder2 = project.add_coder("Dr Jones")
  # ... (code same segments)
  rel = project.check_reliability()

  # Build themes
  project.analyzer.create_theme("Economic Precarity", ["financial stress", "job insecurity"])

  # Check saturation
  sat = project.check_saturation(document_order=[doc.document_id, ...])

  # Generate report
  project.generate_report("report.txt")
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .audit import AuditTrail, EntryType
from .coding import CodeBook, Coder
from .corpus import Corpus, Document, SegmentationStrategy
from .reliability import ReliabilityCalculator, ReliabilityReport
from .report import ReportGenerator
from .saturation import SaturationDetector, SaturationResult
from .themes import ThematicAnalyzer


class Project:
    """
    Unified research project — single object for a complete study.

    Manages all components and provides a clean, high-level API
    that enforces rigorous qualitative research practice.
    """

    def __init__(
        self,
        name: str,
        db_path: str | Path | None = None,
        lead_researcher: str = "Researcher",
    ):
        self.name = name
        self.lead_researcher = lead_researcher

        db_path = db_path or f"{name.replace(' ', '_').lower()}_audit.db"
        self.audit = AuditTrail(db_path)
        self.corpus = Corpus(name)
        self.codebook = CodeBook()
        self.analyzer = ThematicAnalyzer(self.codebook, researcher=lead_researcher)
        self.coders: dict[str, Coder] = {}

        self.audit.log(
            EntryType.PROJECT_CREATED,
            lead_researcher,
            f"Project '{name}' created.",
            data={"name": name},
        )

    # ------------------------------------------------------------------ #
    #  Corpus                                                               #
    # ------------------------------------------------------------------ #

    def add_interview(
        self,
        path_or_text: str | Path,
        participant_id: str | None = None,
        collection_date: str | None = None,
        context: str = "",
        notes: str = "",
        title: str = "Untitled Interview",
        strategy: SegmentationStrategy = SegmentationStrategy.TURN,
    ) -> Document:
        return self._add_document(
            path_or_text,
            source_type="interview",
            participant_id=participant_id,
            collection_date=collection_date,
            context=context,
            notes=notes,
            title=title,
            strategy=strategy,
        )

    def add_focus_group(
        self,
        path_or_text: str | Path,
        collection_date: str | None = None,
        context: str = "",
        notes: str = "",
    ) -> Document:
        return self._add_document(
            path_or_text,
            source_type="focus_group",
            collection_date=collection_date,
            context=context,
            notes=notes,
            strategy=SegmentationStrategy.TURN,
        )

    def add_field_note(
        self,
        path_or_text: str | Path,
        collection_date: str | None = None,
        context: str = "",
    ) -> Document:
        return self._add_document(
            path_or_text,
            source_type="field_note",
            collection_date=collection_date,
            context=context,
            strategy=SegmentationStrategy.PARAGRAPH,
        )

    def add_document(
        self,
        path_or_text: str | Path,
        source_type: str = "document",
        **kwargs,
    ) -> Document:
        return self._add_document(path_or_text, source_type=source_type, **kwargs)

    def _add_document(
        self,
        path_or_text: str | Path,
        source_type: str,
        strategy: SegmentationStrategy = SegmentationStrategy.PARAGRAPH,
        title: str = "Untitled",
        **kwargs,
    ) -> Document:
        s = str(path_or_text)
        p = Path(s)
        is_file = len(s) < 260 and p.exists()
        if is_file:
            doc = self.corpus.load_file(p, source_type=source_type, segment_strategy=strategy, title=title, **kwargs)
        else:
            # treat as raw text
            doc = self.corpus.add_document(
                title=title,
                raw_text=str(path_or_text),
                source_type=source_type,
                segment_strategy=strategy,
                **kwargs,
            )

        self.audit.log(
            EntryType.DOCUMENT_ADDED,
            self.lead_researcher,
            f"Added {source_type}: '{doc.title}'",
            data={
                "document_id": doc.document_id,
                "title": doc.title,
                "segments": doc.segment_count(),
                "words": doc.word_count(),
            },
        )
        return doc

    def add_sampling_note(self, note: str) -> None:
        """Record purposive sampling rationale."""
        self.corpus.add_sampling_note(note)

    # ------------------------------------------------------------------ #
    #  Coders                                                               #
    # ------------------------------------------------------------------ #

    def add_coder(self, name: str, role: str = "researcher") -> Coder:
        coder = Coder(name=name, role=role)
        self.coders[name] = coder
        return coder

    def get_coder(self, name: str) -> Coder:
        if name not in self.coders:
            raise KeyError(f"Coder '{name}' not found. Add with project.add_coder('{name}').")
        return self.coders[name]

    # ------------------------------------------------------------------ #
    #  Reliability                                                          #
    # ------------------------------------------------------------------ #

    def check_reliability(
        self,
        segment_ids: list[str] | None = None,
        raters: list[str] | None = None,
    ) -> ReliabilityReport:
        """
        Compute inter-rater reliability.
        Run this on a 15–20% random double-coded subsample before full analysis.
        """
        calc = ReliabilityCalculator(self.codebook)
        report = calc.calculate(segment_ids=segment_ids, raters=raters)

        self.audit.log(
            EntryType.RELIABILITY_CHECK,
            self.lead_researcher,
            f"Reliability check: α={report.krippendorffs_alpha:.4f}",
            rationale=report.recommendation,
            data={
                "alpha": report.krippendorffs_alpha,
                "pairwise_kappas": [
                    {"pair": f"{p.rater_a}×{p.rater_b}", "kappa": p.cohens_kappa}
                    for p in report.pairwise
                ],
            },
        )
        return report

    # ------------------------------------------------------------------ #
    #  Saturation                                                           #
    # ------------------------------------------------------------------ #

    def check_saturation(
        self,
        document_order: list[str] | None = None,
        window: int = 3,
        threshold: float = 0.05,
    ) -> SaturationResult:
        """
        Analyse theoretical saturation across documents.
        document_order: list of document_ids in collection order.
        Defaults to corpus document insertion order if omitted.
        """
        if document_order is None:
            document_order = list(self.corpus.documents.keys())

        detector = SaturationDetector(self.codebook, window=window, threshold=threshold)
        result = detector.analyse(document_order)

        self.audit.log(
            EntryType.SATURATION_CHECK,
            self.lead_researcher,
            f"Saturation check: reached={result.saturation_reached}",
            rationale=result.recommendation,
            data={
                "saturation_reached": result.saturation_reached,
                "at_document": result.saturation_document_index,
                "unique_codes": result.total_unique_codes,
            },
        )
        return result

    # ------------------------------------------------------------------ #
    #  Reporting                                                            #
    # ------------------------------------------------------------------ #

    def generate_report(
        self,
        output_path: str,
        fmt: str = "text",
        reliability_report: ReliabilityReport | None = None,
        saturation_result: SaturationResult | None = None,
    ) -> None:
        gen = ReportGenerator(
            project_name=self.name,
            corpus=self.corpus,
            codebook=self.codebook,
            analyzer=self.analyzer,
            audit=self.audit,
        )
        gen.save(
            output_path,
            fmt=fmt,
            reliability_report=reliability_report,
            saturation_result=saturation_result,
            coders=list(self.coders.values()),
        )

        self.audit.log(
            EntryType.REPORT_GENERATED,
            self.lead_researcher,
            f"Report generated: {output_path} ({fmt})",
        )

    # ------------------------------------------------------------------ #
    #  Convenience                                                          #
    # ------------------------------------------------------------------ #

    def summary(self) -> None:
        """Print a quick project overview."""
        cs = self.corpus.stats()
        themes = list(self.analyzer.iter_themes())
        print(f"\n{'='*60}")
        print(f"  PROJECT: {self.name}")
        print(f"{'='*60}")
        print(f"  Corpus:   {cs['document_count']} docs | {cs['total_words']:,} words | {cs['total_segments']} segments")
        print(f"  Codes:    {sum(1 for _ in self.codebook.iter_active())} active")
        print(f"  Themes:   {len(themes)} ({sum(1 for t in themes if not t.is_provisional)} final)")
        print(f"  Coders:   {list(self.coders.keys())}")
        audit_sum = self.audit.summary()
        print(f"  Audit:    {sum(audit_sum.values())} entries")
        print(f"{'='*60}\n")

    def __repr__(self) -> str:
        return (
            f"Project('{self.name}', "
            f"docs={len(self.corpus.documents)}, "
            f"codes={sum(1 for _ in self.codebook.iter_active())}, "
            f"themes={len(self.analyzer.themes)})"
        )
