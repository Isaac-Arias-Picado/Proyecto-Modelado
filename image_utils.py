import os
import requests
import cv2
import numpy as np
from datetime import datetime

DEFAULT_TIMEOUT = 10

def fetch_image_from_url(url, timeout=DEFAULT_TIMEOUT):
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None

def decode_image(image_bytes):
    try:
        arr = np.asarray(bytearray(image_bytes), dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None

def save_image(image_data, folder, serie, prefix="capture"):
    if image_data is None:
        return None
    
    if not os.path.exists(folder):
        os.makedirs(folder)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"{prefix}_{serie}_{timestamp}.jpg"
    ruta_completa = os.path.join(folder, nombre_archivo)
    
    try:
        if isinstance(image_data, np.ndarray):
            cv2.imwrite(ruta_completa, image_data)
        else:
            with open(ruta_completa, "wb") as f:
                f.write(image_data)
        return ruta_completa
    except Exception as e:
        print(f"Error guardando imagen: {e}")
        return None
import os
import requests
import cv2
import numpy as np
from datetime import datetime

DEFAULT_TIMEOUT = 10

def fetch_image_from_url(url, timeout=DEFAULT_TIMEOUT):
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None

def decode_image(image_bytes):
    try:
        arr = np.asarray(bytearray(image_bytes), dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None

def save_image(image_data, folder, serie, prefix="capture"):
    if image_data is None:
        return None
    
    if not os.path.exists(folder):
        os.makedirs(folder)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"{prefix}_{serie}_{timestamp}.jpg"
    ruta_completa = os.path.join(folder, nombre_archivo)
    
    try:
        if isinstance(image_data, np.ndarray):
            cv2.imwrite(ruta_completa, image_data)
        else:
            with open(ruta_completa, "wb") as f:
                f.write(image_data)
        return ruta_completa
    except Exception as e:
        print(f"Error guardando imagen: {e}")
        return None
