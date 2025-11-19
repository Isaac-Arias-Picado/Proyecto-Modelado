import threading
import os
import time
import requests
import cv2
import numpy as np
from datetime import datetime

CAPTURAS_DIR = "capturas_placas"

class DetectorPlacasManager:
    def __init__(self):
        self.detectores_activas = {}
        self._threads = {}
        os.makedirs(CAPTURAS_DIR, exist_ok=True)

    def activar_detector(self, serie, ip, modelo=None):
        self.detectores_activas[serie] = {
            'ip': ip,
            'modelo': modelo or 'Detector Placas',
            'monitoreando': False
        }
        return True

    def desactivar_detector(self, serie):
        
        if serie in self._threads:
            th = self._threads.pop(serie)
            
            if serie in self.detectores_activas:
                self.detectores_activas[serie]['monitoreando'] = False
            
            time.sleep(0.1)
        if serie in self.detectores_activas:
            del self.detectores_activas[serie]
        return True

    def _fetch_image(self, ip, timeout=5):
        
        urls = [
            f"http://{ip}/shot.jpg",
            f"http://{ip}/jpg",
            f"http://{ip}/snapshot.jpg",
            f"http://{ip}/image.jpg",
            f"http://{ip}/"
        ]
        for u in urls:
            try:
                r = requests.get(u, timeout=timeout)
                if r.status_code == 200 and r.content:
                    arr = np.frombuffer(r.content, dtype=np.uint8)
                    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
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
        """Intenta detectar placa en una sola captura.
        Retorna (detected_bool, placa_text_or_None, path_or_None)
        """
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
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"placa_{serie}_{ts}.jpg"
            path = os.path.join(CAPTURAS_DIR, filename)
            try:
                cv2.imwrite(path, img)
            except Exception:
                path = None
        return detected, placa_text, path

    def iniciar_monitoreo(self, serie, intervalo=5, callback_evento=None):
        if serie not in self.detectores_activas:
            return False
        if self.detectores_activas[serie].get('monitoreando'):
            return False
        self.detectores_activas[serie]['monitoreando'] = True
        stop_flag = {'run': True}
        def loop():
            while self.detectores_activas.get(serie, {}).get('monitoreando'):
                try:
                    detected, placa, path = self.detectar_placa_once(serie)
                    if detected:
                        if callback_evento:
                            try:
                                callback_evento(serie, placa, path)
                            except Exception:
                                pass
                    time.sleep(intervalo)
                except Exception:
                    time.sleep(intervalo)
            
        th = threading.Thread(target=loop, daemon=True)
        self._threads[serie] = th
        th.start()
        return True

    def detener_monitoreo(self, serie):
        if serie in self.detectores_activas:
            self.detectores_activas[serie]['monitoreando'] = False
        return True
 