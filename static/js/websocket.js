let socket;

function initWebSockets(role) {
    socket = io();
    
    socket.on('connect', () => {
        console.log('Connected to VenueFlow WebSocket');
    });

    socket.on('gate_update', (data) => {
        if (role === 'admin') {
            updateAdminDashboard(data);
        } else if (role === 'staff') {
            updateStaffDashboard(data);
        }
    });

    socket.on('entry_update', () => {
        if (navigator.vibrate) navigator.vibrate([100, 50, 100]); // Haptic feedback on entry
    });
}

function updateAdminDashboard(data) {
    const grid = document.getElementById('gates-grid');
    const alertsContainer = document.getElementById('alerts-container');
    
    if (!grid) return;
    
    let totalCurrent = 0;
    let totalMax = 0;
    let newAlerts = false;
    let alertsHTML = '';

    grid.innerHTML = '';
    
    // Render gates UI
    Object.keys(data).forEach(gate => {
        const info = data[gate];
        totalCurrent += info.current;
        totalMax += info.max;
        
        let colorClass = 'bg-green-500';
        if (info.status === 'full') {
            colorClass = 'bg-red-500';
            newAlerts = true;
            alertsHTML += `<div class="p-4 bg-red-900/20 border border-red-500 rounded-xl text-sm text-red-200">🚨 <b>${gate}</b> capacity critical. Override needed.</div>`;
        } else if (info.status === 'busy') {
            colorClass = 'bg-yellow-500';
        }

        grid.innerHTML += `
            <div class="bg-gray-800 rounded-2xl p-4 border border-white/5 transition-all duration-300 ${info.status==='full'?'ring-2 ring-red-500/80 shadow-[0_0_15px_rgba(239,68,68,0.5)]':''}">
                <div class="flex justify-between items-center mb-3">
                    <span class="font-semibold text-sm uppercase tracking-wider text-gray-300">${gate}</span>
                    <span class="w-3 h-3 rounded-full ${colorClass} ${info.status==='full'?'pulse-dot':''}"></span>
                </div>
                <div class="text-xl font-bold font-mono text-white mb-2">${info.current} / <span class="text-gray-500 text-sm">${info.max}</span></div>
                <div class="w-full bg-black/60 rounded-full h-2">
                    <div class="${colorClass} h-full rounded-full transition-all duration-700" style="width: ${(info.current/info.max)*100}%"></div>
                </div>
            </div>
        `;
    });

    // Totals processing
    const totalText = document.getElementById('total-text');
    const totalBar = document.getElementById('total-bar');
    if(totalText) totalText.innerText = `${totalCurrent} / ${totalMax}`;
    if(totalBar) totalBar.style.width = `${(totalCurrent/totalMax)*100}%`;

    // Alert injections
    if(alertsContainer) {
        if(newAlerts) {
            alertsContainer.innerHTML = alertsHTML;
        } else {
            alertsContainer.innerHTML = `<p class="text-green-500 italic text-sm py-2">✓ Entire grid operating normally.</p>`;
        }
    }
}

function updateStaffDashboard(data) {
    const statusDot = document.getElementById('gate5-status');
    const countText = document.getElementById('gate5-count');
    
    if(!statusDot || !countText) return;
    
    if(data['Gate 5']) {
        const info = data['Gate 5'];
        countText.innerText = `${info.current}`;
        
        statusDot.className = 'absolute top-4 right-4 w-3 h-3 rounded-full pulse-dot bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.8)]';
        
        if (info.status === 'full') {
            statusDot.className = 'absolute top-4 right-4 w-3 h-3 rounded-full pulse-dot bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]';
        } else if (info.status === 'busy') {
            statusDot.className = 'absolute top-4 right-4 w-3 h-3 rounded-full pulse-dot bg-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.8)]';
        }
    }
}
