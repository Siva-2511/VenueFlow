import os
import random
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- AUTH SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Mock DB
class User(UserMixin):
    def __init__(self, id, email, password_hash, role):
        self.id = id
        self.email = email
        self.password_hash = password_hash
        self.role = role

users = {
    "1": User("1", "admin@venue.com", generate_password_hash("admin123"), "admin"),
    "2": User("2", "staff@venue.com", generate_password_hash("staff123"), "staff"),
    "3": User("3", "user@venue.com", generate_password_hash("user123"), "user"),
    "4": User("4", "guest@venue.com", generate_password_hash("guest"), "guest")
}

def get_user_by_email(email):
    for u in users.values():
        if u.email == email:
            return u
    return None

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# --- GATE STATE ---
gate_data = {f"Gate {i}": {"current": random.randint(10, 150), "max": 200, "status": "open"} for i in range(1, 13)}

# --- ROUTES ---
@app.route('/')
def index():
    # Landing page converts to login flow
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(f'{current_user.role}_dashboard'))
        
    if request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')
        auth_type = data.get('type')
        
        if auth_type == 'guest':
            login_user(users["4"])
            return jsonify({"status": "success", "redirect": url_for('user_dashboard')})
        elif auth_type == 'google':
            login_user(users["3"])
            return jsonify({"status": "success", "redirect": url_for('user_dashboard')})
        
        user = get_user_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({"status": "success", "redirect": url_for(f'{user.role}_dashboard')})
        
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role not in ['admin', 'guest']:
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/staff')
@login_required
def staff_dashboard():
    if current_user.role not in ['staff', 'admin', 'guest']:
        return redirect(url_for('login'))
    return render_template('staff.html')

@app.route('/user')
@login_required
def user_dashboard():
    return render_template('user.html')

# --- API ENDPOINTS ---
@app.route('/scan_qr', methods=['POST'])
@login_required
def process_entry():
    if current_user.role not in ['staff', 'admin', 'guest']:
        return jsonify({"status": "error"}), 403
        
    ticket_data = request.json.get('qr_data')
    # Hardcoding Gate 5 for scanning demo purposes
    gate_data['Gate 5']['current'] += 1
    if gate_data['Gate 5']['current'] >= gate_data['Gate 5']['max']:
        gate_data['Gate 5']['status'] = 'full'
    elif gate_data['Gate 5']['current'] >= gate_data['Gate 5']['max'] * 0.7:
        gate_data['Gate 5']['status'] = 'busy'
        
    socketio.emit('gate_update', gate_data)
    socketio.emit('entry_update')
    return jsonify({"status": "success", "message": f"Ticket {ticket_data} scanned at Gate 5!"})

# --- WEBSOCKETS ---
@socketio.on('connect')
def handle_connect():
    emit('gate_update', gate_data)

def background_simulation():
    """Simulate crowd moving every 3 seconds"""
    while True:
        socketio.sleep(3)
        changed = False
        for gate_name, gate in gate_data.items():
            if random.random() > 0.5:
                # Small random variation over time
                delta = random.randint(-5, 5)
                # Don't decrease Gate 5 too much to allow testing QR scanner accumulation
                if gate_name == 'Gate 5' and delta < 0:
                    delta = 0
                gate['current'] = max(0, min(gate['max'], gate['current'] + delta))
                gate['status'] = 'full' if gate['current'] >= gate['max'] * 0.9 else ('busy' if gate['current'] >= gate['max'] * 0.7 else 'open')
                changed = True
        if changed:
            socketio.emit('gate_update', gate_data)

if __name__ == '__main__':
    socketio.start_background_task(background_simulation)
    # Using eventlet instead of standard app.run
    socketio.run(app, debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
