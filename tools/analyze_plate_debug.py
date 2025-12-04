import cv2
import pytesseract
import os
import sys
import numpy as np

# Configurar path de tesseract si es necesario (ajustar según entorno del usuario si falla)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def analyze_image(image_path):
    if not os.path.exists(image_path):
        print(f"Error: File not found {image_path}")
        return

    print(f"--- Analyzing {os.path.basename(image_path)} ---")
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image.")
        return

    # 1. Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Resize (Upscaling often helps OCR)
    scale_percent = 200 # percent of original size
    width = int(gray.shape[1] * scale_percent / 100)
    height = int(gray.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized = cv2.resize(gray, dim, interpolation = cv2.INTER_CUBIC)

    # 3. Denoise
    denoised = cv2.fastNlMeansDenoising(resized, None, 10, 7, 21)

    # 4. Thresholding (Otsu)
    thresh_otsu = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # 5. Adaptive Thresholding
    thresh_adapt = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # 6. Inverted Threshold (sometimes text is white on black)
    thresh_inv = cv2.bitwise_not(thresh_otsu)

    # 7. Blue channel extraction (since user said blue letters)
    # Reload original and split channels
    b_channel, g_channel, r_channel = cv2.split(cv2.resize(img, dim, interpolation = cv2.INTER_CUBIC))
    # Blue letters on white background -> Blue channel might be dark? No, white is (255,255,255), Blue is (255,0,0) in BGR? No (B,G,R). Blue is (255,0,0).
    # White background (255,255,255). Blue text (High B, Low G, Low R).
    # Actually, if text is blue, it is bright in Blue channel, dark in Red/Green.
    # If background is white, it is bright in all channels.
    # So contrast is lowest in Blue channel (Bright text on Bright BG).
    # Contrast is highest in Red or Green channel (Dark text on Bright BG).
    # Let's try Red channel.
    
    processed_images = {
        "Original Gray": gray,
        "Resized Gray": resized,
        "Otsu Threshold": thresh_otsu,
        "Adaptive Threshold": thresh_adapt,
        "Inverted Otsu": thresh_inv,
        "Red Channel (High Contrast for Blue Text)": r_channel,
        "Red Channel Threshold": cv2.threshold(r_channel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    }

    configs = [
        '--psm 7', # Treat the image as a single text line.
        '--psm 8', # Treat the image as a single word.
        '--psm 11', # Sparse text.
        '--psm 6' # Assume a single uniform block of text.
    ]

    for name, p_img in processed_images.items():
        print(f"\nFilter: {name}")
        for config in configs:
            try:
                text = pytesseract.image_to_string(p_img, config=config)
                clean_text = ''.join([c for c in text if c.isalnum()]).strip()
                if clean_text:
                    print(f"  Config {config}: '{clean_text}'")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    # Use the most recent manual capture
    folder = r"c:\Users\Isaac\OneDrive\Desktop\Progra\Python\Proyecto-Modelado - Copy\capturas_placas"
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.startswith("manual")]
    if not files:
        print("No manual captures found.")
    else:
        latest_file = max(files, key=os.path.getctime)
        analyze_image(latest_file)
