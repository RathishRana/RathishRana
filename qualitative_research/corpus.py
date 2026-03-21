"""
Corpus Management
=================
Manages the body of qualitative data: transcripts, field notes,
documents, focus group records, and any textual source.

Each Document is segmented into Segments (the unit of analysis).
Segmentation strategies:
  - SENTENCE  — NLP sentence boundary detection
  - PARAGRAPH — blank-line delimited blocks
  - TURN      — interview turn (speaker-labelled lines)
  - MANUAL    — researcher-defined boundaries
  - LINE      — raw line-by-line

Thick description metadata is stored with every document to support
transferability (Lincoln & Guba, 1985).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterator


class SegmentationStrategy(str, Enum):
    SENTENCE  = "sentence"
    PARAGRAPH = "paragraph"
    TURN      = "turn"
    MANUAL    = "manual"
    LINE      = "line"


@dataclass
class Segment:
    """The atomic unit of analysis — a contiguous stretch of text."""

    segment_id: str
    document_id: str
    text: str
    index: int                              # position within document
    speaker: str | None = None              # for interview/focus-group turns
    metadata: dict = field(default_factory=dict)

    def word_count(self) -> int:
        return len(self.text.split())

    def char_count(self) -> int:
        return len(self.text)

    def __repr__(self) -> str:
        preview = self.text[:60].replace("\n", " ")
        return f"Segment({self.index}, '{preview}...')"


@dataclass
class Document:
    """
    A single source in the corpus with rich provenance metadata.

    Thick description fields support transferability judgements.
    """

    document_id: str
    title: str
    raw_text: str
    source_type: str                        # e.g. "interview", "focus_group", "field_note"
    participant_id: str | None = None
    collection_date: str | None = None      # ISO-8601 date
    context: str = ""                       # setting, circumstances
    researcher: str = ""                    # who collected this
    notes: str = ""                         # any collection notes
    metadata: dict = field(default_factory=dict)
    segments: list[Segment] = field(default_factory=list, repr=False)

    # ------------------------------------------------------------------ #
    #  Segmentation                                                         #
    # ------------------------------------------------------------------ #

    def segment(
        self, strategy: SegmentationStrategy = SegmentationStrategy.PARAGRAPH
    ) -> list[Segment]:
        if strategy == SegmentationStrategy.PARAGRAPH:
            self.segments = self._by_paragraph()
        elif strategy == SegmentationStrategy.SENTENCE:
            self.segments = self._by_sentence()
        elif strategy == SegmentationStrategy.TURN:
            self.segments = self._by_turn()
        elif strategy == SegmentationStrategy.LINE:
            self.segments = self._by_line()
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        return self.segments

    def _make_segment(self, text: str, index: int, speaker: str | None = None) -> Segment:
        return Segment(
            segment_id=str(uuid.uuid4()),
            document_id=self.document_id,
            text=text.strip(),
            index=index,
            speaker=speaker,
        )

    def _by_paragraph(self) -> list[Segment]:
        blocks = re.split(r"\n\s*\n", self.raw_text.strip())
        return [
            self._make_segment(b, i)
            for i, b in enumerate(blocks)
            if b.strip()
        ]

    def _by_sentence(self) -> list[Segment]:
        # Robust sentence splitter without requiring spaCy/NLTK
        pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"\'])")
        sentences = pattern.split(self.raw_text.strip())
        return [
            self._make_segment(s, i)
            for i, s in enumerate(sentences)
            if s.strip()
        ]

    def _by_turn(self) -> list[Segment]:
        """
        Parse interview/focus-group transcripts with speaker labels.
        Supported formats:
          INTERVIEWER: text
          [Interviewer]: text
          P1: text
        """
        pattern = re.compile(r"^(\[?[\w\s]+\]?):\s*(.+)", re.MULTILINE)
        turns = pattern.findall(self.raw_text)
        if turns:
            return [
                self._make_segment(text, i, speaker=speaker.strip("[]"))
                for i, (speaker, text) in enumerate(turns)
                if text.strip()
            ]
        # Fall back to paragraph if no turns detected
        return self._by_paragraph()

    def _by_line(self) -> list[Segment]:
        return [
            self._make_segment(line, i)
            for i, line in enumerate(self.raw_text.splitlines())
            if line.strip()
        ]

    # ------------------------------------------------------------------ #
    #  Convenience                                                          #
    # ------------------------------------------------------------------ #

    def word_count(self) -> int:
        return len(self.raw_text.split())

    def segment_count(self) -> int:
        return len(self.segments)

    def iter_segments(self) -> Iterator[Segment]:
        yield from self.segments


class Corpus:
    """
    The complete body of data for a research project.

    Manages documents, tracks purposive sampling decisions, and
    provides iteration over all segments across all documents.
    """

    def __init__(self, name: str):
        self.name = name
        self.documents: dict[str, Document] = {}
        self.sampling_notes: list[str] = []   # purposive sampling rationale

    # ------------------------------------------------------------------ #
    #  Document management                                                  #
    # ------------------------------------------------------------------ #

    def add_document(
        self,
        title: str,
        raw_text: str,
        source_type: str = "document",
        participant_id: str | None = None,
        collection_date: str | None = None,
        context: str = "",
        researcher: str = "",
        notes: str = "",
        segment_strategy: SegmentationStrategy = SegmentationStrategy.PARAGRAPH,
        metadata: dict | None = None,
    ) -> Document:
        doc = Document(
            document_id=str(uuid.uuid4()),
            title=title,
            raw_text=raw_text,
            source_type=source_type,
            participant_id=participant_id,
            collection_date=collection_date,
            context=context,
            researcher=researcher,
            notes=notes,
            metadata=metadata or {},
        )
        doc.segment(segment_strategy)
        self.documents[doc.document_id] = doc
        return doc

    def load_file(
        self,
        path: Path | str,
        source_type: str = "document",
        segment_strategy: SegmentationStrategy = SegmentationStrategy.PARAGRAPH,
        **kwargs,
    ) -> Document:
        path = Path(path)
        text = path.read_text(encoding="utf-8")
        return self.add_document(
            title=path.stem,
            raw_text=text,
            source_type=source_type,
            segment_strategy=segment_strategy,
            **kwargs,
        )

    def get_document(self, document_id: str) -> Document:
        return self.documents[document_id]

    def add_sampling_note(self, note: str) -> None:
        """Record purposive sampling rationale for transferability."""
        self.sampling_notes.append(note)

    # ------------------------------------------------------------------ #
    #  Iteration                                                            #
    # ------------------------------------------------------------------ #

    def iter_documents(self) -> Iterator[Document]:
        yield from self.documents.values()

    def iter_segments(self) -> Iterator[Segment]:
        for doc in self.iter_documents():
            yield from doc.iter_segments()

    def all_segments(self) -> list[Segment]:
        return list(self.iter_segments())

    def get_segment(self, segment_id: str) -> Segment | None:
        for seg in self.iter_segments():
            if seg.segment_id == segment_id:
                return seg
        return None

    # ------------------------------------------------------------------ #
    #  Stats                                                                #
    # ------------------------------------------------------------------ #

    def stats(self) -> dict:
        docs = list(self.documents.values())
        total_words = sum(d.word_count() for d in docs)
        total_segs  = sum(d.segment_count() for d in docs)
        source_types = {}
        for d in docs:
            source_types[d.source_type] = source_types.get(d.source_type, 0) + 1
        return {
            "document_count": len(docs),
            "total_words": total_words,
            "total_segments": total_segs,
            "source_types": source_types,
        }

    def __repr__(self) -> str:
        s = self.stats()
        return (
            f"Corpus('{self.name}', docs={s['document_count']}, "
            f"segments={s['total_segments']}, words={s['total_words']})"
        )
