import os
import cv2
import warnings

warnings.filterwarnings('ignore')

from image_utils import fetch_image_from_url, decode_image, save_image
from monitoring_utils import BaseMonitor

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

CAPTURAS_DIR = "capturas_placas"
_reader = None  # Cache global para no reinicializar


class OCRNotFoundError(Exception):
    pass


def get_reader():
    """Obtiene el reader de EasyOCR (singleton)"""
    global _reader
    if _reader is None:
        if not EASYOCR_AVAILABLE:
            raise OCRNotFoundError("EasyOCR no está instalado")
        _reader = easyocr.Reader(['es', 'en'], gpu=False, verbose=False)
    return _reader


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
        """Obtiene imagen de la IP"""
        if not ip or not str(ip).strip():
            return None
        
        urls_to_try = [
            f"http://{ip}/photo.jpg",
            f"http://{ip}:8080/photo.jpg",
            f"http://{ip}/jpg",
            f"http://{ip}/snapshot.jpg",
        ]
        
        for url in urls_to_try:
            try:
                content = fetch_image_from_url(url, timeout)
                if content:
                    img = decode_image(content)
                    if img is not None:
                        return img
            except:
                continue
        
        return None

    def tomar_fotografia(self, serie):
        info = self.detectores_activas.get(serie)
        if not info:
            return None
        ip = info.get('ip')
        return self._fetch_image(ip)

    def detectar_placa_once(self, serie, save_always=False):
        img = self.tomar_fotografia(serie)
        if img is None:
            return False, None, None
        
        # SIEMPRE rotar 90 grados a la derecha
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        
        # Guardar imagen SOLO si save_always (para pruebas manuales)
        path = None
        if save_always:
            path = save_image(img, CAPTURAS_DIR, serie, "manual")
            print(f"[{serie}] Imagen guardada (manual): {path}")
        
        placa_text = None
        candidates = []
        
        try:
            reader = get_reader()
            
            # Preparar imagen
            h, w = img.shape[:2]
            if w < 800:
                scale = 2.0
                img_scaled = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
            else:
                img_scaled = img
            
            gray = cv2.cvtColor(img_scaled, cv2.COLOR_BGR2GRAY)
            denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            
            images_to_try = [
                ("enhanced", enhanced),
                ("original", gray),
                ("rotated_90", cv2.rotate(enhanced, cv2.ROTATE_90_CLOCKWISE)),
                ("rotated_270", cv2.rotate(enhanced, cv2.ROTATE_90_COUNTERCLOCKWISE)),
            ]
            
            for name, test_img in images_to_try:
                results = reader.readtext(test_img, detail=0, workers=0)
                
                for text in results:
                    # Limpiar: solo alfanuméricos
                    clean = ''.join([c for c in str(text) if c.isalnum()]).upper()
                    
                    # Validar: 5-8 caracteres, letras Y números
                    if 5 <= len(clean) <= 8:
                        has_letter = any(c.isalpha() for c in clean)
                        has_digit = any(c.isdigit() for c in clean)
                        
                        if has_letter and has_digit:
                            candidates.append(clean)
            
            # Eliminar duplicados
            unique_candidates = list(set(candidates))
            
            if unique_candidates:
                # Tomar el primero (preferencia por orden de aparición)
                placa_text = unique_candidates[0]
                print(f"✓ PLACA DETECTADA: {placa_text}")
                
                # Guardar si es válido
                if not save_always:
                    path = save_image(img, CAPTURAS_DIR, serie, "placa")
                    print(f"[{serie}] Imagen guardada: {path}")
            else:
                print(f"✗ No se detectó placa válida")
        
        except OCRNotFoundError:
            raise
        except Exception as e:
            print(f"Error OCR: {e}")
        
        detected = (placa_text is not None)
        return detected, placa_text, path

    def _monitor_task(self, serie, callback_evento):
        try:
            detected, placa, path = self.detectar_placa_once(serie)
            if detected and callback_evento:
                try:
                    callback_evento(serie, placa, path)
                except:
                    pass
        except:
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

