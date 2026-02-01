import sqlite3
import threading
import os
import time

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    DB_PATH = "automation.db"

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._local = threading.local()
        self._init_db()

    def _get_conn(self):
        """Get thread-local connection."""
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.DB_PATH, timeout=30.0) # High timeout for safety
            self._local.conn.row_factory = sqlite3.Row
            
            # Enable WAL mode for concurrency
            self._local.conn.execute("PRAGMA journal_mode=WAL;")
            self._local.conn.execute("PRAGMA synchronous=NORMAL;")
        return self._local.conn

    def _init_db(self):
        """Initialize Schema."""
        conn = sqlite3.connect(self.DB_PATH)
        curr = conn.cursor()
        
        # 1. Senders Table
        # status: PENDING, USED, FAILED, BLOCKED, NOT_LOGINED, NEED_PREMIUM
        # rounds_completed: Tracks partial progress
        curr.execute("""
            CREATE TABLE IF NOT EXISTS senders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT,
                status TEXT,
                rounds_completed INTEGER DEFAULT 0,
                original_row INTEGER, -- To map back to Excel
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Recipients Table
        # status: AVAILABLE, USED, FAILED, PROCESSING
        curr.execute("""
            CREATE TABLE IF NOT EXISTS recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                status TEXT,
                original_row INTEGER, -- To map back to Excel
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index for speed
        curr.execute("CREATE INDEX IF NOT EXISTS idx_sender_status ON senders(status)")
        curr.execute("CREATE INDEX IF NOT EXISTS idx_recipient_status ON recipients(status)")
        
        conn.commit()
        conn.close()

    # ---------------------------------------------------
    # PUBLIC API
    # ---------------------------------------------------

    def execute(self, query, params=()):
        """Execute a write operation (INSERT/UPDATE/DELETE)."""
        conn = self._get_conn()
        try:
            with conn: # Auto-commit
                curr = conn.execute(query, params)
                return curr.lastrowid
        except Exception as e:
            print(f"❌ DB Execute Error: {e} | Query: {query}")
            raise

    def execute_many(self, query, params_list):
        """Bulk execute."""
        conn = self._get_conn()
        try:
            with conn:
                conn.executemany(query, params_list)
        except Exception as e:
            print(f"❌ DB Bulk Error: {e}")
            raise

    def fetch_one(self, query, params=()):
        """Fetch a single row."""
        conn = self._get_conn()
        curr = conn.cursor()
        curr.execute(query, params)
        return curr.fetchone()

    def fetch_all(self, query, params=()):
        """Fetch all rows."""
        conn = self._get_conn()
        curr = conn.cursor()
        curr.execute(query, params)
        return curr.fetchall()

    def close(self):
        """Close connection if open (called explicitly if needed)."""
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            del self._local.conn
