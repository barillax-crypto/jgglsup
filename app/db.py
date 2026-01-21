"""Database layer for user state and logs."""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import Config

logger = logging.getLogger(__name__)


class Database:
    """SQLite database wrapper."""

    def __init__(self, db_path: Path = Config.DB_PATH):
        """Initialize database."""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                language TEXT NOT NULL DEFAULT 'en',
                created_at TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                action TEXT NOT NULL,
                internal_sources TEXT,
                retrieval_scores TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            )
            """
        )

        conn.commit()
        conn.close()
        logger.info("Database schema initialized")

    def get_user(self, telegram_id: int) -> Optional[dict]:
        """Get user by telegram_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def set_user_language(self, telegram_id: int, language: str) -> None:
        """Create or update user (language param kept for compatibility, always uses en)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        existing = self.get_user(telegram_id)
        if existing:
            cursor.execute(
                "UPDATE users SET language = ? WHERE telegram_id = ?",
                ("en", telegram_id),
            )
        else:
            cursor.execute(
                "INSERT INTO users (telegram_id, language, created_at) VALUES (?, ?, ?)",
                (telegram_id, "en", now),
            )

        conn.commit()
        conn.close()

    def log_interaction(
        self,
        telegram_id: int,
        question: str,
        action: str,
        internal_sources: Optional[str] = None,
        retrieval_scores: Optional[str] = None,
    ) -> int:
        """Log a user interaction. Returns log ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO logs (telegram_id, question, action, internal_sources, retrieval_scores, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (telegram_id, question, action, internal_sources, retrieval_scores, now),
        )

        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return log_id

    def get_last_log(self, telegram_id: int) -> Optional[dict]:
        """Get the last log entry for a user (admin use only)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM logs WHERE telegram_id = ? ORDER BY created_at DESC LIMIT 1",
            (telegram_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None


def get_db() -> Database:
    """Get database instance."""
    return Database()
