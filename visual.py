import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from data_logic import SecurityLogic
from datetime import datetime

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

        self.notebook.add(self.tab_estado, text="Estado General")
        self.notebook.add(self.tab_disp, text="Dispositivos")
        self.notebook.add(self.tab_event, text="Eventos")

        self.mostrar_estado()
        self.mostrar_dispositivos()
        self.mostrar_eventos()

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
        ttk.Button(self.tab_estado, text="Borrar Todos los Eventos", style="Dark.TButton", width=BTN_WIDTH, command=self.borrar_eventos).pack(pady=5)

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

    def registrar_dispositivo(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Registrar Dispositivo")
        dialog.configure(bg=COLOR_CARD)
        dialog.geometry("420x360")

        tipos = [
            "Sensor de Movimiento", "Cerradura Inteligente", "Detector de Humo",
            "Cámara de Seguridad", "Simulador Presencia", "Sensor Puerta",
            "Detector Placas", "Detector Láser"
        ]

        form = tk.Frame(dialog, bg=COLOR_CARD)
        form.pack(pady=20)

        tk.Label(form, text="Serie:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=0, column=0, pady=10, sticky="e")
        e1 = ttk.Entry(form, width=30, style="Dark.TEntry")
        e1.grid(row=0, column=1, padx=10)

        tk.Label(form, text="Tipo:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=1, column=0, pady=10, sticky="e")
        cb = ttk.Combobox(form, values=tipos, width=28, state="readonly")
        cb.grid(row=1, column=1, padx=10)

        tk.Label(form, text="Nombre:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=2, column=0, pady=10, sticky="e")
        e2 = ttk.Entry(form, width=30, style="Dark.TEntry")
        e2.grid(row=2, column=1, padx=10)

        tk.Label(form, text="Ubicación:", bg=COLOR_CARD, fg=COLOR_TEXTO).grid(row=3, column=0, pady=10, sticky="e")
        e3 = ttk.Entry(form, width=30, style="Dark.TEntry")
        e3.grid(row=3, column=1, padx=10)

        def guardar():
            try:
                self.logic.registrar_dispositivo(e1.get().strip(), cb.get().strip(), e2.get().strip(), e3.get().strip())
                dialog.destroy()
                self.refrescar_dispositivos()
                messagebox.showinfo("Éxito", "Dispositivo registrado correctamente")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(dialog, text="Registrar", style="Dark.TButton", width=BTN_WIDTH, command=guardar).pack(pady=10)

    def _get_selected_device_serie(self):
        sel = self.tree_disp.selection()
        if not sel:
            return None
        vals = self.tree_disp.item(sel[0], "values")
        return vals[1] if vals else None

    def cambiar_modo_seleccionado(self):
        serie = self._get_selected_device_serie()
        if not serie:
            messagebox.showerror("Error", "Seleccione un dispositivo")
            return
        modo = simpledialog.askstring("Cambiar Modo", "Ingrese modo (manual / automatico / inactivo):")
        if not modo:
            return
        modo = modo.strip().lower()
        try:
            self.logic.cambiar_modo_dispositivo(serie, modo)
            self.refrescar_dispositivos()
            messagebox.showinfo("Éxito", f"Modo cambiado a {modo}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def cambiar_estado_seleccionado(self):
        serie = self._get_selected_device_serie()
        if not serie:
            messagebox.showerror("Error", "Seleccione un dispositivo")
            return
        estado = simpledialog.askstring("Cambiar Estado", "Ingrese estado (activo / inactivo):")
        if not estado:
            return
        estado = estado.strip().lower()
        try:
            self.logic.cambiar_estado_dispositivo(serie, estado)
            self.refrescar_dispositivos()
            messagebox.showinfo("Éxito", f"Estado cambiado a {estado}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def eliminar_dispositivo_seleccionado(self):
        serie = self._get_selected_device_serie()
        if not serie:
            messagebox.showerror("Error", "Seleccione un dispositivo")
            return
        if not messagebox.askyesno("Confirmar", f"Eliminar dispositivo {serie}? Esta acción es irreversible."):
            return
        try:
            self.logic.eliminar_dispositivo(serie)
            self.refrescar_dispositivos()
            messagebox.showinfo("Éxito", "Dispositivo eliminado")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def mostrar_eventos(self):
        for w in self.tab_event.winfo_children():
            w.destroy()

        tk.Label(self.tab_event, text="Registro de Eventos", font=("Segoe UI", 20, "bold"), bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(pady=10)

        filtro_frame = tk.Frame(self.tab_event, bg=COLOR_FONDO)
        filtro_frame.pack(pady=5, fill="x")

        tk.Label(filtro_frame, text="Dispositivo:", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side="left", padx=5)
        dispositivos = [d.get("serie") for d in self.logic.obtener_dispositivos()]
        self.cb_filtro_disp = ttk.Combobox(filtro_frame, values=[""] + dispositivos, width=20, state="readonly")
        self.cb_filtro_disp.pack(side="left", padx=5)

        tk.Label(filtro_frame, text="Fecha inicio (YYYY-MM-DD):", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side="left", padx=5)
        self.e_fecha_ini = ttk.Entry(filtro_frame, width=12)
        self.e_fecha_ini.pack(side="left", padx=5)

        tk.Label(filtro_frame, text="Fecha fin (YYYY-MM-DD):", bg=COLOR_FONDO, fg=COLOR_TEXTO).pack(side="left", padx=5)
        self.e_fecha_fin = ttk.Entry(filtro_frame, width=12)
        self.e_fecha_fin.pack(side="left", padx=5)

        ttk.Button(filtro_frame, text="Aplicar Filtro", style="Dark.TButton", width=BTN_WIDTH, command=self.aplicar_filtro_eventos).pack(side="left", padx=5)
        ttk.Button(filtro_frame, text="Limpiar Filtro", style="Dark.TButton", width=BTN_WIDTH, command=self.mostrar_eventos).pack(side="left", padx=5)

        cols = ("ID", "Fecha", "Tipo", "Dispositivo", "Descripción")
        self.tree_event = ttk.Treeview(self.tab_event, columns=cols, show="headings")
        for c in cols:
            self.tree_event.heading(c, text=c)
        self.tree_event.column("ID", width=40)
        self.tree_event.column("Fecha", width=160)
        self.tree_event.column("Descripción", width=400)
        self.tree_event.pack(expand=True, fill="both", padx=10, pady=10)

        self.refrescar_eventos(self.logic.obtener_eventos())

    def aplicar_filtro_eventos(self):
        disp = self.cb_filtro_disp.get().strip() or None
        fi = self.e_fecha_ini.get().strip() or None
        ff = self.e_fecha_fin.get().strip() or None
        for d in (fi, ff):
            if d:
                try:
                    datetime.strptime(d, "%Y-%m-%d")
                except Exception:
                    messagebox.showerror("Error", f"Fecha inválida: {d}. Formato YYYY-MM-DD")
                    return
        eventos = self.logic.filtrar_eventos(dispositivo=disp, fecha_inicio=fi, fecha_fin=ff)
        self.refrescar_eventos(eventos)

    def refrescar_eventos(self, eventos):
        for r in self.tree_event.get_children():
            self.tree_event.delete(r)
        for i, ev in enumerate(eventos, start=1):
            self.tree_event.insert("", "end", values=(i, ev.get("fecha"), ev.get("tipo"), ev.get("dispositivo"), ev.get("descripcion")))

if __name__ == "__main__":
    root = tk.Tk()
    app = SecurityUI(root)
    root.mainloop()
