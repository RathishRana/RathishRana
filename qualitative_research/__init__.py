"""
Qualitative Research Toolkit
=============================
A rigorous, credible qualitative research system grounded in:
  - Lincoln & Guba (1985) trustworthiness criteria
  - Braun & Clarke (2006, 2019) reflexive thematic analysis
  - Glaser & Strauss grounded theory coding
  - Morse et al. saturation theory
  - Krippendorff & Cohen inter-rater reliability standards

Credibility pillars implemented:
  CREDIBILITY     — triangulation, member checking, negative case analysis
  TRANSFERABILITY — thick description, purposive sampling records
  DEPENDABILITY   — full audit trail, decision log
  CONFIRMABILITY  — reflexivity journal, external audit support
"""

from .project import Project
from .corpus import Corpus, Document, Segment
from .coding import CodeBook, Coder, Code, CodeInstance
from .themes import ThematicAnalyzer, Theme
from .reliability import ReliabilityCalculator
from .saturation import SaturationDetector
from .audit import AuditTrail
from .report import ReportGenerator

__version__ = "1.0.0"
__all__ = [
    "Project",
    "Corpus",
    "Document",
    "Segment",
    "CodeBook",
    "Coder",
    "Code",
    "CodeInstance",
    "ThematicAnalyzer",
    "Theme",
    "ReliabilityCalculator",
    "SaturationDetector",
    "AuditTrail",
    "ReportGenerator",
]
