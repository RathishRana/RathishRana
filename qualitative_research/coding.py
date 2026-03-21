"""
Coding Engine
=============
Implements multi-paradigm coding for qualitative research:

  DESCRIPTIVE  — what is happening (Miles & Huberman, 1994)
  IN_VIVO      — participant's own words as code label
  PROCESS      — gerund-form codes (Charmaz, 2006)
  EMOTION      — affective coding (Goleman; Saldaña, 2009)
  MAGNITUDE    — intensity/frequency qualifiers
  AXIAL        — relational codes linking categories (Strauss & Corbin)
  THEORETICAL  — abstract, concept-level codes (grounded theory)

Each CodeInstance records: who coded, when, with what rationale.
Memos can be attached to any code or instance for analytic depth.

Reference: Saldaña, J. (2021). The Coding Manual for Qualitative Researchers (4th ed.).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Iterator


class CodingParadigm(str, Enum):
    DESCRIPTIVE  = "descriptive"
    IN_VIVO      = "in_vivo"
    PROCESS      = "process"
    EMOTION      = "emotion"
    MAGNITUDE    = "magnitude"
    AXIAL        = "axial"
    THEORETICAL  = "theoretical"


@dataclass
class Code:
    """
    A named analytical construct applied to text segments.

    Includes definition, inclusion/exclusion criteria, and
    example anchors — hallmarks of rigorous codebook design
    (MacQueen et al., 1998).
    """

    code_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    definition: str = ""
    inclusion_criteria: str = ""
    exclusion_criteria: str = ""
    example_anchor: str = ""             # prototypical text example
    paradigm: CodingParadigm = CodingParadigm.DESCRIPTIVE
    parent_code_id: str | None = None    # for hierarchical code trees
    memos: list[str] = field(default_factory=list)
    created_by: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    revised_at: str | None = None
    is_active: bool = True

    def add_memo(self, memo: str) -> None:
        self.memos.append(memo)

    def revise(self, **kwargs) -> None:
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        self.revised_at = datetime.now(timezone.utc).isoformat()

    def is_child_of(self, parent_code_id: str) -> bool:
        return self.parent_code_id == parent_code_id

    def __repr__(self) -> str:
        return f"Code('{self.name}', {self.paradigm.value})"


@dataclass
class CodeInstance:
    """
    A single application of a Code to a Segment.

    Records full provenance: researcher, timestamp, rationale,
    and an optional disconfirming note (for negative case analysis).
    """

    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    code_id: str = ""
    segment_id: str = ""
    document_id: str = ""
    researcher: str = ""
    rationale: str = ""
    disconfirming_note: str = ""         # for negative case analysis
    weight: float = 1.0                  # 0–1 confidence weight
    coded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    memo: str = ""

    def __repr__(self) -> str:
        return f"CodeInstance(code={self.code_id[:8]}, seg={self.segment_id[:8]})"


class CodeBook:
    """
    The master code dictionary for a research project.

    Supports:
    - Hierarchical code trees (parent/child)
    - Code merging with audit trail
    - Retrieval by name, paradigm, or parent
    - Export for inter-rater reliability setup
    """

    def __init__(self):
        self.codes: dict[str, Code] = {}
        self.instances: list[CodeInstance] = []

    # ------------------------------------------------------------------ #
    #  Code management                                                      #
    # ------------------------------------------------------------------ #

    def create_code(
        self,
        name: str,
        definition: str = "",
        inclusion_criteria: str = "",
        exclusion_criteria: str = "",
        example_anchor: str = "",
        paradigm: CodingParadigm = CodingParadigm.DESCRIPTIVE,
        parent_code_id: str | None = None,
        created_by: str = "",
    ) -> Code:
        # Prevent duplicate names (case-insensitive)
        if self.find_by_name(name):
            raise ValueError(f"Code '{name}' already exists. Use revise() to update.")

        code = Code(
            name=name,
            definition=definition,
            inclusion_criteria=inclusion_criteria,
            exclusion_criteria=exclusion_criteria,
            example_anchor=example_anchor,
            paradigm=paradigm,
            parent_code_id=parent_code_id,
            created_by=created_by,
        )
        self.codes[code.code_id] = code
        return code

    def get_code(self, code_id: str) -> Code:
        return self.codes[code_id]

    def find_by_name(self, name: str) -> Code | None:
        name_lower = name.lower()
        return next(
            (c for c in self.codes.values() if c.name.lower() == name_lower and c.is_active),
            None,
        )

    def get_or_create(self, name: str, created_by: str = "", **kwargs) -> Code:
        existing = self.find_by_name(name)
        return existing or self.create_code(name, created_by=created_by, **kwargs)

    def merge_codes(
        self, source_name: str, target_name: str, rationale: str = ""
    ) -> Code:
        """
        Merge source into target: re-assign all instances and deactivate source.
        Returns the surviving target code.
        """
        source = self.find_by_name(source_name)
        target = self.find_by_name(target_name)
        if not source or not target:
            raise ValueError("Both source and target codes must exist.")

        for inst in self.instances:
            if inst.code_id == source.code_id:
                inst.code_id = target.code_id

        source.is_active = False
        target.memos.append(f"Merged from '{source_name}': {rationale}")
        return target

    def iter_active(self) -> Iterator[Code]:
        yield from (c for c in self.codes.values() if c.is_active)

    def children_of(self, parent_code_id: str) -> list[Code]:
        return [c for c in self.codes.values() if c.parent_code_id == parent_code_id]

    def top_level_codes(self) -> list[Code]:
        return [c for c in self.codes.values() if c.parent_code_id is None and c.is_active]

    # ------------------------------------------------------------------ #
    #  Instance management                                                  #
    # ------------------------------------------------------------------ #

    def apply_code(
        self,
        code: Code | str,
        segment_id: str,
        document_id: str,
        researcher: str,
        rationale: str = "",
        weight: float = 1.0,
        memo: str = "",
        disconfirming_note: str = "",
    ) -> CodeInstance:
        if isinstance(code, str):
            code = self.find_by_name(code) or self.get_code(code)

        # Prevent duplicate coding of same segment by same researcher
        if self._already_coded(code.code_id, segment_id, researcher):
            raise ValueError(
                f"Researcher '{researcher}' already applied '{code.name}' "
                f"to segment {segment_id[:8]}. Remove first to recode."
            )

        inst = CodeInstance(
            code_id=code.code_id,
            segment_id=segment_id,
            document_id=document_id,
            researcher=researcher,
            rationale=rationale,
            weight=weight,
            memo=memo,
            disconfirming_note=disconfirming_note,
        )
        self.instances.append(inst)
        return inst

    def remove_code(
        self, code_id: str, segment_id: str, researcher: str
    ) -> bool:
        before = len(self.instances)
        self.instances = [
            i for i in self.instances
            if not (
                i.code_id == code_id
                and i.segment_id == segment_id
                and i.researcher == researcher
            )
        ]
        return len(self.instances) < before

    def _already_coded(
        self, code_id: str, segment_id: str, researcher: str
    ) -> bool:
        return any(
            i.code_id == code_id
            and i.segment_id == segment_id
            and i.researcher == researcher
            for i in self.instances
        )

    # ------------------------------------------------------------------ #
    #  Retrieval                                                            #
    # ------------------------------------------------------------------ #

    def instances_for_segment(self, segment_id: str) -> list[CodeInstance]:
        return [i for i in self.instances if i.segment_id == segment_id]

    def instances_for_code(self, code_id: str) -> list[CodeInstance]:
        return [i for i in self.instances if i.code_id == code_id]

    def instances_for_researcher(self, researcher: str) -> list[CodeInstance]:
        return [i for i in self.instances if i.researcher == researcher]

    def instances_for_document(self, document_id: str) -> list[CodeInstance]:
        return [i for i in self.instances if i.document_id == document_id]

    def code_frequency(self) -> dict[str, int]:
        """Return code name → application count, sorted descending."""
        freq: dict[str, int] = {}
        for inst in self.instances:
            code = self.codes.get(inst.code_id)
            if code:
                freq[code.name] = freq.get(code.name, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))

    def segments_per_code(self) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {}
        for inst in self.instances:
            code = self.codes.get(inst.code_id)
            if code:
                result.setdefault(code.name, set()).add(inst.segment_id)
        return result

    # ------------------------------------------------------------------ #
    #  Export                                                               #
    # ------------------------------------------------------------------ #

    def export_codebook(self) -> list[dict]:
        """Export full codebook as list of dicts (for PDF/Excel reporting)."""
        result = []
        for code in self.iter_active():
            children = self.children_of(code.code_id)
            result.append({
                "code_id": code.code_id,
                "name": code.name,
                "paradigm": code.paradigm.value,
                "definition": code.definition,
                "inclusion_criteria": code.inclusion_criteria,
                "exclusion_criteria": code.exclusion_criteria,
                "example_anchor": code.example_anchor,
                "frequency": len(self.instances_for_code(code.code_id)),
                "child_codes": [c.name for c in children],
                "memos": code.memos,
            })
        return result

    def __repr__(self) -> str:
        active = sum(1 for c in self.codes.values() if c.is_active)
        return f"CodeBook(active_codes={active}, instances={len(self.instances)})"


class Coder:
    """
    A researcher persona that applies codes with consistent identity tracking.

    Using named coders is essential for inter-rater reliability calculations.
    """

    def __init__(self, name: str, role: str = "researcher"):
        self.name = name
        self.role = role
        self.reflexivity_notes: list[str] = []

    def code(
        self,
        codebook: CodeBook,
        code_name: str,
        segment_id: str,
        document_id: str,
        rationale: str = "",
        weight: float = 1.0,
        memo: str = "",
    ) -> CodeInstance:
        code = codebook.get_or_create(code_name, created_by=self.name)
        return codebook.apply_code(
            code=code,
            segment_id=segment_id,
            document_id=document_id,
            researcher=self.name,
            rationale=rationale,
            weight=weight,
            memo=memo,
        )

    def add_reflexivity_note(self, note: str) -> None:
        """
        Record researcher reflexivity — how positionality, assumptions,
        and prior knowledge may influence analysis (Lincoln & Guba, 1985).
        """
        self.reflexivity_notes.append(
            f"[{datetime.now(timezone.utc).isoformat()}] {note}"
        )

    def __repr__(self) -> str:
        return f"Coder('{self.name}', role='{self.role}')"
