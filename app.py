import os
import requests as http_requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import d1_client

app = Flask(__name__)
app.config['SECRET_KEY'] = 'venueflow-secret-2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

GOOGLE_CLIENT_ID = "863719014670-0qs78m46r71c1r0o1e0useav95n2ss90.apps.googleusercontent.com"

# Prepare D1 Schemas
d1_client.init_db()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, email, role, gate_id=None, name=None):
        self.id = email
        self.email = email
        self.role = role
        self.gate_id = gate_id or 1
        self.name = name or email.split('@')[0]

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin@gmail.com":
        return User(user_id, "admin", name="Admin")
    elif user_id.startswith("staffg"):
        try:
            gate_id = int(user_id.split("@")[0].replace("staffg", ""))
            return User(user_id, "staff", gate_id)
        except:
            return User(user_id, "user")
    else:
        user_db = d1_client.execute("SELECT assigned_gate, name FROM users WHERE email=?", [user_id])
        if user_db:
            return User(user_id, "user", user_db[0].get('assigned_gate', 1), user_db[0].get('name'))
        return User(user_id, "user", 1)

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f"{current_user.role}_dashboard"))
        
    if request.method == 'POST':
        data = request.json
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if email == 'admin@gmail.com' and password == 'admin123':
            login_user(User(email, 'admin', name='Admin'))
            return jsonify({"status": "success", "redirect": url_for('admin_dashboard')})
        
        elif email.startswith('staffg') and email.endswith('@gmail.com'):
            expected_pass = email.split('@')[0]  # staffg1
            if password == expected_pass:
                try:
                    gate_id = int(expected_pass.replace("staffg", ""))
                    login_user(User(email, 'staff', gate_id))
                    return jsonify({"status": "success", "redirect": url_for('staff_dashboard')})
                except:
                    pass
        
        elif email and len(password) > 0:
            # New user: assign to least-busy gate
            gate_id = get_least_busy_gate()
            d1_client.execute(
                "INSERT OR IGNORE INTO users (email, name, role, assigned_gate) VALUES (?, ?, ?, ?)",
                [email, email.split('@')[0].replace('.', ' ').title(), 'user', gate_id]
            )
            user_rec = d1_client.execute("SELECT name, assigned_gate FROM users WHERE email=?", [email])
            name = user_rec[0]['name'] if user_rec else email.split('@')[0]
            gate_id = user_rec[0].get('assigned_gate', gate_id) if user_rec else gate_id
            login_user(User(email, 'user', gate_id, name))
            return jsonify({"status": "success", "redirect": url_for('user_dashboard')})
            
        return jsonify({"status": "error", "message": "Invalid credentials. Check email & password."}), 401

    return render_template('login.html', google_client_id=GOOGLE_CLIENT_ID)

@app.route('/auth/google', methods=['POST'])
def google_auth():
    """Verify Google JWT using Google's tokeninfo endpoint (works without google-auth library issues)."""
    token = request.json.get('token')
    if not token:
        return jsonify({"status": "error", "message": "No token provided"}), 400
    
    try:
        # Use Google's tokeninfo API - no library version issues
        resp = http_requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={token}",
            timeout=10
        )
        
        if resp.status_code != 200:
            return jsonify({"status": "error", "message": "Google could not verify token"}), 401
        
        idinfo = resp.json()
        
        # Validate the audience matches our client ID
        if idinfo.get('aud') != GOOGLE_CLIENT_ID:
            return jsonify({"status": "error", "message": "Token audience mismatch"}), 401
        
        email = idinfo.get('email', '').lower()
        name = idinfo.get('name', email.split('@')[0])
        
        if not email:
            return jsonify({"status": "error", "message": "No email in Google token"}), 401
        
        if email == 'admin@gmail.com':
            role, gate_id = 'admin', None
        elif email.startswith('staffg') and email.endswith('@gmail.com'):
            role = 'staff'
            try:
                gate_id = int(email.split('@')[0].replace("staffg", ""))
            except:
                gate_id = 1
        else:
            role = 'user'
            # Check if user already registered; otherwise pick least-busy gate
            existing = d1_client.execute("SELECT assigned_gate FROM users WHERE email=?", [email])
            if existing:
                gate_id = existing[0].get('assigned_gate', 1)
            else:
                gate_id = get_least_busy_gate()
            
        # Ensure stored in D1
        d1_client.execute(
            "INSERT OR IGNORE INTO users (email, name, role, assigned_gate) VALUES (?, ?, ?, ?)",
            [email, name, role, gate_id]
        )

        login_user(User(email, role, gate_id, name))
        return jsonify({"status": "success", "redirect": url_for(f'{role}_dashboard')})
    
    except Exception as e:
        print(f"Google Auth Error: {e}")
        return jsonify({"status": "error", "message": f"Authentication failed: {str(e)}"}), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

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
    name = db_user[0]['name'] if db_user else current_user.name
    assigned_gate = db_user[0].get('assigned_gate', 5) if db_user else 5
    return render_template('user.html', name=name, email=current_user.email, gate_id=assigned_gate)

# --- API CORE ---
@app.route('/scan_qr', methods=['POST'])
@login_required
def process_entry():
    if current_user.role != 'staff':
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
        
    ticket_data = request.json.get('qr_data', '').strip()
    gate_id = current_user.gate_id
    
    if not ticket_data:
        return jsonify({"status": "error", "message": "No QR data received"}), 400
    
    # Prevent double-entry
    existing = d1_client.execute("SELECT id FROM entries WHERE ticket_id=?", [ticket_data])
    if existing:
        return jsonify({"status": "error", "message": "Ticket ALREADY SCANNED at another gate!"}), 400
        
    gate_rows = d1_client.execute("SELECT current, capacity, status FROM gates WHERE id=?", [gate_id])
    if not gate_rows:
        return jsonify({"status": "error", "message": "Gate not found"}), 404
    
    gate = gate_rows[0]
    if gate['status'] == 'closed':
        return jsonify({"status": "error", "message": "Gate CLOSED by Admin!"}), 400
    if gate['current'] >= gate['capacity']:
        return jsonify({"status": "error", "message": "Gate is FULL!"}), 400

    # Extract email from ticket format TICKET-email@x.com-gateId
    parts = ticket_data.split('-', 2)
    user_email = parts[1] if len(parts) >= 2 else 'Anonymous'

    d1_client.execute(
        "INSERT INTO entries (user_email, gate_id, ticket_id) VALUES (?, ?, ?)", 
        [user_email, gate_id, ticket_data]
    )
    
    new_count = gate['current'] + 1
    new_status = ('full' if new_count >= gate['capacity'] 
                  else 'busy' if new_count >= gate['capacity'] * 0.70 
                  else 'open')
    
    d1_client.execute("UPDATE gates SET current=?, status=? WHERE id=?", [new_count, new_status, gate_id])
    
    # Push real log to Admin only
    socketio.emit('new_log', {'log': f"Entry: {user_email}", 'gate': f"Gate {gate_id}"})
    broadcast_gates()
    socketio.emit('entry_update')
    return jsonify({
        "status": "success", 
        "message": f"Verified! ({new_count}/{gate['capacity']})", 
        "user": user_email
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
        socketio.emit('staff_alert', {'message': f'⛔ Admin CLOSED Gate {gate_id}. Stop admitting.'}, room=f"gate_{gate_id}")
        socketio.emit('user_alert', {'message': f'Gate {gate_id} is CLOSED. Please find an open gate.'}, room=f"gate_{gate_id}")
    
    elif action == 'open':
        d1_client.execute("UPDATE gates SET status='open' WHERE id=?", [gate_id])
        socketio.emit('staff_alert', {'message': f'✅ Admin OPENED Gate {gate_id}. Resume operations.'}, room=f"gate_{gate_id}")
    
    elif action == 'redirect':
        t_gate = data.get('target_gate', '')
        socketio.emit('staff_alert', {'message': f'🔀 Admin: Redirect crowd to Gate {t_gate}.'}, room=f"gate_{gate_id}")
        socketio.emit('user_alert', {'message': f'Gate {gate_id} is busy. Please walk to Gate {t_gate}.'}, room=f"gate_{gate_id}")

    elif action == 'broadcast':
        msg = data.get('message', '')
        if msg:
            socketio.emit('broadcast', {'message': msg})
            socketio.emit('staff_alert', {'message': f'📢 {msg}'})

    broadcast_gates()

def broadcast_gates():
    gates = d1_client.execute("SELECT * FROM gates")
    data_dict = {}
    for g in gates:
        data_dict[g["name"]] = {
            "current": g["current"], 
            "max": g["capacity"], 
            "status": g["status"], 
            "id": g["id"]
        }
    socketio.emit('gate_update', data_dict)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
