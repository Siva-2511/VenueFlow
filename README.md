# VenueFlow AI 🏟️

**Real-time Stadium Crowd Intelligence Platform**  
*Built for Hack2Skill PromptWars #1 — Physical Event Experience Vertical*

---

## 🎯 Challenge Vertical
**Physical Event Experience** — Improving the attendee journey at large-scale sporting venues (IPL Final 2026, 60,000-seat stadium) through real-time coordination, smart crowd routing, and seamless check-in.

---

## 🚀 Features

### 👑 Admin Dashboard
- Live aggregate capacity gauge (all 12 gates, 2400 total seats)
- Real-time gate-by-gate crowd heatmap with status indicators (Open / Busy / Full / Closed)
- One-click gate locking/unlocking — broadcasts alert to staff
- Crowd redirection dispatch — sends push alert to affected staff and users
- Live scan event log (only real entries, zero fake data)

### 🧑 Staff Terminal (per-gate)
- Gate-specific login (`staffg1@gmail.com` → Gate 1, etc.)
- Animated capacity ring + occupancy bar, live-updated via WebSockets
- Tap-to-activate QR scanner (ZXing library, works on mobile & desktop)
- Duplicate-entry prevention (client-side Set + server-side DB check)
- Entry Register table with timestamped scan history
- Admin alert banner with auto-dismiss

### 🎟️ User Dashboard
- Personal digital e-ticket (IPL Final 2026) with QR code
- QR code generated in-browser (qrious.js) bound to user email + gate
- Live gate status ring (animated SVG radial progress)
- AR-style navigation panel with animated SVG path guide
- Auto-assigned to **least-busy open gate** on registration
- Real-time redirect alert if gate is closed or full

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python Flask + Flask-SocketIO (eventlet) |
| Database | Cloudflare D1 (SQLite at the edge) |
| Auth | Google Identity Services (GIS) + manual credentials |
| Real-time | WebSockets via Socket.IO |
| Frontend | HTML + Tailwind CSS (CDN) + Vanilla JS |
| Animations | GSAP 3.12 (60fps transitions) |
| QR Scanning | ZXing @0.18.6 |
| QR Generation | Qrious.js |
| 3D Background | Three.js r128 |

---

## 🔑 Credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@gmail.com | admin123 |
| Staff Gate 1 | staffg1@gmail.com | staffg1 |
| Staff Gate 5 | staffg5@gmail.com | staffg5 |
| ... | staffg[N]@gmail.com | staffg[N] |
| User | any email | any password |

*Users are automatically assigned to the least-busy open gate.*

---

## 🏃 Running Locally

```bash
pip install flask flask-socketio flask-login eventlet requests google-auth
python app.py
# Open http://localhost:8080
```

---

## ☁️ Database Schema (Cloudflare D1)

```sql
CREATE TABLE gates   (id INTEGER PRIMARY KEY, name TEXT, current INT DEFAULT 0, capacity INT DEFAULT 200, staff_email TEXT, status TEXT DEFAULT 'open');
CREATE TABLE entries (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, gate_id INT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, ticket_id TEXT UNIQUE);
CREATE TABLE users   (email TEXT PRIMARY KEY, name TEXT, role TEXT DEFAULT 'user', assigned_gate INT DEFAULT 1);
```

---

## 🔒 Security

- Google token verified via `https://oauth2.googleapis.com/tokeninfo` (no library version issues)
- Duplicate ticket scanning blocked at both DB level (`UNIQUE` constraint) and client side (`Set`)
- Role-based route protection via Flask-Login
- Gate closure commands authenticated — only admin WebSocket events accepted

---

*VenueFlow AI · IPL Final 2026 · Hack2Skill PromptWars #1*
