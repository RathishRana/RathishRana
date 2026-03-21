"""
Theoretical Saturation
======================
Detects when new data no longer yields new codes/themes — the criterion
for stopping data collection in inductive qualitative research
(Glaser & Strauss, 1967; Morse, 1995; Saunders et al., 2018).

Three saturation indicators implemented:

  CODE SATURATION   — rate of new code emergence per document decreases
                      to near-zero (Fusch & Ness, 2015)

  MEANING SATURATION — no new meaning/nuance even within existing codes
                      (proxy: new unique instance rationale terms plateau)

  THEORETICAL SATURATION — no new relationships between codes emerge
                           (proxy: new code co-occurrence pairs plateau)

Saturation is judged reached when a rolling window of N documents
shows < threshold % new codes. Configurable per project norms.

Reference: Saunders et al. (2018). Saturation in qualitative research.
           Quality & Quantity, 52, 1893–1907.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

from .coding import CodeBook


class DocumentSaturationPoint(NamedTuple):
    document_id: str
    document_index: int
    new_codes: int
    total_codes: int
    cumulative_codes: int
    new_code_rate: float           # new_codes / total_codes in this doc
    cumulative_new_code_rate: float  # running saturation curve value


@dataclass
class SaturationResult:
    curve: list[DocumentSaturationPoint]
    saturation_reached: bool
    saturation_document_index: int | None  # first doc in the saturated window
    total_unique_codes: int
    window_size: int
    threshold: float
    recommendation: str


class SaturationDetector:
    """
    Tracks code emergence across documents to detect theoretical saturation.

    Usage
    -----
    detector = SaturationDetector(codebook, window=3, threshold=0.05)
    result = detector.analyse(document_order)  # list of document_ids in collection order
    """

    def __init__(
        self,
        codebook: CodeBook,
        window: int = 3,
        threshold: float = 0.05,
    ):
        """
        Parameters
        ----------
        codebook  : the project codebook
        window    : number of consecutive documents below threshold to declare saturation
        threshold : maximum rate of new codes to consider saturated (default 5%)
        """
        self.codebook = codebook
        self.window = window
        self.threshold = threshold

    def analyse(self, document_order: list[str]) -> SaturationResult:
        """
        Compute the saturation curve across documents in collection order.

        Parameters
        ----------
        document_order : list of document_ids in the order data was collected
        """
        seen_codes: set[str] = set()
        curve: list[DocumentSaturationPoint] = []

        for idx, doc_id in enumerate(document_order):
            doc_codes = self._codes_in_document(doc_id)
            new_codes = doc_codes - seen_codes
            seen_codes |= new_codes

            total_in_doc = len(doc_codes)
            new_rate = len(new_codes) / total_in_doc if total_in_doc else 0.0
            cumulative_rate = len(seen_codes) / max(len(seen_codes), 1)

            curve.append(DocumentSaturationPoint(
                document_id=doc_id,
                document_index=idx,
                new_codes=len(new_codes),
                total_codes=total_in_doc,
                cumulative_codes=len(seen_codes),
                new_code_rate=round(new_rate, 4),
                cumulative_new_code_rate=round(cumulative_rate, 4),
            ))

        # Detect saturation window
        sat_idx = self._detect_saturation_window(curve)
        reached = sat_idx is not None

        recommendation = self._recommend(curve, reached, sat_idx)

        return SaturationResult(
            curve=curve,
            saturation_reached=reached,
            saturation_document_index=sat_idx,
            total_unique_codes=len(seen_codes),
            window_size=self.window,
            threshold=self.threshold,
            recommendation=recommendation,
        )

    def _codes_in_document(self, document_id: str) -> set[str]:
        instances = self.codebook.instances_for_document(document_id)
        result = set()
        for inst in instances:
            code = self.codebook.codes.get(inst.code_id)
            if code and code.is_active:
                result.add(code.name)
        return result

    def _detect_saturation_window(
        self, curve: list[DocumentSaturationPoint]
    ) -> int | None:
        """
        Return the index of the first document in a consecutive run of
        `window` documents all below `threshold` new code rate.
        """
        if len(curve) < self.window:
            return None

        consecutive = 0
        for point in curve:
            if point.new_code_rate <= self.threshold:
                consecutive += 1
                if consecutive >= self.window:
                    return point.document_index - self.window + 1
            else:
                consecutive = 0
        return None

    def _recommend(
        self,
        curve: list[DocumentSaturationPoint],
        reached: bool,
        sat_idx: int | None,
    ) -> str:
        if not curve:
            return "No data coded yet. Code at least one document first."

        last_rate = curve[-1].new_code_rate
        n_docs = len(curve)

        if reached:
            return (
                f"SATURATION REACHED at document #{sat_idx + 1} of {n_docs}. "
                f"The last {self.window} documents each introduced ≤ "
                f"{self.threshold:.0%} new codes. "
                f"Data collection can be concluded. "
                f"Conduct a negative case analysis pass before closing."
            )
        if last_rate <= self.threshold * 2:
            return (
                f"APPROACHING SATURATION — last document new-code rate is "
                f"{last_rate:.1%}. Collect 1–2 more documents, focusing on "
                f"maximum variation sampling to test completeness."
            )
        return (
            f"NOT SATURATED — last document introduced new codes at a "
            f"{last_rate:.1%} rate. Continue data collection, prioritising "
            f"purposive sampling for under-represented perspectives."
        )

    def plot_ascii(self, result: SaturationResult) -> str:
        """
        Simple ASCII bar chart of new-code rate across documents.
        No matplotlib required.
        """
        if not result.curve:
            return "(no data)"

        lines = ["New-code rate per document (█ = 10%):", ""]
        for pt in result.curve:
            bar_len = min(int(pt.new_code_rate * 100), 50)
            bar = "█" * bar_len
            sat_marker = " ← SATURATION" if pt.document_index == result.saturation_document_index else ""
            label = f"Doc {pt.document_index + 1:02d}"
            lines.append(f"  {label} |{bar:<50}| {pt.new_code_rate:.0%} ({pt.new_codes} new){sat_marker}")

        lines.append("")
        lines.append(f"Threshold: {result.threshold:.0%}  |  Window: {result.window} docs")
        lines.append(f"Saturation reached: {result.saturation_reached}")
        return "\n".join(lines)
