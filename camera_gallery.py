import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import time
import base64
import cv2

CAPTURAS_DIR = "capturas_camara"

class CameraGallery:
    def __init__(self, root, logic, cam_manager, camera_ctrl, styles=None):
        self.root = root
        self.logic = logic
        self.cam_manager = cam_manager
        self.camera_ctrl = camera_ctrl
        self.styles = styles or {}
        self.win = None
        self.live_thread = None
        self._live_running = False
        self.current_photo = None

    def _encode_image_to_tk(self, img):
        
        try:
            _, buf = cv2.imencode('.png', img)
            b64 = base64.b64encode(buf.tobytes())
            return tk.PhotoImage(data=b64)
        except Exception:
            return None

    def show(self):
        if self.win and self.win.winfo_exists():
            self.win.lift()
            return
        self.win = tk.Toplevel(self.root)
        self.win.title("Visor de Cámaras")
        self.win.geometry("1000x700")
        self.win.configure(bg=self.styles.get('COLOR_FONDO','#1F2024'))

        left = tk.Frame(self.win, bg=self.styles.get('COLOR_FONDO','#1F2024'), width=250)
        left.pack(side='left', fill='y')
        right = tk.Frame(self.win, bg=self.styles.get('COLOR_FONDO','#1F2024'))
        right.pack(side='right', expand=True, fill='both')

        tk.Label(left, text='Cámaras', bg=self.styles.get('COLOR_FONDO','#1F2024'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF'), font=("Segoe UI", 14, "bold")).pack(pady=8)
        self.list_cams = tk.Listbox(left, width=30)
        self.list_cams.pack(padx=8, pady=8, fill='y', expand=True)
        self.list_cams.bind('<<ListboxSelect>>', lambda e: self._on_cam_select())

        btn_frame = tk.Frame(left, bg=self.styles.get('COLOR_FONDO','#1F2024'))
        btn_frame.pack(pady=6)
        ttk.Button(btn_frame, text='Actualizar', style='Dark.TButton', command=self._refresh_list).pack(side='left', padx=4)
        ttk.Button(btn_frame, text='Cerrar', style='Dark.TButton', command=self._close).pack(side='left', padx=4)

        
        self.display_label = tk.Label(right, bg=self.styles.get('COLOR_CARD','#4B4952'))
        self.display_label.pack(fill='both', expand=True, padx=10, pady=10)

        bottom = tk.Frame(right, bg=self.styles.get('COLOR_FONDO','#1F2024'), height=150)
        bottom.pack(fill='x')
        self.thumb_frame = tk.Frame(bottom, bg=self.styles.get('COLOR_FONDO','#1F2024'))
        self.thumb_frame.pack(fill='x', padx=10, pady=6)

        self._refresh_list()

        self.win.protocol('WM_DELETE_WINDOW', self._close)

    def _refresh_list(self):
        
        self.list_cams.delete(0, tk.END)
        try:
            
            for d in self.logic.obtener_dispositivos():
                if d.get('tipo') == 'Cámara de Seguridad':
                    label = f"{d.get('serie')} - {d.get('nombre')} ({d.get('modo')})"
                    self.list_cams.insert(tk.END, label)
        except Exception as e:
            print('Error cargando dispositivos:', e)

    def _on_cam_select(self):
        sel = self.list_cams.curselection()
        if not sel:
            return
        txt = self.list_cams.get(sel[0])
        serie = txt.split(' - ')[0]
        dispositivo = self.logic.obtener_dispositivo_por_serie(serie)
        modo = dispositivo.get('modo') if dispositivo else None
        
        if modo == 'Grabación Continua':
            self._start_live(serie)
        else:
            self._stop_live()
            self._load_thumbs_for_serie(serie)

    def _load_thumbs_for_serie(self, serie):
        
        for w in self.thumb_frame.winfo_children():
            w.destroy()
        files = []
        if os.path.isdir(CAPTURAS_DIR):
            for f in os.listdir(CAPTURAS_DIR):
                if serie in f:
                    files.append(os.path.join(CAPTURAS_DIR, f))
        files.sort(reverse=True)
        for p in files[:12]:
            try:
                img = cv2.imread(p)
                if img is None:
                    continue
                thumb = cv2.resize(img, (160, 90))
                tkimg = self._encode_image_to_tk(thumb)
                if tkimg:
                    lbl = tk.Label(self.thumb_frame, image=tkimg)
                    lbl.image = tkimg
                    lbl.pack(side='left', padx=4)
                    lbl.bind('<Button-1>', lambda e, path=p: self._show_image(path))
            except Exception:
                continue
        if not files:
            self.display_label.config(text='No hay capturas para esta cámara', image='')

    def _show_image(self, path):
        img = cv2.imread(path)
        if img is None:
            messagebox.showerror('Error', 'No se pudo abrir la imagen')
            return
        tkimg = self._encode_image_to_tk(img)
        if tkimg:
            self.display_label.config(image=tkimg, text='')
            self.display_label.image = tkimg

    def _start_live(self, serie):
        
        self._stop_live()
        self._live_running = True
        def loop():
            while self._live_running:
                try:
                    img = self.cam_manager.tomar_fotografia(serie)
                    if img is not None:
                        tkimg = self._encode_image_to_tk(img)
                        if tkimg:
                            
                            def upd():
                                self.display_label.config(image=tkimg, text='')
                                self.display_label.image = tkimg
                            self.display_label.after(0, upd)
                    time.sleep(0.25)
                except Exception:
                    time.sleep(0.5)
        self.live_thread = threading.Thread(target=loop, daemon=True)
        self.live_thread.start()

    def _stop_live(self):
        self._live_running = False
        if self.live_thread:
            try:
                self.live_thread.join(timeout=0.1)
            except Exception:
                pass
            self.live_thread = None

    def _close(self):
        self._stop_live()
        if self.win:
            try:
                self.win.destroy()
            except Exception:
                pass
        self.win = None