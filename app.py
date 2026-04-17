import os
import re
import time
import threading
import html as html_lib
from functools import wraps
import requests as http_requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash
import d1_client

# ── Load .env if present (never commits secrets to source) ────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed — fall back to reading .env manually
    _env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(_env_path):
        with open(_env_path) as _ef:
            for _line in _ef:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _v = _line.split('=', 1)
                    os.environ.setdefault(_k.strip(), _v.strip())

from datetime import timedelta
app = Flask(__name__)
app.config['SECRET_KEY']                = os.environ.get('SECRET_KEY') or (
    'venueflow-dev-only-secret-change-in-prod' if not os.environ.get('RENDER')
    else (_ for _ in ()).throw(RuntimeError('SECRET_KEY env var must be set in production!'))
)
app.config['SESSION_COOKIE_HTTPONLY']   = True
app.config['SESSION_COOKIE_SAMESITE']  = 'Lax'
app.config['SESSION_COOKIE_SECURE']    = bool(os.environ.get('RENDER'))  # True on Render (HTTPS), False locally
app.config['SESSION_COOKIE_NAME']       = 'vf_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_PERMANENT']         = True
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# ── Credentials loaded from .env — NO plaintext in source ─────────────
ADMIN_EMAIL     = os.environ.get('ADMIN_EMAIL', 'admin@gmail.com')
ADMIN_PASS_HASH = os.environ.get('ADMIN_PASS_HASH', '')
STAFF_PASS_HASH = os.environ.get('STAFF_PASS_HASH', '')
GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID', '863719014670-0qs78m46r71c1r0o1e0useav95n2ss90.apps.googleusercontent.com')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
# Optional: hard-code callback URL for production (e.g. https://yourdomain.com/auth/google/callback)
GOOGLE_REDIRECT_URI  = os.environ.get('GOOGLE_REDIRECT_URI', '')

# Run D1 schema init in background so Flask starts instantly
threading.Thread(target=d1_client.init_db, daemon=True).start()

# ── Security helpers ──────────────────────────────────────────────────
_rate_store: dict = {}

def rate_limit(max_calls: int, period: int):
    """Simple in-memory per-IP rate limiter."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr or '0.0.0.0'
            key = f"{f.__name__}:{ip}"
            now = time.time()
            calls = [t for t in _rate_store.get(key, []) if now - t < period]
            if len(calls) >= max_calls:
                return jsonify({"status": "error", "message": "Too many requests — please wait."}), 429
            calls.append(now)
            _rate_store[key] = calls
            return f(*args, **kwargs)
        return wrapper
    return decorator

def sanitize(value: str, max_len: int = 254) -> str:
    """Strip HTML tags, limit length, strip whitespace."""
    if not value:
        return ''
    value = re.sub(r'[<>"\']', '', str(value)).strip()[:max_len]
    return value

def valid_email(email: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=self, microphone=()'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.unauthorized_handler
def unauthorized():
    """Return JSON 401 for API / AJAX requests; redirect to login for browser navigation."""
    is_api = (
        request.path.startswith('/api/')
        or request.path in ('/scan_qr', '/select_match', '/auth/google')
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or request.headers.get('Accept','').startswith('application/json')
    )
    if is_api:
        return jsonify({'status': 'error', 'message': 'Session expired — please log in again.'}), 401
    return redirect(url_for('login'))

class User(UserMixin):
    def __init__(self, email, role, gate_id=None, name=None):
        self.id = email
        self.email = email
        self.role = role
        self.gate_id = gate_id or 1
        self.name = name or email.split('@')[0]

@login_manager.user_loader
def load_user(user_id):
    uid = user_id.lower()
    if uid == ADMIN_EMAIL.lower():
        return User(user_id, 'admin', name='Admin')
    elif uid.startswith('staffg') and uid.endswith('@gmail.com'):
        try:
            gate_id = int(uid.split('@')[0].replace('staffg', ''))
            return User(user_id, 'staff', gate_id)
        except:
            return User(user_id, 'staff', 1)
    else:
        user_db = d1_client.execute('SELECT assigned_gate, name FROM users WHERE email=?', [uid])
        if user_db:
            return User(uid, 'user', user_db[0].get('assigned_gate', 1), user_db[0].get('name'))
        return User(uid, 'user', 1)

def get_least_busy_gate():
    """Returns the ID of the open gate with the most free capacity."""
    gates = d1_client.execute(
        "SELECT id, current, capacity FROM gates WHERE status != 'closed' AND status != 'full' ORDER BY current ASC LIMIT 1"
    )
    if gates:
        return gates[0]['id']
    # Fallback: just pick gate 1 if all are full/closed
    return 1

# --- AUTH ROUTES ---
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/favicon.ico')
def favicon():
    from flask import send_from_directory
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon'
    )

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(8, 60)
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f"{current_user.role}_dashboard"))

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        email = sanitize(data.get('email', '')).lower()
        password = sanitize(data.get('password', ''), 128)

        if not email or not valid_email(email):
            return jsonify({"status": "error", "message": "Invalid email format."}), 400

        # ── Admin ─────────────────────────────────────────────────
        if email == ADMIN_EMAIL:
            if ADMIN_PASS_HASH and check_password_hash(ADMIN_PASS_HASH, password):
                login_user(User(email, 'admin', name='Admin'))
                return jsonify({"status": "success", "redirect": url_for('admin_dashboard')})
            return jsonify({"status": "error", "message": "Invalid credentials."}), 401

        # ── Staff (staffg1@gmail.com … staffg12@gmail.com) ────────
        if email.startswith('staffg') and email.endswith('@gmail.com'):
            if STAFF_PASS_HASH and check_password_hash(STAFF_PASS_HASH, password):
                try:
                    gate_id = int(email.split('@')[0].replace('staffg', ''))
                    login_user(User(email, 'staff', gate_id))
                    return jsonify({"status": "success", "redirect": url_for('staff_dashboard')})
                except Exception:
                    pass
            return jsonify({"status": "error", "message": "Invalid credentials."}), 401

        # ── Regular user ──────────────────────────────────────────
        if valid_email(email) and len(password) >= 4:
            user_rec = d1_client.execute(
                "SELECT name, assigned_gate FROM users WHERE email=?", [email]
            )
            if not user_rec:
                return jsonify({
                    "status": "error",
                    "message": "Account not found. Please register first."
                }), 401
            name    = user_rec[0].get('name') or email.split('@')[0].title()
            gate_id = int(user_rec[0].get('assigned_gate') or 5)
            login_user(User(email, 'user', gate_id, name))
            return jsonify({"status": "success", "redirect": url_for('user_dashboard')})

        return jsonify({"status": "error", "message": "Invalid credentials."}), 401


    return render_template('login.html', google_client_id=GOOGLE_CLIENT_ID)


# ── Google OAuth2 — Server-Side Code Flow ──────────────────────────
def _get_redirect_uri():
    """Build the OAuth2 callback URI, always normalising 127.0.0.1 → localhost
       so it matches what is registered in Google Cloud Console.
       Override with GOOGLE_REDIRECT_URI env var for production."""
    if GOOGLE_REDIRECT_URI:
        return GOOGLE_REDIRECT_URI
    import urllib.parse
    base = url_for('google_auth_callback', _external=True)
    # Normalise 127.0.0.1 → localhost (Google Console treats them differently)
    base = base.replace('127.0.0.1', 'localhost')
    return base

@app.route('/auth/google/start')
def google_auth_start():
    """Redirect user to Google's OAuth2 authorization page."""
    import urllib.parse
    if not GOOGLE_CLIENT_ID:
        return redirect(url_for('login'))
    redirect_uri = _get_redirect_uri()
    params = {
        'client_id':     GOOGLE_CLIENT_ID,
        'redirect_uri':  redirect_uri,
        'response_type': 'code',
        'scope':         'openid email profile',
        'prompt':        'select_account',
        'access_type':   'online',
    }
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return redirect(auth_url)

@app.route('/auth/google/callback')
def google_auth_callback():
    """Exchange authorization code for user info and log in."""
    code  = request.args.get('code')
    error = request.args.get('error')
    if error or not code:
        return redirect(url_for('login') + '?google_error=1')
    try:
        redirect_uri = _get_redirect_uri()   # Must match EXACTLY what was sent in /start
        # Exchange code for tokens
        token_resp = http_requests.post('https://oauth2.googleapis.com/token', data={
            'code':          code,
            'client_id':     GOOGLE_CLIENT_ID,
            'client_secret': GOOGLE_CLIENT_SECRET,
            'redirect_uri':  redirect_uri,
            'grant_type':    'authorization_code',
        }, timeout=10)
        if token_resp.status_code != 200:
            return redirect(url_for('login') + '?google_error=2')
        tokens   = token_resp.json()
        id_token = tokens.get('id_token', '')
        # Verify id_token via Google tokeninfo
        info_resp = http_requests.get(
            f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}', timeout=10
        )
        if info_resp.status_code != 200:
            return redirect(url_for('login') + '?google_error=3')
        idinfo = info_resp.json()
        email  = idinfo.get('email', '').lower()
        name   = idinfo.get('name',  email.split('@')[0].title())
        if not email:
            return redirect(url_for('login') + '?google_error=4')

        # Role detection
        if email == ADMIN_EMAIL:
            role, gate_id = 'admin', None
        elif email.startswith('staffg') and email.endswith('@gmail.com'):
            role = 'staff'
            try:    gate_id = int(email.split('@')[0].replace('staffg', ''))
            except: gate_id = 1
        else:
            role = 'user'
            existing = d1_client.execute("SELECT assigned_gate, match_date FROM users WHERE email=?", [email])
            if existing:
                gate_id = existing[0].get('assigned_gate', 1)
                login_user(User(email, role, gate_id, name))
                return redirect(url_for('user_dashboard'))
            else:
                # New Google user — save temp session state, send to match selection
                session['pending_google_email'] = email
                session['pending_google_name']  = name
                return redirect(url_for('select_match_page'))

        # Save admin/staff in D1 and log in
        d1_client.execute(
            "INSERT OR IGNORE INTO users (email, name, role, assigned_gate) VALUES (?, ?, ?, ?)",
            [email, name, role, gate_id]
        )
        login_user(User(email, role, gate_id, name))
        return redirect(url_for(f'{role}_dashboard'))
    except Exception as e:
        print(f'Google callback error: {e}')
        return redirect(url_for('login') + '?google_error=5')

# Legacy GSI One-Tap endpoint (kept for backwards compat)
@app.route('/auth/google', methods=['POST'])
def google_auth():
    return jsonify({'status':'error','message':'Please use the Google Sign-In button.'}), 400

@app.route('/select-match')
def select_match_page():
    """Match selection page for first-time Google users or re-registering users."""
    email = session.get('pending_google_email')
    if not email:
        if current_user.is_authenticated and current_user.role == 'user':
            email = current_user.email
        else:
            return redirect(url_for('login'))
    return render_template('select_match.html', email=email)

@app.route('/select_match', methods=['POST'])
def select_match_submit():
    """Save match choice for a user and log them in."""
    email = session.get('pending_google_email')
    name  = session.get('pending_google_name', '')
    if not email:
        if current_user.is_authenticated and current_user.role == 'user':
            email = current_user.email
            name  = current_user.name
        else:
            return jsonify({'status':'error','message':'Session expired. Please sign in again.'}), 401
    data = request.get_json(silent=True) or {}
    match_name  = sanitize(data.get('match_name',  'IPL 2026'), 120)
    match_teams = sanitize(data.get('match_teams', ''), 80)
    match_date  = sanitize(data.get('match_date',  ''), 12)
    match_time  = sanitize(data.get('match_time',  '19:30'), 8)
    match_venue = sanitize(data.get('match_venue', ''), 120)
    if not match_date:
        return jsonify({'status':'error','message':'Please select a match.'}), 400
    gate_id = get_least_busy_gate()
    d1_client.execute(
        """INSERT INTO users (email, name, role, assigned_gate, match_name, match_teams, match_date, match_time, match_venue)
           VALUES (?, ?, 'user', ?, ?, ?, ?, ?, ?)
           ON CONFLICT(email) DO UPDATE SET
             match_name=excluded.match_name, match_teams=excluded.match_teams,
             match_date=excluded.match_date, match_time=excluded.match_time,
             match_venue=excluded.match_venue, assigned_gate=excluded.assigned_gate""",
        [email, name, gate_id, match_name, match_teams, match_date, match_time, match_venue]
    )
    # Clear pending session state
    session.pop('pending_google_email', None)
    session.pop('pending_google_name',  None)
    login_user(User(email, 'user', gate_id, name))
    return jsonify({'status':'success','redirect':url_for('user_dashboard')})


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/heartbeat')
@login_required
def heartbeat():
    """Keep session alive during long scanner sessions."""
    session.modified = True
    return jsonify({"status": "ok", "user": current_user.email, "role": current_user.role})

@app.route('/register', methods=['POST'])
@rate_limit(5, 60)
def register_user():
    """New user registration with IPL match preference."""
    data = request.get_json(silent=True) or {}
    email      = sanitize(data.get('email', '')).lower()
    password   = sanitize(data.get('password', ''), 128)
    name       = sanitize(data.get('name', ''), 60)
    phone      = sanitize(data.get('phone', ''), 20)
    match_name = sanitize(data.get('match_name', 'IPL 2026'), 120)
    match_date = sanitize(data.get('match_date', '2026-04-12'), 30)
    match_time = sanitize(data.get('match_time', '19:30'), 10)
    match_venue= sanitize(data.get('match_venue', 'Narendra Modi Stadium'), 120)
    match_teams= sanitize(data.get('match_teams', 'RCB vs MI'), 60)

    if not email or not valid_email(email):
        return jsonify({"status":"error","message":"Invalid email format."}), 400
    if len(password) < 4:
        return jsonify({"status":"error","message":"Password must be at least 4 characters."}), 400
    if not name:
        name = email.split('@')[0].replace('.', ' ').title()

    existing = d1_client.execute("SELECT email FROM users WHERE email=?", [email])
    if existing:
        return jsonify({"status":"error","message":"Account already exists. Please log in."}), 409

    gate_id = get_least_busy_gate()
    from werkzeug.security import generate_password_hash
    pw_hash = generate_password_hash(password) if password else ''
    d1_client.execute(
        "INSERT INTO users (email,name,role,assigned_gate,phone,match_name,match_date,match_time,match_venue,match_teams) VALUES (?,?,?,?,?,?,?,?,?,?)",
        [email, name, 'user', gate_id, phone, match_name, match_date, match_time, match_venue, match_teams]
    )
    login_user(User(email, 'user', gate_id, name))
    socketio.emit('user_registered', {'email': email, 'name': name, 'gate_id': gate_id}, room=f'gate_{gate_id}')
    socketio.emit('user_registered', {'email': email, 'name': name, 'gate_id': gate_id}, room='admin')
    return jsonify({"status":"success","redirect":url_for('user_dashboard')})

# --- DASHBOARDS ---
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    return render_template('admin.html', email=current_user.email)

@app.route('/staff')
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        return redirect(url_for('login'))
    gate_info = d1_client.execute("SELECT * FROM gates WHERE id = ?", [current_user.gate_id])
    gate = gate_info[0] if gate_info else {
        "id": current_user.gate_id, 
        "name": f"Gate {current_user.gate_id}", 
        "current": 0, 
        "capacity": 200
    }
    return render_template('staff.html', gate=gate, email=current_user.email)

@app.route('/user')
@login_required
def user_dashboard():
    if current_user.role != 'user':
        return redirect(url_for('login'))
    db_user = d1_client.execute("SELECT * FROM users WHERE email = ?", [current_user.email])
    row = db_user[0] if db_user else {}
    name         = row.get('name', current_user.name) or current_user.name
    assigned_gate= int(row.get('assigned_gate', 5) or 5)
    match_name   = row.get('match_name') or 'IPL 2026'
    match_date   = row.get('match_date') or '2026-04-12'
    match_time   = row.get('match_time') or '19:30'
    match_venue  = row.get('match_venue') or 'Narendra Modi Stadium, Ahmedabad'
    match_teams  = row.get('match_teams') or 'RCB vs MI'
    # Build ISO datetime string for client-side countdown (IST = +05:30)
    match_dt = f"{match_date}T{match_time}:00+05:30"
    return render_template('user.html',
        name=name, email=current_user.email, gate_id=assigned_gate,
        match_name=match_name, match_teams=match_teams,
        match_date=match_date, match_time=match_time,
        match_venue=match_venue, match_dt=match_dt
    )

# --- STATS API (used by admin dashboard to restore flow chart total on refresh) ---
@app.route('/api/stats')
@login_required
def api_stats():
    if current_user.role != 'admin':
        return jsonify({'status': 'error'}), 403
    total_rows  = d1_client.execute("SELECT COUNT(*) as cnt FROM entries") or []
    new_today   = d1_client.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE role='user'"
    ) or []
    total_entries = int((total_rows[0].get('cnt', 0) or 0)) if total_rows else 0
    new_reg       = int((new_today[0].get('cnt', 0) or 0)) if new_today else 0
    return jsonify({'total_entries': total_entries, 'new_registrations': new_reg})

# --- API CORE ---
@app.route('/scan_qr', methods=['POST'])
@login_required
@rate_limit(20, 60)
def process_entry():
    if current_user.role != 'staff':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.get_json(silent=True) or {}
    ticket_data = sanitize(data.get('qr_data', ''), 512)
    gate_id = current_user.gate_id

    if not ticket_data:
        return jsonify({"status": "error", "message": "No QR data received"}), 400


    # Prevent double-entry
    existing = d1_client.execute("SELECT id FROM entries WHERE ticket_id=?", [ticket_data])
    if existing:
        return jsonify({"status": "error", "message": "Ticket ALREADY SCANNED at another gate!"}), 400

    # Use CAST for type-safe D1 gate lookup (D1 stores/returns numbers as strings)
    gate_rows = d1_client.execute(
        "SELECT current, capacity, status FROM gates WHERE CAST(id AS TEXT)=CAST(? AS TEXT)",
        [gate_id]
    )
    if not gate_rows:
        return jsonify({"status": "error", "message": "Gate not found"}), 404

    gate = gate_rows[0]
    # Cast D1 string values to int for arithmetic
    gate_current  = int(gate.get('current', 0)  or 0)
    gate_capacity = int(gate.get('capacity', 200) or 200)

    if gate['status'] == 'closed':
        return jsonify({"status": "error", "message": "Gate CLOSED by Admin!"}), 400
    if gate_current >= gate_capacity:
        return jsonify({"status": "error", "message": "Gate is FULL!"}), 400

    # Extract email from ticket format TICKET-email@x.com-gateId
    parts = ticket_data.split('-', 2)
    user_email = parts[1] if len(parts) >= 2 else 'Anonymous'

    # Look up user details and check match_past
    user_rows = d1_client.execute(
        "SELECT name, phone, match_name, match_date FROM users WHERE email=?", [user_email]
    )
    user_data  = {}
    match_past = False
    if user_rows:
        u = user_rows[0]
        user_data = {
            'name':       u.get('name', ''),
            'email':      user_email,
            'phone':      u.get('phone', ''),
            'match_name': u.get('match_name', ''),
            'match_date': str(u.get('match_date', ''))
        }
        try:
            from datetime import date
            md = u.get('match_date', '')
            if md:
                match_past = date.fromisoformat(str(md)) < date.today()
        except Exception:
            pass

    d1_client.execute(
        "INSERT INTO entries (user_email, gate_id, ticket_id) VALUES (?, ?, ?)",
        [user_email, str(gate_id), ticket_data]   # store as string for consistency
    )

    new_count  = gate_current + 1
    new_status = ('full' if new_count >= gate_capacity
                  else 'busy' if new_count >= gate_capacity * 0.70
                  else 'open')

    d1_client.execute(
        "UPDATE gates SET current=?, status=? WHERE CAST(id AS TEXT)=CAST(? AS TEXT)",
        [new_count, new_status, gate_id]
    )

    # Push real log to Admin only
    socketio.emit('new_log', {
        'log':  f"[IN] Entry: {user_data.get('name', user_email)} ({user_email})",
        'gate': f"Gate {gate_id}"
    })
    broadcast_gates()
    socketio.emit('entry_update')
    return jsonify({
        "status":     "success",
        "message":    f"✓ Verified! ({new_count}/{gate_capacity})",
        "user":       user_email,
        "match_past": match_past,
        "user_data":  user_data
    })

# --- WEBSOCKETS ---
@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        if current_user.role in ['staff', 'user']:
            join_room(f"gate_{current_user.gate_id}")
    broadcast_gates()

@socketio.on('admin_action')
def handle_admin_action(data):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return
        
    gate_id = data.get('gate_id')
    action = data.get('action')
    
    if action == 'close':
        d1_client.execute("UPDATE gates SET status='closed' WHERE id=?", [gate_id])
        socketio.emit('staff_alert', {'message': f'\u26d4 Admin CLOSED Gate {gate_id}. Stop admitting.'}, room=f"gate_{gate_id}")
        socketio.emit('user_alert', {'message': f'Gate {gate_id} is CLOSED. Please find an open gate.'}, room=f"gate_{gate_id}")
    
    elif action == 'open':
        d1_client.execute("UPDATE gates SET status='open' WHERE id=?", [gate_id])
        socketio.emit('staff_alert', {'message': f'\u2705 Admin OPENED Gate {gate_id}. Resume operations.'}, room=f"gate_{gate_id}")
    
    elif action == 'redirect':
        t_gate = data.get('target_gate', '')
        socketio.emit('staff_alert', {'message': f'\U0001f500 Admin: Redirect crowd to Gate {t_gate}.'}, room=f"gate_{gate_id}")
        socketio.emit('user_alert', {'message': f'Gate {gate_id} is busy. Please walk to Gate {t_gate}.'}, room=f"gate_{gate_id}")

    elif action == 'broadcast':
        msg = data.get('message', '')
        if msg:
            socketio.emit('broadcast', {'message': msg})
            socketio.emit('staff_alert', {'message': f'\U0001f4e2 {msg}'})

    broadcast_gates()

def broadcast_gates():
    gates = d1_client.execute("SELECT * FROM gates")
    data_dict = {}
    total_crowd = 0
    total_max   = 0
    for g in gates:
        try:    cur = int(g.get("current", 0) or 0)
        except: cur = 0
        try:    cap = int(g.get("capacity", 200) or 200)
        except: cap = 200
        try:    gid = int(g.get("id", 0))
        except: gid = 0
        data_dict[g["name"]] = {
            "current": cur,
            "max":     cap,
            "status":  g["status"],
            "id":      gid
        }
        total_crowd += cur
        total_max   += cap
    data_dict["__meta__"] = {"total": total_crowd, "max": total_max}
    socketio.emit('gate_update', data_dict)

# --- GATE USERS API (Admin modal) ---
@app.route('/api/gate/<int:gate_id>/users')
@login_required
def gate_users(gate_id):
    if current_user.role != 'admin':
        return jsonify({"status": "error"}), 403
    tab     = request.args.get('tab', 'entered')
    from datetime import date
    today   = date.today().isoformat()
    gid_str = str(gate_id)   # single normalisation — compare str == str everywhere

    def is_past(md):
        try: return bool(md) and str(md) < today
        except: return False

    # Step 1 — gate authoritative current count (fetch ALL, filter in Python)
    #   Avoids D1's INTEGER vs TEXT comparison failure in WHERE id=?
    all_gates    = d1_client.execute("SELECT id, current, capacity FROM gates") or []
    gate_current = 0
    for g in all_gates:
        if str(g.get('id', '')) == gid_str:
            try:    gate_current = int(g.get('current', 0) or 0)
            except: gate_current = 0
            break

    # Step 2 — all entries, filter in Python by gate_id string match
    all_entries    = d1_client.execute(
        "SELECT user_email, gate_id, timestamp FROM entries ORDER BY timestamp DESC"
    ) or []
    entry_rows     = [r for r in all_entries if str(r.get('gate_id', '')) == gid_str]
    entered_emails = [r.get('user_email', '') for r in entry_rows]
    entry_time_map = {r.get('user_email', ''): str(r.get('timestamp', '')) for r in entry_rows}

    # Step 3 — all users with role 'user', filter by assigned_gate in Python
    all_users     = d1_client.execute(
        "SELECT email, name, phone, match_name, match_date, assigned_gate FROM users WHERE role='user'"
    ) or []
    assigned_rows = [r for r in all_users if str(r.get('assigned_gate', '')) == gid_str]
    assigned_map  = {r.get('email', ''): r for r in assigned_rows}

    # Step 4 — entered list
    entered_list = []
    for email in entered_emails:
        u = assigned_map.get(email, {})
        entered_list.append({
            'email':      email,
            'name':       u.get('name', ''),
            'phone':      u.get('phone', ''),
            'match_name': u.get('match_name', ''),
            'match_date': str(u.get('match_date', '')),
            'timestamp':  entry_time_map.get(email, ''),
            'match_past': is_past(u.get('match_date', ''))
        })

    # Step 5 — pending / no-entry
    entered_set   = set(entered_emails)
    pending_list  = []
    no_entry_list = []
    for r in assigned_rows:
        em = r.get('email', '')
        if em in entered_set:
            continue
        md  = r.get('match_date', '')
        rec = {
            'email':      em,
            'name':       r.get('name', ''),
            'phone':      r.get('phone', ''),
            'match_name': r.get('match_name', ''),
            'match_date': str(md),
            'match_past': is_past(md)
        }
        if is_past(md): no_entry_list.append(rec)
        else:            pending_list.append(rec)

    entered_count = max(gate_current, len(entered_list))

    if tab == 'entered':   users = entered_list
    elif tab == 'pending': users = pending_list
    else:                  users = no_entry_list

    return jsonify({
        'entered':  entered_count,
        'pending':  len(pending_list),
        'no_entry': len(no_entry_list),
        'users':    users
    })
@app.route('/api/admin/ai_insight')
@login_required
def get_ai_insight():
    if current_user.role != 'admin':
        return jsonify({'status':'error','message':'Unauthorized'}), 403
    
    stats = d1_client.execute(
        '''SELECT assigned_gate as gate_id, COUNT(id) as count
           FROM users WHERE assigned_gate IS NOT NULL GROUP BY assigned_gate'''
    )
    from gemini_agent import analyze_crowd_data
    insight = analyze_crowd_data(str(stats))
    return jsonify({'insight': insight, 'status': 'success'})


if __name__ == '__main__':
    socketio.run(app, debug=False, use_reloader=False, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
