import os
import time
import cv2
import numpy as np
from datetime import datetime

from image_utils import fetch_image_from_url, decode_image, save_image
from monitoring_utils import BaseMonitor

CAPTURAS_DIR = "capturas_placas"
DEFAULT_CAPTURE_PORT = 8080
DEFAULT_CAPTURE_PATH = "photo.jpg"


class DetectorPlacasManager:
    def __init__(self):
        self.detectores_activas = {}
        self.monitor = BaseMonitor()
        os.makedirs(CAPTURAS_DIR, exist_ok=True)

    def activar_detector(self, serie, ip, modelo=None):
        self.detectores_activas[serie] = {
            'ip': ip,
            'modelo': modelo or 'Detector Placas',
            'monitoreando': False
        }
        return True

    def desactivar_detector(self, serie):
        if serie in self.detectores_activas:
            if self.detectores_activas[serie].get('monitoreando'):
                self.detener_monitoreo(serie)
            del self.detectores_activas[serie]
        return True

    def _fetch_image(self, ip, timeout=5):
        # Construir una lista de URLs posibles de forma robusta.
        candidates = []

        s = str(ip or '').strip()
        if not s:
            return None

        # Si ya viene con esquema, usarlo como base
        if s.startswith('http://') or s.startswith('https://'):
            base = s.rstrip('/')
            candidates.append(base)
            candidates.extend([
                f"{base}/photo.jpg",
                f"{base}/shot.jpg",
                f"{base}/jpg",
                f"{base}/snapshot.jpg",
                f"{base}/image.jpg",
            ])
        else:
            # Si contiene '/' o ':' ya incluye puerto o path; no añadir :8080 extra
            if '/' in s or ':' in s:
                candidates.append(f"http://{s}".rstrip('/'))
                candidates.extend([
                    f"http://{s}/photo.jpg",
                    f"http://{s}/shot.jpg",
                    f"http://{s}/jpg",
                    f"http://{s}/snapshot.jpg",
                    f"http://{s}/image.jpg",
                ])
            else:
                # IP simple: probar con puerto 8080/photo.jpg primero (como CamaraModule)
                candidates.append(f"http://{s}:{DEFAULT_CAPTURE_PORT}/{DEFAULT_CAPTURE_PATH}")
                candidates.append(f"http://{s}:{DEFAULT_CAPTURE_PORT}/")
                candidates.extend([
                    f"http://{s}/photo.jpg",
                    f"http://{s}/shot.jpg",
                    f"http://{s}/jpg",
                    f"http://{s}/snapshot.jpg",
                    f"http://{s}/image.jpg",
                ])

        for u in candidates:
            try:
                content = fetch_image_from_url(u, timeout)
                if not content:
                    continue
                img = decode_image(content)
                if img is not None:
                    return img
            except Exception:
                continue

        return None

    def tomar_fotografia(self, serie):
        info = self.detectores_activas.get(serie)
        if not info:
            return None
        ip = info.get('ip')
        img = self._fetch_image(ip)
        return img

    def detectar_placa_once(self, serie):
        img = self.tomar_fotografia(serie)
        if img is None:
            return False, None, None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        placa_text = None
        try:
            import pytesseract
            b = cv2.bilateralFilter(gray, 11, 17, 17)
            edged = cv2.Canny(b, 30, 200)
            cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:10]
            screenCnt = None
            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.018 * peri, True)
                if len(approx) == 4:
                    screenCnt = approx
                    break
            roi = None
            if screenCnt is not None:
                mask = np.zeros(gray.shape, np.uint8)
                cv2.drawContours(mask, [screenCnt], 0, 255, -1)
                x, y, w, h = cv2.boundingRect(screenCnt)
                roi = gray[y:y + h, x:x + w]
            else:
                roi = gray
            
            txt = pytesseract.image_to_string(roi, config='--psm 7')
            txt = ''.join([c for c in txt if c.isalnum()])
            if len(txt) >= 4:
                placa_text = txt.upper()
        except Exception:
            placa_text = None
        
        detected = False
        if placa_text:
            detected = True
        else:
            blurred = cv2.GaussianBlur(gray, (5,5), 0)
            thresh = cv2.adaptiveThreshold(blurred,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
            cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in cnts:
                x,y,w,h = cv2.boundingRect(c)
                ar = w / float(h) if h>0 else 0
                if w > 60 and h>15 and 2.0 < ar < 6.0:
                    detected = True
                    break
        
        path = None
        if detected:
            path = save_image(img, CAPTURAS_DIR, serie, "placa")
        return detected, placa_text, path

    def _monitor_task(self, serie, callback_evento):
        try:
            detected, placa, path = self.detectar_placa_once(serie)
            if detected:
                if callback_evento:
                    try:
                        callback_evento(serie, placa, path)
                    except Exception:
                        pass
        except Exception:
            pass

    def iniciar_monitoreo(self, serie, intervalo=5, callback_evento=None):
        if serie not in self.detectores_activas:
            return False
        if self.detectores_activas[serie].get('monitoreando'):
            return False
        
        self.detectores_activas[serie]['monitoreando'] = True
        self.monitor.start_monitoring(serie, self._monitor_task, intervalo, serie, callback_evento)
        return True

    def detener_monitoreo(self, serie):
        if serie in self.detectores_activas:
            self.detectores_activas[serie]['monitoreando'] = False
        self.monitor.stop_monitoring(serie)
        return True

 