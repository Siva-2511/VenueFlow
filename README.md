# 🏟️ VenueFlow AI — IPL 2026 Venue Management System

> **Production-grade, AI-powered venue management platform** for IPL 2026.  
> Real-time crowd tracking · QR entry scanning · Role-based dashboards · Cloudflare D1 · Socket.IO

---

## 🌐 Live Demo

### 🔗 [https://venueflow-cxn6.onrender.com](https://venueflow-cxn6.onrender.com)

> **Deployed on Render.com** · Python 3 · Flask + SocketIO · Cloudflare D1 (Edge Database)

> ⏳ **Note:** The app is hosted on Render's **free tier** — if it hasn't been accessed recently, it may take **30–60 seconds to wake up** (cold start). Just wait a moment and refresh.  
> Once loaded, all features including real-time WebSocket updates, QR scanning, and live gate monitoring work normally.

---

## 📝 Note for Evaluators

> **This is a test simulation environment.** Use the credentials below to explore all three role-based dashboards without needing to set up accounts.

| Role | Login Email | Password |
|------|------------|----------|
| 👑 **Admin** | `admin@gmail.com` | `admin123` |
| 🧑 **Staff Gate 1** | `staffg1@gmail.com` | `VenueStaff@2026` |
| 🧑 **Staff Gate 2** | `staffg2@gmail.com` | `VenueStaff@2026` |
| 🧑 **Staff Gate 3–12** | `staffg3@gmail.com` … `staffg12@gmail.com` | `VenueStaff@2026` |
| 🎟️ **User** | Register on the Register tab or use Google Sign-In | — |

> **User accounts**: Click **Register here →** on the login page, fill in your name, email, phone, and pick your IPL match. The system auto-assigns you to a gate. You can also sign in via Google — first-time Google users are directed to a match-selection page.

---

## 🖼️ Preview

| Login | User Ticket | Admin Dashboard | Staff Scanner |
|-------|------------|-----------------|---------------|
| Dark glassmorphism card with animated neural-net background, Google OAuth button, Login/Register tabs | E-ticket with QR code, match countdown, gate assignment, venue navigator | Live 3D stadium model, 12-gate control matrix, KPI cards, entry flow chart | Camera QR scanner, live entry log, gate occupancy ring |

> All pages feature a premium dark UI with neon accents, GSAP animations, particle bursts on click, and holographic card effects.

---

## ✨ Key Features

### 🔐 Authentication
- **Email + password login** (PBKDF2-SHA256 hashed, stored in `.env`)
- **Google Sign-In** via server-side OAuth2 code flow (works on `localhost`)
- **Role-based access**: Admin · Staff (Gate 1–12) · User
- New Google users are routed to a **match selection page** before entering the system
- Session cookies, rate limiting, XSS/CSRF protection

### 👑 Admin Dashboard (`/admin`)
- **Live KPI cards**: Total Crowd, Gates Active, Avg Wait, Saturation %, New Registrations
- **3D Stadium** rendered with Three.js — gates glow green/amber/red/grey by occupancy status
- **Gate Control Matrix**: 12 clickable gate cards with live counts, Alert & Lock buttons
- **Gate Detail Modal**: Click any gate to see Entered / Pending / No-Entry user lists
- **Entry Flow Chart**: Chart.js time-series of scan events
- **Emergency Broadcast**: Push alerts to all staff terminals via Socket.IO
- **Scan Stream**: Real-time entry log with timestamps

### 🧑 Staff Terminal (`/staff`)
- **ZXing QR Camera Scanner** — opens device camera, decodes QR in real-time
- **Entry verification**: checks ticket validity, gate assignment, match date, duplicate entries
- **Live occupancy ring**: Animated SVG capacity indicator
- **Entry Data Stream**: Expandable log rows with Name/Email/Phone/Match details
- Match-past warning (`⚠️ PAST`) shown on expired tickets
- Gate status updates via WebSocket (`open → busy → full → closed`)

### 🎟️ User Dashboard (`/user`)
- **Official E-Ticket** with QR code (QRious.js, 220×220)
- **Match countdown** (Days / Hrs / Min / Sec, auto-detects if match is over)
- **Tabbed interface**: Ticket · Gate Info · AR Navigator · Fan Zone · Info
- **Match-complete detection**: Red banner + re-registration link if match date passed

### 🔒 Security
- All credentials in `.env` — never in source code
- PBKDF2-SHA256 hashed passwords
- `@login_required` with custom JSON 401 for API endpoints
- XSS sanitization on all inputs
- Rate limiting (20 scans/min per IP)
- HTTP security headers (HSTS, X-Frame-Options, etc.)

---

## 📁 File Structure

```
venueflow/
├── app.py                        # Flask app, routes, WebSocket, auth, APIs
├── d1_client.py                  # Cloudflare D1 (SQLite) REST client
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container deployment config
├── .env                          # 🔒 Secrets (never commit)
├── .gitignore
│
├── templates/
│   ├── login.html                # Login + Register page (Google OAuth, IPL match picker)
│   ├── admin.html                # Admin Command Grid dashboard
│   ├── staff.html                # Staff Terminal with ZXing scanner
│   ├── user.html                 # User E-Ticket dashboard
│   ├── select_match.html         # Match selection for first-time Google users
│   ├── index.html                # Landing / splash page
│   └── ar-nav.html               # AR venue navigator
│
└── static/
    ├── css/
    │   └── style.css             # Global premium CSS + animation library v3
    ├── js/
    │   ├── gsap.min.js           # GSAP 3.12 animation engine (local)
    │   ├── socket.io.min.js      # Socket.IO 4.7 client (local)
    │   ├── zxing.min.js          # ZXing QR scanner library (local)
    │   ├── qrious.min.js         # QR code generator (local)
    │   ├── three.min.js          # Three.js 3D renderer (local)
    │   ├── chart.min.js          # Chart.js data visualization (local)
    │   ├── tailwind.min.js       # Tailwind CSS Play CDN (local, patched)
    │   ├── websocket.js          # WebSocket logic for all roles
    │   ├── main.js               # Shared animations, particle bursts, cursor glow
    │   ├── qr-scanner.js         # Staff camera scanner (legacy entry)
    │   ├── auth.js               # Client-side auth helpers
    │   └── three-stadium.js      # 3D stadium renderer
    ├── favicon.ico
    ├── manifest.json             # PWA manifest
    └── service-worker.js         # Offline caching
```

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10 · Flask · Flask-SocketIO · Flask-Login |
| **Async** | Eventlet (WebSocket server) |
| **Database** | Cloudflare D1 (SQLite-compatible, edge-hosted) |
| **Auth** | Werkzeug PBKDF2 · Google OAuth2 Authorization Code Flow |
| **Frontend** | Vanilla HTML/CSS/JS · Tailwind CSS (local) |
| **Animations** | GSAP 3.12 · Custom CSS animation library v3 |
| **3D** | Three.js (stadium visualisation) |
| **Charts** | Chart.js (entry flow analysis) |
| **QR** | QRious.js (generate) · ZXing.js (scan) |
| **Deployment** | Docker · Cloudflare D1 |

---

## 🚀 Quick Start

### 1. Prerequisites
```bash
pip install flask flask-socketio flask-login werkzeug requests eventlet python-dotenv
```

### 2. Configure `.env`
```env
SECRET_KEY=your-random-secret-here
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASS_HASH=pbkdf2:sha256:...   # generate with werkzeug
STAFF_PASS_HASH=pbkdf2:sha256:...
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

Generate a password hash:
```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('yourpassword'))"
```

### 3. Run
```bash
python app.py
```
Open: **http://localhost:8080**

### 4. Docker
```bash
docker build -t venueflow .
docker run -p 8080:8080 --env-file .env venueflow
```

---

## 👤 User Roles

| Role | Login | Access |
|------|-------|--------|
| `admin` | `admin@gmail.com` + admin password | Full dashboard, gate control, broadcast |
| `staff` | `staffg1@gmail.com` … `staffg12@gmail.com` + staff password | Staff terminal for assigned gate |
| `user` | Any other email (registration or Google) | E-ticket, countdown, gate info |

> Staff accounts are automatically created by email pattern (`staffg<N>@gmail.com`). No manual DB setup needed.

---

## 🎨 UI/UX Design Highlights

- **Zero CDN dependencies** — all libraries bundled locally (no tracking, no blocking, works offline)
- **Glassmorphism cards** with animated holographic sheen
- **Neural network background** on login (canvas-animated)
- **Particle burst** on every button click
- **Custom cursor glow** (desktop)
- **Scroll-reveal** entrance animations via `IntersectionObserver`
- **GSAP** counter animations on KPI updates
- **Premium color palette**: Indigo `#6366f1` · Cyan `#06b6d4` · Rose `#ec4899` · Emerald `#22c55e`

---

## 🌐 Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID (Web application)
3. Add **Authorised redirect URIs**:
   - `http://localhost:8080/auth/google/callback` (local dev)
   - `https://yourdomain.com/auth/google/callback` (production)
4. Add Client ID + Secret to `.env`

---

## ⚠️ Production Notes

| Item | Note |
|------|------|
| **HTTPS** | Camera scanning (ZXing) requires HTTPS. Use nginx + Let's Encrypt. |
| **SESSION_COOKIE_SECURE** | Set to `True` in app.py when deploying with HTTPS |
| **Tailwind** | Replace Play CDN JS with a compiled `tailwind.css` build for best performance |
| **D1 Limits** | Cloudflare D1 free tier: 5M rows read/day, 100K writes/day |
| **Secret Key** | Change `SECRET_KEY` in `.env` before any public deployment |

---

## 📜 License

MIT © 2026 VenueFlow AI — Built for IPL 2026
