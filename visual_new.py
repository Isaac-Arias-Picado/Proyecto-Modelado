import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
import threading

from data_logic import SecurityLogic
from CamaraModule import CamaraManager
from camera_controller import CameraController
from devices_view import DeviceView
from cameras_view import CameraView
from DetectorPlacasModule import DetectorPlacasManager
from plates_controller import PlatesController
from plates_view import PlatesView
from contacts_view import ContactsView
from panic_view import PanicView
from monitor_boton_pico import MonitorBotonPico

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
        self.camara_manager = CamaraManager()
        self.camara_manager.set_event_callback(self.logic.registrar_evento)
        self.camera_ctrl = CameraController(self.camara_manager, self.logic)
        self.placas_manager = DetectorPlacasManager()
        self.plates_ctrl = PlatesController(self.placas_manager, self.logic)
        self.device_view = None
        self.camera_view = None
        self.contacts_view = None
        self.panic_view = None
        self.actualizacion_automatica_activa = False
        self.job_actualizacion = None
        self.filtros_activos = False
        
        self.monitor_boton = MonitorBotonPico(
            callback_panico=self.on_boton_fisico_presionado,
            callback_silencioso=self.on_boton_silencioso_presionado,
            callback_movimiento=self.on_movimiento_pico,
            callback_humo=self.on_humo_detectado,
            callback_magnet_on=self.on_magnet_on,
            callback_magnet_off=self.on_magnet_off,
            callback_laser_blocked=self.on_laser_blocked,
            callback_laser_ok=self.on_laser_ok
        )
        self.camara_manager.set_monitor_boton(self.monitor_boton)
        
        self.registrar_boton_fisico_automatico()
        
        self.iniciar_monitor_boton()
        
        self.estado_simulador_enviado = None 

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def estilo(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=COLOR_FONDO, foreground=COLOR_TEXTO)
        style.configure("Card.TFrame", background=COLOR_CARD)
        style.configure("Dark.TEntry", padding=6, fieldbackground=COLOR_CAMPO, foreground=COLOR_TEXTO, insertcolor=COLOR_TEXTO, relief="flat")
        style.configure("Dark.TButton", background=COLOR_BOTON, foreground=COLOR_TEXTO, font=("Segoe UI", 12, "bold"), padding=8, relief="flat")
        style.map("Dark.TButton", background=[("active", COLOR_BOTON_HOVER)])
        style.configure("Small.TButton", background=COLOR_BOTON, foreground=COLOR_TEXTO, font=("Segoe UI", 9), padding=4, relief="flat")
        style.map("Small.TButton", background=[("active", COLOR_BOTON_HOVER)])
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

    
    def registrar_boton_fisico_automatico(self):
        """Registra automáticamente el botón físico y sensor si no existen"""
        try:
            boton = self.logic.obtener_dispositivo_por_serie("PICO-BOTON-001")
            if not boton:
                self.logic.registrar_dispositivo(
                    serie="PICO-BOTON-001",
                    tipo="Botón de Pánico",
                    nombre="Botón Físico Pico",
                    ubicacion="Raspberry Pi Pico"
                )
            
            sensor = self.logic.obtener_dispositivo_por_serie("PICO-SENSOR-001")
            if not sensor:
                self.logic.registrar_dispositivo(
                    serie="PICO-SENSOR-001",
                    tipo="Sensor de Movimiento",
                    nombre="Sensor HC-SR04 Pico",
                    ubicacion="Raspberry Pi Pico"
                )
            
            simulador = self.logic.obtener_dispositivo_por_serie("PICO-SIMULADOR-001")
            if not simulador:
                self.logic.registrar_dispositivo(
                    serie="PICO-SIMULADOR-001",
                    tipo="Simulador Presencia",
                    nombre="Simulador LED Pico",
                    ubicacion="Raspberry Pi Pico"
                )
            
            humo = self.logic.obtener_dispositivo_por_serie("PICO-HUMO-001")
            if not humo:
                self.logic.registrar_dispositivo(
                    serie="PICO-HUMO-001",
                    tipo="Detector de Humo",
                    nombre="Detector Humo Pico",
                    ubicacion="Raspberry Pi Pico"
                )
            
            puerta = self.logic.obtener_dispositivo_por_serie("PICO-PUERTA-001")
            if not puerta:
                self.logic.registrar_dispositivo(
                    serie="PICO-PUERTA-001",
                    tipo="Sensor Puertas y Ventanas",
                    nombre="Sensor Puerta Pico",
                    ubicacion="Raspberry Pi Pico"
                )
            elif puerta.get("tipo") != "Sensor Puertas y Ventanas":
                self.logic.actualizar_tipo_dispositivo("PICO-PUERTA-001", "Sensor Puertas y Ventanas")
            
            laser = self.logic.obtener_dispositivo_por_serie("PICO-LASER-001")
            if not laser:
                self.logic.registrar_dispositivo(
                    serie="PICO-LASER-001",
                    tipo="Detector Láser",
                    nombre="Barrera Láser Pico",
                    ubicacion="Raspberry Pi Pico"
                )
        except Exception:
            pass

    def mostrar_principal(self):
        for w in self.root.winfo_children():
            w.destroy()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        self.tab_estado = tk.Frame(self.notebook, bg=COLOR_FONDO)
        self.tab_disp = tk.Frame(self.notebook, bg=COLOR_FONDO)
        self.tab_event = tk.Frame(self.notebook, bg=COLOR_FONDO)
        self.tab_camaras = tk.Frame(self.notebook, bg=COLOR_FONDO)
        self.tab_placas = tk.Frame(self.notebook, bg=COLOR_FONDO)
        self.tab_contactos = tk.Frame(self.notebook, bg=COLOR_FONDO)
        self.tab_panico = tk.Frame(self.notebook, bg=COLOR_FONDO)

        self.notebook.add(self.tab_estado, text="Estado General")
        self.notebook.add(self.tab_disp, text="Dispositivos")
        self.notebook.add(self.tab_event, text="Eventos")
        self.notebook.add(self.tab_camaras, text="Cámaras")
        self.notebook.add(self.tab_placas, text="Detector Placas")
        self.notebook.add(self.tab_contactos, text="Contactos")
        self.notebook.add(self.tab_panico, text="🚨 Emergencia")

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        self.logic.agregar_observador_eventos(self.on_evento_registrado)
        self.mostrar_estado()

        self.device_view = DeviceView(self.tab_disp, self.root, self.logic, self.camara_manager, self.camera_ctrl, self.plates_ctrl, styles={
            'COLOR_FONDO': COLOR_FONDO,
            'COLOR_CARD': COLOR_CARD,
            'COLOR_TEXTO': COLOR_TEXTO
        })
        self.camera_view = CameraView(self.tab_camaras, self.root, self.logic, self.camara_manager, self.camera_ctrl, styles={
            'COLOR_FONDO': COLOR_FONDO,
            'COLOR_CARD': COLOR_CARD,
            'COLOR_TEXTO': COLOR_TEXTO
        })
        self.plates_view = PlatesView(self.tab_placas, self.root, self.logic, self.placas_manager, self.plates_ctrl, styles={
            'COLOR_FONDO': COLOR_FONDO,
            'COLOR_CARD': COLOR_CARD,
            'COLOR_TEXTO': COLOR_TEXTO
        })
        self.contacts_view = ContactsView(self.tab_contactos, self.root, self.logic, styles={
            'COLOR_FONDO': COLOR_FONDO,
            'COLOR_CARD': COLOR_CARD,
            'COLOR_TEXTO': COLOR_TEXTO
        })
        self.panic_view = PanicView(self.tab_panico, self.root, self.logic, self.camara_manager, styles={
            'COLOR_FONDO': COLOR_FONDO,
            'COLOR_CARD': COLOR_CARD,
            'COLOR_TEXTO': COLOR_TEXTO
        })

        self.device_view.mostrar_dispositivos()
        self.mostrar_eventos()
        try:
            self.camera_ctrl.load_cameras_from_db()
            def on_motion(s, r):
                self.logic.registrar_evento(s, f"Movimiento detectado - Imagen: {r}", "Detección Movimiento")
            self.camera_ctrl.sync_monitoring_modes(on_motion)
        except Exception:
            pass
        self.camera_view.mostrar_camaras()
        try:
            self.plates_ctrl.load_detectores_from_db()
            # No iniciar monitoreo automáticamente - solo cuando cambie a "Activo"
        except Exception:
            pass
        self.plates_view.mostrar_plaquetas()
        self.contacts_view.mostrar_contactos()
        self.panic_view.mostrar_panel_panico()


        self.camara_manager.set_schedule_checker(self.check_schedule)

        self.iniciar_actualizacion_automatica()

    def check_schedule(self, serie):
        inicio, fin = self.logic.obtener_horario_dispositivo(serie)
        if not inicio or not fin:
            return True 
        
        try:
            now = datetime.now().time()
            start = datetime.strptime(inicio, "%H:%M").time()
            end = datetime.strptime(fin, "%H:%M").time()
            
            if start <= end:
                return start <= now <= end
            else: 
                return start <= now or now <= end
        except Exception:
            return True

    def mostrar_estado(self):
        for w in self.tab_estado.winfo_children():
            w.destroy()

        tk.Label(self.tab_estado, text="Estado General", font=("Segoe UI", 20, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=15)

        card = tk.Frame(self.tab_estado, bg=COLOR_CARD, padx=20, pady=20)
        card.pack(padx=20, pady=10, fill="x")

        total, activos, hoy = self.logic.obtener_resumen()
        txt = f"Dispositivos Totales: {total}\nDispositivos Activos: {activos}\nEventos Hoy: {hoy}"

        tk.Label(card, text=txt, bg=COLOR_CARD, fg=COLOR_TEXTO, font=("Segoe UI", 14), justify="left").pack()

        actions_frame = tk.Frame(self.tab_estado, bg=COLOR_FONDO)
        actions_frame.pack(pady=20)

        ttk.Button(actions_frame, text="Desactivar Alarma", style="Dark.TButton", width=BTN_WIDTH, command=self.desactivar_alarma_accion).pack(pady=5)
        
        self.btn_cerradura = ttk.Button(actions_frame, text="Abrir Cerradura", style="Dark.TButton", width=BTN_WIDTH, command=self.toggle_cerradura)
        self.btn_cerradura.pack(pady=5)
        
        ttk.Button(actions_frame, text="Cerrar Sesión", style="Dark.TButton", width=BTN_WIDTH, command=self.mostrar_login).pack(pady=5)

    def desactivar_alarma_accion(self):
        try:
            self.camara_manager.desactivar_alarma()
            messagebox.showinfo("Éxito", "Se ha enviado la orden de desactivar la alarma.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo desactivar la alarma: {e}")

    def toggle_cerradura(self):
        """Alterna el estado de la cerradura inteligente"""
        try:
            # Buscar dispositivo de tipo Cerradura Inteligente
            cerradura = None
            dispositivos = self.logic.obtener_dispositivos()
            for d in dispositivos:
                if d.get("tipo") == "Cerradura Inteligente":
                    cerradura = d
                    break
            
            if not cerradura:
                messagebox.showwarning("Atención", "No se encontró ninguna 'Cerradura Inteligente' registrada.")
                return

            if cerradura.get("estado") != "activo" or cerradura.get("modo") == "Inactivo":
                messagebox.showwarning("Atención", "La cerradura está inactiva en el sistema.")
                return

            # Determinar acción basada en texto del botón
            texto_actual = self.btn_cerradura.cget("text")
            abrir = "Abrir" in texto_actual
            
            if abrir:
                self.monitor_boton.controlar_cerradura(abrir=True)
                self.btn_cerradura.config(text="Cerrar Cerradura")
                self.logic.registrar_evento(cerradura.get("nombre"), "Cerradura ABIERTA remotamente", "Acceso")
            else:
                self.monitor_boton.controlar_cerradura(abrir=False)
                self.btn_cerradura.config(text="Abrir Cerradura")
                self.logic.registrar_evento(cerradura.get("nombre"), "Cerradura CERRADA remotamente", "Acceso")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al controlar cerradura: {e}")

    def refrescar_dispositivos(self):
        if self.device_view:
            self.device_view.refrescar_dispositivos()

    def cambiar_modo_seleccionado(self):
        if self.device_view:
            self.device_view.cambiar_modo_seleccionado()

    def eliminar_dispositivo_seleccionado(self):
        if self.device_view:
            self.device_view.eliminar_dispositivo_seleccionado()
            if self.camera_view:
                self.camera_view.actualizar_estado_camaras()

    def registrar_dispositivo(self):
        if self.device_view:
            self.device_view.registrar_dispositivo()

    def mostrar_eventos(self):
        self.filtros_activos = False
        for w in self.tab_event.winfo_children():
            w.destroy()

        tk.Label(self.tab_event, text="Registro de Eventos", font=("Segoe UI", 20, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=10)

        btn_frame = tk.Frame(self.tab_event, bg=COLOR_FONDO)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Filtrar Eventos", style="Dark.TButton", width=BTN_WIDTH, command=self.abrir_ventana_filtros).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Mostrar Todo", style="Dark.TButton", width=BTN_WIDTH, command=self.mostrar_todo_eventos).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Borrar Todos los Eventos", style="Dark.TButton", width=BTN_WIDTH, command=self.borrar_eventos).pack(side="left", padx=5)

        self.btn_auto_update = ttk.Button(btn_frame, text="⏸Pausar Auto-Actualización", style="Dark.TButton", width=BTN_WIDTH, command=self.toggle_actualizacion_automatica)
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

    def iniciar_actualizacion_automatica(self):
        self.actualizacion_automatica_activa = True
        self.programar_proxima_actualizacion()

    def detener_actualizacion_automatica(self):
        self.actualizacion_automatica_activa = False
        if self.job_actualizacion:
            self.root.after_cancel(self.job_actualizacion)
            self.job_actualizacion = None

    def programar_proxima_actualizacion(self):
        if self.actualizacion_automatica_activa:
            self.job_actualizacion = self.root.after(2000, self.actualizar_eventos_automatico)

    def actualizar_eventos_automatico(self):
        if self.actualizacion_automatica_activa:
            try:
                self.verificar_simulador_presencia()
            except Exception:
                pass
            self.programar_proxima_actualizacion()

    def verificar_simulador_presencia(self):
        """Verifica si el simulador debe estar encendido o apagado según horario"""
        try:
            simulador = self.logic.obtener_dispositivo_por_serie("PICO-SIMULADOR-001")
            if not simulador:
                # Intentar buscar cualquier dispositivo de tipo "Simulador Presencia"
                dispositivos = self.logic.obtener_dispositivos()
                for d in dispositivos:
                    if d.get("tipo") == "Simulador Presencia":
                        simulador = d
                        break
                
                if not simulador:
                    return

            serie = simulador.get("serie")
            nombre = simulador.get("nombre")

            # Si el dispositivo está inactivo o su modo es Inactivo, apagar
            if simulador.get("estado") != "activo" or simulador.get("modo") == "Inactivo":
                nuevo_estado = False
                motivo = "Dispositivo Inactivo/Modo Inactivo"
            else:
                # Verificar horario
                nuevo_estado = self.check_schedule(serie)
                motivo = "Horario Activo" if nuevo_estado else "Fuera de Horario"

            # Enviar comando solo si el estado cambió
            if nuevo_estado != self.estado_simulador_enviado:
                if nuevo_estado:
                    if self.monitor_boton.activar_simulador():
                        self.logic.registrar_evento(
                            dispositivo=nombre,
                            descripcion=f"Simulador de presencia ACTIVADO ({motivo})",
                            tipo="Simulación"
                        )
                        self.estado_simulador_enviado = True
                else:
                    if self.monitor_boton.desactivar_simulador():
                        # Solo registrar si estaba encendido previamente (evitar log al inicio)
                        if self.estado_simulador_enviado is True:
                            self.logic.registrar_evento(
                                dispositivo=nombre,
                                descripcion=f"Simulador de presencia DESACTIVADO ({motivo})",
                                tipo="Simulación"
                            )
                        self.estado_simulador_enviado = False
                        
        except Exception as e:
            print(f"Error verificando simulador: {e}")

    def toggle_actualizacion_automatica(self):
        if self.actualizacion_automatica_activa:
            self.detener_actualizacion_automatica()
            self.btn_auto_update.config(text="Reanudar Auto-Actualización")
        else:
            self.iniciar_actualizacion_automatica()
            self.btn_auto_update.config(text="⏸Pausar Auto-Actualización")

    def refrescar_eventos(self, eventos):
        for r in self.tree_event.get_children():
            self.tree_event.delete(r)
        eventos_ordenados = sorted(eventos, key=lambda x: datetime.strptime(x.get("fecha", "2000-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S"), reverse=True)
        for i, ev in enumerate(eventos_ordenados, start=1):
            self.tree_event.insert("", "end", values=(
                i,
                ev.get("fecha"),
                ev.get("tipo"),
                ev.get("dispositivo"),
                ev.get("descripcion")
            ))

    def borrar_eventos(self):
        if messagebox.askyesno("Confirmar", "¿Está seguro de borrar todos los eventos?"):
            self.logic.eliminar_eventos()
            self.mostrar_eventos()
            messagebox.showinfo("Éxito", "Eventos borrados correctamente")

    def abrir_ventana_filtros(self):
        vent = tk.Toplevel(self.root)
        vent.title("Filtrar Eventos")
        vent.geometry("500x520")
        vent.configure(bg=COLOR_CARD)
        tk.Label(vent, text="Filtros de Eventos", font=("Segoe UI", 16, "bold"), bg=COLOR_CARD, fg=COLOR_TEXTO).pack(pady=10)
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
        ttk.Button(vent, text="Aplicar Filtro", style="Dark.TButton", width=20, command=lambda: self.aplicar_filtros_desde_ventana(vent)).pack(pady=15)
        ttk.Button(vent, text="Cerrar", style="Dark.TButton", width=20, command=vent.destroy).pack(pady=5)

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
        self.filtros_activos = True
        self.refrescar_eventos(eventos)
        vent.destroy()

    def mostrar_todo_eventos(self):
        self.filtros_activos = False
        self.refrescar_eventos(self.logic.obtener_eventos())

    def mostrar_camaras(self):
        if self.camera_view:
            self.camera_view.mostrar_camaras()

    def actualizar_estado_camaras(self):
        if self.camera_view:
            self.camera_view.actualizar_estado_camaras()

    def capturar_foto_manual(self):
        if self.camera_view:
            self.camera_view.capturar_foto_manual()

    def iniciar_monitoreo_movimiento(self):
        if self.camera_view:
            self.camera_view.iniciar_monitoreo_movimiento()

    def registrar_evento_movimiento(self, serie, ruta_imagen):
        if self.camera_view:
            self.camera_view.registrar_evento_movimiento(serie, ruta_imagen)

    def detener_monitoreo_movimiento(self):
        if self.camera_view:
            self.camera_view.detener_monitoreo_movimiento()

    def probar_deteccion_movimiento(self):
        if self.camera_view:
            self.camera_view.probar_deteccion_movimiento()

    def on_tab_change(self, event):
        tab_seleccionada = event.widget.tab(event.widget.select(), "text")
        if tab_seleccionada == "Dispositivos":
            self.device_view.mostrar_dispositivos()
        elif tab_seleccionada == "Eventos":
            if not getattr(self, 'filtros_activos', False):
                self.refrescar_eventos(self.logic.obtener_eventos())
        elif tab_seleccionada == "Cámaras":
            self.camera_view.mostrar_camaras()
        elif tab_seleccionada == "Detector Placas":
            self.plates_view.mostrar_plaquetas()
        elif tab_seleccionada == "Contactos":
            self.contacts_view.mostrar_contactos()
        elif tab_seleccionada == "🚨 Emergencia":
            self.panic_view.mostrar_panel_panico()
    
    def iniciar_monitor_boton(self):
        """Inicia el monitor del botón físico en segundo plano"""
        def _start():
            try:
                print("Iniciando servicio de monitoreo Pico...")
                if self.monitor_boton.iniciar_monitoreo():
                    print("Servicio de monitoreo iniciado correctamente.")
                else:
                    print("FALLO al iniciar servicio de monitoreo.")
            except Exception as e:
                print(f"Excepción al iniciar monitor: {e}")
        
        threading.Thread(target=_start, daemon=True).start()
    
    def on_boton_fisico_presionado(self):
        """Callback cuando se presiona el botón físico de pánico"""
        self.root.after(0, self._procesar_panico_fisico)
    
    def _buscar_dispositivo_fisico(self, tipo_objetivo, serie_default):
        """
        Busca un dispositivo válido para procesar el evento físico.
        Prioridad:
        1. Serie específica (PICO-BOTON-001)
        2. Cualquier dispositivo del tipo correcto
        """
        boton = self.logic.obtener_dispositivo_por_serie(serie_default)
        if boton:
            return boton

        dispositivos = self.logic.obtener_dispositivos()
        
        # Lista de tipos equivalentes para sensores de puerta
        tipos_puerta = ["Sensor Puertas y Ventanas", "Sensor Puerta", "Sensor Puerta/Ventana"]
        
        for d in dispositivos:
            # Si buscamos sensor de puerta, aceptar cualquiera de los tipos válidos
            if tipo_objetivo in tipos_puerta:
                if d.get("tipo") in tipos_puerta:
                    return d
            # Para otros dispositivos, búsqueda exacta
            elif d.get("tipo") == tipo_objetivo:
                return d
        
        return None

    def _procesar_panico_fisico(self):
        """Procesa el evento de pánico del botón físico"""
        try:
            boton = self._buscar_dispositivo_fisico("Botón de Pánico", "PICO-BOTON-001")
        
            if not boton:
                return
        
            if boton.get("estado") != "activo" or boton.get("modo") == "Inactivo":
                self.logic.registrar_evento(
                    dispositivo=boton.get("nombre", "Botón Físico"),
                    descripcion="Botón presionado (Ignorado - Dispositivo Inactivo)",
                    tipo="Intento Pánico"
                )
                return
            
            self.logic.registrar_evento(
                dispositivo=boton.get("nombre", "Botón Físico"),
                descripcion="Alarma de pánico activada mediante botón físico",
                tipo="Pánico Físico"
            )

            if self.camara_manager:
                self.camara_manager.activar_alarma(serie="Botón Físico")

            contactos = self.logic.obtener_contactos()
            if contactos and hasattr(self, 'panic_view') and self.panic_view:
                self.panic_view.notifier.notificar_contactos(contactos, tipo_alerta="PÁNICO FÍSICO")

            messagebox.showwarning(
                " Botón de Pánico Físico",
                "¡ALARMA DE PÁNICO ACTIVADA!\n\n"
                f"Dispositivo: {boton.get('nombre')}\n\n"
                "✓ Evento registrado\n"
                "✓ Alarma activada\n"
                "✓ Contactos notificados"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar alarma física: {e}")

    def on_boton_silencioso_presionado(self):
        """Callback cuando se presiona el botón silencioso"""
        self.root.after(0, self._procesar_panico_silencioso)

    def _procesar_panico_silencioso(self):
        """Procesa el evento de pánico silencioso"""
        try:
            boton = self._buscar_dispositivo_fisico("Botón Silencioso", "PICO-SILENT-001")
        
            if not boton:
                return
        
            if boton.get("estado") != "activo" or boton.get("modo") == "Inactivo":
                return

            self.logic.registrar_evento(
                dispositivo=boton.get("nombre", "Botón Silencioso"),
                descripcion="Alarma silenciosa activada mediante botón físico",
                tipo="Alarma Silenciosa"
            )
            
            contactos = self.logic.obtener_contactos()
            if contactos and hasattr(self, 'panic_view') and self.panic_view:
                self.panic_view.notifier.notificar_contactos(contactos, tipo_alerta="SILENCIOSA")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar alarma silenciosa: {e}")

    def on_closing(self):
        """Se ejecuta al intentar cerrar la ventana"""
        try:
            if self.monitor_boton:
                self.monitor_boton.detener_monitoreo()
            
            self.detener_actualizacion_automatica()
        except Exception:
            pass
        finally:
            self.root.destroy()

    def on_movimiento_pico(self):
        """Callback cuando se detecta movimiento en el sensor HC-SR04"""
        self.root.after(0, self._procesar_movimiento_pico)

    def _procesar_movimiento_pico(self):
        """Procesa el evento de movimiento del sensor físico"""
        try:
            sensor = self._buscar_dispositivo_fisico("Sensor de Movimiento", "PICO-SENSOR-001")
        
            if not sensor:
                return
        
            if sensor.get("estado") != "activo" or sensor.get("modo") == "Inactivo":
                return
            
            if self.camara_manager.schedule_checker:
                if not self.camara_manager.schedule_checker(sensor.get("serie")):
                    return

            self.logic.registrar_evento(
                dispositivo=sensor.get("nombre", "Sensor Movimiento"),
                descripcion="Movimiento detectado por sensor HC-SR04",
                tipo="Detección Movimiento"
            )

            if self.camara_manager:
                self.camara_manager.activar_alarma(serie="Sensor Movimiento")
            
        except Exception as e:
            print(f"Error procesando movimiento pico: {e}")

    def on_evento_registrado(self):
        """Callback para actualizar la vista de eventos cuando ocurre uno nuevo"""
        try:
            if self.notebook.index(self.notebook.select()) == 2:
                if not getattr(self, 'filtros_activos', False):
                    eventos_actuales = self.logic.obtener_eventos()
                    self.refrescar_eventos(eventos_actuales)
        except Exception:
            pass

    def on_humo_detectado(self):
        """Callback cuando se detecta humo"""
        self.root.after(0, self._procesar_humo)

    def _procesar_humo(self):
        """Procesa el evento de detección de humo"""
        try:
            detector = self._buscar_dispositivo_fisico("Detector de Humo", "PICO-HUMO-001")
        
            if not detector:
                return
        
            if detector.get("estado") != "activo" or detector.get("modo") == "Inactivo":
                return
            
            # Sin horario, siempre activo si el dispositivo está activo

            self.logic.registrar_evento(
                dispositivo=detector.get("nombre", "Detector Humo"),
                descripcion="¡HUMO DETECTADO! Peligro de incendio",
                tipo="Alarma Incendio"
            )

            if self.camara_manager:
                self.camara_manager.activar_alarma(serie="Detector Humo")
            
            # Notificar contactos de emergencia
            contactos = self.logic.obtener_contactos()
            if contactos and hasattr(self, 'panic_view') and self.panic_view:
                self.panic_view.notifier.notificar_contactos(contactos, tipo_alerta="INCENDIO")

            messagebox.showwarning(
                " ALARMA DE INCENDIO",
                "¡HUMO DETECTADO!\n\n"
                f"Dispositivo: {detector.get('nombre')}\n\n"
                "✓ Evento registrado\n"
                "✓ Alarma activada\n"
                "✓ Contactos notificados"
            )
            
        except Exception as e:
            print(f"Error procesando humo: {e}")

    def on_magnet_on(self):
        """Callback cuando el imán se pega al sensor (Activar Alarma)"""
        self.root.after(0, lambda: self._procesar_magnet(True))

    def on_magnet_off(self):
        """Callback cuando el imán se separa del sensor (Desactivar Alarma)"""
        self.root.after(0, lambda: self._procesar_magnet(False))

    def _procesar_magnet(self, activo):
        """Procesa el evento del sensor magnético"""
        try:
            sensor = self._buscar_dispositivo_fisico("Sensor Puertas y Ventanas", "PICO-PUERTA-001")
        
            if not sensor:
                print(">>> NO SE ACTIVA ALARMA: No existe ningún 'Sensor Puerta' registrado en el sistema.")
                return
        
            if sensor.get("estado") != "activo" or sensor.get("modo") == "Inactivo":
                print(f">>> NO SE ACTIVA ALARMA: Sensor '{sensor.get('nombre')}' está INACTIVO (Estado: {sensor.get('estado')}, Modo: {sensor.get('modo')})")
                return

            if activo:
                print(f">>> ALARMA ACTIVADA: Sensor '{sensor.get('nombre')}' detectó contacto (Imán pegado)")
                # Imán pegado -> Activar Alarma
                self.logic.registrar_evento(
                    dispositivo=sensor.get("nombre", "Sensor Puerta"),
                    descripcion="Contacto Magnético Detectado (Puerta Cerrada/Imán Cerca)",
                    tipo="Alarma Activada"
                )
                if self.camara_manager:
                    self.camara_manager.activar_alarma(serie="Sensor Puerta")
                
                # Notificar contactos (Opcional, para no saturar si es frecuente)
                # contactos = self.logic.obtener_contactos()
                # if contactos and hasattr(self, 'panic_view') and self.panic_view:
                #    self.panic_view.notifier.notificar_contactos(contactos, tipo_alerta="PUERTA_CONTACTO")

            else:
                print(">>> Sensor de puerta perdió contacto (Imán separado) - ALARMA CONTINUA SONANDO")
                # Imán separado -> Solo registrar evento, NO desactivar alarma automáticamente
                self.logic.registrar_evento(
                    dispositivo=sensor.get("nombre", "Sensor Puerta"),
                    descripcion="Contacto Magnético Perdido (Puerta Abierta/Imán Lejos) - Alarma persiste hasta desactivación manual",
                    tipo="Estado Sensor"
                )
                # if self.camara_manager:
                #     self.camara_manager.desactivar_alarma()
            
        except Exception as e:
            print(f"Error procesando magnet: {e}")

    def on_laser_blocked(self):
        """Callback cuando el láser es interrumpido"""
        self.root.after(0, lambda: self._procesar_laser(True))

    def on_laser_ok(self):
        """Callback cuando el láser se restaura"""
        self.root.after(0, lambda: self._procesar_laser(False))

    def _procesar_laser(self, bloqueado):
        """Procesa el evento del sensor láser"""
        try:
            sensor = self._buscar_dispositivo_fisico("Detector Láser", "PICO-LASER-001")
        
            if not sensor:
                return
        
            if sensor.get("estado") != "activo" or sensor.get("modo") == "Inactivo":
                return

            if bloqueado:
                print(">>> ALARMA ACTIVADA: Barrera Láser interrumpida")
                self.logic.registrar_evento(
                    dispositivo=sensor.get("nombre", "Detector Láser"),
                    descripcion="¡INTRUSIÓN! Barrera láser interrumpida",
                    tipo="Alarma Intrusión"
                )
                if self.camara_manager:
                    self.camara_manager.activar_alarma(serie="Detector Láser")
                
                # Notificar contactos
                contactos = self.logic.obtener_contactos()
                if contactos and hasattr(self, 'panic_view') and self.panic_view:
                    self.panic_view.notifier.notificar_contactos(contactos, tipo_alerta="INTRUSION_LASER")

            else:
                print(">>> Barrera Láser restaurada")
                self.logic.registrar_evento(
                    dispositivo=sensor.get("nombre", "Detector Láser"),
                    descripcion="Barrera láser restaurada (Luz detectada nuevamente)",
                    tipo="Estado Sensor"
                )
            
        except Exception as e:
            print(f"Error procesando láser: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sistema de Seguridad")
    root.geometry("1000x700")
    root.configure(bg=COLOR_FONDO)
    app = SecurityUI(root)
    app.estilo()
    app.mostrar_login()
    root.mainloop()
