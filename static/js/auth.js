document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('real-login');
    if(form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            submitLogin({ email, password, type: 'credentials' });
        });
    }
});

function handleAuth(type) {
    submitLogin({ type });
}

function submitLogin(payload) {
    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).then(r => r.json()).then(data => {
        if(data.status === 'success') {
            gsap.to('.login-card', { scale: 0.9, opacity: 0, duration: 0.4, onComplete: () => {
                window.location.href = data.redirect;
            }});
        } else {
            alert(data.message || 'Login credentials invalid.');
        }
    }).catch(err => {
        alert("Server error processing login request.");
    });
}
