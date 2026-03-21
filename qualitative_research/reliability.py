"""
Inter-Rater Reliability
========================
Implements gold-standard reliability metrics for qualitative coding:

  COHEN'S KAPPA        — pairwise agreement corrected for chance
                         (Cohen, 1960; κ ≥ 0.80 = strong agreement)

  KRIPPENDORFF'S ALPHA — generalised multi-rater, multi-level metric
                         (Krippendorff, 2004; α ≥ 0.80 = reliable)

  PERCENTAGE AGREEMENT — simple overlap, reported alongside κ/α

  SCOTTS PI            — alternative chance-correction (Scott, 1955)

Discrepancy analysis identifies which codes/segments disagree most,
directing training and calibration (O'Connor & Joffe, 2020).

Usage: run reliability checks BEFORE full analysis (calibration phase)
and AFTER (confirmability check). Both runs are logged to the audit trail.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import NamedTuple

from .coding import CodeBook


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

class PairResult(NamedTuple):
    rater_a: str
    rater_b: str
    cohens_kappa: float
    scotts_pi: float
    percent_agreement: float
    n_segments: int
    n_agreed: int
    interpretation: str


@dataclass
class ReliabilityReport:
    pairwise: list[PairResult]
    krippendorffs_alpha: float
    overall_percent_agreement: float
    discrepancies: list[dict]           # segments where raters disagreed
    recommendation: str


# ─────────────────────────────────────────────────────────────────────────────
# Interpretation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _interpret_kappa(k: float) -> str:
    """Landis & Koch (1977) kappa benchmarks."""
    if k < 0:   return "Poor (worse than chance)"
    if k < 0.2: return "Slight"
    if k < 0.4: return "Fair"
    if k < 0.6: return "Moderate"
    if k < 0.8: return "Substantial"
    return "Almost Perfect"


def _recommend(alpha: float, min_pair_kappa: float) -> str:
    if alpha >= 0.80 and min_pair_kappa >= 0.80:
        return (
            "PASS — reliability meets the α ≥ 0.80 and κ ≥ 0.80 thresholds "
            "recommended by Krippendorff (2004) and Landis & Koch (1977). "
            "Proceed to full analysis."
        )
    if alpha >= 0.67:
        return (
            "MARGINAL — α ≥ 0.67 may be acceptable for exploratory work "
            "(Krippendorff, 2004) but calibration sessions are recommended "
            "before publishing findings."
        )
    return (
        "FAIL — reliability is below acceptable thresholds. "
        "Conduct calibration sessions, review code definitions, add inclusion/"
        "exclusion criteria and anchor examples, then re-code a fresh sample."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Core calculator
# ─────────────────────────────────────────────────────────────────────────────

class ReliabilityCalculator:
    """
    Calculates inter-rater reliability across two or more coders.

    Works on any segment set — typically a 15–20% random double-coded
    subsample (O'Connor & Joffe, 2020).
    """

    def __init__(self, codebook: CodeBook):
        self.codebook = codebook

    # ------------------------------------------------------------------ #
    #  Public API                                                           #
    # ------------------------------------------------------------------ #

    def calculate(
        self,
        segment_ids: list[str] | None = None,
        raters: list[str] | None = None,
    ) -> ReliabilityReport:
        """
        Compute full reliability report.

        Parameters
        ----------
        segment_ids : optional subset of segments to evaluate
        raters      : optional subset of researcher names to include
        """
        rating_matrix = self._build_rating_matrix(segment_ids, raters)
        actual_raters = list(rating_matrix.keys())

        if len(actual_raters) < 2:
            raise ValueError(
                "At least 2 raters must have coded the same segments. "
                "Ensure double-coding is complete before running reliability."
            )

        # Pairwise metrics
        pairwise = []
        for ra, rb in combinations(actual_raters, 2):
            pairwise.append(self._pair_result(ra, rb, rating_matrix))

        # Krippendorff's alpha (all raters jointly)
        alpha = self._krippendorffs_alpha(rating_matrix)

        # Overall percent agreement
        all_agreed = sum(p.n_agreed for p in pairwise)
        all_segs   = sum(p.n_segments for p in pairwise)
        overall_pa = all_agreed / all_segs if all_segs else 0.0

        # Discrepancy analysis
        discrepancies = self._find_discrepancies(rating_matrix)

        # Recommendation
        min_kappa = min(p.cohens_kappa for p in pairwise)
        recommendation = _recommend(alpha, min_kappa)

        return ReliabilityReport(
            pairwise=pairwise,
            krippendorffs_alpha=alpha,
            overall_percent_agreement=overall_pa,
            discrepancies=discrepancies,
            recommendation=recommendation,
        )

    # ------------------------------------------------------------------ #
    #  Rating matrix                                                        #
    # ------------------------------------------------------------------ #

    def _build_rating_matrix(
        self,
        segment_ids: list[str] | None,
        raters: list[str] | None,
    ) -> dict[str, dict[str, set[str]]]:
        """
        Returns: { researcher: { segment_id: {code_names} } }
        """
        matrix: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

        for inst in self.codebook.instances:
            if raters and inst.researcher not in raters:
                continue
            if segment_ids and inst.segment_id not in segment_ids:
                continue
            code = self.codebook.codes.get(inst.code_id)
            if code:
                matrix[inst.researcher][inst.segment_id].add(code.name)

        return {r: dict(segs) for r, segs in matrix.items()}

    # ------------------------------------------------------------------ #
    #  Cohen's Kappa                                                        #
    # ------------------------------------------------------------------ #

    def _pair_result(
        self,
        ra: str,
        rb: str,
        matrix: dict[str, dict[str, set[str]]],
    ) -> PairResult:
        segs_a = matrix[ra]
        segs_b = matrix[rb]
        shared = set(segs_a) & set(segs_b)

        if not shared:
            raise ValueError(
                f"Raters '{ra}' and '{rb}' coded no segments in common."
            )

        # Build flat binary vectors per code
        all_codes = sorted(
            {c for s in shared for c in segs_a.get(s, set()) | segs_b.get(s, set())}
        )

        # Observed agreement (Po)
        agreements = sum(
            1
            for seg in shared
            if segs_a.get(seg, set()) == segs_b.get(seg, set())
        )
        n = len(shared)
        po = agreements / n

        kappa = self._cohen_kappa_from_vectors(
            [segs_a.get(s, set()) for s in shared],
            [segs_b.get(s, set()) for s in shared],
            all_codes,
        )
        pi = self._scotts_pi_from_vectors(
            [segs_a.get(s, set()) for s in shared],
            [segs_b.get(s, set()) for s in shared],
            all_codes,
        )

        return PairResult(
            rater_a=ra,
            rater_b=rb,
            cohens_kappa=round(kappa, 4),
            scotts_pi=round(pi, 4),
            percent_agreement=round(po, 4),
            n_segments=n,
            n_agreed=agreements,
            interpretation=_interpret_kappa(kappa),
        )

    def _cohen_kappa_from_vectors(
        self,
        labels_a: list[set[str]],
        labels_b: list[set[str]],
        all_codes: list[str],
    ) -> float:
        """Multi-label Cohen's kappa using per-code binary agreement."""
        if not all_codes:
            return 1.0

        po_sum, pe_sum = 0.0, 0.0
        n = len(labels_a)

        for code in all_codes:
            a_pos = sum(1 for s in labels_a if code in s)
            b_pos = sum(1 for s in labels_b if code in s)
            agree = sum(
                1
                for sa, sb in zip(labels_a, labels_b)
                if (code in sa) == (code in sb)
            )
            po_sum += agree / n
            # Expected agreement for this code
            p_a_yes = a_pos / n
            p_b_yes = b_pos / n
            pe_sum += (p_a_yes * p_b_yes) + ((1 - p_a_yes) * (1 - p_b_yes))

        po = po_sum / len(all_codes)
        pe = pe_sum / len(all_codes)
        if pe == 1.0:
            return 1.0
        return (po - pe) / (1 - pe)

    def _scotts_pi_from_vectors(
        self,
        labels_a: list[set[str]],
        labels_b: list[set[str]],
        all_codes: list[str],
    ) -> float:
        """Scott's Pi — uses joint marginals rather than separate ones."""
        if not all_codes:
            return 1.0

        n = len(labels_a)
        po_sum, pe_sum = 0.0, 0.0

        for code in all_codes:
            agree = sum(
                1
                for sa, sb in zip(labels_a, labels_b)
                if (code in sa) == (code in sb)
            )
            total_yes = sum(1 for s in labels_a if code in s) + sum(1 for s in labels_b if code in s)
            joint_p_yes = total_yes / (2 * n)
            po_sum += agree / n
            pe_sum += joint_p_yes ** 2 + (1 - joint_p_yes) ** 2

        po = po_sum / len(all_codes)
        pe = pe_sum / len(all_codes)
        if pe == 1.0:
            return 1.0
        return (po - pe) / (1 - pe)

    # ------------------------------------------------------------------ #
    #  Krippendorff's Alpha                                                 #
    # ------------------------------------------------------------------ #

    def _krippendorffs_alpha(
        self,
        matrix: dict[str, dict[str, set[str]]],
    ) -> float:
        """
        Nominal Krippendorff's Alpha for multi-rater, multi-label coding.

        Uses the binary decomposition approach — one binary variable per
        code, then average alpha across codes.

        Reference: Krippendorff (2004), pp. 221–229.
        """
        all_segs = sorted({seg for rater in matrix.values() for seg in rater})
        all_codes = sorted({
            c
            for rater in matrix.values()
            for codes in rater.values()
            for c in codes
        })

        if not all_codes or len(matrix) < 2:
            return float("nan")

        alphas = []
        for code in all_codes:
            alpha = self._alpha_for_code(code, matrix, all_segs)
            if not math.isnan(alpha):
                alphas.append(alpha)

        return round(sum(alphas) / len(alphas), 4) if alphas else float("nan")

    def _alpha_for_code(
        self,
        code: str,
        matrix: dict[str, dict[str, set[str]]],
        all_segs: list[str],
    ) -> float:
        # Build reliability data matrix: raters × units (binary present/absent)
        raters = sorted(matrix.keys())
        data: dict[str, dict[str, int | None]] = {
            r: {s: (1 if code in matrix[r].get(s, set()) else 0) for s in all_segs}
            for r in raters
        }

        # Count coincidences
        n_units = len(all_segs)
        n_values = sum(
            1
            for s in all_segs
            for r in raters
            if data[r][s] is not None
        )
        if n_values == 0:
            return float("nan")

        # Observed disagreement (Do)
        do = 0.0
        n_pairs = 0
        for s in all_segs:
            coded_by = [r for r in raters if data[r].get(s) is not None]
            for r1, r2 in combinations(coded_by, 2):
                v1, v2 = data[r1][s], data[r2][s]
                do += (v1 - v2) ** 2
                n_pairs += 1

        if n_pairs == 0:
            return float("nan")
        do /= n_pairs

        # Expected disagreement (De) from value distribution
        all_values = [
            data[r][s]
            for s in all_segs
            for r in raters
            if data[r].get(s) is not None
        ]
        n_v = len(all_values)
        if n_v < 2:
            return float("nan")

        de = sum(
            (all_values[i] - all_values[j]) ** 2
            for i in range(n_v)
            for j in range(i + 1, n_v)
        ) / (n_v * (n_v - 1) / 2)

        if de == 0:
            return 1.0

        return 1.0 - (do / de)

    # ------------------------------------------------------------------ #
    #  Discrepancy analysis                                                 #
    # ------------------------------------------------------------------ #

    def _find_discrepancies(
        self,
        matrix: dict[str, dict[str, set[str]]],
    ) -> list[dict]:
        """
        Identify segments where raters disagreed — for calibration sessions.
        Returns sorted by disagreement severity (most discrepant first).
        """
        raters = sorted(matrix.keys())
        all_segs = sorted({seg for r in matrix.values() for seg in r})
        discrepancies = []

        for seg in all_segs:
            codings = {r: matrix[r].get(seg, set()) for r in raters}
            unique_codings = list(codings.values())
            if len(set(frozenset(c) for c in unique_codings)) > 1:
                discrepancies.append({
                    "segment_id": seg,
                    "codings": {r: sorted(v) for r, v in codings.items()},
                    "disagreement_count": len(set(frozenset(c) for c in unique_codings)) - 1,
                })

        return sorted(discrepancies, key=lambda x: x["disagreement_count"], reverse=True)
