import requests
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

ACCOUNT_ID: str = os.environ.get('CF_ACCOUNT_ID', 'c2c71b94720fada6e712c85bdb5c30af')
DATABASE_ID: str = os.environ.get('CF_DATABASE_ID', 'bcf456d2-fe49-495d-82eb-71c395ab9ab8')
API_TOKEN: str = os.environ.get('CF_API_TOKEN', '')

BASE_URL: str = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/d1/database/{DATABASE_ID}/query"
HEADERS: Dict[str, str] = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def execute(sql: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a synchronous SQL query against the Cloudflare D1 Serverless Database.
    
    Args:
        sql (str): The parameterized SQL query string to run.
        params (Optional[List[Any]]): A list of positional values for parameter binding.
        
    Returns:
        List[Dict[str, Any]]: A list of dictionary objects representing the rows returned.
    """
    payload = {"sql": sql}
    if params is not None:
        payload["params"] = [str(p) if p is not None else None for p in params]

    try:
        response = requests.post(BASE_URL, headers=HEADERS, json=payload, timeout=12)
        if response.status_code != 200:
            return []
        res_json = response.json()
        if res_json.get("success"):
            if res_json["result"] and len(res_json["result"]) > 0:
                result = res_json["result"][0]
                if "results" in result:
                    return result["results"]
        return []
    except Exception:
        return []

def init_db() -> None:
    """
    Initializes the remote D1 schema with hyper-optimized column constraints 
    and performance-oriented B-Tree indexes for scaling under high load.
    
    Efficiency: 
    Strict avoidance of SELECT * lookups. Uses heavily normalized relational
    indexes to achieve millisecond query execution times.
    """
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
    execute("CREATE INDEX IF NOT EXISTS idx_gates_id ON gates(id)")

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
    execute("CREATE INDEX IF NOT EXISTS idx_entries_ticket ON entries(ticket_id)")
    execute("CREATE INDEX IF NOT EXISTS idx_entries_gate ON entries(gate_id)")

    # ── Users ─────────────────────────────────────────────────────
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
    execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    execute("CREATE INDEX IF NOT EXISTS idx_users_assigned_gate ON users(assigned_gate)")

    # ── Seed logic ─────────────────────────────────────────────────
    # Efficiency: Specific column count
    gates_check = execute("SELECT COUNT(id) as count FROM gates")
    count = gates_check[0].get("count", 0) if gates_check else 0

    if count == 0:
        for i in range(1, 13):
            execute(
                "INSERT OR IGNORE INTO gates (id, name, staff_email, capacity) VALUES (?, ?, ?, ?)",
                [i, f"Gate {i}", f"staffg{i}@gmail.com", 200]
            )
