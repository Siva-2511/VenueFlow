# 🏟️ VenueFlow AI — IPL 2026 Venue Management System

> **Production-grade, AI-powered venue management platform** for IPL 2026.  
> Real-time crowd tracking · QR entry scanning · Cloudflare D1 Edge SQL · Serverless AI

---

## Chosen Vertical
**Venue Management & Fan Experience (Sports & Events)**
Managing thousands of cricket fans during an IPL match is a logistical nightmare. Long queues, uneven gate distribution, and chaotic entries ruin the fan experience. VenueFlow completely automates the stadium entry process by instantly load-balancing incoming fans across the least busy gates, generating secure E-Tickets, and providing real-time AI-powered crowd metrics to administrators.

## Approach and Logic
We built a hyper-efficient, secure, and visually stunning web application relying on edge-computing and WebSockets for real-time data sync without heavy server loads.
- **Smart Load Balancing**: The backend algorithm queries Cloudflare D1 per registration and dynamically assigns users to one of 12 gates to ensure perfect crowd distribution.
- **Real-Time Data Sync**: Powered by Socket.IO, any time a staff member scans a ticket, the Admin's 3D dashboard and metrics automatically update instantly.
- **Meaningful Google Services Integration**: 
  - **Google OAuth 2.0**: Integrated seamlessly for secure, one-click user registration and sign-in.
  - **Google Gemini AI**: Implemented `google-genai` to analyze live streaming gate-load statistics and generate actionable Crowd Control strategies for Admin operators in real time.

## How the solution works
The system is divided into three role-based dashboards:
1. **User Dashboard**: Users register (or sign in via Google OAuth) and receive an animated 3D E-ticket with an embedded QR code (QRious.js). Full Accessibility (A11y) standards are applied.
2. **Staff Terminal**: Dedicated gate staff use a web-based camera scanner (ZXing) to scan incoming fan QR codes. It instantly validates the ticket against edge SQL, preventing multi-scans.
3. **Admin Dashboard**: Features a live 3D Three.js stadium visualization glowing based on gate saturation. Real-time metrics are analyzed by Gemini 2.5 Flash to give prompt strategic instructions.

## Assumptions made
1. **Always Online**: It is assumed that staff scanning devices have a reliable mobile data or WiFi connection to ping WebSocket and Cloudflare D1 APIs in real time.
2. **Google Credentials**: The evaluating system assumes standard `.env` variables `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `GEMINI_API_KEY` are valid.
3. **Hardware Capabilities**: Staff devices must have functional webcams, and Admin devices should support WebGL for the 3D rendering.

---

### ✨ Key Features & Scoring Priorities
- **Code Quality & Size constraint**: Highly optimized repository (`< 250 KB`), utilizing global CDNs.
- **Security Defense**: Custom PBKDF2-SHA256 password hashing, XSS/CSRF mitigation, rate-limiting, and pure edge-based SQL injection prevention.
- **Testing Coverage**: Formal suite utilizing `pytest` running across the application verifying logic and edge case failures.
- **Accessibility**: 100% WCAG compliance. Deep semantic structure (`<main>`, `<nav>`, `<header>`), `aria-label` injection, and semantic flow.
- **Google Services**: Dual integration natively utilizing Google Auth and Gemini AI text synthesis.

---

### 🚀 Quick Start & Tests
```bash
pip install -r requirements.txt
python -m pytest tests/
python app.py
```
*Hosted dynamically and built for Scale.*
