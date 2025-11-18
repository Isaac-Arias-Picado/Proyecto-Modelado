import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from data_logic import SecurityLogic
from datetime import datetime
from CamaraModule import CamaraManager
import threading 

COLOR_FONDO = "#1F2024"
COLOR_CARD = "#4B4952"
COLOR_TEXTO = "#FFFFFF"
COLOR_CAMPO = "#2A2B2F"
COLOR_BOTON = "#004F4D"
COLOR_BOTON_HOVER = "#A68F97"
COLOR_HEADER = "#004F4D"
COLOR_SELECCION = "#A68F97"

BTN_WIDTH = 20

class SecurityUI:
    def __init__(self, root):
        self.root = root
        self.logic = SecurityLogic()
        self.camara_manager = CamaraManager(self.logic)
        
        self.actualizacion_automatica_activa = False
        self.job_actualizacion = None
        
        self.root.title("Sistema de Seguridad")
        self.root.geometry("1100x720")
        self.root.configure(bg=COLOR_FONDO)

        self.estilo()
        self.mostrar_login()

    def estilo(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=COLOR_FONDO, foreground=COLOR_TEXTO)
        style.configure("Card.TFrame", background=COLOR_CARD)
        style.configure("Dark.TEntry", padding=6, fieldbackground=COLOR_CAMPO, foreground=COLOR_TEXTO, insertcolor=COLOR_TEXTO, relief="flat")
        style.configure("Dark.TButton", background=COLOR_BOTON, foreground=COLOR_TEXTO, font=("Segoe UI", 12, "bold"), padding=8, relief="flat")
        style.map("Dark.TButton", background=[("active", COLOR_BOTON_HOVER)])
        style.configure("Treeview", background=COLOR_CAMPO, foreground=COLOR_TEXTO, fieldbackground=COLOR_CAMPO, rowheight=26)
        style.configure("Treeview.Heading", background=COLOR_HEADER, foreground="#FFFFFF", relief="flat", font=("Segoe UI", 11, "bold"))
        style.map("Treeview", background=[("selected", COLOR_SELECCION)], foreground=[("selected", "#FFFFFF")])

    def mostrar_login(self):
        for w in self.root.winfo_children():
            w.destroy()

        frame = tk.Frame(self.root, bg=COLOR_FONDO)
        frame.pack(expand=True)

        card = tk.Frame(frame, bg=COLOR_CARD, padx=30, pady=30)
        card.pack()

        tk.Label(card, text="Acceso al Sistema", font=("Segoe UI", 22, "bold"), bg=COLOR_CARD, fg=COLOR_TEXTO).pack(pady=10)

        form = tk.Frame(card, bg=COLOR_CARD)
        form.pack(pady=10)

        tk.Label(form, text="Usuario:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=0, column=0, pady=10, sticky="e")
        self.in_usuario = ttk.Entry(form, width=23, style="Dark.TEntry")
        self.in_usuario.grid(row=0, column=1, padx=10)

        tk.Label(form, text="Contraseña:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=1, column=0, pady=10, sticky="e")
        self.in_pass = ttk.Entry(form, width=23, show="*", style="Dark.TEntry")
        self.in_pass.grid(row=1, column=1, padx=10)

        ttk.Button(card, text="Iniciar Sesión", style="Dark.TButton", width=BTN_WIDTH, command=self.login).pack(pady=10)
        ttk.Button(card, text="Crear Nuevo Usuario", style="Dark.TButton", width=BTN_WIDTH, command=self.mostrar_crear_usuario).pack(pady=5)

    def mostrar_crear_usuario(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Crear Usuario")
        dialog.configure(bg=COLOR_CARD)
        dialog.geometry("400x250")

        form = tk.Frame(dialog, bg=COLOR_CARD)
        form.pack(pady=20)

        tk.Label(form, text="Nuevo Usuario:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=0, column=0, pady=10, sticky="e")
        e_user = ttk.Entry(form, width=20, style="Dark.TEntry")
        e_user.grid(row=0, column=1, padx=10)

        tk.Label(form, text="Contraseña:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=1, column=0, pady=10, sticky="e")
        e_pass = ttk.Entry(form, width=20, show="*", style="Dark.TEntry")
        e_pass.grid(row=1, column=1, padx=10)

        def crear():
            try:
                self.logic.crear_usuario(e_user.get().strip(), e_pass.get().strip())
                messagebox.showinfo("Éxito", "Usuario creado correctamente")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dialog, text="Crear Usuario", style="Dark.TButton", width=BTN_WIDTH, command=crear).pack(pady=10)

    def login(self):
        u = self.in_usuario.get().strip()
        p = self.in_pass.get().strip()
        if not u or not p:
            messagebox.showerror("Error", "Ingrese usuario y contraseña")
            return
        if self.logic.autenticar(u, p):
            self.mostrar_principal()
        else:
            messagebox.showerror("Error", "Credenciales inválidas.")

    def mostrar_principal(self):
        for w in self.root.winfo_children():
            w.destroy()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.tab_estado = tk.Frame(self.notebook, bg=COLOR_FONDO)
        self.tab_disp = tk.Frame(self.notebook, bg=COLOR_FONDO)
        self.tab_event = tk.Frame(self.notebook, bg=COLOR_FONDO)
        self.tab_camaras = tk.Frame(self.notebook, bg=COLOR_FONDO)

        self.notebook.add(self.tab_estado, text="Estado General")
        self.notebook.add(self.tab_disp, text="Dispositivos")
        self.notebook.add(self.tab_event, text="Eventos")
        self.notebook.add(self.tab_camaras, text="Cámaras")

        self.logic.agregar_observador_eventos(self.actualizar_eventos_automatico)

        self.mostrar_estado()
        self.mostrar_dispositivos()
        self.mostrar_eventos()
        self.mostrar_camaras()
        
        self.iniciar_actualizacion_automatica()
    
    def iniciar_actualizacion_automatica(self):
        """Inicia la actualización automática de eventos"""
        self.actualizacion_automatica_activa = True
        self.programar_proxima_actualizacion()

    def detener_actualizacion_automatica(self):
        """Detiene la actualización automática"""
        self.actualizacion_automatica_activa = False
        if self.job_actualizacion:
            self.root.after_cancel(self.job_actualizacion)
            self.job_actualizacion = None

    def programar_proxima_actualizacion(self):
        """Programa la próxima actualización automática"""
        if self.actualizacion_automatica_activa:
            self.job_actualizacion = self.root.after(2000, self.actualizar_eventos_automatico)

    def actualizar_eventos_automatico(self):
        """Actualiza los eventos automáticamente"""
        if self.actualizacion_automatica_activa:
            try:
                if self.notebook.index(self.notebook.select()) == 2:  
                    eventos_actuales = self.logic.obtener_eventos()
                    self.refrescar_eventos(eventos_actuales)
            except Exception as e:
                print(f"Error en actualización automática: {e}")
            
            self.programar_proxima_actualizacion()
    
    def mostrar_eventos(self):
        for w in self.tab_event.winfo_children():
            w.destroy()

        tk.Label(self.tab_event, text="Registro de Eventos", font=("Segoe UI", 20, "bold"),
                 bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=10)

        btn_frame = tk.Frame(self.tab_event, bg=COLOR_FONDO)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Filtrar Eventos", style="Dark.TButton",
                   width=BTN_WIDTH, command=self.abrir_ventana_filtros).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Mostrar Todo", style="Dark.TButton",
                   width=BTN_WIDTH, command=lambda: self.refrescar_eventos(self.logic.obtener_eventos())).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Borrar Todos los Eventos", style="Dark.TButton",
                   width=BTN_WIDTH, command=self.borrar_eventos).pack(side="left", padx=5)
        
        self.btn_auto_update = ttk.Button(btn_frame, text="⏸️ Pausar Auto-Actualización", style="Dark.TButton",
                   width=BTN_WIDTH, command=self.toggle_actualizacion_automatica)
        self.btn_auto_update.pack(side="left", padx=5)

        cols = ("ID", "Fecha", "Tipo", "Dispositivo", "Descripción")
        self.tree_event = ttk.Treeview(self.tab_event, columns=cols, show="headings")

        for c in cols:
            self.tree_event.heading(c, text=c)

        self.tree_event.column("ID", width=40)
        self.tree_event.column("Fecha", width=160)
        self.tree_event.column("Descripción", width=400)

        self.tree_event.pack(expand=True, fill="both", padx=10, pady=10)

        self.refrescar_eventos(self.logic.obtener_eventos())

    def toggle_actualizacion_automatica(self):
        """Activa/desactiva la actualización automática"""
        if self.actualizacion_automatica_activa:
            self.detener_actualizacion_automatica()
            self.btn_auto_update.config(text="▶️ Reanudar Auto-Actualización")
        else:
            self.iniciar_actualizacion_automatica()
            self.btn_auto_update.config(text="⏸️ Pausar Auto-Actualización")

    def refrescar_eventos(self, eventos):
        """Actualiza la lista de eventos en la interfaz"""
        for r in self.tree_event.get_children():
            self.tree_event.delete(r)
        
        eventos_ordenados = sorted(eventos, 
                                 key=lambda x: datetime.strptime(x.get("fecha", "2000-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S"), 
                                 reverse=True)
        
        for i, ev in enumerate(eventos_ordenados, start=1):
            self.tree_event.insert("", "end", values=(
                i,
                ev.get("fecha"),
                ev.get("tipo"),
                ev.get("dispositivo"),
                ev.get("descripcion")
            ))
    
    def mostrar_camaras(self):
        for w in self.tab_camaras.winfo_children():
            w.destroy()

        tk.Label(self.tab_camaras, text="Gestión de Cámaras de Seguridad", 
                font=("Segoe UI", 20, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=10)

        btn_frame = tk.Frame(self.tab_camaras, bg=COLOR_FONDO)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="🔄 Iniciar Monitoreo", style="Dark.TButton", 
                  command=self.iniciar_monitoreo).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⏹️ Detener Monitoreo", style="Dark.TButton", 
                  command=self.detener_monitoreo).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📸 Capturar Foto Manual", style="Dark.TButton", 
                  command=self.capturar_foto_manual).pack(side="left", padx=5)

        estado_frame = tk.Frame(self.tab_camaras, bg=COLOR_CARD, padx=20, pady=10)
        estado_frame.pack(fill="x", padx=20, pady=10)

        self.estado_camaras_var = tk.StringVar(value="Estado: Cargando...")
        tk.Label(estado_frame, textvariable=self.estado_camaras_var, 
                bg=COLOR_CARD, fg=COLOR_TEXTO, font=("Segoe UI", 12)).pack()

        cols = ("Serie", "Nombre", "Ubicación", "IP", "Estado", "Conectada")
        self.tree_camaras = ttk.Treeview(self.tab_camaras, columns=cols, show="headings")
        
        for col in cols:
            self.tree_camaras.heading(col, text=col)
            self.tree_camaras.column(col, width=120)
        
        self.tree_camaras.pack(expand=True, fill="both", padx=10, pady=10)

        self.actualizar_estado_camaras()

    def actualizar_estado_camaras(self):
        for item in self.tree_camaras.get_children():
            self.tree_camaras.delete(item)

        estado_camaras = self.camara_manager.obtener_estado_camaras()
        
        for serie, info in estado_camaras.items():
            self.tree_camaras.insert("", "end", values=(
                serie,
                info['nombre'],
                info['ubicacion'],
                self.camara_manager.camaras_activas[serie]['ip'],
                info['estado'],
                "✅" if info['conectada'] else "❌"
            ))

        total = len(estado_camaras)
        conectadas = sum(1 for info in estado_camaras.values() if info['conectada'])
        self.estado_camaras_var.set(f"Cámaras: {conectadas}/{total} conectadas - Monitoreo: {'ACTIVO' if self.camara_manager.monitoreo_activo else 'INACTIVO'}")

    def iniciar_monitoreo(self):
        if not self.camara_manager.camaras_activas:
            messagebox.showwarning("Advertencia", "No hay cámaras registradas")
            return

        self.camara_manager.iniciar_monitoreo_automatico()
        self.actualizar_estado_camaras()
        messagebox.showinfo("Éxito", "Monitoreo automático iniciado")

    def detener_monitoreo(self):
        self.camara_manager.detener_monitoreo_automatico()
        self.actualizar_estado_camaras()
        messagebox.showinfo("Éxito", "Monitoreo automático detenido")

    def capturar_foto_manual(self):
        seleccion = self.tree_camaras.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona una cámara primero")
            return
        
        item = seleccion[0]
        serie = self.tree_camaras.item(item, 'values')[0]
        conectada = self.tree_camaras.item(item, 'values')[5] == "✅"
    
        if not conectada:
            messagebox.showerror("Error", "La cámara seleccionada no está conectada")
            return

        item = seleccion[0]
        serie = self.tree_camaras.item(item, 'values')[0]

        def capturar():
            if self.camara_manager.capturar_foto(serie):
                self.root.after(0, lambda: messagebox.showinfo("Éxito", "Foto capturada correctamente"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Error capturando foto"))

        threading.Thread(target=capturar, daemon=True).start()

    def mostrar_estado(self):
        for w in self.tab_estado.winfo_children():
            w.destroy()

        tk.Label(self.tab_estado, text="Estado General", font=("Segoe UI", 20, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=15)

        card = tk.Frame(self.tab_estado, bg=COLOR_CARD, padx=20, pady=20)
        card.pack(padx=20, pady=10, fill="x")

        total, activos, hoy = self.logic.obtener_resumen()
        txt = f"Dispositivos Totales: {total}\nDispositivos Activos: {activos}\nEventos Hoy: {hoy}"

        tk.Label(card, text=txt, bg=COLOR_CARD, fg=COLOR_TEXTO, font=("Segoe UI", 14), justify="left").pack()

        ttk.Button(self.tab_estado, text="Cerrar Sesión", style="Dark.TButton", width=BTN_WIDTH, command=self.mostrar_login).pack(pady=20)

    def borrar_eventos(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro de borrar todos los eventos?"):
            self.logic.eliminar_eventos()
            self.mostrar_eventos()
            messagebox.showinfo("Éxito", "Eventos borrados correctamente")

    def mostrar_dispositivos(self):
        for w in self.tab_disp.winfo_children():
            w.destroy()

        tk.Label(self.tab_disp, text="Gestión de Dispositivos", font=("Segoe UI", 20, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=10)

        ttk.Button(self.tab_disp, text="Registrar Dispositivo", style="Dark.TButton", width=BTN_WIDTH, command=self.registrar_dispositivo).pack(pady=5)

        actions = tk.Frame(self.tab_disp, bg=COLOR_FONDO)
        actions.pack(pady=5)

        ttk.Button(actions, text="Cambiar Modo", style="Dark.TButton", width=BTN_WIDTH, command=self.cambiar_modo_seleccionado).pack(side="left", padx=8, ipadx=4)
        ttk.Button(actions, text="Cambiar Estado", style="Dark.TButton", width=BTN_WIDTH, command=self.cambiar_estado_seleccionado).pack(side="left", padx=8, ipadx=4)
        ttk.Button(actions, text="Eliminar Dispositivo", style="Dark.TButton", width=BTN_WIDTH, command=self.eliminar_dispositivo_seleccionado).pack(side="left", padx=8, ipadx=4)

        cols = ("ID", "Serie", "Tipo", "Nombre", "Estado", "Modo", "Ubicación")
        self.tree_disp = ttk.Treeview(self.tab_disp, columns=cols, show="headings")
        for c in cols:
            self.tree_disp.heading(c, text=c)
            width = 100 if c == "Nombre" else 120
            self.tree_disp.column(c, width=width)
        self.tree_disp.pack(expand=True, fill="both", padx=10, pady=10)

        self.refrescar_dispositivos()

    def refrescar_dispositivos(self):
        for r in self.tree_disp.get_children():
            self.tree_disp.delete(r)
        for i, d in enumerate(self.logic.obtener_dispositivos(), start=1):
            self.tree_disp.insert("", "end", values=(
                i,
                d.get("serie"),
                d.get("tipo"),
                d.get("nombre"),
                d.get("estado"),
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
        
        modo_actual = dispositivo.get("modo", "Normal")
        
        if dispositivo.get("tipo") == "Cerradura Inteligente":
            modos = ["Normal", "Siempre Abierto", "Siempre Cerrado"]
        elif dispositivo.get("tipo") == "Cámara de Seguridad":
            modos = ["Normal", "Grabación Continua", "Detección Movimiento"]
        else:
            modos = ["Normal", "Alta Sensibilidad", "Baja Sensibilidad"]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Cambiar Modo")
        dialog.configure(bg=COLOR_CARD)
        dialog.geometry("300x150")
        
        tk.Label(dialog, text=f"Modo actual: {modo_actual}", 
                bg=COLOR_CARD, fg=COLOR_TEXTO, font=("Segoe UI", 10)).pack(pady=10)
        
        tk.Label(dialog, text="Nuevo modo:", bg=COLOR_CARD, fg=COLOR_TEXTO).pack(pady=5)
        
        modo_var = tk.StringVar(value=modo_actual)
        combobox = ttk.Combobox(dialog, textvariable=modo_var, values=modos, state="readonly")
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
        
        estado_actual = dispositivo.get("estado", "Inactivo")
        nuevo_estado = "Activo" if estado_actual == "Inactivo" else "Inactivo"
        
        try:
            self.logic.cambiar_estado_dispositivo(serie, nuevo_estado)
            self.refrescar_dispositivos()
            messagebox.showinfo("Éxito", f"Estado cambiado a: {nuevo_estado}")
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
                    self.camara_manager.eliminar_camara(serie)
                else:
                    self.logic.eliminar_dispositivo(serie)
                    
                self.refrescar_dispositivos()
                self.actualizar_estado_camaras() 
                messagebox.showinfo("Éxito", "Dispositivo eliminado correctamente")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def registrar_dispositivo(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Dispositivo")
        dialog.configure(bg=COLOR_CARD)
        dialog.geometry("450x400")

        tipos = [
            "Sensor de Movimiento", "Cerradura Inteligente", "Detector de Humo",
            "Cámara de Seguridad", "Simulador Presencia", "Sensor Puerta",
            "Detector Placas", "Detector Láser"
        ]

        form = tk.Frame(dialog, bg=COLOR_CARD)
        form.pack(pady=20)

        tk.Label(form, text="Serie:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=0, column=0, pady=8, sticky="e")
        e_serie = ttk.Entry(form, width=30, style="Dark.TEntry")
        e_serie.grid(row=0, column=1, padx=10)

        tk.Label(form, text="Tipo:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=1, column=0, pady=8, sticky="e")
        cb_tipo = ttk.Combobox(form, values=tipos, width=28, state="readonly")
        cb_tipo.grid(row=1, column=1, padx=10)

        tk.Label(form, text="Nombre:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=2, column=0, pady=8, sticky="e")
        e_nombre = ttk.Entry(form, width=30, style="Dark.TEntry")
        e_nombre.grid(row=2, column=1, padx=10)

        tk.Label(form, text="Ubicación:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=3, column=0, pady=8, sticky="e")
        e_ubicacion = ttk.Entry(form, width=30, style="Dark.TEntry")
        e_ubicacion.grid(row=3, column=1, padx=10)

        self.camara_frame = tk.Frame(form, bg=COLOR_CARD)
        self.camara_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="we")

        tk.Label(self.camara_frame, text="IP de la Cámara:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=0, column=0, pady=5, sticky="e")
        self.e_ip_camara = ttk.Entry(self.camara_frame, width=30, style="Dark.TEntry")
        self.e_ip_camara.grid(row=0, column=1, padx=10, pady=5)
        self.e_ip_camara.insert(0, "192.168.0.102")

        self.camara_frame.grid_remove()

        def on_tipo_change(event):
            if cb_tipo.get() == "Cámara de Seguridad":
                self.camara_frame.grid()
                dialog.geometry("450x450")
            else:
                self.camara_frame.grid_remove()
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
                    ip_camara = self.e_ip_camara.get().strip()
                    if not ip_camara:
                        messagebox.showerror("Error", "La IP de la cámara es obligatoria")
                        return

                    self.camara_manager.registrar_camara(serie, nombre, ubicacion, ip_camara)
                    
                else:
                    self.logic.registrar_dispositivo(serie, tipo, nombre, ubicacion)

                dialog.destroy()
                self.refrescar_dispositivos()
                self.actualizar_estado_camaras()
                messagebox.showinfo("Éxito", "Dispositivo registrado correctamente")
                
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dialog, text="Registrar", style="Dark.TButton", width=BTN_WIDTH, command=guardar).pack(pady=10)

    def mostrar_eventos(self):
        for w in self.tab_event.winfo_children():
            w.destroy()

        tk.Label(self.tab_event, text="Registro de Eventos", font=("Segoe UI", 20, "bold"),
                 bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=10)

        btn_frame = tk.Frame(self.tab_event, bg=COLOR_FONDO)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Filtrar Eventos", style="Dark.TButton",
                   width=BTN_WIDTH, command=self.abrir_ventana_filtros).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Mostrar Todo", style="Dark.TButton",
                   width=BTN_WIDTH, command=lambda: self.refrescar_eventos(self.logic.obtener_eventos())).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Borrar Todos los Eventos", style="Dark.TButton",
                   width=BTN_WIDTH, command=self.borrar_eventos).pack(side="left", padx=5)

        cols = ("ID", "Fecha", "Tipo", "Dispositivo", "Descripción")
        self.tree_event = ttk.Treeview(self.tab_event, columns=cols, show="headings")

        for c in cols:
            self.tree_event.heading(c, text=c)

        self.tree_event.column("ID", width=40)
        self.tree_event.column("Fecha", width=160)
        self.tree_event.column("Descripción", width=400)

        self.tree_event.pack(expand=True, fill="both", padx=10, pady=10)

        self.refrescar_eventos(self.logic.obtener_eventos())

    def abrir_ventana_filtros(self):
        vent = tk.Toplevel(self.root)
        vent.title("Filtrar Eventos")
        vent.geometry("500x520")
        vent.configure(bg=COLOR_CARD)

        tk.Label(vent, text="Filtros de Eventos", font=("Segoe UI", 16, "bold"),
                 bg=COLOR_CARD, fg=COLOR_TEXTO).pack(pady=10)

        frame = tk.Frame(vent, bg=COLOR_CARD)
        frame.pack(pady=10)

        tk.Label(frame, text="Dispositivo (Serie):", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=0, column=0, pady=8, sticky="e")
        dispositivos = [d.get("serie") for d in self.logic.obtener_dispositivos()]
        self.f_disp = ttk.Combobox(frame, values=[""] + dispositivos, width=25, state="readonly")
        self.f_disp.grid(row=0, column=1, padx=10)

        tk.Label(frame, text="Tipo:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=1, column=0, pady=8, sticky="e")
        tipos = list({d.get("tipo") for d in self.logic.obtener_dispositivos()})
        self.f_tipo = ttk.Combobox(frame, values=[""] + tipos, width=25, state="readonly")
        self.f_tipo.grid(row=1, column=1, padx=10)

        tk.Label(frame, text="Nombre:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=2, column=0, pady=8, sticky="e")
        nombres = list({d.get("nombre") for d in self.logic.obtener_dispositivos()})
        self.f_nombre = ttk.Combobox(frame, values=[""] + nombres, width=25, state="readonly")
        self.f_nombre.grid(row=2, column=1, padx=10)

        tk.Label(frame, text="Número de Serie:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=3, column=0, pady=8, sticky="e")
        self.f_serie = ttk.Entry(frame, width=27)
        self.f_serie.grid(row=3, column=1, padx=10)

        tk.Label(frame, text="Ubicación:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=4, column=0, pady=8, sticky="e")
        ubicaciones = list({d.get("ubicacion") for d in self.logic.obtener_dispositivos()})
        self.f_ubicacion = ttk.Combobox(frame, values=[""] + ubicaciones, width=25, state="readonly")
        self.f_ubicacion.grid(row=4, column=1, padx=10)

        tk.Label(frame, text="Fecha inicio (YYYY-MM-DD):", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=5, column=0, pady=8, sticky="e")
        self.f_fecha_ini = ttk.Entry(frame, width=27)
        self.f_fecha_ini.grid(row=5, column=1, padx=10)

        tk.Label(frame, text="Fecha fin (YYYY-MM-DD):", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=6, column=0, pady=8, sticky="e")
        self.f_fecha_fin = ttk.Entry(frame, width=27)
        self.f_fecha_fin.grid(row=6, column=1, padx=10)

        ttk.Button(vent, text="Aplicar Filtro", style="Dark.TButton", width=20,
                   command=lambda: self.aplicar_filtros_desde_ventana(vent)).pack(pady=15)

        ttk.Button(vent, text="Cerrar", style="Dark.TButton", width=20,
                   command=vent.destroy).pack(pady=5)

    def aplicar_filtros_desde_ventana(self, vent):
        disp = self.f_disp.get().strip() or None
        tipo = self.f_tipo.get().strip() or None
        nombre = self.f_nombre.get().strip() or None
        serie = self.f_serie.get().strip() or None
        ubic = self.f_ubicacion.get().strip() or None
        fi = self.f_fecha_ini.get().strip() or None
        ff = self.f_fecha_fin.get().strip() or None

        for d in (fi, ff):
            if d:
                try:
                    datetime.strptime(d, "%Y-%m-%d")
                except ValueError:
                    messagebox.showerror("Error", f"Fecha inválida: {d}. Formato: YYYY-MM-DD")
                    return

        eventos = self.logic.filtrar_eventos(
            dispositivo=disp,
            tipo=tipo,
            nombre=nombre,
            serie=serie,
            ubicacion=ubic,
            fecha_inicio=fi,
            fecha_fin=ff
        )

        self.refrescar_eventos(eventos)
        vent.destroy()  

    def refrescar_eventos(self, eventos):
        for r in self.tree_event.get_children():
            self.tree_event.delete(r)
        for i, ev in enumerate(eventos, start=1):
            self.tree_event.insert("", "end", values=(
                i,
                ev.get("fecha"),
                ev.get("tipo"),
                ev.get("dispositivo"),
                ev.get("descripcion")
            ))

if __name__ == "__main__":
    root = tk.Tk()
    app = SecurityUI(root)
    root.mainloop()