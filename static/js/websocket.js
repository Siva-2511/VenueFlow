let socket;

function initWebSockets(role, currentGateName = null, gateId = null) {
    socket = io();
    
    socket.on('connect', () => {});
    
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

    socket.on('user_registered', (data) => {
        if (role === 'staff') {
            // Delegate to staff page pending-arrivals system
            if (typeof window.onUserRegistered === 'function') window.onUserRegistered(data);
            showAlert(`🔔 New arrival assigned: ${data.name || data.email}`, 'info');
        }
        if (role === 'admin') {
            adminNewUser++;
            const kpiEl = document.getElementById('kpi-new');
            if (kpiEl) {
                const cur = { v: parseInt(kpiEl.innerText) || 0 };
                gsap.to(cur, { v: adminNewUser, duration: .8, ease: 'expo.out', onUpdate: () => kpiEl.innerText = Math.floor(cur.v) });
            }
            adminAddRealLog({ log: `👤 New user registered: ${data.email} → Gate ${data.gate_id}`, gate: `G${data.gate_id}` });
        }
    });
}

let adminNewUser = 0;

// ============================================================
// ADMIN DASHBOARD
// ============================================================
let adminGridReady = false;

function updateAdminDashboard(data) {
    const grid = document.getElementById('gates-grid');
    if (!grid) return;
    
    let totalCurrent = 0, totalMax = 0;

    const sorted = Object.keys(data)
        .filter(k => k !== '__meta__')
        .sort((a, b) => parseInt(a.replace('Gate ', '')) - parseInt(b.replace('Gate ', '')));

    if (!adminGridReady) {
        adminGridReady = true;
        grid.innerHTML = ''; // Clear shimmer placeholders

        sorted.forEach(gate => {
            const info = data[gate];
            const card = document.createElement('div');
            card.id = `gate-box-${info.id}`;
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px) scale(0.95)';
            card.className = 'gate-box gate-cell glass rounded-2xl p-4 border border-indigo-500/15 relative overflow-hidden cursor-pointer';
            card.addEventListener('click', (e) => {
                if(e.target.tagName==='BUTTON') return; // don't intercept action buttons
                if(typeof openGateModal === 'function') openGateModal(info.id, gate);
            });
            const neonCfg = { open: { border:'rgba(59,130,246,.4)', dot:'#3b82f6', glow:'rgba(59,130,246,.5)' }, busy: { border:'rgba(245,158,11,.4)', dot:'#f59e0b', glow:'rgba(245,158,11,.5)' }, full: { border:'rgba(239,68,68,.5)', dot:'#ef4444', glow:'rgba(239,68,68,.7)' }, closed: { border:'rgba(107,114,128,.25)', dot:'#6b7280', glow:'none' } };
            const nc = neonCfg[info.status] || neonCfg.open;
            card.innerHTML = `
                <div class="absolute top-0 left-0 right-0 h-0.5" style="background:${nc.border}"></div>
                <div class="flex justify-between items-center mb-3">
                    <span class="font-orb text-[9px] font-black tracking-widest" style="color:rgba(255,255,255,.45)">${gate}</span>
                    <span id="dot-${info.id}" class="w-2.5 h-2.5 rounded-full transition-all duration-500" style="background:${nc.dot};box-shadow:0 0 8px ${nc.glow}"></span>
                </div>
                <div class="flex items-baseline gap-1 mb-3">
                    <span class="font-orb text-3xl font-black text-white" id="count-${info.id}">0</span>
                    <span class="text-xs font-mono" style="color:rgba(255,255,255,.4)">/${info.max}</span>
                </div>
                <div class="relative h-1.5 rounded-full overflow-hidden mb-2" style="background:rgba(255,255,255,.04)">
                    <div id="bar-${info.id}" class="absolute left-0 top-0 h-full rounded-full w-0 transition-all duration-700" style="background:${nc.dot}"></div>
                </div>
                <div class="flex justify-between items-center mb-3">
                    <span id="pct-${info.id}" class="text-[8px] font-mono font-bold" style="color:${nc.dot}">0%</span>
                    <span class="text-[8px] font-mono" style="color:rgba(255,255,255,.35)">${info.max}</span>
                </div>
                <div class="gate-actions grid grid-cols-2 gap-1.5">
                    <button onclick="adminRedirect(${info.id})" class="text-[7px] font-orb font-black uppercase tracking-widest py-1.5 rounded-lg border transition-all" style="background:rgba(99,102,241,.1);color:#818cf8;border-color:rgba(99,102,241,.25)" onmouseover="this.style.background='rgba(99,102,241,.25)'" onmouseout="this.style.background='rgba(99,102,241,.1)'">Alert</button>
                    <button onclick="adminToggleGate(${info.id})" id="lock-btn-${info.id}" class="text-[7px] font-orb font-black uppercase tracking-widest py-1.5 rounded-lg border transition-all" style="background:rgba(239,68,68,.1);color:#f87171;border-color:rgba(239,68,68,.25)" onmouseover="this.style.background='rgba(239,68,68,.25)'" onmouseout="this.style.background='rgba(239,68,68,.1)'">Lock</button>
                </div>
            `;
            grid.appendChild(card);
        });
        gsap.to('.gate-box', { opacity: 1, y: 0, scale: 1, duration: 0.7, stagger: 0.05, ease: 'back.out(1.3)' });
    }

    const neonColors = { open:'#3b82f6', busy:'#f59e0b', full:'#ef4444', closed:'#6b7280' };
    sorted.forEach((gate, idx) => {
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
        const nc = neonColors[info.status] || neonColors.open;

        // Animate number counter
        const cur = { val: parseInt(count.innerText) || 0 };
        gsap.to(cur, { val: info.current, duration: 1.2, ease: 'expo.out',
                        onUpdate: () => count.innerText = Math.floor(cur.val) });
        
        // Bar + pct
        if (bar) { gsap.to(bar, { width: `${fillPct}%`, duration: 1.2, ease: 'expo.out' }); bar.style.background = nc; }
        if (pct) { pct.innerText = `${fillPct}%`; pct.style.color = nc; }
        if (dot) { dot.style.background = nc; dot.style.boxShadow = `0 0 10px ${nc}`; }

        // Update neon border on box top line
        const topBar = box.querySelector(':scope > div:first-child');
        if (topBar) topBar.style.background = nc;

        // Particle burst if full
        if (info.status === 'full') {
            gsap.fromTo(box, { boxShadow: `0 0 40px ${nc}` }, { boxShadow: '0 0 0 rgba(0,0,0,0)', duration: 2 });
            if (fillPct >= 90 && Math.random() > 0.7) {
                gsap.fromTo('body', { filter: 'brightness(1.4) saturate(1.4)' }, { filter: 'brightness(1) saturate(1)', duration: .8 });
            }
        }
        if (info.status === 'closed') { box.style.opacity = '.5'; box.style.filter = 'grayscale(0.6)'; }
        else { box.style.opacity = '1'; box.style.filter = 'none'; }

        if (lockBtn) {
            const isLocked = info.status === 'closed';
            lockBtn.innerText = isLocked ? 'Unlock' : 'Lock';
            lockBtn.style.background = isLocked ? 'rgba(34,197,94,.1)' : 'rgba(239,68,68,.1)';
            lockBtn.style.color = isLocked ? '#4ade80' : '#f87171';
            lockBtn.style.borderColor = isLocked ? 'rgba(34,197,94,.25)' : 'rgba(239,68,68,.25)';
        }

        // Update Three.js stadium pillar
        if (typeof window._updateStadiumPillar === 'function') {
            window._updateStadiumPillar(idx, fillPct / 100, info.status);
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

    // Update KPI Total Crowd card (uses __meta__ from backend)
    const meta = data['__meta__'];
    if (meta && typeof window._updateTotalCrowdKPI === 'function') {
        window._updateTotalCrowdKPI(meta.total, meta.max);
    } else {
        // fallback: sum from sorted data
        if (typeof window._updateTotalCrowdKPI === 'function') {
            window._updateTotalCrowdKPI(totalCurrent, totalMax);
        }
    }
}

function adminAddRealLog(data) {
    const container = document.getElementById('alerts-container');
    if (!container) return;
    const placeholder = container.querySelector('[data-placeholder]');
    if (placeholder) placeholder.remove();

    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const div = document.createElement('div');
    div.style.cssText = 'display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:8px;border-left:2px solid rgba(34,197,94,.5);background:rgba(34,197,94,.05);font-family:JetBrains Mono,monospace;font-size:10px';
    div.innerHTML = `<span style="color:#4ade80;font-weight:900">[IN]</span><span style="color:#86efac;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${data.log}</span><span style="color:rgba(255,255,255,.45);font-size:9px">${data.gate||''}</span><span style="color:rgba(255,255,255,.4);font-size:9px">${time}</span>`;
    container.prepend(div);
    gsap.from(div, { x: 20, opacity: 0, duration: 0.4, ease: 'power3.out' });
    if (container.children.length > 80) container.removeChild(container.lastChild);
    // bump flow chart queue
    if (typeof window._scanQueueAdd === 'function') window._scanQueueAdd();
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

    // Update ring (circumference = 2π×52 ≈ 326.7)
    if (ring) {
        const offset = 326.7 - (pct / 100) * 326.7;
        gsap.to(ring, { attr: { 'stroke-dashoffset': Math.max(0, offset) }, duration: 1.5, ease: 'elastic.out(1,.75)' });
        const colors = { open: 'url(#rg)', busy: '#f59e0b', full: '#ef4444', closed: '#6b7280' };
        ring.setAttribute('stroke', colors[info.status] || colors.open);
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

    const gradients = {
        warning: 'linear-gradient(135deg,rgba(139,92,246,.95),rgba(239,68,68,.95))',
        info:    'linear-gradient(135deg,rgba(59,130,246,.95),rgba(6,182,212,.95))',
        success: 'linear-gradient(135deg,rgba(34,197,94,.95),rgba(6,182,212,.95))',
    };
    banner.style.background = gradients[type] || gradients.warning;
    msg.innerText = message;
    if (icon) icon.innerText = type === 'success' ? '✅' : type === 'info' ? 'ℹ️' : '⚠️';

    gsap.to(banner, { y: 0, duration: 0.6, ease: 'back.out(1.4)' });
    if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
    // Screen flash for critical alerts
    if (type === 'warning') {
        gsap.fromTo('body', { filter: 'brightness(1.5) saturate(1.5)' }, { filter: 'brightness(1) saturate(1)', duration: 1 });
        try { const ac=new(AudioContext||webkitAudioContext)();const o=ac.createOscillator();const g=ac.createGain();o.connect(g);g.connect(ac.destination);o.type='sawtooth';o.frequency.value=220;g.gain.setValueAtTime(.04,ac.currentTime);g.gain.linearRampToValueAtTime(0,ac.currentTime+0.5);o.start();o.stop(ac.currentTime+0.5); }catch{}
    }
    setTimeout(() => gsap.to(banner, { y: '-100%', duration: 0.5, ease: 'power2.in' }), 8000);
}
