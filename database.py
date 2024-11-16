import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Create tables
        c.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            timestamp TEXT,
            activity_type TEXT,
            duration INTEGER,
            details TEXT
        )''')

        c.execute('''
        CREATE TABLE IF NOT EXISTS fatigue_events (
            timestamp TEXT,
            event_type TEXT,
            confidence REAL,
            action_taken TEXT
        )''')

        conn.commit()
        conn.close()

    def log_activity(self, activity_type, duration, details=""):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO activity_logs VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), activity_type, duration, details)
        )
        conn.commit()
        conn.close()

    def log_fatigue_event(self, event_type, confidence, action_taken):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO fatigue_events VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), event_type, confidence, action_taken)
        )
        conn.commit()
        conn.close()