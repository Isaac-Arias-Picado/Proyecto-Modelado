"""
Script simple para diagnosticar si Tesseract está funcionando correctamente
y ver qué texto se extrae de las imágenes capturadas
"""
import os
import cv2
import pytesseract
from pathlib import Path

# Crear carpeta de debug si no existe
debug_folder = "debug_ocr"
os.makedirs(debug_folder, exist_ok=True)

# Buscar imágenes capturadas
capturas_folder = "capturas_placas"
if not os.path.exists(capturas_folder):
    print(f"Error: La carpeta '{capturas_folder}' no existe")
    exit(1)

files = sorted([f for f in os.listdir(capturas_folder) if f.endswith('.jpg')], 
               key=lambda x: os.path.getctime(os.path.join(capturas_folder, x)), 
               reverse=True)

if not files:
    print(f"No hay imágenes en '{capturas_folder}'")
    exit(1)

print(f"Encontradas {len(files)} imágenes. Procesando las 3 más recientes...\n")

for file in files[:3]:
    filepath = os.path.join(capturas_folder, file)
    print(f"\n{'='*70}")
    print(f"Archivo: {file}")
    print('='*70)
    
    img = cv2.imread(filepath)
    if img is None:
        print("Error al leer imagen")
        continue
    
    print(f"Dimensiones originales: {img.shape}")
    
    # Convertir a escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Upscale
    scale_percent = 220
    width = int(gray.shape[1] * scale_percent / 100)
    height = int(gray.shape[0] * scale_percent / 100)
    dim = (max(width, 1), max(height, 1))
    resized = cv2.resize(gray, dim, interpolation=cv2.INTER_CUBIC)
    
    print(f"Dimensiones escaladas: {resized.shape}")
    
    # Denoising
    denoised = cv2.fastNlMeansDenoising(resized, None, 10, 7, 21)
    
    # CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Thresholding
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    thresh_inv = cv2.bitwise_not(thresh)
    
    # Guardar versiones procesadas para inspección visual
    cv2.imwrite(os.path.join(debug_folder, f"{file[:-4]}_original.jpg"), gray)
    cv2.imwrite(os.path.join(debug_folder, f"{file[:-4]}_scaled.jpg"), resized)
    cv2.imwrite(os.path.join(debug_folder, f"{file[:-4]}_denoised.jpg"), denoised)
    cv2.imwrite(os.path.join(debug_folder, f"{file[:-4]}_enhanced.jpg"), enhanced)
    cv2.imwrite(os.path.join(debug_folder, f"{file[:-4]}_thresh.jpg"), thresh)
    cv2.imwrite(os.path.join(debug_folder, f"{file[:-4]}_thresh_inv.jpg"), thresh_inv)
    
    # Probar diferentes configuraciones de Tesseract
    configs = [
        "--oem 3 --psm 6",
        "--oem 3 --psm 7",
        "--oem 3 --psm 8",
        "--oem 3 --psm 11",
        "--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    ]
    
    images_to_test = [
        ("enhanced", enhanced),
        ("thresh", thresh),
        ("thresh_inv", thresh_inv),
    ]
    
    all_results = []
    
    for img_name, img_data in images_to_test:
        print(f"\n--- Probando con imagen: {img_name} ---")
        for config in configs:
            try:
                result = pytesseract.image_to_string(img_data, config=config)
                result_clean = ''.join([c for c in result if c.isalnum()]).upper()
                
                if result_clean:
                    print(f"  [{config[:20]:20s}] => '{result_clean}'")
                    all_results.append(result_clean)
                    
            except Exception as e:
                print(f"  Error con config '{config[:20]}': {e}")
    
    print(f"\n--- RESUMEN ---")
    if all_results:
        # Eliminar duplicados y ordenar por longitud
        unique = sorted(set(all_results), key=len, reverse=True)
        print(f"Texto(s) detectado(s):")
        for text in unique[:5]:
            print(f"  • {text} (longitud: {len(text)})")
    else:
        print("❌ No se detectó ningún texto")

print(f"\n{'='*70}")
print(f"Imágenes procesadas guardadas en carpeta: {debug_folder}")
print(f"Revisa las imágenes para ver cómo se ven después del procesamiento")
print('='*70)
