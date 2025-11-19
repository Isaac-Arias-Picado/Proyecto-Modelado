import tkinter as tk
from tkinter import ttk, messagebox
import threading

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

    def mostrar_plaquetas(self):
        for w in self.parent.winfo_children():
            w.destroy()

        tk.Label(self.parent, text="Detector de Placas", font=("Segoe UI", 20, "bold"), bg=self.styles.get('COLOR_FONDO','#1F2024'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack(pady=10)

        btn_frame = tk.Frame(self.parent, bg=self.styles.get('COLOR_FONDO','#1F2024'))
        btn_frame.pack(pady=8)

        ttk.Button(btn_frame, text="▶ Iniciar Monitoreo", style="Dark.TButton", command=self.iniciar_monitoreo).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹ Detener Monitoreo", style="Dark.TButton", command=self.detener_monitoreo).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔍 Probar Detección", style="Dark.TButton", command=self.probar_deteccion).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Registrar Placa", style="Dark.TButton", command=self.registrar_placa_dialog).pack(side="left", padx=5)

        estado = tk.Frame(self.parent, bg=self.styles.get('COLOR_CARD','#4B4952'), padx=10, pady=8)
        estado.pack(fill="x", padx=20, pady=10)
        tk.Label(estado, textvariable=self.status_var, bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack()

        cols = ("Serie", "Nombre", "Ubicación", "IP", "Estado", "Monitoreo")
        self.tree = ttk.Treeview(self.parent, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

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
                nombre = dispositivo.get('nombre','Desconocido') if dispositivo else 'Desconocido'
                ubic = dispositivo.get('ubicacion','Desconocida') if dispositivo else 'Desconocida'
                conectada = self.manager._fetch_image(info.get('ip')) is not None
                monit = info.get('monitoreando', False)
                estado_mon = '🟢 Activo' if monit else '🔴 Inactivo'
                self.tree.insert('', 'end', values=(serie, nombre, ubic, info.get('ip','N/A'), '✅' if conectada else '❌', estado_mon))
            total = len(detectores)
            mon = sum(1 for v in detectores.values() if v.get('monitoreando', False))
            self.status_var.set(f"Detectores: {total} registrados - Monitoreo: {mon} activos")
        except Exception as e:
            self.status_var.set(f"Error: {e}")

    def iniciar_monitoreo(self):
        if not self.manager.detectores_activas:
            messagebox.showwarning("Advertencia", "No hay detectores activados")
            return
        started = self.ctrl.start_monitoring_all(intervalo=5, callback_evento=self._evento_detectado)
        self.actualizar_lista()
        messagebox.showinfo("Éxito", f"Monitoreo iniciado en {started} detectores")

    def detener_monitoreo(self):
        self.ctrl.stop_monitoring_all()
        self.actualizar_lista()
        messagebox.showinfo("Éxito", "Monitoreo detenido")

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
            detected, placa, ruta = self.ctrl.detectar_placa_once(serie)
            if detected:
                self.root.after(0, lambda: messagebox.showinfo("Placa", f"Placa: {placa or 'N/D'}\nImagen: {ruta or 'N/A'}"))
            else:
                self.root.after(0, lambda: messagebox.showinfo("Sin Detección", "No se detectó ninguna placa"))
        threading.Thread(target=run, daemon=True).start()

    def registrar_placa_dialog(self):
        def guardar():
            placa = e_placa.get().strip().upper()
            prop = e_prop.get().strip()
            if not placa:
                messagebox.showerror("Error", "Ingrese la placa")
                return
            try:
                self.logic.guardar_placa(placa, prop)
                messagebox.showinfo("Éxito", "Placa registrada")
                top.destroy()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))
        top = tk.Toplevel(self.root)
        top.title("Registrar Placa")
        top.configure(bg=self.styles.get('COLOR_CARD','#4B4952'))
        tk.Label(top, text="Placa:", bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack(pady=5)
        e_placa = ttk.Entry(top)
        e_placa.pack(padx=10)
        tk.Label(top, text="Propietario:", bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack(pady=5)
        e_prop = ttk.Entry(top)
        e_prop.pack(padx=10)
        ttk.Button(top, text="Guardar", style="Dark.TButton", command=guardar).pack(pady=10)
 