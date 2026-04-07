document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    if (!startBtn) return; // Only process if we're on the staff scanner page
    
    let codeReader;
    const resultElement = document.getElementById('scan-result');
    const scanFrame = document.getElementById('scan-frame');
    let isScanning = false;

    startBtn.addEventListener('click', () => {
        startBtn.style.display = 'none';
        
        // Lazy load to prevent issues
        codeReader = new ZXing.BrowserQRCodeReader(); 
        startScanning();
    });

    function startScanning() {
        if (isScanning) return;
        isScanning = true;
        
        codeReader.getVideoInputDevices()
            .then((videoInputDevices) => {
                // Select rear camera if multiple are available
                const device = videoInputDevices.length > 1 ? videoInputDevices[1].deviceId : videoInputDevices[0].deviceId;
                
                codeReader.decodeFromVideoDevice(device, 'video', (result, err) => {
                    if (result && isScanning) {
                        isScanning = false; // Pause while processing
                        
                        scanFrame.className = 'absolute inset-0 border-4 border-solid border-green-500 pointer-events-none rounded-2xl m-6 z-10 transition-colors shadow-[inset_0_0_20px_rgba(34,197,94,0.5)]';
                        resultElement.innerText = "Processing ticket...";
                        
                        // Fake short beep/vibration
                        if(navigator.vibrate) navigator.vibrate([100, 50, 100]);

                        // Push processing to backend Socket update
                        fetch('/scan_qr', {
                            method: 'POST',
                            headers:{ 'Content-Type': 'application/json' },
                            body: JSON.stringify({ qr_data: result.text })
                        }).then(r=>r.json()).then(data => {
                            if(data.status === 'success') {
                                resultElement.innerHTML = `<span class="text-green-500 font-bold text-lg">${data.message}</span>`;
                            } else {
                                resultElement.innerHTML = `<span class="text-red-500 font-bold text-lg">ACCESS DENIED</span>`;
                            }
                            
                            // Cooldown before next scan
                            setTimeout(() => {
                                scanFrame.className = 'absolute inset-0 border-4 border-dashed border-white/30 pointer-events-none rounded-2xl m-6 z-10 transition-colors';
                                resultElement.innerText = "Point camera at ticket QR...";
                                isScanning = true; // resume scanning
                            }, 3000);
                        });
                    }
                });
            })
            .catch((err) => {
                console.error(err);
                resultElement.innerHTML = "<span class='text-red-500'>Camera access denied or device error. Ensure HTTPS.</span>";
            });
    }
});
