import cv2
import pytesseract
import os

pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Leer última captura
files = sorted([f for f in os.listdir('capturas_placas') if f.endswith('.jpg')], reverse=True)
if files:
    img_path = os.path.join('capturas_placas', files[0])
    print(f'Probando: {files[0]}')
    img = cv2.imread(img_path)
    
    if img is None:
        print("Error: No se pudo cargar la imagen")
    else:
        print(f"Imagen cargada: {img.shape}")
        
        # Convertir a gris
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Threshold
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        
        # OCR
        print("Ejecutando OCR...")
        text = pytesseract.image_to_string(binary, lang='spa+eng', config='--psm 8')
        
        print(f"Texto detectado: {repr(text)}")
        
        clean = ''.join([c for c in text if c.isalnum()]).upper()
        print(f"Limpio: {clean}")
else:
    print("No hay capturas")
