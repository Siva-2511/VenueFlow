import requests

ACCOUNT_ID = "c2c71b94720fada6e712c85bdb5c30af"
DATABASE_ID = "bcf456d2-fe49-495d-82eb-71c395ab9ab8"
API_TOKEN = "cfut_hboJVgg8FGKocqXp2PLx1QNpXlBXqGhNcdSiHhGr5d74c735"

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

def init_db():
    print("Ensuring D1 schema exists...")
    
    # Gates table
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
    
    # Entries table  
    execute("""
    CREATE TABLE IF NOT EXISTS entries (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_email TEXT,
      gate_id INT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      ticket_id TEXT UNIQUE
    )
    """)
    
    # Users table
    execute("""
    CREATE TABLE IF NOT EXISTS users (
      email TEXT PRIMARY KEY,
      name TEXT,
      role TEXT DEFAULT 'user',
      assigned_gate INT DEFAULT 5
    )
    """)
    
    # Seed 12 gates if empty
    gates = execute("SELECT COUNT(*) as count FROM gates")
    count = gates[0].get('count', 0) if gates else 0
    
    if count == 0:
        print("Seeding 12 gates...")
        for i in range(1, 13):
            execute(
                "INSERT OR IGNORE INTO gates (id, name, staff_email, capacity) VALUES (?, ?, ?, ?)",
                [i, f'Gate {i}', f'staffg{i}@gmail.com', 200]
            )
        print("Gates seeded successfully.")
