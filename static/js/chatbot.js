/**
 * VenueFlow AI Chatbot Logic
 * Handles the floating UI, state management, and API calls.
 */
class VenueFlowChat {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.msgHistory = []; // Track timestamps for rate limiting
        this.init();
    }

    init() {
        // Toggle button and window
        this.btn = document.getElementById('chat-toggle');
        this.window = document.getElementById('chat-window');
        this.form = document.getElementById('chat-form');
        this.input = document.getElementById('chat-input');
        this.container = document.getElementById('chat-messages');

        if (!this.btn || !this.window) return;

        this.btn.onclick = () => this.toggle();
        this.form.onsubmit = (e) => {
            e.preventDefault();
            this.send();
        };

        // Close on Esc
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) this.toggle();
        });

        // Greeting
        this.addMessage('bot', "Hello! I'm VenueFlow AI. How can I assist you with the stadium experience today? 🏏");
    }

    toggle() {
        this.isOpen = !this.isOpen;
        if (this.isOpen) {
            this.window.style.display = 'flex';
            this.window.classList.add('animate-in');
            this.input.focus();
        } else {
            this.window.style.display = 'none';
        }
    }

    addMessage(sender, text) {
        const div = document.createElement('div');
        div.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'} mb-3`;
        
        const content = document.createElement('div');
        content.className = `max-w-[80%] rounded-2xl px-4 py-2 text-xs font-medium leading-relaxed ${
            sender === 'user' 
            ? 'bg-indigo-600 text-white rounded-tr-none' 
            : 'bg-white/5 border border-white/10 text-gray-200 rounded-tl-none'
        }`;
        content.innerText = text;
        
        div.appendChild(content);
        this.container.appendChild(div);
        this.container.scrollTop = this.container.scrollHeight;
        
        if (window.gsap) {
            try {
                gsap.from(content, { opacity: 0, scale: 0.8, x: sender === 'user' ? 10 : -10, duration: 0.3 });
            } catch (e) {
                content.style.opacity = '1';
            }
        } else {
            content.style.opacity = '1';
        }
    }

    async send() {
        const msg = this.input.value.trim();
        if (!msg) return;

        // Rate Limiting: Max 10 messages per minute
        const now = Date.now();
        this.msgHistory = this.msgHistory.filter(t => now - t < 60000);
        if (this.msgHistory.length >= 10) {
            this.addMessage('bot', "System standard: Please wait a moment (Quota protection active) 🛡️");
            return;
        }
        this.msgHistory.push(now);

        this.input.value = '';
        this.addMessage('user', msg);

        // Typing indicator
        const loading = document.createElement('div');
        loading.className = 'text-[10px] text-indigo-400 font-mono italic animate-pulse mb-2';
        loading.innerText = 'AI is thinking...';
        this.container.appendChild(loading);

        try {
            const res = await fetch('/api/ai_assist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg, context: 'Role: Assistant Chat' })
            });
            const data = await res.json();
            
            this.container.removeChild(loading);
            this.addMessage('bot', data.response || "I'm having trouble connecting right now.");
        } catch (e) {
            this.container.removeChild(loading);
            this.addMessage('bot', "Error: System unreachable.");
        }
    }
}

// Global "Pro-Tip" Assistant
async function loadSmartTip(page) {
    const tipEl = document.getElementById('ai-pro-tip');
    if (!tipEl) return;
    
    try {
        const res = await fetch(`/api/ai_assist?page=${page}`);
        const data = await res.json();
        if (data.status === 'success') {
            tipEl.innerText = data.tip;
            if (window.gsap) gsap.from(tipEl, { opacity: 0, y: 5, duration: 1 });
        }
    } catch(e) {}
}

document.addEventListener('DOMContentLoaded', () => {
    window.vfChat = new VenueFlowChat();
    // Auto-load tip if container exists
    const main = document.querySelector('main');
    if (main) {
        const pageName = document.title.split('|')[1]?.trim().toLowerCase() || 'dashboard';
        loadSmartTip(pageName);
    }
});
