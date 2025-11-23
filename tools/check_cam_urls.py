"""
Script de diagnóstico para probar rutas comunes de cámara/IP.
Uso: python tools\check_cam_urls.py 192.168.0.111:8080

El script intenta varias URLs y reporta si devuelven respuesta 200
y si el contenido parece una imagen (por header o magia de bytes).
"""
import sys
import requests

def is_image_bytes(b):
    if not b or len(b) < 2:
        return False
    # JPEG magic: 0xFF 0xD8, PNG: 0x89 0x50
    return (b[0] == 0xFF and b[1] == 0xD8) or (b[0] == 0x89 and b[1] == 0x50)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Uso: python tools\\check_cam_urls.py <IP[:PORT][/path]>\nEj: python tools\\check_cam_urls.py 192.168.0.111:8080")
        sys.exit(1)

    ip = sys.argv[1].strip()
    candidates = []

    s = ip
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
        # si contiene '/', puede incluir path
        if '/' in s:
            candidates.append(f"http://{s}")
            candidates.extend([
                f"http://{s}/photo.jpg",
                f"http://{s}/shot.jpg",
            ])
        else:
            candidates.append(f"http://{s}:{8080}/photo.jpg")
            candidates.append(f"http://{s}:{8080}/")
            candidates.extend([
                f"http://{s}/photo.jpg",
                f"http://{s}/shot.jpg",
                f"http://{s}/jpg",
                f"http://{s}/snapshot.jpg",
                f"http://{s}/image.jpg",
                f"http://{s}/",
            ])

    print(f"Probando {len(candidates)} URLs para: {ip}\n")

    for u in candidates:
        try:
            print(f"-> Probando: {u}")
            r = requests.get(u, timeout=5)
            status = r.status_code
            ct = r.headers.get('content-type','')
            img_guess = False
            try:
                if 'image' in ct.lower():
                    img_guess = True
                else:
                    # mirar primeros bytes
                    img_guess = is_image_bytes(r.content[:8])
            except Exception:
                img_guess = False

            print(f"   Status: {status}, Content-Type: {ct}, PareceImagen: {img_guess}")
        except Exception as e:
            print(f"   ERROR: {e}")

    print('\nFin del test.')
