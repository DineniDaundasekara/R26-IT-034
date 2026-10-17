"""SQLite persistence for past career risk / industry stability assessments."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DB_PATH = Path(__file__).resolve().parent / "assessment_history.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                role TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                profile_json TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_assessment(profile: dict[str, Any], result: dict[str, Any]) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    role = str(profile.get("role") or "Unknown")
    risk_level = str(
        (result.get("modelPrediction") or {}).get("value") or "Unknown"
    )

    with _connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO assessments (
                created_at, role, risk_level, profile_json, result_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                created_at,
                role,
                risk_level,
                json.dumps(profile),
                json.dumps(result),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)


def list_assessments(limit: int = 50) -> list[dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, role, risk_level
            FROM assessments
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [
        {
            "id": row["id"],
            "createdAt": row["created_at"],
            "role": row["role"],
            "riskLevel": row["risk_level"],
        }
        for row in rows
    ]


def get_assessment(assessment_id: int) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT id, created_at, role, risk_level, profile_json, result_json
            FROM assessments
            WHERE id = ?
            """,
            (assessment_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "createdAt": row["created_at"],
        "role": row["role"],
        "riskLevel": row["risk_level"],
        "profile": json.loads(row["profile_json"]),
        "result": json.loads(row["result_json"]),
    }


def delete_assessment(assessment_id: int) -> bool:
    with _connect() as conn:
        cursor = conn.execute(
            "DELETE FROM assessments WHERE id = ?",
            (assessment_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
