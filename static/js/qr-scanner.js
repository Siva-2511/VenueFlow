document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('start-btn');
    if (!startBtn) return; // Only process on Staff page
    
    let codeReader;
    const resultElement = document.getElementById('scan-result');
    const scanFrame = document.getElementById('scan-frame');
    const scanSuccess = document.getElementById('scan-success');
    const entryList = document.getElementById('entry-list');
    let isScanning = false;

    startBtn.addEventListener('click', () => {
        startBtn.style.display = 'none';
        codeReader = new ZXing.BrowserQRCodeReader(); 
        startScanning();
    });

    function startScanning() {
        if (isScanning) return;
        isScanning = true;
        
        codeReader.getVideoInputDevices()
            .then((videoInputDevices) => {
                const device = videoInputDevices.length > 1 ? videoInputDevices[1].deviceId : videoInputDevices[0].deviceId;
                
                codeReader.decodeFromVideoDevice(device, 'video', (result, err) => {
                    if (result && isScanning) {
                        isScanning = false;
                        
                        scanFrame.className = 'absolute inset-0 border-4 border-solid border-blue-500 pointer-events-none rounded-[2rem] m-6 z-10 transition-colors shadow-[inset_0_0_20px_rgba(59,130,246,0.5)]';
                        resultElement.innerHTML = `<span class="text-blue-400 font-bold uppercase tracking-widest text-[10px]">Processing Database Link...</span>`;
                        
                        if(navigator.vibrate) navigator.vibrate([100, 50, 100]);

                        fetch('/scan_qr', {
                            method: 'POST',
                            headers:{
                                'Content-Type': 'application/json',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            credentials: 'same-origin',
                            body: JSON.stringify({ qr_data: result.text })
                        }).then(r => {
                            if (r.status === 403) throw new Error('Not authorized — please log in as staff');
                            if (r.status === 401) throw new Error('Session expired — please refresh and log in');
                            return r.json();
                        }).then(data => {
                            if(data.status === 'success') {
                                scanFrame.className = 'absolute inset-0 border-4 border-solid border-green-500 pointer-events-none rounded-[2rem] m-6 z-10 transition-colors shadow-[inset_0_0_30px_rgba(34,197,94,0.6)]';
                                scanSuccess.classList.remove('hidden');
                                gsap.fromTo(scanSuccess, {scale: 0.5, opacity: 0}, {scale: 1, opacity: 1, duration: 0.5, ease: "back.out(2)"});
                                resultElement.innerHTML = `<span class="text-green-500 font-black text-xl drop-shadow-[0_0_10px_rgba(34,197,94,0.5)]">ACCESS GRANTED</span>`;
                                
                                if(entryList) {
                                    if(entryList.innerHTML.includes('Waiting for scans')) entryList.innerHTML = '';
                                    const entry = document.createElement('div');
                                    entry.className = "bg-gradient-to-r from-gray-900 to-black border border-gray-800 p-4 rounded-xl flex justify-between items-center text-xs font-mono text-gray-300 shadow-xl";
                                    const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'});
                                    const ud = data.user_data || {};
                                    const pastWarn = data.match_past ? '<span style="color:#fbbf24;font-size:9px;margin-left:6px">⚠️ PAST</span>' : '';
                                    entry.innerHTML = `<span class="text-blue-400 font-bold tracking-widest uppercase">IN</span> <span class="text-gray-100 font-bold px-2">${ud.name||data.user}</span>${pastWarn} <span class="bg-black py-1 px-2 rounded-lg text-gray-500">${time}</span>`;
                                    entryList.prepend(entry);
                                    gsap.from(entry, { x: -50, opacity: 0, scale: 0.9, duration: 0.6, ease: "elastic.out(1, 0.75)" });
                                }

                            } else {
                                resultElement.innerHTML = `<span class="text-red-500 font-black text-xl drop-shadow-[0_0_15px_rgba(239,68,68,0.7)] uppercase">${data.message}</span>`;
                                scanFrame.className = 'absolute inset-0 border-4 border-solid border-red-500 pointer-events-none rounded-[2rem] m-6 z-10 transition-colors shadow-[inset_0_0_50px_rgba(239,68,68,0.8)]';
                                gsap.fromTo(scanFrame, { x: -10 }, { x: 10, yoyo: true, repeat: 7, duration: 0.05 });
                                if(navigator.vibrate) navigator.vibrate([200, 100, 200]);
                            }
                            
                            setTimeout(() => {
                                scanSuccess.classList.add('hidden');
                                scanFrame.className = 'absolute inset-0 border-2 border-dashed border-white/20 pointer-events-none rounded-[2rem] m-6 z-10 transition-colors';
                                resultElement.innerHTML = "<span class='text-gray-500 uppercase tracking-widest font-bold text-[10px]'>Awaiting optic link...</span>";
                                isScanning = true;
                            }, 2500);
                        }).catch(err => {
                            resultElement.innerHTML = `<span class="text-red-400 font-bold text-sm">${err.message || 'Network error'}</span>`;
                            scanFrame.className = 'absolute inset-0 border-4 border-solid border-red-500 pointer-events-none rounded-[2rem] m-6 z-10';
                            setTimeout(() => {
                                scanFrame.className = 'absolute inset-0 border-2 border-dashed border-white/20 pointer-events-none rounded-[2rem] m-6 z-10';
                                resultElement.innerHTML = "<span class='text-gray-500 uppercase tracking-widest font-bold text-[10px]'>Awaiting optic link...</span>";
                                isScanning = true;
                            }, 3000);
                        });
                    }
                });
            })
            .catch((err) => {
                console.error(err);
                resultElement.innerHTML = "<span class='text-red-500 text-xs font-bold'>Camera error. Use HTTPS context.</span>";
            });
    }
});
