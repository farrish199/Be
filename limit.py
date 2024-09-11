import sqlite3
from datetime import datetime

DB_PATH = 'your_database_path.db'  # Gantikan dengan laluan sebenar kepada pangkalan data anda

def set_daily_limit(user_id: int, feature: str, limit: int) -> None:
    """Tetapkan had harian untuk fungsi tertentu bagi pengguna versi percuma tertentu."""
    today = datetime.now().date()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_usage (user_id, feature, usage, limit, last_updated)
            VALUES (?, ?, 0, ?, ?)
            ON CONFLICT(user_id, feature) DO UPDATE SET
                limit = ?,
                last_updated = ?
            WHERE user_id = ? AND feature = ?
        """, (user_id, feature, limit, today, limit, today, user_id, feature))
        conn.commit()
