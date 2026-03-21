"""
Audit Trail
===========
Implements Lincoln & Guba's (1985) audit trail for dependability and
confirmability. Every decision, code assignment, theme revision, and
memo is logged with timestamps, researcher identity, and rationale.

All entries are stored in SQLite for persistence and queryability.
"""

from __future__ import annotations

import sqlite3
import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any


class EntryType(str, Enum):
    PROJECT_CREATED   = "PROJECT_CREATED"
    DOCUMENT_ADDED    = "DOCUMENT_ADDED"
    CODE_CREATED      = "CODE_CREATED"
    CODE_REVISED      = "CODE_REVISED"
    CODE_MERGED       = "CODE_MERGED"
    CODE_DELETED      = "CODE_DELETED"
    SEGMENT_CODED     = "SEGMENT_CODED"
    SEGMENT_UNCODED   = "SEGMENT_UNCODED"
    THEME_CREATED     = "THEME_CREATED"
    THEME_REVISED     = "THEME_REVISED"
    THEME_MERGED      = "THEME_MERGED"
    MEMO_ADDED        = "MEMO_ADDED"
    REFLEXIVITY_ENTRY = "REFLEXIVITY_ENTRY"
    MEMBER_CHECK      = "MEMBER_CHECK"
    PEER_DEBRIEF      = "PEER_DEBRIEF"
    NEGATIVE_CASE     = "NEGATIVE_CASE"
    SATURATION_CHECK  = "SATURATION_CHECK"
    RELIABILITY_CHECK = "RELIABILITY_CHECK"
    REPORT_GENERATED  = "REPORT_GENERATED"


@dataclass
class AuditEntry:
    entry_type: EntryType
    researcher: str
    description: str
    rationale: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["entry_type"] = self.entry_type.value
        return d


class AuditTrail:
    """
    Persistent, queryable audit trail for a research project.

    Supports external audit (Lincoln & Guba, 1985) by providing a
    complete record of analytic decisions and their rationale.
    """

    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_entries (
                    entry_id   TEXT PRIMARY KEY,
                    entry_type TEXT NOT NULL,
                    researcher TEXT NOT NULL,
                    timestamp  TEXT NOT NULL,
                    description TEXT NOT NULL,
                    rationale  TEXT,
                    data       TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_type      ON audit_entries(entry_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_researcher ON audit_entries(researcher)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_entries(timestamp)
            """)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def log(
        self,
        entry_type: EntryType,
        researcher: str,
        description: str,
        rationale: str = "",
        data: dict | None = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            entry_type=entry_type,
            researcher=researcher,
            description=description,
            rationale=rationale,
            data=data or {},
        )
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO audit_entries
                   (entry_id, entry_type, researcher, timestamp, description, rationale, data)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    entry.entry_id,
                    entry.entry_type.value,
                    entry.researcher,
                    entry.timestamp,
                    entry.description,
                    entry.rationale,
                    json.dumps(entry.data),
                ),
            )
        return entry

    def query(
        self,
        entry_type: EntryType | None = None,
        researcher: str | None = None,
        since: str | None = None,
        limit: int = 500,
    ) -> list[AuditEntry]:
        clauses, params = [], []
        if entry_type:
            clauses.append("entry_type = ?")
            params.append(entry_type.value)
        if researcher:
            clauses.append("researcher = ?")
            params.append(researcher)
        if since:
            clauses.append("timestamp >= ?")
            params.append(since)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM audit_entries {where} ORDER BY timestamp DESC LIMIT ?",
                params,
            ).fetchall()

        return [self._row_to_entry(r) for r in rows]

    def _row_to_entry(self, row: tuple) -> AuditEntry:
        entry_id, entry_type, researcher, timestamp, description, rationale, data = row
        return AuditEntry(
            entry_id=entry_id,
            entry_type=EntryType(entry_type),
            researcher=researcher,
            timestamp=timestamp,
            description=description,
            rationale=rationale or "",
            data=json.loads(data or "{}"),
        )

    def all_entries(self) -> list[AuditEntry]:
        return self.query(limit=100_000)

    def summary(self) -> dict[str, int]:
        """Return count of each entry type — useful for audit overview."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT entry_type, COUNT(*) FROM audit_entries GROUP BY entry_type"
            ).fetchall()
        return {r[0]: r[1] for r in rows}
