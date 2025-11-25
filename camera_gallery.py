import tkinter as tk
from tkinter import ttk, messagebox
import os
import threading
import time
import base64
import cv2
import numpy as np
from image_utils import decode_image

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
        self.current_list = []
        self.current_index = -1
        self.view_mode = 'gallery'
        self.selected_serie = None

    def _encode_image_to_tk(self, img):
        try:
            _, buf = cv2.imencode('.png', img)
            b64 = base64.b64encode(buf.tobytes())
            return tk.PhotoImage(data=b64)
        except Exception:
            return None

    def _scale_image_to_fit(self, img, max_w=None, max_h=None):
        try:
            h, w = img.shape[:2]
            shrink_factor = 0.7
            cap_w = 600
            cap_h = 400
            try:
                lbl_w = int(self.display_label.winfo_width())
            except Exception:
                lbl_w = 0
            try:
                lbl_h = int(self.display_label.winfo_height())
            except Exception:
                lbl_h = 0
            if max_w is None:
                max_w = lbl_w or cap_w
            if max_h is None:
                max_h = lbl_h or cap_h
            if max_w <= 1:
                max_w = cap_w
            if max_h <= 1:
                max_h = cap_h
            max_w = int(min(max_w, cap_w) * shrink_factor)
            max_h = int(min(max_h, cap_h) * shrink_factor)
            scale_w = max_w / float(w)
            scale_h = max_h / float(h)
            scale = min(scale_w, scale_h, 1.0)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            if new_w == w and new_h == h:
                return img
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            return resized
        except Exception:
            return img

    def show(self):
        if self.win and self.win.winfo_exists():
            self.win.lift()
            return
        self.win = tk.Toplevel(self.root)
        self.win.title("Visor de Cámaras")
        self.win.geometry("1000x700")
        self.win.configure(bg=self.styles.get('COLOR_FONDO', '#1F2024'))

        left = tk.Frame(self.win, bg=self.styles.get('COLOR_FONDO', '#1F2024'), width=250)
        left.pack(side='left', fill='y')
        right = tk.Frame(self.win, bg=self.styles.get('COLOR_FONDO', '#1F2024'))
        right.pack(side='right', expand=True, fill='both')

        tk.Label(left, text='Cámaras', bg=self.styles.get('COLOR_FONDO', '#1F2024'), fg=self.styles.get('COLOR_TEXTO', '#FFFFFF'), font=("Segoe UI", 14, "bold")).pack(pady=8)
        self.list_cams = tk.Listbox(left, width=30)
        self.list_cams.pack(padx=8, pady=8, fill='y', expand=True)
        self.list_cams.bind('<<ListboxSelect>>', lambda e: self._on_cam_select())

        tk.Label(left, text='Modo Visualización', bg=self.styles.get('COLOR_FONDO', '#1F2024'), fg=self.styles.get('COLOR_TEXTO', '#FFFFFF'), font=("Segoe UI", 11, "bold")).pack(pady=(10, 5))
        
        self.btn_live = ttk.Button(left, text='🔴 Ver en Vivo', style='Dark.TButton', command=self._enable_live_mode)
        self.btn_live.pack(fill='x', padx=10, pady=2)
        
        self.btn_gallery = ttk.Button(left, text='🖼 Ver Capturas', style='Dark.TButton', command=self._enable_gallery_mode)
        self.btn_gallery.pack(fill='x', padx=10, pady=2)

        btn_frame = tk.Frame(left, bg=self.styles.get('COLOR_FONDO', '#1F2024'))
        btn_frame.pack(pady=6)
        ttk.Button(btn_frame, text='Actualizar', style='Dark.TButton', command=self._refresh_list).pack(side='left', padx=4)
        ttk.Button(btn_frame, text='Cerrar', style='Dark.TButton', command=self._close).pack(side='left', padx=4)

        self.display_label = tk.Label(right, bg=self.styles.get('COLOR_CARD', '#4B4952'))
        self.display_label.pack(fill='both', expand=True, padx=10, pady=10)
        self.info_label = tk.Label(right, text='', bg=self.styles.get('COLOR_FONDO', '#1F2024'), fg=self.styles.get('COLOR_TEXTO', '#FFFFFF'))
        self.info_label.pack(fill='x', padx=10, pady=(0, 6))
        nav_frame = tk.Frame(right, bg=self.styles.get('COLOR_FONDO', '#1F2024'))
        nav_frame.pack(fill='x', padx=10, pady=(0, 6))
        self.btn_prev = ttk.Button(nav_frame, text='⟨ Anterior', style='Small.TButton', command=lambda: self._show_prev())
        self.btn_prev.pack(side='left')
        self.btn_next = ttk.Button(nav_frame, text='Siguiente ⟩', style='Small.TButton', command=lambda: self._show_next())
        self.btn_next.pack(side='right')

        bottom = tk.Frame(right, bg=self.styles.get('COLOR_FONDO', '#1F2024'), height=150)
        bottom.pack(fill='x')
        self.thumb_frame = tk.Frame(bottom, bg=self.styles.get('COLOR_FONDO', '#1F2024'))
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
        self.selected_serie = serie
        self._update_view()

    def _enable_live_mode(self):
        if not self.selected_serie:
            messagebox.showwarning("Advertencia", "Selecciona una cámara primero")
            return
        
        # Verificar que el dispositivo no esté en modo Inactivo
        dispositivo = self.logic.obtener_dispositivo_por_serie(self.selected_serie)
        if dispositivo and dispositivo.get('modo') == 'Inactivo':
            messagebox.showerror("Error", "No se puede ver en vivo. El dispositivo está en modo Inactivo.")
            return
        
        self.view_mode = 'live'
        self._update_view()

    def _enable_gallery_mode(self):
        self.view_mode = 'gallery'
        self._update_view()

    def _update_view(self):
        if not self.selected_serie:
            return
        
        if self.view_mode == 'live':
            # Limpiar miniaturas
            for w in self.thumb_frame.winfo_children():
                w.destroy()
            self.info_label.config(text=f"VISTA EN VIVO - Cámara {self.selected_serie}")
            self._start_live(self.selected_serie)
        else:
            self._stop_live()
            self.info_label.config(text=f"Galería - Cámara {self.selected_serie}")
            self._load_thumbs_for_serie(self.selected_serie)

    def _load_thumbs_for_serie(self, serie):
        for w in self.thumb_frame.winfo_children():
            w.destroy()
        files = []
        if os.path.isdir(CAPTURAS_DIR):
            for f in os.listdir(CAPTURAS_DIR):
                if serie in f:
                    files.append(os.path.join(CAPTURAS_DIR, f))
        files.sort(reverse=True)
        self.current_list = files
        self.current_index = 0 if files else -1
        for i, p in enumerate(files[:12]):
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
                    lbl.bind('<Button-1>', lambda e, idx=i: self._show_image_by_index(idx))
            except Exception:
                continue
        if not files:
            self.display_label.config(text='No hay capturas para esta cámara', image='')
        else:
            try:
                self._show_image_by_index(0)
            except Exception:
                pass
        self._update_nav_buttons()

    def _show_image(self, path):
        img = cv2.imread(path)
        if img is None:
            messagebox.showerror('Error', 'No se pudo abrir la imagen')
            return
        img = self._scale_image_to_fit(img)
        tkimg = self._encode_image_to_tk(img)
        if tkimg:
            self.display_label.config(image=tkimg, text='')
            self.display_label.image = tkimg

    def _show_image_by_index(self, index):
        try:
            if not self.current_list:
                return
            if index < 0 or index >= len(self.current_list):
                return
            path = self.current_list[index]
            img = cv2.imread(path)
            if img is None:
                return
            img = self._scale_image_to_fit(img)
            tkimg = self._encode_image_to_tk(img)
            if tkimg:
                self.display_label.config(image=tkimg, text='')
                self.display_label.image = tkimg
                base = os.path.basename(path)
                serie = base.split('_')[1] if '_' in base else 'N/D'
                self.info_label.config(text=f"Capturada por: {serie} — {base}")
                self.current_index = index
                self._update_nav_buttons()
        except Exception:
            pass

    def _show_next(self):
        if not self.current_list:
            return
        next_idx = self.current_index + 1 if self.current_index >= 0 else 0
        if next_idx >= len(self.current_list):
            return
        self._show_image_by_index(next_idx)

    def _show_prev(self):
        if not self.current_list:
            return
        prev_idx = self.current_index - 1
        if prev_idx < 0:
            return
        self._show_image_by_index(prev_idx)

    def _update_nav_buttons(self):
        try:
            if not self.current_list or self.current_index < 0:
                self.btn_prev.config(state='disabled')
                self.btn_next.config(state='disabled')
                return
            if self.current_index <= 0:
                self.btn_prev.config(state='disabled')
            else:
                self.btn_prev.config(state='normal')
            if self.current_index >= len(self.current_list) - 1:
                self.btn_next.config(state='disabled')
            else:
                self.btn_next.config(state='normal')
        except Exception:
            pass

    def _start_live(self, serie):
        self._stop_live()
        self._live_running = True
        def loop():
            while self._live_running:
                try:
                    img_bytes = self.cam_manager.tomar_fotografia(serie)
                    if img_bytes is not None:
                        img = decode_image(img_bytes)
                        if img is not None:
                            img2 = self._scale_image_to_fit(img)
                            tkimg = self._encode_image_to_tk(img2)
                            if tkimg:
                                def upd():
                                    if self.win and self.win.winfo_exists():
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