let socket;

function initWebSockets(role, currentGateName = null, gateId = null) {
    socket = io();
    
    socket.on('connect', () => console.log('[VenueFlow] WS OK'));
    
    socket.on('gate_update', (data) => {
        if (role === 'admin') updateAdminDashboard(data);
        else if (role === 'staff' && currentGateName) updateStaffLiveData(data, currentGateName);
        else if (role === 'user' && gateId) {
            if (typeof updateUserGateStatus === 'function') updateUserGateStatus(data, gateId);
        }
    });

    socket.on('entry_update', () => {
        if (navigator.vibrate) navigator.vibrate([60, 30, 60]);
    });
    
    socket.on('new_log', (data) => {
        if (role === 'admin') {
            adminAddRealLog(data);
            if (typeof scanQueue !== 'undefined') scanQueue++;
        }
    });
    
    socket.on('staff_alert', (data) => {
        if (role === 'staff') showAlert(data.message, 'warning');
    });

    socket.on('user_alert', (data) => {
        if (role === 'user') {
            showAlert(data.message, 'warning');
            if (typeof handleUserRedirect === 'function') handleUserRedirect(data.message);
        }
    });
    
    // Emergency/admin broadcast
    socket.on('broadcast', (data) => {
        showAlert(data.message, 'warning');
    });
}

// ============================================================
// ADMIN DASHBOARD
// ============================================================
let adminGridReady = false;

function updateAdminDashboard(data) {
    const grid = document.getElementById('gates-grid');
    if (!grid) return;
    
    let totalCurrent = 0, totalMax = 0;

    const sorted = Object.keys(data).sort((a, b) =>
        parseInt(a.replace('Gate ', '')) - parseInt(b.replace('Gate ', ''))
    );

    if (!adminGridReady) {
        adminGridReady = true;
        grid.innerHTML = ''; // Clear shimmer placeholders

        sorted.forEach(gate => {
            const info = data[gate];
            const card = document.createElement('div');
            card.id = `gate-box-${info.id}`;
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.className = 'gate-box bg-gradient-to-b from-gray-900 to-black rounded-[1.4rem] p-5 border border-gray-800/50 shadow-xl relative overflow-hidden group cursor-default hover:border-gray-600 hover:scale-[1.02] transition-all duration-300';
            card.innerHTML = `
                <div class="absolute inset-0 bg-gradient-to-b from-white/[0.015] to-transparent pointer-events-none rounded-[1.4rem]"></div>
                <div class="relative z-10">
                    <div class="flex justify-between items-center mb-4">
                        <span class="font-black text-xs text-gray-400 tracking-widest uppercase">${gate}</span>
                        <span id="dot-${info.id}" class="w-2.5 h-2.5 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.7)] transition-all duration-500"></span>
                    </div>
                    <div class="flex items-baseline gap-1.5 mb-4">
                        <span class="text-4xl font-black font-mono text-white transition-all" id="count-${info.id}">0</span>
                        <span class="text-gray-700 text-sm font-mono">/ ${info.max}</span>
                    </div>
                    <div class="w-full bg-black/80 rounded-full h-1.5 overflow-hidden mb-1">
                        <div id="bar-${info.id}" class="h-full rounded-full bg-blue-500 w-0 transition-all duration-700"></div>
                    </div>
                    <div class="flex justify-between mb-3">
                        <span id="pct-${info.id}" class="text-gray-700 text-[9px] font-mono">0%</span>
                        <span class="text-gray-700 text-[9px] font-mono">${info.max}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <button onclick="adminRedirect(${info.id})" class="text-[9px] uppercase font-bold tracking-widest bg-blue-500/10 text-blue-400 hover:bg-blue-500/25 border border-blue-500/20 py-2 rounded-xl transition-all">Alert</button>
                        <button onclick="adminToggleGate(${info.id})" id="lock-btn-${info.id}" class="text-[9px] uppercase font-bold tracking-widest bg-red-500/10 text-red-400 hover:bg-red-500/25 border border-red-500/20 py-2 rounded-xl transition-all">Lock</button>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });

        // Staggered entrance with GSAP (inline style, no Tailwind opacity conflict)
        gsap.to('.gate-box', { opacity: 1, y: 0, duration: 0.7, stagger: 0.06, ease: 'back.out(1.3)' });
    }

    sorted.forEach(gate => {
        const info = data[gate];
        totalCurrent += info.current;
        totalMax += info.max;

        const box     = document.getElementById(`gate-box-${info.id}`);
        const count   = document.getElementById(`count-${info.id}`);
        const bar     = document.getElementById(`bar-${info.id}`);
        const dot     = document.getElementById(`dot-${info.id}`);
        const pct     = document.getElementById(`pct-${info.id}`);
        const lockBtn = document.getElementById(`lock-btn-${info.id}`);
        if (!box || !count) return;

        const fillPct = Math.round((info.current / info.max) * 100);

        // Animate number
        const cur = { val: parseInt(count.innerText) || 0 };
        gsap.to(cur, { val: info.current, duration: 1, ease: 'power2.out',
                        onUpdate: () => count.innerText = Math.floor(cur.val) });
        
        // Bar + pct
        gsap.to(bar, { width: `${fillPct}%`, duration: 1, ease: 'power2.out' });
        if (pct) pct.innerText = `${fillPct}%`;

        // Status colors
        const cfg = {
            open:   { dot: '#3b82f6', dotGlow: '0 0 8px rgba(59,130,246,0.7)',  bar: 'bg-blue-500',    border: 'border-gray-800/50' },
            busy:   { dot: '#facc15', dotGlow: '0 0 8px rgba(250,204,21,0.7)',  bar: 'bg-yellow-400',  border: 'border-yellow-500/25' },
            full:   { dot: '#ef4444', dotGlow: '0 0 14px rgba(239,68,68,0.9)', bar: 'bg-red-500',     border: 'border-red-500/40' },
            closed: { dot: '#6b7280', dotGlow: 'none',                           bar: 'bg-gray-600',    border: 'border-gray-700/30' }
        };
        const c = cfg[info.status] || cfg.open;
        dot.style.backgroundColor = c.dot;
        dot.style.boxShadow = c.dotGlow;
        bar.className = `h-full rounded-full ${c.bar} transition-all duration-700`;
        box.className = `gate-box bg-gradient-to-b from-gray-900 to-black rounded-[1.4rem] p-5 border ${c.border} shadow-xl relative overflow-hidden group cursor-default hover:border-gray-600 hover:scale-[1.02] transition-all duration-300 ${info.status === 'closed' ? 'opacity-60 grayscale' : ''}`;

        if (lockBtn) {
            const isLocked = info.status === 'closed';
            lockBtn.innerText = isLocked ? 'Unlock' : 'Lock';
            lockBtn.className = `text-[9px] uppercase font-bold tracking-widest py-2 rounded-xl transition-all border ${isLocked
                ? 'bg-green-500/10 text-green-400 hover:bg-green-500/25 border-green-500/20'
                : 'bg-red-500/10 text-red-400 hover:bg-red-500/25 border-red-500/20'}`;
        }
    });

    // Total bar
    const totalBar  = document.getElementById('total-bar');
    const totalText = document.getElementById('total-text');
    if (totalText) {
        const cur = { val: parseInt(totalText.innerText.split(' / ')[0]) || 0 };
        gsap.to(cur, { val: totalCurrent, duration: 1.5, ease: 'power2.out',
                        onUpdate: () => totalText.innerText = `${Math.floor(cur.val)} / ${totalMax}` });
    }
    if (totalBar) gsap.to(totalBar, { width: `${(totalCurrent / totalMax) * 100}%`, duration: 2, ease: 'expo.out' });
}

function adminAddRealLog(data) {
    const container = document.getElementById('alerts-container');
    if (!container) return;
    const placeholder = container.querySelector('[data-placeholder]');
    if (placeholder) placeholder.remove();

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const div = document.createElement('div');
    div.className = 'flex items-center gap-3 p-3 rounded-xl bg-blue-900/10 border border-blue-500/15';
    div.innerHTML = `
        <div class="w-7 h-7 rounded-lg bg-blue-500/15 flex items-center justify-center text-blue-400 text-[10px] font-black shrink-0">▶</div>
        <div class="flex-grow min-w-0">
            <p class="text-xs font-bold text-white truncate">${data.log}</p>
        </div>
        <span class="text-[10px] font-mono text-gray-600 bg-black/40 px-2 py-0.5 rounded shrink-0">${time}</span>
    `;
    container.prepend(div);
    gsap.from(div, { x: 30, opacity: 0, duration: 0.6, ease: 'elastic.out(1, 0.7)' });
    if (container.children.length > 60) container.removeChild(container.lastChild);
}

// ============================================================
// STAFF LIVE DATA
// ============================================================
function updateStaffLiveData(data, currentGateName) {
    if (!data[currentGateName]) return;
    const info = data[currentGateName];

    const countEl    = document.getElementById('gate-count');
    const barEl      = document.getElementById('capacity-bar');
    const pctEl      = document.getElementById('capacity-pct');
    const remaining  = document.getElementById('remaining-slots');
    const statusSm   = document.getElementById('gate-status-sm');
    const ring       = document.getElementById('cap-ring');

    if (countEl) {
        const cur = { val: parseInt(countEl.innerText) || 0 };
        gsap.to(cur, { val: info.current, duration: 1.5, ease: 'expo.out',
                        onUpdate: () => countEl.innerText = Math.floor(cur.val) });
    }

    const pct = Math.round((info.current / info.max) * 100);

    // Update ring (circumference = 2π×48 ≈ 301.59)
    if (ring) {
        const offset = 301.59 - (pct / 100) * 301.59;
        gsap.to(ring, { attr: { 'stroke-dashoffset': offset }, duration: 1.5, ease: 'power2.out' });
        const colors = { open: '#3b82f6', busy: '#facc15', full: '#ef4444', closed: '#6b7280' };
        ring.style.stroke = colors[info.status] || colors.open;
    }

    if (barEl) {
        const colorMap = {
            open:   'from-blue-500 to-indigo-500',
            busy:   'from-yellow-400 to-orange-400',
            full:   'from-red-500 to-red-600',
            closed: 'from-gray-600 to-gray-700'
        };
        barEl.className = `h-full bg-gradient-to-r ${colorMap[info.status] || colorMap.open} rounded-full`;
        gsap.to(barEl, { width: `${pct}%`, duration: 1.5, ease: 'power2.out' });
    }

    if (pctEl) pctEl.innerText = `${pct}% filled`;
    if (remaining) {
        const cur = { val: parseInt(remaining.innerText) || 0 };
        gsap.to(cur, { val: info.max - info.current, duration: 1.5, ease: 'power2.out',
                        onUpdate: () => remaining.innerText = Math.floor(cur.val) });
    }
    if (statusSm) {
        const label = (info.status || 'open');
        statusSm.innerText = label.charAt(0).toUpperCase() + label.slice(1);
    }

    // Delegate to staff-page badge function
    if (typeof updateGateStatusBadge === 'function') updateGateStatusBadge(info.status);
}

// ============================================================
// ADMIN GATE ACTIONS
// ============================================================
window.adminRedirect = function (gateId) {
    const target = prompt(`Send crowd from Gate ${gateId} → which gate? (1–12):`);
    if (target && parseInt(target)) {
        socket.emit('admin_action', { action: 'redirect', gate_id: gateId, target_gate: parseInt(target) });
        gsap.fromTo(`#gate-box-${gateId}`,
            { boxShadow: '0 0 0 3px rgba(99,102,241,0.8)' },
            { boxShadow: '0 0 0 0px rgba(99,102,241,0)',   duration: 2 }
        );
    }
};

window.adminToggleGate = function (gateId) {
    const lockBtn = document.getElementById(`lock-btn-${gateId}`);
    const isLocked = lockBtn && lockBtn.innerText.toLowerCase() === 'unlock';
    const action = isLocked ? 'open' : 'close';
    if (confirm(`${action === 'close' ? '🔒 LOCK' : '🔓 UNLOCK'} Gate ${gateId}?`)) {
        socket.emit('admin_action', { action, gate_id: gateId });
    }
};

// ============================================================
// USER REDIRECT (inline AR path morph on user.html)
// ============================================================
function handleUserRedirect(message) {
    const match = message.match(/Gate\s*(\d+)/gi);
    if (!match || match.length < 2) return;
    const newGate = match[match.length - 1].replace(/Gate\s*/i, '');

    const gateDisplay = document.getElementById('gate-display');
    const navGate     = document.getElementById('nav-gate');
    const hint        = document.getElementById('status-hint');

    if (gateDisplay) {
        gsap.fromTo(gateDisplay, { color: '#ef4444', scale: 1.3 }, { color: '#ffffff', scale: 1, duration: 1, ease: 'bounce.out' });
        gateDisplay.innerText = `G${newGate}`;
    }
    if (navGate) navGate.innerText = newGate;
    if (hint) hint.innerText = `⚠️ Redirected! Walk to Gate ${newGate}`;

    const path = document.getElementById('ar-path');
    if (path) {
        const len = path.getTotalLength();
        gsap.to(path, {
            strokeDashoffset: len, duration: 0.5, onComplete: () => {
                path.setAttribute('d', 'M 50 170 C 64 145, 38 115, 50 85 S 66 48, 50 18');
                gsap.to(path, { strokeDashoffset: 0, duration: 2, ease: 'power2.inOut', delay: 0.1 });
            }
        });
    }
}

// ============================================================
// GLOBAL ALERT BANNER
// ============================================================
function showAlert(message, type = 'warning') {
    const banner = document.getElementById('alert-banner');
    const msg    = document.getElementById('alert-msg');
    const icon   = document.getElementById('alert-icon');
    if (!banner || !msg) return;

    const styles = {
        warning: 'fixed top-0 left-0 w-full z-[200] bg-gradient-to-r from-red-600 to-orange-600 text-white font-black py-4 px-6 text-center flex items-center justify-center gap-3 shadow-2xl',
        info:    'fixed top-0 left-0 w-full z-[200] bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-black py-4 px-6 text-center flex items-center justify-center gap-3 shadow-2xl',
        success: 'fixed top-0 left-0 w-full z-[200] bg-gradient-to-r from-green-600 to-emerald-600 text-white font-black py-4 px-6 text-center flex items-center justify-center gap-3 shadow-2xl',
    };
    banner.className = styles[type] || styles.warning;
    msg.innerText = message;
    if (icon) icon.innerText = type === 'success' ? '✅' : type === 'info' ? 'ℹ️' : '⚠️';

    gsap.to(banner, { y: 0, duration: 0.8, ease: 'bounce.out' });
    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
    setTimeout(() => gsap.to(banner, { y: '-100%', duration: 0.6, ease: 'power2.in' }), 10000);
}
