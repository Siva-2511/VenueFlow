import requests
import os
from dotenv import load_dotenv
load_dotenv()

ACCOUNT_ID  = os.environ.get('CF_ACCOUNT_ID',  'c2c71b94720fada6e712c85bdb5c30af')
DATABASE_ID = os.environ.get('CF_DATABASE_ID', 'bcf456d2-fe49-495d-82eb-71c395ab9ab8')
API_TOKEN   = os.environ.get('CF_API_TOKEN',   '')

BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DATABASE_ID}/query"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def execute(sql, params=None):
    payload = {"sql": sql}
    if params is not None:
        payload["params"] = [str(p) if p is not None else None for p in params]

    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        res_json = response.json()

        if res_json.get("success"):
            if res_json["result"] and len(res_json["result"]) > 0:
                result = res_json["result"][0]
                if "results" in result:
                    return result["results"]
        else:
            print("D1 Error:", res_json.get("errors"))
        return []
    except Exception as e:
        print(f"D1 API Exception: {e}")
        return []


def _get_existing_columns(table: str) -> set:
    """Return the set of column names that currently exist in `table`."""
    rows = execute(f"PRAGMA table_info({table})")
    return {r["name"] for r in rows} if rows else set()


def _add_column_if_missing(table: str, col: str, col_def: str, existing: set):
    """Send ALTER TABLE only when the column is genuinely absent."""
    if col not in existing:
        print(f"  Adding column: {table}.{col}")
        execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")


def init_db():
    print("Ensuring D1 schema exists...")

    # ── Gates ───────────────────────────────────────────────────────
    execute("""
    CREATE TABLE IF NOT EXISTS gates (
      id INTEGER PRIMARY KEY,
      name TEXT NOT NULL,
      current INT DEFAULT 0,
      capacity INT DEFAULT 200,
      staff_email TEXT,
      status TEXT DEFAULT 'open'
    )
    """)

    # ── Entries ─────────────────────────────────────────────────────
    execute("""
    CREATE TABLE IF NOT EXISTS entries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_email TEXT,
      gate_id INT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      ticket_id TEXT UNIQUE
    )
    """)

    # ── Users (full schema for new installs) ────────────────────────
    execute("""
    CREATE TABLE IF NOT EXISTS users (
      email TEXT PRIMARY KEY,
      name TEXT,
      role TEXT DEFAULT 'user',
      assigned_gate INT DEFAULT 5,
      phone TEXT,
      match_name TEXT DEFAULT 'IPL 2026',
      match_date TEXT DEFAULT '2026-04-12',
      match_time TEXT DEFAULT '19:30',
      match_venue TEXT DEFAULT 'Narendra Modi Stadium, Ahmedabad',
      match_teams TEXT DEFAULT 'RCB vs MI'
    )
    """)

    # For databases created before the match columns were added,
    # check existing columns first — only ALTER TABLE if actually missing.
    existing = _get_existing_columns("users")
    _add_column_if_missing("users", "phone",        "TEXT",                                        existing)
    _add_column_if_missing("users", "match_name",   "TEXT DEFAULT 'IPL 2026'",                    existing)
    _add_column_if_missing("users", "match_date",   "TEXT DEFAULT '2026-04-12'",                  existing)
    _add_column_if_missing("users", "match_time",   "TEXT DEFAULT '19:30'",                       existing)
    _add_column_if_missing("users", "match_venue",  "TEXT DEFAULT 'Narendra Modi Stadium, Ahmedabad'", existing)
    _add_column_if_missing("users", "match_teams",  "TEXT DEFAULT 'RCB vs MI'",                   existing)

    # ── Seed 12 gates if the table is empty ─────────────────────────
    gates = execute("SELECT COUNT(*) as count FROM gates")
    count = gates[0].get("count", 0) if gates else 0

    if count == 0:
        print("Seeding 12 gates...")
        for i in range(1, 13):
            execute(
                "INSERT OR IGNORE INTO gates (id, name, staff_email, capacity) VALUES (?, ?, ?, ?)",
                [i, f"Gate {i}", f"staffg{i}@gmail.com", 200]
            )
        print("Gates seeded successfully.")

    print("D1 schema ready.")
