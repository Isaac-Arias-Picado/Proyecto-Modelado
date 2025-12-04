import os
import time
import cv2
import threading
import numpy as np

from image_utils import fetch_image_from_url, decode_image, save_image
from pico_controller import activar_alarma_pico, desactivar_alarma_pico
from monitoring_utils import BaseMonitor

DEFAULT_CAPTURE_PORT = 8080
DEFAULT_CAPTURE_PATH = "photo.jpg"
DEFAULT_TIMEOUT = 10
DEFAULT_FRAME_GAP = 0.5
DEFAULT_DIFF_THRESHOLD = 30
MIN_AREA_FACTOR = 0.01 

class CamaraManager:
    def __init__(self, carpeta_imagenes="capturas_camara", monitor_boton=None):
        self.camaras_activas = {}
        self.monitor = BaseMonitor()
        self.carpeta_imagenes = carpeta_imagenes
        self.alarma_lock = threading.Lock()
        self.event_callback = None
        self.monitor_boton = monitor_boton
        self.schedule_checker = None
        if not os.path.exists(self.carpeta_imagenes):
            os.makedirs(self.carpeta_imagenes)

    def set_monitor_boton(self, monitor):
        self.monitor_boton = monitor

    def set_event_callback(self, callback):
        self.event_callback = callback

    def set_schedule_checker(self, callback):
        self.schedule_checker = callback

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

    def _camera_url(self, ip):
        return f"http://{ip}:{DEFAULT_CAPTURE_PORT}/{DEFAULT_CAPTURE_PATH}"

    def tomar_fotografia(self, serie):
        if serie not in self.camaras_activas:
            return None
        cam = self.camaras_activas[serie]
        url = self._camera_url(cam["ip"])
        return fetch_image_from_url(url, DEFAULT_TIMEOUT)
    
    def activar_alarma(self, serie=None):
        def _run_alarma():
            with self.alarma_lock:
                print(f">>> INTENTO DE ACTIVAR ALARMA POR: {serie if serie else 'Sistema'}")
                # Intentar usar el monitor de botón si está disponible
                if self.monitor_boton and self.monitor_boton.activar_alarma():
                    if self.event_callback:
                        dispositivo = serie if serie else "Sistema"
                        self.event_callback(dispositivo, "Alarma activada por detección de movimiento", "Alarma")
                    return

                puerto = "COM5"  # Puerto de la Raspberry Pi Pico
                
                resultado = activar_alarma_pico(puerto)
                
                if resultado:
                    if self.event_callback:
                        dispositivo = serie if serie else "Sistema"
                        self.event_callback(dispositivo, "Alarma activada por detección de movimiento", "Alarma")

        threading.Thread(target=_run_alarma, daemon=True).start()

    def desactivar_alarma(self):
        def _run_desactivar():
            with self.alarma_lock:
                # Intentar usar el monitor de botón si está disponible
                if self.monitor_boton and self.monitor_boton.desactivar_alarma():
                    if self.event_callback:
                        self.event_callback("Sistema", "Alarma desactivada manualmente", "Alarma")
                    return

                puerto = "COM5"  # Puerto de la Raspberry Pi Pico
                
                resultado = desactivar_alarma_pico(puerto)
                
                if resultado:
                    if self.event_callback:
                        self.event_callback("Sistema", "Alarma desactivada manualmente", "Alarma")

        threading.Thread(target=_run_desactivar, daemon=True).start()

    def guardar_imagen(self, imagen_data, serie, prefijo="movimiento"):
        return save_image(imagen_data, self.carpeta_imagenes, serie, prefijo)

    def _preprocess_gray(self, img, blur_ksize=(21, 21)):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, blur_ksize, 0)
        return blurred

    def detectar_movimiento(self, serie, frame_gap=DEFAULT_FRAME_GAP, diff_threshold=DEFAULT_DIFF_THRESHOLD):
        if serie not in self.camaras_activas:
            return False, None

        try:
            b1 = self.tomar_fotografia(serie)
            if not b1: return False, None
            img1 = decode_image(b1)
            if img1 is None: return False, None

            time.sleep(frame_gap)

            b2 = self.tomar_fotografia(serie)
            if not b2: return False, None
            img2 = decode_image(b2)
            if img2 is None: return False, None

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
                # La alarma se activará en _monitor_task si corresponde

            return movimiento_detectado, ruta_imagen

        except Exception:
            return False, None

    def _monitor_task(self, serie, callback_evento):
        try:
            # Verificar horario si existe un checker configurado
            if self.schedule_checker:
                if not self.schedule_checker(serie):
                    return

            movimiento, ruta = self.detectar_movimiento(serie)
            if movimiento:
                # Activar alarma automáticamente al detectar movimiento en monitoreo
                self.activar_alarma(serie)
                
                if callback_evento:
                    try:
                        callback_evento(serie, ruta)
                    except Exception:
                        pass
        except Exception:
            pass

    def iniciar_monitoreo_movimiento(self, serie, intervalo=1, callback_evento=None):
        if serie not in self.camaras_activas:
            return False
        
        # Forzamos el estado a True
        self.camaras_activas[serie]["monitoreando"] = True
        
        # Iniciamos el monitor (BaseMonitor se encarga de matar hilos viejos si existen)
        self.monitor.start_monitoring(serie, self._monitor_task, intervalo, serie, callback_evento)
        return True

    def detener_monitoreo_movimiento(self, serie):
        if serie in self.camaras_activas:
            self.camaras_activas[serie]["monitoreando"] = False
        self.monitor.stop_monitoring(serie)
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
