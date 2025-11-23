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


COLOR_FONDO = "#1F2024"

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

        self.logic.agregar_observador_eventos(self.actualizar_eventos_automatico)
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
        self.panic_view = PanicView(self.tab_panico, self.root, self.logic, styles={
            'COLOR_FONDO': COLOR_FONDO,
            'COLOR_CARD': COLOR_CARD,
            'COLOR_TEXTO': COLOR_TEXTO
        })

        self.device_view.mostrar_dispositivos()
        self.mostrar_eventos()
        try:
            self.camera_ctrl.load_cameras_from_db()
        except Exception:
            pass
        self.camera_view.mostrar_camaras()
        try:
            self.plates_ctrl.load_detectores_from_db()
        except Exception:
            pass
        self.plates_view.mostrar_plaquetas()
        self.contacts_view.mostrar_contactos()
        self.panic_view.mostrar_panel_panico()

        self.iniciar_actualizacion_automatica()

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

    def refrescar_dispositivos(self):
        if self.device_view:
            self.device_view.refrescar_dispositivos()

    def cambiar_modo_seleccionado(self):
        if self.device_view:
            self.device_view.cambiar_modo_seleccionado()

    def cambiar_estado_seleccionado(self):
        if self.device_view:
            self.device_view.cambiar_estado_seleccionado()

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
                if self.notebook.index(self.notebook.select()) == 2:
                    if not getattr(self, 'filtros_activos', False):
                        eventos_actuales = self.logic.obtener_eventos()
                        self.refrescar_eventos(eventos_actuales)
            except Exception as e:
                print(f"Error en actualización automática: {e}")
            self.programar_proxima_actualizacion()

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


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Sistema de Seguridad")
    root.geometry("1000x700")
    root.configure(bg=COLOR_FONDO)
    app = SecurityUI(root)
    app.estilo()
    app.mostrar_login()
    root.mainloop()

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



        self.logic.agregar_observador_eventos(self.actualizar_eventos_automatico)



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

        self.panic_view = PanicView(self.tab_panico, self.root, self.logic, styles={

            'COLOR_FONDO': COLOR_FONDO,

            'COLOR_CARD': COLOR_CARD,

            'COLOR_TEXTO': COLOR_TEXTO

        })



        self.device_view.mostrar_dispositivos()

        self.mostrar_eventos()

        try:

            self.camera_ctrl.load_cameras_from_db()

        except Exception:

            pass

        self.camera_view.mostrar_camaras()

        try:

            self.plates_ctrl.load_detectores_from_db()

        except Exception:

            pass

        self.plates_view.mostrar_plaquetas()

        self.contacts_view.mostrar_contactos()

        self.panic_view.mostrar_panel_panico()



        self.iniciar_actualizacion_automatica()



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



                                                 

    def refrescar_dispositivos(self):

        if self.device_view:

            self.device_view.refrescar_dispositivos()



    def cambiar_modo_seleccionado(self):

        if self.device_view:

            self.device_view.cambiar_modo_seleccionado()



    def cambiar_estado_seleccionado(self):

        if self.device_view:

            self.device_view.cambiar_estado_seleccionado()



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



        tk.Label(self.tab_event, text="Registro de Eventos", font=("Segoe UI", 20, "bold"),

                 bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=10)



        btn_frame = tk.Frame(self.tab_event, bg=COLOR_FONDO)

        btn_frame.pack(pady=10)



        ttk.Button(btn_frame, text="Filtrar Eventos", style="Dark.TButton",

               width=BTN_WIDTH, command=self.abrir_ventana_filtros).pack(side="left", padx=5)

        ttk.Button(btn_frame, text="Mostrar Todo", style="Dark.TButton",

               width=BTN_WIDTH, command=self.mostrar_todo_eventos).pack(side="left", padx=5)

        ttk.Button(btn_frame, text="Borrar Todos los Eventos", style="Dark.TButton",

                   width=BTN_WIDTH, command=self.borrar_eventos).pack(side="left", padx=5)



        self.btn_auto_update = ttk.Button(btn_frame, text="⏸Pausar Auto-Actualización", style="Dark.TButton",

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

                if self.notebook.index(self.notebook.select()) == 2:

                    if not getattr(self, 'filtros_activos', False):

                        eventos_actuales = self.logic.obtener_eventos()

                        self.refrescar_eventos(eventos_actuales)

            except Exception as e:

                print(f"Error en actualización automática: {e}")

            self.programar_proxima_actualizacion()



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





if __name__ == "__main__":

    root = tk.Tk()

    root.title("Sistema de Seguridad")

    root.geometry("1000x700")

    root.configure(bg=COLOR_FONDO)

    app = SecurityUI(root)

    app.estilo()

    app.mostrar_login()

    root.mainloop()