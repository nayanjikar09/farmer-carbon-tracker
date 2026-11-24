import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")

# ensure data/ exists once at import time
os.makedirs(DATA_DIR, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    """Return a configured SQLite connection."""
    conn = sqlite3.connect(
        DB_PATH,
        timeout=10,                    # wait up to 10s if locked
        check_same_thread=False,       # safe for FastAPI thread pool
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")     # concurrent reads + writes
    conn.execute("PRAGMA synchronous=NORMAL;")   # safe with WAL, faster
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=10000;")   # 10s busy timeout
    return conn


def init_db() -> None:
    """Create tables + indexes. Idempotent — safe to call every startup."""
    conn = get_conn()
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS farmers (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          village TEXT NOT NULL,
          acres REAL NOT NULL,
          crop TEXT NOT NULL,
          gps_lat REAL,
          gps_lng REAL,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS collections (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          farmer_id INTEGER NOT NULL,
          waste_quantity_tonnes REAL NOT NULL,
          collection_date TEXT NOT NULL,
          actual_weight_tonnes REAL,
          payment_inr REAL,
          estimated_cost_inr REAL,
          status TEXT DEFAULT 'Pending',
          FOREIGN KEY (farmer_id) REFERENCES farmers(id)
        );

        CREATE TABLE IF NOT EXISTS production_batches (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          collection_id INTEGER,
          biomass_input_tonnes REAL NOT NULL,
          biochar_output_tonnes REAL NOT NULL,
          carbon_stored_tonnes REAL,
          batch_date TEXT NOT NULL,
          FOREIGN KEY (collection_id) REFERENCES collections(id)
        );

        -- indexes for fast lookups / dashboard aggregates
        CREATE INDEX IF NOT EXISTS idx_farmer_village
            ON farmers(village);
        CREATE INDEX IF NOT EXISTS idx_collection_status
            ON collections(status);
        CREATE INDEX IF NOT EXISTS idx_collection_farmer
            ON collections(farmer_id);
        CREATE INDEX IF NOT EXISTS idx_collection_date
            ON collections(collection_date);
        CREATE INDEX IF NOT EXISTS idx_batch_date
            ON production_batches(batch_date);

        -- prevent duplicate farmers (same name in same village)
        CREATE UNIQUE INDEX IF NOT EXISTS uq_farmer_name_village
            ON farmers(name, village);
        """)
        conn.commit()
    finally:
        conn.close()