// =========================================================
// FUNCIONES GLOBALES PARA SER LLAMADAS POR EL ONCLICK
// =========================================================

// Función de utilidad: No depende de variables locales de DOMContentLoaded
function checkSecureContext() {
    return true; 
}

// 🎯 FUNCIÓN GLOBAL: Debe estar al inicio del archivo para ser encontrada por el onclick
async function tryToStartCameraFlow(e) {
    // Si la función es llamada desde onclick, e es el objeto evento
    if (e && e.preventDefault) {
        e.preventDefault(); 
        e.stopPropagation(); 
    }
    
    // Solo si el DOM está cargado, podemos acceder a las referencias
    if (typeof initializeWebcam === 'undefined') {
        console.error("Webcam no inicializada. DOM no listo.");
        return false;
    }

    const startButton = document.getElementById('start-webcam-btn'); 
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        initializeWebcam.showMessage("Tu navegador no soporta la API de cámara.", true);
        if (startButton) {
            startButton.disabled = true;
            startButton.textContent = "Cámara No Soportada";
        }
        return false; 
    }
    
    if (startButton) {
        startButton.disabled = true;
        startButton.textContent = "Cargando...";
    }

    const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => { reject(new Error("TimeoutError")); }, 12000)
    );

    const softConstraints = { 
        video: { facingMode: "user", width: { ideal: 320 }, height: { ideal: 240 } } 
    };
    const minimalConstraints = { video: true };

    try {
        await Promise.race([initializeWebcam.startCamera(softConstraints), timeoutPromise]);
    } catch (err1) {
        if (err1.name !== "TimeoutError" && err1.name !== "SecurityError" && err1.name !== "NotAllowedError" && err1.name !== "HTMLElementNotFoundError") {
            if (startButton) startButton.textContent = "Intentando con restricciones mínimas...";
            try {
                await Promise.race([initializeWebcam.startCamera(minimalConstraints), timeoutPromise]);
            } catch (err2) {
                initializeWebcam.handleCameraError(err2);
            }
        } else {
            initializeWebcam.handleCameraError(err1);
        }
    }

    return false; // Fuerza la detención del envío de formulario.
}

// Objeto para contener todas las funciones privadas
const initializeWebcam = {
    // Referencias y variables
    video: null,
    canvas: null,
    captureButton: null,
    startButton: null,
    fotoPerfilInput: null,
    form: null,
    messageContainer: null,
    stream: null,
    videoInitialized: false,

    showMessage: function(msg, isError = false) {
        if (!this.messageContainer) return; 
        this.messageContainer.innerHTML = '';
        const div = document.createElement('div');
        div.innerHTML = msg;
        div.className = 'alert ' + (isError ? 'alert-danger' : 'alert-success'); 
        this.messageContainer.appendChild(div);
        const duration = isError ? 15000 : 5000;
        if (!isError) {
            setTimeout(() => div.remove(), duration); 
        }
    },

    initializeCameraUI: function() {
        if (this.videoInitialized) return; 
        this.videoInitialized = true;
        if (this.startButton) this.startButton.style.display = 'none'; 
        
        if (this.video) this.video.style.display = 'block'; 
        if (this.captureButton) {
            this.captureButton.style.display = 'block';
            this.captureButton.disabled = false;
            this.captureButton.textContent = "📸 Tomar Foto";
            this.captureButton.style.opacity = 1;
        }
        this.showMessage("Cámara iniciada correctamente. Cuando termine, puede tomar la foto.", false);
    },

    startCamera: function(constraints) {
         return new Promise((resolve, reject) => {
            if (!this.video) {
                reject(new Error("HTMLElementNotFoundError: El elemento 'video' no se encontró."));
                return;
            }
            
            navigator.mediaDevices.getUserMedia(constraints) 
                .then(s => {
                    this.stream = s;
                    this.video.srcObject = s;
                    this.video.play();
                    this.video.addEventListener('playing', this.initializeCameraUI.bind(this), { once: true });
                    this.video.onloadedmetadata = function() {
                        if (this.readyState >= 3) {
                            setTimeout(() => {
                                if (!initializeWebcam.videoInitialized) {
                                    initializeWebcam.initializeCameraUI();
                                }
                            }, 5000);
                        }
                    }
                    resolve();
                })
                .catch(err => {
                    reject(err);
                });
        });
    },

    handleCameraError: function(err) {
        if (this.stream) this.stopCamera();
        let errorName = err.name || (err.message && err.message.includes('TimeoutError') ? 'TimeoutError' : 'ErrorDesconocido');
        let errorMessage = `❌ **No se pudo iniciar la cámara.** Error: **${errorName}**. `;
        
        if (errorName === "NotAllowedError" || errorName === "SecurityError") {
            errorMessage += "El acceso fue **denegado** por el usuario o bloqueado por el navegador. Recargue y otorgue permiso.";
        } else if (errorName === "NotFoundError") {
            errorMessage += "No se encontró ninguna cámara conectada.";
        } else if (errorName === "NotReadableError") {
            errorMessage += "La cámara está siendo usada por otra aplicación.";
        } else if (errorName === "TimeoutError") {
             errorMessage = "❌ **Fallo por Tiempo de Espera.** La cámara no respondió en 12 segundos.";
        } else {
            errorMessage += `Error desconocido o ${err.message}.`;
        }

        this.showMessage(errorMessage, true);
        if (this.startButton) {
            this.startButton.textContent = "❌ Fallo al iniciar Cámara";
            this.startButton.disabled = true;
        }
        if (this.captureButton) this.captureButton.style.display = 'none';
    },

    stopCamera: function() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => {
                if (track.readyState === 'live') {
                    track.stop();
                }
            });
            this.stream = null;
            this.videoInitialized = false;
            if (this.video) this.video.style.display = 'none';
            if (this.captureButton) this.captureButton.style.display = 'none';
            if (this.startButton) {
                this.startButton.style.display = 'block'; 
                this.startButton.disabled = false;
                this.startButton.textContent = "▶️ Activar Cámara / Escanear QR";
            }
            console.log("Cámara detenida y liberada.");
        }
    },
    
    // Función de inicialización
    init: function() {
        this.video = document.getElementById('webcam-feed');
        this.canvas = document.getElementById('photo-canvas');
        this.captureButton = document.getElementById('capture-btn');
        this.startButton = document.getElementById('start-webcam-btn'); 
        this.fotoPerfilInput = document.getElementById('id_foto_perfil'); 
        this.form = document.querySelector('form');
        this.messageContainer = document.getElementById('status-message');

        if (!this.startButton) {
            console.error("ERROR CRÍTICO: El botón 'start-webcam-btn' no existe en el HTML.");
            return; 
        }

        // FUERZA EL ESTADO INICIAL DEL BOTÓN:
        this.startButton.style.display = 'block'; 
        this.startButton.disabled = false;
        this.startButton.textContent = "▶️ Activar Cámara / Escanear QR";

        // --- Event Listener para el botón de Captura ---
        this.captureButton.addEventListener('click', this.handleCapture.bind(this));
        
        if (this.form) this.form.addEventListener('submit', this.stopCamera.bind(this)); 
        window.addEventListener('beforeunload', this.stopCamera.bind(this));
    },

    handleCapture: function(e) {
        e.preventDefault(); 

        if (!this.videoInitialized || !this.stream || !this.canvas || !this.fotoPerfilInput) {
            this.showMessage("La cámara o los elementos de destino no están listos.", true);
            return;
        }
        
        this.canvas.width = this.video.videoWidth;
        this.canvas.height = this.video.videoHeight;
        const context = this.canvas.getContext('2d');
        context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        
        this.canvas.toBlob((blob) => {
            if (blob) {
                const fileName = `empleado_capture_${Date.now()}.jpeg`;
                const file = new File([blob], fileName, { type: 'image/jpeg' });
                
                try {
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(file);
                    this.fotoPerfilInput.files = dataTransfer.files;
                } catch (e) {
                    console.warn("DataTransfer falló. Usando hack de FileList.", e);
                    const fileList = Object.assign(new Array(1), { 0: file, length: 1 });
                    this.fotoPerfilInput.files = fileList;
                    if (this.fotoPerfilInput.files.length === 0) {
                        this.showMessage("Error al asignar la foto al campo 'Foto de Perfil'. Pruebe a subir el archivo manualmente.", true);
                    }
                }
                
                if (this.captureButton) {
                    this.captureButton.textContent = "✅ ¡Foto Capturada! Listo para Guardar";
                    this.captureButton.style.backgroundColor = "#28a745";
                    this.captureButton.style.opacity = 1;
                }
                this.showMessage("Foto capturada y asignada. ¡Guarde el formulario para subirla!", false);
                this.stopCamera(); 
                
            } else {
                this.showMessage("Error al procesar la imagen capturada (Blob fallido).", true);
            }
        }, 'image/jpeg', 0.9);
    }
};

// Iniciar después de que el DOM esté completamente cargado
window.addEventListener('DOMContentLoaded', () => {
    initializeWebcam.init();
});