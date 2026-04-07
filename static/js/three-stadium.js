function initLogin3D() {
    const container = document.getElementById('canvas-container');
    if(!container || !window.THREE) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, window.innerWidth/window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    const gridHelper = new THREE.GridHelper(100, 50, 0x3b82f6, 0x3b82f6);
    gridHelper.position.y = -5;
    scene.add(gridHelper);

    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    for ( let i = 0; i < 250; i ++ ) {
        vertices.push( THREE.MathUtils.randFloatSpread(100), THREE.MathUtils.randFloatSpread(100), THREE.MathUtils.randFloatSpread(100) );
    }
    geometry.setAttribute( 'position', new THREE.Float32BufferAttribute( vertices, 3 ) );
    const particles = new THREE.Points( geometry, new THREE.PointsMaterial( { color: 0x88CCFF, size: 0.6, transparent: true, opacity: 0.8 } ) );
    scene.add( particles );

    camera.position.z = 25;
    camera.position.y = 5;
    camera.lookAt(0,0,0);

    function animate() {
        requestAnimationFrame(animate);
        particles.rotation.y += 0.001;
        particles.rotation.x += 0.0005;
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}
