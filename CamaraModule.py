import os
import time
import threading
from datetime import datetime

import requests
import cv2
import numpy as np


DEFAULT_CAPTURE_PORT = 8080
DEFAULT_CAPTURE_PATH = "photo.jpg"
DEFAULT_TIMEOUT = 10
DEFAULT_FRAME_GAP = 1.5
DEFAULT_DIFF_THRESHOLD = 30
MIN_AREA_FACTOR = 0.01 


class CamaraManager:
    """Gestión y monitoreo de cámaras.

    Responsabilidades separadas por grupos de métodos:
    - Gestión de cámaras activas (activar/desactivar)
    - Captura y guardado de imágenes
    - Procesamiento y detección de movimiento
    - Control de hilos de monitoreo
    """

    def __init__(self, carpeta_imagenes="capturas_camara"):
        self.camaras_activas = {}
        self.hilos_monitoreo = {}
        self.carpeta_imagenes = carpeta_imagenes
        if not os.path.exists(self.carpeta_imagenes):
            os.makedirs(self.carpeta_imagenes)

    # ------------------------- Gestión de cámaras -------------------------
    def activar_camara(self, serie, ip, modelo=None):
        self.camaras_activas[serie] = {
            "ip": ip,
            "modelo": modelo,
            "monitoreando": False,
        }
        return True

    def desactivar_camara(self, serie):
        if serie in self.camaras_activas:
            
            if self.camaras_activas[serie].get("monitoreando"):
                self.detener_monitoreo_movimiento(serie)
            self.camaras_activas.pop(serie, None)
            return True
        return False

    # ------------------------- Captura y guardado -------------------------
    def _camera_url(self, ip):
        return f"http://{ip}:{DEFAULT_CAPTURE_PORT}/{DEFAULT_CAPTURE_PATH}"

    def tomar_fotografia(self, serie):
        """Devuelve bytes de la imagen tomada por la cámara o None."""
        if serie not in self.camaras_activas:
            return None
        cam = self.camaras_activas[serie]
        url = self._camera_url(cam["ip"])
        try:
            resp = requests.get(url, timeout=DEFAULT_TIMEOUT)
            resp.raise_for_status()
            return resp.content
        except Exception:
            return None

    def guardar_imagen(self, imagen_data, serie, prefijo="movimiento"):
        """Guardar imagen en archivo. `imagen_data` puede ser bytes.

        Devuelve la ruta completa del archivo o None en error.
        """
        if imagen_data is None:
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"{prefijo}_{serie}_{timestamp}.jpg"
        ruta_completa = os.path.join(self.carpeta_imagenes, nombre_archivo)
        try:
            
            if isinstance(imagen_data, np.ndarray):
                cv2.imwrite(ruta_completa, imagen_data)
            else:
                with open(ruta_completa, "wb") as f:
                    f.write(imagen_data)
            return ruta_completa
        except Exception as e:
            print(f"Error guardando imagen: {e}")
            return None

    # ------------------------- Utilidades de imagen -------------------------
    def _decode_image(self, image_bytes):
        try:
            arr = np.asarray(bytearray(image_bytes), dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            return img
        except Exception:
            return None

    def _preprocess_gray(self, img, blur_ksize=(21, 21)):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, blur_ksize, 0)
        return blurred

    # ------------------------- Detección de movimiento -------------------------
    def detectar_movimiento(self, serie, frame_gap=DEFAULT_FRAME_GAP, diff_threshold=DEFAULT_DIFF_THRESHOLD):
        """Detecta movimiento comparando dos capturas consecutivas.

        Mejora para reducir falsos positivos:
        - Redimensiona ambos frames a la misma forma
        - Calcula un umbral por píxel y aplica operaciones morfológicas
        - Requiere que el área total cambiada supere un umbral relativo al tamaño del frame

        Devuelve (movimiento_detectado: bool, ruta_imagen: Optional[str])
        """
        if serie not in self.camaras_activas:
            return False, None

        cam = self.camaras_activas[serie]
        try:
            
            b1 = self.tomar_fotografia(serie)
            if not b1:
                return False, None
            img1 = self._decode_image(b1)
            if img1 is None:
                return False, None

            time.sleep(frame_gap)

            
            b2 = self.tomar_fotografia(serie)
            if not b2:
                return False, None
            img2 = self._decode_image(b2)
            if img2 is None:
                return False, None

            
            if img1.shape != img2.shape:
                h, w = img1.shape[:2]
                img2 = cv2.resize(img2, (w, h))

            
            g1 = self._preprocess_gray(img1)
            g2 = self._preprocess_gray(img2)
            diff = cv2.absdiff(g1, g2)
            _, th = cv2.threshold(diff, diff_threshold, 255, cv2.THRESH_BINARY)
            
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            th = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)
            th = cv2.dilate(th, None, iterations=2)

            contours_info = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            contours = contours_info[0] if len(contours_info) == 2 else contours_info[1]

            
            frame_area = img1.shape[0] * img1.shape[1]
            min_area = max(500, int(frame_area * MIN_AREA_FACTOR))

            movimiento_detectado = False
            for c in contours:
                if cv2.contourArea(c) >= min_area:
                    movimiento_detectado = True
                    break

            ruta_imagen = None
            if movimiento_detectado:
                
                ruta_imagen = self.guardar_imagen(img2, serie, "movimiento")

            return movimiento_detectado, ruta_imagen

        except Exception as e:
            print(f"Error en detección de movimiento: {e}")
            return False, None

    # ------------------------- Monitoreo (hilos) -------------------------
    def iniciar_monitoreo_movimiento(self, serie, intervalo=5, callback_evento=None):
        """Inicia un hilo que detecta movimiento periódicamente y llama `callback_evento(serie, ruta)`"""
        if serie not in self.camaras_activas:
            return False
        if self.camaras_activas[serie].get("monitoreando"):
            return False

        stop_flag = threading.Event()

        def _monitorear():
            while self.camaras_activas.get(serie, {}).get("monitoreando", False):
                try:
                    movimiento, ruta = self.detectar_movimiento(serie)
                    if movimiento:
                        print(f"⚠️  Movimiento detectado en cámara {serie}")
                        print(f"📸 Imagen guardada: {ruta}")
                        if callback_evento:
                            try:
                                callback_evento(serie, ruta)
                            except Exception as e:
                                print(f"Error en callback_evento: {e}")
                    time.sleep(intervalo)
                except Exception as e:
                    print(f"Error en monitoreo de cámara {serie}: {e}")
                    time.sleep(intervalo)

        self.camaras_activas[serie]["monitoreando"] = True
        hilo = threading.Thread(target=_monitorear, daemon=True)
        self.hilos_monitoreo[serie] = hilo
        hilo.start()
        print(f"🎥 Monitoreo iniciado para cámara {serie} (intervalo: {intervalo}s)")
        return True

    def detener_monitoreo_movimiento(self, serie):
        if serie in self.camaras_activas:
            self.camaras_activas[serie]["monitoreando"] = False
        if serie in self.hilos_monitoreo:
            
            self.hilos_monitoreo.pop(serie, None)
        return True

    def capturar_foto(self, serie):
        imagen_data = self.tomar_fotografia(serie)
        if imagen_data:
            ruta = self.guardar_imagen(imagen_data, serie, "manual")
            return ruta is not None
        return False

    def obtener_estado_monitoreo(self, serie):
        if serie in self.camaras_activas:
            return self.camaras_activas[serie].get("monitoreando", False)
        return False