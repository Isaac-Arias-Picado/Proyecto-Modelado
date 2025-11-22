import tkinter as tk
from tkinter import ttk, messagebox

class DeviceView:
    def __init__(self, parent, root, logic, camara_manager, camera_ctrl, plates_ctrl=None, styles=None):
        self.parent = parent
        self.root = root
        self.logic = logic
        self.camara_manager = camara_manager
        self.camera_ctrl = camera_ctrl
        self.plates_ctrl = plates_ctrl
        self.styles = styles or {}
        self.tree_disp = None

    def mostrar_dispositivos(self):
        for w in self.parent.winfo_children():
            w.destroy()

        tk.Label(self.parent, text="Gestión de Dispositivos", font=("Segoe UI", 20, "bold"), bg=self.styles.get('COLOR_FONDO','#1F2024'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack(pady=10)

        ttk.Button(self.parent, text="Registrar Dispositivo", style="Dark.TButton", width=20, command=self.registrar_dispositivo).pack(pady=5)

        actions = tk.Frame(self.parent, bg=self.styles.get('COLOR_FONDO','#1F2024'))
        actions.pack(pady=5)

        ttk.Button(actions, text="Cambiar Modo", style="Dark.TButton", width=20, command=self.cambiar_modo_seleccionado).pack(side="left", padx=8, ipadx=4)
        ttk.Button(actions, text="Cambiar Estado", style="Dark.TButton", width=20, command=self.cambiar_estado_seleccionado).pack(side="left", padx=8, ipadx=4)
        ttk.Button(actions, text="Eliminar Dispositivo", style="Dark.TButton", width=20, command=self.eliminar_dispositivo_seleccionado).pack(side="left", padx=8, ipadx=4)

        cols = ("ID", "Serie", "Tipo", "Nombre", "Estado", "Modo", "Ubicación")
        self.tree_disp = ttk.Treeview(self.parent, columns=cols, show="headings")
        for c in cols:
            self.tree_disp.heading(c, text=c)
            width = 100 if c == "Nombre" else 120
            self.tree_disp.column(c, width=width)
        self.tree_disp.pack(expand=True, fill="both", padx=10, pady=10)

        self.refrescar_dispositivos()

    def refrescar_dispositivos(self):
        if self.tree_disp is None:
            return
        for r in self.tree_disp.get_children():
            self.tree_disp.delete(r)
        for i, d in enumerate(self.logic.obtener_dispositivos(), start=1):
            estado_mostrar = "Activo" if d.get("estado") == "activo" else "Inactivo"
            self.tree_disp.insert("", "end", values=(
                i,
                d.get("serie"),
                d.get("tipo"),
                d.get("nombre"),
                estado_mostrar,
                d.get("modo"),
                d.get("ubicacion")
            ))

    def cambiar_modo_seleccionado(self):
        seleccion = self.tree_disp.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un dispositivo primero")
            return
        item = seleccion[0]
        serie = self.tree_disp.item(item, 'values')[1]
        dispositivo = self.logic.obtener_dispositivo_por_serie(serie)
        if not dispositivo:
            messagebox.showerror("Error", "Dispositivo no encontrado")
            return
        tipo_dispositivo = dispositivo.get("tipo")
        modo_actual = dispositivo.get("modo", "Normal")
        modos_validos = self.logic.MODOS_POR_TIPO.get(tipo_dispositivo, ["Normal", "Inactivo"])
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Cambiar Modo - {tipo_dispositivo}")
        dialog.configure(bg=self.styles.get('COLOR_CARD','#4B4952'))
        dialog.geometry("350x200")
        tk.Label(dialog, text=f"Dispositivo: {dispositivo.get('nombre')}", bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF'), font=("Segoe UI", 10, "bold")).pack(pady=10)
        tk.Label(dialog, text=f"Modo actual: {modo_actual}", bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF'), font=("Segoe UI", 10)).pack(pady=5)
        tk.Label(dialog, text="Nuevo modo:", bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).pack(pady=5)
        modo_var = tk.StringVar(value=modo_actual)
        combobox = ttk.Combobox(dialog, textvariable=modo_var, values=modos_validos, state="readonly")
        combobox.pack(pady=5)
        def aplicar_cambio():
            nuevo_modo = modo_var.get()
            try:
                self.logic.cambiar_modo_dispositivo(serie, nuevo_modo)
                dialog.destroy()
                self.refrescar_dispositivos()
                messagebox.showinfo("Éxito", f"Modo cambiado a: {nuevo_modo}")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        ttk.Button(dialog, text="Aplicar", style="Dark.TButton", command=aplicar_cambio).pack(pady=10)

    def cambiar_estado_seleccionado(self):
        seleccion = self.tree_disp.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un dispositivo primero")
            return
        item = seleccion[0]
        serie = self.tree_disp.item(item, 'values')[1]
        dispositivo = self.logic.obtener_dispositivo_por_serie(serie)
        if not dispositivo:
            messagebox.showerror("Error", "Dispositivo no encontrado")
            return
        estado_actual = dispositivo.get("estado", "inactivo")
        estado_actual_mostrar = "Activo" if estado_actual == "activo" else "Inactivo"
        nuevo_estado = "inactivo" if estado_actual == "activo" else "activo"
        nuevo_estado_mostrar = "Inactivo" if estado_actual == "activo" else "Activo"
        if messagebox.askyesno("Confirmar Cambio", f"¿Cambiar estado del dispositivo '{dispositivo.get('nombre')}' de {estado_actual_mostrar} a {nuevo_estado_mostrar}?"):
            try:
                self.logic.cambiar_estado_dispositivo(serie, nuevo_estado)
                self.refrescar_dispositivos()
                messagebox.showinfo("Éxito", f"Estado cambiado a: {nuevo_estado_mostrar}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def eliminar_dispositivo_seleccionado(self):
        seleccion = self.tree_disp.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un dispositivo primero")
            return
        item = seleccion[0]
        serie = self.tree_disp.item(item, 'values')[1]
        nombre = self.tree_disp.item(item, 'values')[3]
        tipo = self.tree_disp.item(item, 'values')[2]
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de eliminar el dispositivo '{nombre}'?"):
            try:
                if tipo == "Cámara de Seguridad":
                
                    try:
                        self.camera_ctrl.desactivar_camara(serie)
                    except Exception:
                    
                        self.camara_manager.desactivar_camara(serie)
                elif tipo == "Detector Placas":
                
                    if self.plates_ctrl:
                        try:
                            self.plates_ctrl.desactivar_detector(serie)
                        except Exception as e:
                            print(f"Error desactivando detector: {e}")
                self.logic.eliminar_dispositivo(serie)
                self.refrescar_dispositivos()
                
                messagebox.showinfo("Éxito", "Dispositivo eliminado correctamente")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def registrar_dispositivo(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Dispositivo")
        dialog.configure(bg=self.styles.get('COLOR_CARD','#4B4952'))
        dialog.geometry("450x400")
        tipos = [
            "Sensor de Movimiento", "Cerradura Inteligente", "Detector de Humo",
            "Cámara de Seguridad", "Simulador Presencia", "Sensor Puerta",
            "Detector Placas", "Detector Láser"
        ]
        form = tk.Frame(dialog, bg=self.styles.get('COLOR_CARD','#4B4952'))
        form.pack(pady=20)
        tk.Label(form, text="Serie:", bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).grid(row=0, column=0, pady=8, sticky="e")
        e_serie = ttk.Entry(form, width=30, style="Dark.TEntry")
        e_serie.grid(row=0, column=1, padx=10)
        tk.Label(form, text="Tipo:", bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).grid(row=1, column=0, pady=8, sticky="e")
        cb_tipo = ttk.Combobox(form, values=tipos, width=28, state="readonly")
        cb_tipo.grid(row=1, column=1, padx=10)
        tk.Label(form, text="Nombre:", bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).grid(row=2, column=0, pady=8, sticky="e")
        e_nombre = ttk.Entry(form, width=30, style="Dark.TEntry")
        e_nombre.grid(row=2, column=1, padx=10)
        tk.Label(form, text="Ubicación:", bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).grid(row=3, column=0, pady=8, sticky="e")
        e_ubicacion = ttk.Entry(form, width=30, style="Dark.TEntry")
        e_ubicacion.grid(row=3, column=1, padx=10)
        camara_frame = tk.Frame(form, bg=self.styles.get('COLOR_CARD','#4B4952'))
        camara_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="we")
        tk.Label(camara_frame, text="IP de la Cámara:", bg=self.styles.get('COLOR_CARD','#4B4952'), fg=self.styles.get('COLOR_TEXTO','#FFFFFF')).grid(row=0, column=0, pady=5, sticky="e")
        e_ip_camara = ttk.Entry(camara_frame, width=30, style="Dark.TEntry")
        e_ip_camara.grid(row=0, column=1, padx=10, pady=5)
        e_ip_camara.insert(0, "192.168.0.102")
        camara_frame.grid_remove()
        def on_tipo_change(event):
            if cb_tipo.get() in ("Cámara de Seguridad", "Detector Placas"):
                camara_frame.grid()
                dialog.geometry("450x450")
            else:
                camara_frame.grid_remove()
                dialog.geometry("450x400")
        cb_tipo.bind('<<ComboboxSelected>>', on_tipo_change)
        def guardar():
            try:
                serie = e_serie.get().strip()
                tipo = cb_tipo.get().strip()
                nombre = e_nombre.get().strip()
                ubicacion = e_ubicacion.get().strip()
                if not all([serie, tipo, nombre, ubicacion]):
                    messagebox.showerror("Error", "Todos los campos básicos son obligatorios")
                    return
                dispositivo_existente = self.logic.obtener_dispositivo_por_serie(serie)
                if dispositivo_existente:
                    messagebox.showerror("Error", f"Ya existe un dispositivo con la serie: {serie}")
                    return
                if tipo == "Cámara de Seguridad":
                    ip_camara = e_ip_camara.get().strip()
                    if not ip_camara:
                        messagebox.showerror("Error", "La IP de la cámara es obligatoria")
                        return
                    
                    if self.camera_ctrl.activar_camara(serie, ip_camara, "IP Camera"):
                        self.logic.registrar_dispositivo(serie, tipo, nombre, ubicacion)
                    else:
                        messagebox.showerror("Error", "No se pudo activar la cámara")
                        return
                elif tipo == "Detector Placas":
                    ip_camara = e_ip_camara.get().strip()
                    if not ip_camara:
                        messagebox.showerror("Error", "La IP del detector es obligatoria")
                        return
                    if self.plates_ctrl:
                        if self.plates_ctrl.activar_detector(serie, ip_camara, "Detector Placas"):
                            self.logic.registrar_dispositivo(serie, tipo, nombre, ubicacion)
                        else:
                            messagebox.showerror("Error", "No se pudo activar el detector de placas")
                            return
                    else:
                        
                        self.logic.registrar_dispositivo(serie, tipo, nombre, ubicacion)
                else:
                    self.logic.registrar_dispositivo(serie, tipo, nombre, ubicacion)
                dialog.destroy()
                self.refrescar_dispositivos()
                messagebox.showinfo("Éxito", "Dispositivo registrado correctamente")
            except Exception as e:
                messagebox.showerror("Error", str(e))
        ttk.Button(dialog, text="Registrar", style="Dark.TButton", width=20, command=guardar).pack(pady=10)
