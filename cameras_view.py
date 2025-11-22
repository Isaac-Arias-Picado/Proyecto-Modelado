import tkinter as tk
from tkinter import ttk, messagebox
import threading
from camera_gallery import CameraGallery

class CameraView:
    def __init__(self, parent, root, logic, camara_manager, camera_ctrl, styles=None):
        self.parent = parent
        self.root = root
        self.logic = logic
        self.camara_manager = camara_manager
        self.camera_ctrl = camera_ctrl
        self.styles = styles or {}
        self.estado_camaras_var = tk.StringVar(value="Estado: Cargando...")
        self.tree_camaras = None

    def mostrar_camaras(self):
        for w in self.parent.winfo_children():
            w.destroy()

        tk.Label(self.parent, text="Gestión de Cámaras de Seguridad", 
                font=("Segoe UI", 20, "bold"), bg=self.styles.get('COLOR_FONDO','#1F2024'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack(pady=10)

        btn_frame = tk.Frame(self.parent, bg=self.styles.get('COLOR_FONDO','#1F2024'))
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="▶ Iniciar Monitoreo Movimiento", style="Dark.TButton", 
                command=self.iniciar_monitoreo_movimiento).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹ Detener Monitoreo Movimiento", style="Dark.TButton", 
                command=self.detener_monitoreo_movimiento).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔍 Probar Detección", style="Dark.TButton", 
                command=self.probar_deteccion_movimiento).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📸 Capturar Foto Manual", style="Dark.TButton", 
                command=self.capturar_foto_manual).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🖼 Ver Capturas / Vista en Vivo", style="Dark.TButton",
            command=self.abrir_visor).pack(side="left", padx=5)

        estado_frame = tk.Frame(self.parent, bg=self.styles.get('COLOR_CARD','#4B4952'), padx=20, pady=10)
        estado_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(estado_frame, textvariable=self.estado_camaras_var, 
                bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF'), font=("Segoe UI", 12)).pack()

        cols = ("Serie", "Nombre", "Ubicación", "IP", "Estado", "Monitoreo")
        self.tree_camaras = ttk.Treeview(self.parent, columns=cols, show="headings")
        for col in cols:
            self.tree_camaras.heading(col, text=col)
            self.tree_camaras.column(col, width=120)
        self.tree_camaras.pack(expand=True, fill="both", padx=10, pady=10)

        self.actualizar_estado_camaras()

    def actualizar_estado_camaras(self):
        if self.tree_camaras is None:
            return
        for item in self.tree_camaras.get_children():
            self.tree_camaras.delete(item)
        try:
            camaras_activas = self.camara_manager.camaras_activas
            for serie, info in camaras_activas.items():
                dispositivo_db = self.logic.obtener_dispositivo_por_serie(serie)
                # Skip devices that no longer exist in the database
                if not dispositivo_db:
                    continue
                nombre = dispositivo_db.get('nombre', 'Desconocido')
                ubicacion = dispositivo_db.get('ubicacion', 'Desconocida')
                conectada = self.camara_manager.tomar_fotografia(serie) is not None
                monitoreando = info.get('monitoreando', False)
                estado_monitoreo = "🟢 Activo" if monitoreando else "🔴 Inactivo"
                self.tree_camaras.insert("", "end", values=(
                    serie,
                    nombre,
                    ubicacion,
                    info.get('ip', 'N/A'),
                    "✅" if conectada else "❌",
                    estado_monitoreo
                ))
            # Count only cameras that still exist in the database
            total = sum(1 for serie in camaras_activas.keys() 
                       if self.logic.obtener_dispositivo_por_serie(serie) is not None)
            conectadas = sum(1 for serie in camaras_activas.keys() 
                            if self.logic.obtener_dispositivo_por_serie(serie) is not None 
                            and self.camara_manager.tomar_fotografia(serie) is not None)
            monitoreando = sum(1 for serie, info in camaras_activas.items() 
                            if self.logic.obtener_dispositivo_por_serie(serie) is not None 
                            and info.get('monitoreando', False))
            self.estado_camaras_var.set(f"Cámaras: {conectadas}/{total} conectadas - Monitoreo: {monitoreando} activos")
        except Exception as e:
            print(f"Error actualizando estado de cámaras: {e}")
            self.estado_camaras_var.set(f"Error cargando cámaras: {e}")

    def capturar_foto_manual(self):
        seleccion = self.tree_camaras.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una cámara primero")
            return
        item = seleccion[0]
        values = self.tree_camaras.item(item, 'values')
        serie = values[0]
        estado_icon = values[4]
        conectada = estado_icon == "✅"
        if not conectada:
            messagebox.showerror("Error", "La cámara seleccionada no está conectada")
            return
        def capturar():
            if self.camara_manager.capturar_foto(serie):
                self.root.after(0, lambda: messagebox.showinfo("Éxito", "Foto capturada correctamente"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Error capturando foto"))
        threading.Thread(target=capturar, daemon=True).start()

    def iniciar_monitoreo_movimiento(self):
        if not self.camara_manager.camaras_activas:
            messagebox.showwarning("Advertencia", "No hay cámaras registradas")
            return
        iniciadas = self.camera_ctrl.start_monitoring_all(intervalo=5, callback_evento=self.registrar_evento_movimiento)
        self.actualizar_estado_camaras()
        messagebox.showinfo("Éxito", f"Monitoreo de movimiento iniciado en {iniciadas} cámaras")

    def registrar_evento_movimiento(self, serie, ruta_imagen):
        descripcion = f"Movimiento detectado - Imagen: {ruta_imagen}"
        self.logic.registrar_evento(serie, descripcion, "Detección Movimiento")

    def detener_monitoreo_movimiento(self):
        self.camera_ctrl.stop_monitoring_all()
        self.actualizar_estado_camaras()
        messagebox.showinfo("Éxito", "Monitoreo de movimiento detenido")

    def probar_deteccion_movimiento(self):
        seleccion = self.tree_camaras.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una cámara primero")
            return
        item = seleccion[0]
        serie = self.tree_camaras.item(item, 'values')[0]
        def probar():
            movimiento, ruta_imagen = self.camara_manager.detectar_movimiento(serie)
            if movimiento:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Movimiento Detectado", 
                    f"¡Movimiento detectado en cámara {serie}!\nImagen guardada: {ruta_imagen}"
                ))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    "Sin Movimiento", 
                    "No se detectó movimiento"
                ))
        threading.Thread(target=probar, daemon=True).start()

    def abrir_visor(self):
        try:
            gallery = CameraGallery(self.root, self.logic, self.camara_manager, self.camera_ctrl, styles=self.styles)
            gallery.show()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el visor: {e}")
