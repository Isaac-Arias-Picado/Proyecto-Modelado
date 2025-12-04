import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import cv2
import base64

from ui_helpers import AsyncTreeviewUpdater
from plates_gallery import PlatesGallery
from DetectorPlacasModule import OCRNotFoundError

class PlatesView:
    def __init__(self, parent, root, logic, placas_manager, plates_ctrl, styles=None):
        self.parent = parent
        self.root = root
        self.logic = logic
        self.manager = placas_manager
        self.ctrl = plates_ctrl
        self.styles = styles or {}
        self.tree = None
        self.status_var = tk.StringVar(value="Cargando detectores...")
        self.updater = None
        self.thumb_images = {}

    def mostrar_plaquetas(self):
        for w in self.parent.winfo_children():
            w.destroy()

        tk.Label(self.parent, text="Detector de Placas", font=("Segoe UI", 20, "bold"), bg=self.styles.get('COLOR_FONDO','#1F2024'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack(pady=10)

        btn_frame = tk.Frame(self.parent, bg=self.styles.get('COLOR_FONDO','#1F2024'))
        btn_frame.pack(pady=8)

        # Botones de control manual eliminados, ahora se controla por el Modo del dispositivo
        ttk.Button(btn_frame, text="Registrar Placa", style="Dark.TButton", command=self.registrar_placa_dialog).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📸 Prueba Manual", style="Dark.TButton", command=self.probar_deteccion).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🖼 Ver Capturas", style="Dark.TButton", command=self.abrir_visor_placas).pack(side="left", padx=5)

        estado = tk.Frame(self.parent, bg=self.styles.get('COLOR_CARD','#4B4952'), padx=10, pady=8)
        estado.pack(fill="x", padx=20, pady=10)
        tk.Label(estado, textvariable=self.status_var, bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack()

        cols = ("Serie", "Nombre", "Ubicación", "IP", "Estado", "Monitoreo")
       
        self.tree = ttk.Treeview(self.parent, columns=cols, show="tree headings")
        self.tree.column('#0', width=100, stretch=False)
        self.tree.heading('#0', text='')
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        self.tree.bind('<Double-1>', lambda e: self.abrir_visor_seleccion())
        self.updater = AsyncTreeviewUpdater(self.root, self.tree, self.status_var)
        self.actualizar_lista()

    def actualizar_lista(self):
        if self.tree is None:
            return
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            detectores = self.ctrl.obtener_detectores_activas()
            
            for serie, info in detectores.items():
                dispositivo = self.logic.obtener_dispositivo_por_serie(serie)
                if not dispositivo:
                    continue
                nombre = dispositivo.get('nombre','Desconocido')
                ubic = dispositivo.get('ubicacion','Desconocida')

                monit = info.get('monitoreando', False)
                estado_mon = 'Activo' if monit else 'Inactivo'

        
                thumb = None
                try:
                    files = []
                    folder = 'capturas_placas'
                    if os.path.isdir(folder):
                        for f in os.listdir(folder):
                            if serie in f:
                                files.append(os.path.join(folder, f))
                    files.sort(reverse=True)
                    if files:
                        img = cv2.imread(files[0])
                        if img is not None:
                            target_h = 22
                            h, w = img.shape[:2]
                            scale = target_h / float(h) if h>0 else 1.0
                            tw, th = int(w*scale), int(h*scale)
                            if tw < 2: tw = 2
                            if th < 2: th = 2
                            thumb_img = cv2.resize(img, (tw, th))
                            _, buf = cv2.imencode('.png', thumb_img)
                            b64 = base64.b64encode(buf.tobytes())
                            thumb = tk.PhotoImage(data=b64)
                            self.thumb_images[serie] = thumb
                except Exception:
                    thumb = None

                img_param = self.thumb_images.get(serie) or ''
                self.tree.insert('', 'end', iid=serie, text='', image=img_param, values=(serie, nombre, ubic, info.get('ip','N/A'), 'Verificando...', estado_mon))
            
            def check_connection(serie, info):
                return self.manager._fetch_image(info.get('ip')) is not None

            def get_db_info(serie):
                return self.logic.obtener_dispositivo_por_serie(serie)

            def format_status(total, connected, monitoring):
                return f"Detectores: {total} registrados - Monitoreo: {monitoring} activos"

            self.updater.update_status_background(
                detectores,
                check_connection,
                get_db_info,
                format_status
            )
            
        except Exception as e:
            self.status_var.set(f"Error: {e}")

    def iniciar_monitoreo(self):
        pass # Controlado por modo

    def detener_monitoreo(self):
        pass # Controlado por modo

    def _evento_detectado(self, serie, placa, ruta):
        descripcion = f"Placa detectada: {placa or 'N/D'} - Imagen: {ruta or 'N/A'}"
        self.logic.registrar_evento(serie, descripcion, tipo="Detección Placa")
        
        if placa and not self.logic.esta_placa_registrada(placa):
            self.logic.registrar_evento(serie, f"ALERTA: Placa no registrada: {placa}", tipo="Alerta Placa")

    def probar_deteccion(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Advertencia", "Selecciona un detector primero")
            return
        serie = self.tree.item(sel[0], 'values')[0]
        
        def run():
            try:
                detected, placa, ruta = self.ctrl.detectar_placa_once(serie, save_always=True)
                if detected:
                    self.root.after(0, lambda: messagebox.showinfo("✓ Placa", 
                        f"Detectada: {placa}\nImagen: {ruta}"))
                else:
                    msg = "No se detectó placa."
                    if ruta:
                        msg += f"\nImagen: {ruta}"
                    self.root.after(0, lambda: messagebox.showinfo("Resultado", msg))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        threading.Thread(target=run, daemon=True).start()

    def registrar_placa_dialog(self):
        top = tk.Toplevel(self.root)
        top.title("Registrar Placa")
        top.geometry("400x500")
        top.configure(bg=self.styles.get('COLOR_CARD','#4B4952'))
        
        # Sección de registro
        tk.Label(top, text="Registrar Nueva Placa", font=("Segoe UI", 12, "bold"), 
                bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack(pady=10)
        
        tk.Label(top, text="Placa:", bg=self.styles.get('COLOR_CARD','#4B4952'), 
                fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack()
        e_placa = ttk.Entry(top, width=20)
        e_placa.pack(padx=10, pady=5)
        
        tk.Label(top, text="Propietario:", bg=self.styles.get('COLOR_CARD','#4B4952'), 
                fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack()
        e_prop = ttk.Entry(top, width=20)
        e_prop.pack(padx=10, pady=5)
        
        def guardar():
            placa = e_placa.get().strip().upper()
            prop = e_prop.get().strip()
            if not placa:
                messagebox.showerror("Error", "Ingrese la placa")
                return
            try:
                self.logic.guardar_placa(placa, prop)
                messagebox.showinfo("Éxito", "Placa registrada")
                e_placa.delete(0, tk.END)
                e_prop.delete(0, tk.END)
                actualizar_lista()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        
        ttk.Button(top, text="Guardar", style="Dark.TButton", command=guardar).pack(pady=10)
        
        # Separador
        ttk.Separator(top, orient='horizontal').pack(fill='x', pady=10)
        
        # Sección de placas registradas
        tk.Label(top, text="Placas Registradas", font=("Segoe UI", 12, "bold"), 
                bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack(pady=10)
        
        frame_lista = tk.Frame(top, bg=self.styles.get('COLOR_CARD','#4B4952'))
        frame_lista.pack(fill='both', expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(frame_lista)
        scrollbar.pack(side='right', fill='y')
        
        listbox = tk.Listbox(frame_lista, bg=self.styles.get('COLOR_FONDO','#1F2024'), 
                           fg=self.styles.get('COLOR_TEXTO','#FFFFFF'), 
                           yscrollcommand=scrollbar.set, height=10)
        listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=listbox.yview)
        
        def actualizar_lista():
            listbox.delete(0, tk.END)
            try:
                placas = self.logic.obtener_placas()
                for placa, info in placas.items():
                    prop = info.get('propietario', 'Desconocido')
                    listbox.insert(tk.END, f"{placa} - {prop}")
            except Exception:
                pass
        
        def eliminar_placa():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Advertencia", "Selecciona una placa")
                return
            texto = listbox.get(sel[0])
            placa = texto.split(' - ')[0].strip()
            try:
                self.logic.eliminar_placa(placa)
                messagebox.showinfo("Éxito", "Placa eliminada")
                actualizar_lista()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        
        ttk.Button(top, text="Eliminar Seleccionada", style="Dark.TButton", command=eliminar_placa).pack(pady=5)
        
        actualizar_lista()

    def abrir_visor_placas(self):
        try:
            sel = self.tree.selection()
            if sel:
                serie = sel[0]
                gallery = PlatesGallery(self.root, self.logic, self.manager, self.ctrl, styles=self.styles)
                gallery.show()
                try:
                    for i in range(gallery.list_det.size()):
                        txt = gallery.list_det.get(i)
                        if txt.startswith(serie):
                            gallery.list_det.selection_set(i)
                            gallery.list_det.see(i)
                            gallery._load_thumbs_for_serie(serie)
                            break
                except Exception:
                    pass
            else:
                gallery = PlatesGallery(self.root, self.logic, self.manager, self.ctrl, styles=self.styles)
                gallery.show()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el visor de placas: {e}")

    def abrir_visor_seleccion(self):
        sel = self.tree.selection()
        if not sel:
            return
        self.abrir_visor_placas()
 
 