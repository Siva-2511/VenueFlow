// --- Service Worker Registration ---
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js');
    });
}

// --- Theme Toggle ---
const themeToggleBtn = document.getElementById('theme-toggle');
if (themeToggleBtn) {
    // Check local storage
    if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }

    themeToggleBtn.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        localStorage.theme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
        
        // Morph the 3D scene background if it exists
        if(window.sceneBackgroundMaterial) {
            const isDark = document.documentElement.classList.contains('dark');
            gsap.to(window.sceneBackgroundMaterial.color, {
                r: isDark ? 0.06 : 0.95,
                g: isDark ? 0.06 : 0.95,
                b: isDark ? 0.06 : 0.96,
                duration: 0.6
            });
        }
    });
}

// --- Voice Commands (Web Speech API) ---
const voiceBtn = document.getElementById('voice-btn');
if (voiceBtn && 'webkitSpeechRecognition' in window) {
    const recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    voiceBtn.addEventListener('click', () => {
        voiceBtn.classList.add('animate-pulse', 'bg-blue-500', 'text-white');
        recognition.start();
    });

    recognition.onresult = (event) => {
        voiceBtn.classList.remove('animate-pulse', 'bg-blue-500', 'text-white');
        const transcript = event.results[0][0].transcript.toLowerCase();
        console.log("Voice Command: ", transcript);
        if (transcript.includes('gate 3')) {
            alert('Voice Command Intercepted: Navigating 3D Map to Gate 3');
        }
    };
    recognition.onerror = () => {
        voiceBtn.classList.remove('animate-pulse', 'bg-blue-500', 'text-white');
    }
}

// --- Login 3D Hero Scene ---
function initLogin3D() {
    const container = document.getElementById('canvas-container');
    if(!container) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    // Grid representing stadium ground
    const gridHelper = new THREE.GridHelper(100, 50, 0x3b82f6, 0x3b82f6);
    gridHelper.position.y = -5;
    scene.add(gridHelper);

    // Floating particles
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    for ( let i = 0; i < 200; i ++ ) {
        vertices.push( THREE.MathUtils.randFloatSpread( 100 ), THREE.MathUtils.randFloatSpread( 100 ), THREE.MathUtils.randFloatSpread( 100 ) );
    }
    geometry.setAttribute( 'position', new THREE.Float32BufferAttribute( vertices, 3 ) );
    const particles = new THREE.Points( geometry, new THREE.PointsMaterial( { color: 0x88CCFF, size: 0.5 } ) );
    scene.add( particles );

    camera.position.z = 30;

    function animate() {
        requestAnimationFrame(animate);
        particles.rotation.x += 0.001;
        particles.rotation.y += 0.002;
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

// --- Dashboard Logic & 3D Map ---
function initDashboard() {
    gsap.from('.intro-anim', { y: 30, opacity: 0, duration: 0.8, stagger: 0.2, ease: "power2.out" });

    fetch('/predict')
        .then(res => res.json())
        .then(data => {
            const riskCounter = document.getElementById('risk-counter');
            if(riskCounter) {
                gsap.to(riskCounter, { 
                    innerHTML: data.data["Gate 3"], 
                    duration: 2, 
                    snap: { innerHTML: 1 },
                    ease: "power1.out"
                });
            }

            const geminiText = document.getElementById('gemini-text');
            if(geminiText) {
                geminiText.innerText = data.recommendation;
            }

            const gatesList = document.getElementById('gates-list');
            if(gatesList) {
                Object.keys(data.data).forEach(gate => {
                    const value = data.data[gate];
                    const color = value > 80 ? 'bg-red-500' : (value > 50 ? 'bg-yellow-500' : 'bg-green-500');
                    gatesList.innerHTML += `
                        <div class="flex flex-col gap-1">
                            <div class="flex justify-between text-sm">
                                <span>${gate}</span>
                                <span class="font-bold">${value}%</span>
                            </div>
                            <div class="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2 overflow-hidden">
                                <div class="${color} h-2 rounded-full" style="width: 0%" data-target="${value}"></div>
                            </div>
                        </div>
                    `;
                });

                setTimeout(() => {
                    const bars = gatesList.querySelectorAll('[data-target]');
                    bars.forEach(bar => {
                        gsap.to(bar, { width: bar.getAttribute('data-target') + '%', duration: 1.5, ease: "power2.out" });
                    });
                }, 500);
            }
        });

    const container = document.getElementById('stadium-canvas');
    if(!container) return;

    const scene = new THREE.Scene();
    
    // Background morphing config
    const isDark = document.documentElement.classList.contains('dark');
    scene.background = new THREE.Color(isDark ? 0x111111 : 0xffffff);
    window.sceneBackgroundMaterial = scene.background;

    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(10, 20, 10);
    scene.add(dirLight);

    // Mock Stadium
    const stadiumGeo = new THREE.TorusGeometry(10, 3, 16, 100);
    const stadiumMat = new THREE.MeshPhongMaterial({ color: 0x3b82f6, wireframe: true });
    const stadium = new THREE.Mesh(stadiumGeo, stadiumMat);
    stadium.rotation.x = Math.PI / 2;
    scene.add(stadium);

    // Red Pulse Hotspot
    const hotspotGeo = new THREE.SphereGeometry(1.5, 32, 32);
    const hotspotMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    const hotspot = new THREE.Mesh(hotspotGeo, hotspotMat);
    hotspot.position.set(8, 2, 0);
    scene.add(hotspot);

    gsap.to(hotspot.scale, { x: 1.5, y: 1.5, z: 1.5, duration: 1, yoyo: true, repeat: -1 });

    camera.position.set(0, 20, 30);
    camera.lookAt(0, 0, 0);

    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };
    
    container.addEventListener('mousedown', () => { isDragging = true; });
    container.addEventListener('mousemove', (e) => {
        if(isDragging) {
            const deltaMove = { x: e.offsetX - previousMousePosition.x, y: e.offsetY - previousMousePosition.y };
            scene.rotation.y += deltaMove.x * 0.01;
        }
        previousMousePosition = { x: e.offsetX, y: e.offsetY };
    });
    window.addEventListener('mouseup', () => { isDragging = false; });

    scene.position.y = -20;
    gsap.to(scene.position, { y: 0, duration: 2, ease: "power3.out" });

    function animate() {
        requestAnimationFrame(animate);
        if(!isDragging) {
            scene.rotation.y += 0.002;
        }
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        if(container.clientWidth > 0) {
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        }
    });
}
