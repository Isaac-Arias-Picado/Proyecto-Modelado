import tkinter as tk

from tkinter import ttk, messagebox


class ContactsView:

    """Vista para la gestión de contactos de emergencia (RF10)."""
    
    def __init__(self, parent, root, logic, styles=None):
        self.parent = parent
        self.root = root
        self.logic = logic
        self.styles = styles or {}
        self.tree = None

    def mostrar_contactos(self):
        for w in self.parent.winfo_children():
            w.destroy()

        tk.Label(
            self.parent, 
            text="Contactos de Emergencia", 
            font=("Segoe UI", 20, "bold"), 
            bg=self.styles.get('COLOR_FONDO', '#1F2024'), 
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).pack(pady=10)

        btn_frame = tk.Frame(self.parent, bg=self.styles.get('COLOR_FONDO', '#1F2024'))
        btn_frame.pack(pady=10)

        ttk.Button(
            btn_frame, 
            text="➕ Agregar Contacto", 
            style="Dark.TButton", 
            command=self.agregar_contacto_dialog
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame, 
            text="✏️ Editar Contacto", 
            style="Dark.TButton", 
            command=self.editar_contacto_dialog
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame, 
            text="🗑️ Eliminar Contacto", 
            style="Dark.TButton", 
            command=self.eliminar_contacto_seleccionado
        ).pack(side="left", padx=5)

        cols = ("Nombre", "Teléfono", "Relación", "Fecha Registro")
        self.tree = ttk.Treeview(self.parent, columns=cols, show="headings")
        
        for col in cols:
            self.tree.heading(col, text=col)
            width = 200 if col == "Nombre" else 150
            self.tree.column(col, width=width)
        
        self.tree.pack(expand=True, fill="both", padx=10, pady=10)

        self.actualizar_lista()

    def actualizar_lista(self):
        if self.tree is None:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            contactos = self.logic.obtener_contactos()
            for contacto in contactos:
                self.tree.insert("", "end", values=(
                    contacto.get("nombre", ""),
                    contacto.get("telefono", ""),
                    contacto.get("relacion", ""),
                    contacto.get("creado", "")
                ))
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar contactos: {e}")

    def agregar_contacto_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Agregar Contacto de Emergencia")
        dialog.configure(bg=self.styles.get('COLOR_CARD', '#4B4952'))
        dialog.geometry("400x300")

        form = tk.Frame(dialog, bg=self.styles.get('COLOR_CARD', '#4B4952'))
        form.pack(pady=20, padx=20)

        tk.Label(
            form, 
            text="Nombre:", 
            bg=self.styles.get('COLOR_CARD', '#4B4952'), 
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).grid(row=0, column=0, pady=10, sticky="e")
        
        e_nombre = ttk.Entry(form, width=25, style="Dark.TEntry")
        e_nombre.grid(row=0, column=1, padx=10)

        tk.Label(
            form, 
            text="Teléfono:", 
            bg=self.styles.get('COLOR_CARD', '#4B4952'), 
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).grid(row=1, column=0, pady=10, sticky="e")
        
        e_telefono = ttk.Entry(form, width=25, style="Dark.TEntry")
        e_telefono.grid(row=1, column=1, padx=10)

        tk.Label(
            form, 
            text="Relación:", 
            bg=self.styles.get('COLOR_CARD', '#4B4952'), 
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).grid(row=2, column=0, pady=10, sticky="e")
        
        e_relacion = ttk.Entry(form, width=25, style="Dark.TEntry")
        e_relacion.grid(row=2, column=1, padx=10)

        def guardar():
            nombre = e_nombre.get().strip()
            telefono = e_telefono.get().strip()
            relacion = e_relacion.get().strip()
            try:
                self.logic.agregar_contacto(nombre, telefono, relacion)
                self.actualizar_lista()
                messagebox.showinfo("Éxito", "Contacto agregado correctamente")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(
            dialog, 
            text="Guardar", 
            style="Dark.TButton", 
            width=20, 
            command=guardar
        ).pack(pady=15)

    def editar_contacto_dialog(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un contacto primero")
            return
        item = seleccion[0]
        valores = self.tree.item(item, 'values')
        nombre_actual = valores[0]
        telefono_actual = valores[1]
        relacion_actual = valores[2]

        dialog = tk.Toplevel(self.root)
        dialog.title("Editar Contacto de Emergencia")
        dialog.configure(bg=self.styles.get('COLOR_CARD', '#4B4952'))
        dialog.geometry("400x300")

        form = tk.Frame(dialog, bg=self.styles.get('COLOR_CARD', '#4B4952'))
        form.pack(pady=20, padx=20)

        tk.Label(
            form, 
            text="Nombre:", 
            bg=self.styles.get('COLOR_CARD', '#4B4952'), 
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).grid(row=0, column=0, pady=10, sticky="e")
        
        e_nombre = ttk.Entry(form, width=25, style="Dark.TEntry")
        e_nombre.insert(0, nombre_actual)
        e_nombre.grid(row=0, column=1, padx=10)

        tk.Label(
            form, 
            text="Teléfono:", 
            bg=self.styles.get('COLOR_CARD', '#4B4952'), 
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).grid(row=1, column=0, pady=10, sticky="e")
        
        e_telefono = ttk.Entry(form, width=25, style="Dark.TEntry")
        e_telefono.insert(0, telefono_actual)
        e_telefono.grid(row=1, column=1, padx=10)

        tk.Label(
            form, 
            text="Relación:", 
            bg=self.styles.get('COLOR_CARD', '#4B4952'), 
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).grid(row=2, column=0, pady=10, sticky="e")
        
        e_relacion = ttk.Entry(form, width=25, style="Dark.TEntry")
        e_relacion.insert(0, relacion_actual)
        e_relacion.grid(row=2, column=1, padx=10)

        def guardar():
            nuevo_nombre = e_nombre.get().strip()
            nuevo_telefono = e_telefono.get().strip()
            nueva_relacion = e_relacion.get().strip()
            try:
                self.logic.actualizar_contacto(
                    telefono_actual, 
                    nuevo_nombre, 
                    nuevo_telefono, 
                    nueva_relacion
                )
                self.actualizar_lista()
                messagebox.showinfo("Éxito", "Contacto actualizado correctamente")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        ttk.Button(
            dialog, 
            text="Guardar Cambios", 
            style="Dark.TButton", 
            width=20, 
            command=guardar
        ).pack(pady=15)

    def eliminar_contacto_seleccionado(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Selecciona un contacto primero")
            return
        item = seleccion[0]
        valores = self.tree.item(item, 'values')
        telefono = valores[1]
        nombre = valores[0]
        if messagebox.askyesno(
            "Confirmar", 
            f"¿Está seguro de eliminar el contacto '{nombre}'?"
        ):
            try:
                self.logic.eliminar_contacto(telefono)
                self.actualizar_lista()
                messagebox.showinfo("Éxito", "Contacto eliminado correctamente")
            except Exception as e:
                messagebox.showerror("Error", str(e))
import tkinter as tk

from tkinter import ttk, messagebox



class ContactsView:

    """Vista para la gestión de contactos de emergencia (RF10)."""

    

    def __init__(self, parent, root, logic, styles=None):

        self.parent = parent

        self.root = root

        self.logic = logic

        self.styles = styles or {}

        self.tree = None



    def mostrar_contactos(self):

        """Muestra la interfaz de gestión de contactos de emergencia."""

        for w in self.parent.winfo_children():

            w.destroy()



        tk.Label(

            self.parent, 

            text="Contactos de Emergencia", 

            font=("Segoe UI", 20, "bold"), 

            bg=self.styles.get('COLOR_FONDO', '#1F2024'), 

            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')

        ).pack(pady=10)



                           

        btn_frame = tk.Frame(self.parent, bg=self.styles.get('COLOR_FONDO', '#1F2024'))

        btn_frame.pack(pady=10)



        ttk.Button(

            btn_frame, 

            text="➕ Agregar Contacto", 

            style="Dark.TButton", 

            command=self.agregar_contacto_dialog

        ).pack(side="left", padx=5)

        

        ttk.Button(

            btn_frame, 

            text="✏️ Editar Contacto", 

            style="Dark.TButton", 

            command=self.editar_contacto_dialog

        ).pack(side="left", padx=5)

        

        ttk.Button(

            btn_frame, 

            text="🗑️ Eliminar Contacto", 

            style="Dark.TButton", 

            command=self.eliminar_contacto_seleccionado

        ).pack(side="left", padx=5)



                            

        cols = ("Nombre", "Teléfono", "Relación", "Fecha Registro")

        self.tree = ttk.Treeview(self.parent, columns=cols, show="headings")

        

        for col in cols:

            self.tree.heading(col, text=col)

            width = 200 if col == "Nombre" else 150

            self.tree.column(col, width=width)

        

        self.tree.pack(expand=True, fill="both", padx=10, pady=10)



                             

        self.actualizar_lista()



    def actualizar_lista(self):

        """Actualiza la lista de contactos en el TreeView."""

        if self.tree is None:

            return

        

                       

        for item in self.tree.get_children():

            self.tree.delete(item)

        

                          

        try:

            contactos = self.logic.obtener_contactos()

            for contacto in contactos:

                self.tree.insert("", "end", values=(

                    contacto.get("nombre", ""),

                    contacto.get("telefono", ""),

                    contacto.get("relacion", ""),

                    contacto.get("creado", "")

                ))

        except Exception as e:

            messagebox.showerror("Error", f"Error al cargar contactos: {e}")



    def agregar_contacto_dialog(self):

        """Abre un diálogo para agregar un nuevo contacto de emergencia."""

        dialog = tk.Toplevel(self.root)

        dialog.title("Agregar Contacto de Emergencia")

        dialog.configure(bg=self.styles.get('COLOR_CARD', '#4B4952'))

        dialog.geometry("400x300")



        form = tk.Frame(dialog, bg=self.styles.get('COLOR_CARD', '#4B4952'))

        form.pack(pady=20, padx=20)



                

        tk.Label(

            form, 

            text="Nombre:", 

            bg=self.styles.get('COLOR_CARD', '#4B4952'), 

            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')

        ).grid(row=0, column=0, pady=10, sticky="e")

        

        e_nombre = ttk.Entry(form, width=25, style="Dark.TEntry")

        e_nombre.grid(row=0, column=1, padx=10)



                  

        tk.Label(

            form, 

            text="Teléfono:", 

            bg=self.styles.get('COLOR_CARD', '#4B4952'), 

            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')

        ).grid(row=1, column=0, pady=10, sticky="e")

        

        e_telefono = ttk.Entry(form, width=25, style="Dark.TEntry")

        e_telefono.grid(row=1, column=1, padx=10)



                  

        tk.Label(

            form, 

            text="Relación:", 

            bg=self.styles.get('COLOR_CARD', '#4B4952'), 

            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')

        ).grid(row=2, column=0, pady=10, sticky="e")

        

        e_relacion = ttk.Entry(form, width=25, style="Dark.TEntry")

        e_relacion.grid(row=2, column=1, padx=10)



        def guardar():

            nombre = e_nombre.get().strip()

            telefono = e_telefono.get().strip()

            relacion = e_relacion.get().strip()

            

            try:

                self.logic.agregar_contacto(nombre, telefono, relacion)

                self.actualizar_lista()

                messagebox.showinfo("Éxito", "Contacto agregado correctamente")

                dialog.destroy()

            except Exception as e:

                messagebox.showerror("Error", str(e))



        ttk.Button(

            dialog, 

            text="Guardar", 

            style="Dark.TButton", 

            width=20, 

            command=guardar

        ).pack(pady=15)



    def editar_contacto_dialog(self):

        """Abre un diálogo para editar un contacto existente."""

        seleccion = self.tree.selection()

        if not seleccion:

            messagebox.showwarning("Advertencia", "Selecciona un contacto primero")

            return

        

        item = seleccion[0]

        valores = self.tree.item(item, 'values')

        nombre_actual = valores[0]

        telefono_actual = valores[1]

        relacion_actual = valores[2]



        dialog = tk.Toplevel(self.root)

        dialog.title("Editar Contacto de Emergencia")

        dialog.configure(bg=self.styles.get('COLOR_CARD', '#4B4952'))

        dialog.geometry("400x300")



        form = tk.Frame(dialog, bg=self.styles.get('COLOR_CARD', '#4B4952'))

        form.pack(pady=20, padx=20)



                

        tk.Label(

            form, 

            text="Nombre:", 

            bg=self.styles.get('COLOR_CARD', '#4B4952'), 

            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')

        ).grid(row=0, column=0, pady=10, sticky="e")

        

        e_nombre = ttk.Entry(form, width=25, style="Dark.TEntry")

        e_nombre.insert(0, nombre_actual)

        e_nombre.grid(row=0, column=1, padx=10)



                  

        tk.Label(

            form, 

            text="Teléfono:", 

            bg=self.styles.get('COLOR_CARD', '#4B4952'), 

            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')

        ).grid(row=1, column=0, pady=10, sticky="e")

        

        e_telefono = ttk.Entry(form, width=25, style="Dark.TEntry")

        e_telefono.insert(0, telefono_actual)

        e_telefono.grid(row=1, column=1, padx=10)



                  

        tk.Label(

            form, 

            text="Relación:", 

            bg=self.styles.get('COLOR_CARD', '#4B4952'), 

            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')

        ).grid(row=2, column=0, pady=10, sticky="e")

        

        e_relacion = ttk.Entry(form, width=25, style="Dark.TEntry")

        e_relacion.insert(0, relacion_actual)

        e_relacion.grid(row=2, column=1, padx=10)



        def guardar():

            nuevo_nombre = e_nombre.get().strip()

            nuevo_telefono = e_telefono.get().strip()

            nueva_relacion = e_relacion.get().strip()

            

            try:

                self.logic.actualizar_contacto(

                    telefono_actual, 

                    nuevo_nombre, 

                    nuevo_telefono, 

                    nueva_relacion

                )

                self.actualizar_lista()

                messagebox.showinfo("Éxito", "Contacto actualizado correctamente")

                dialog.destroy()

            except Exception as e:

                messagebox.showerror("Error", str(e))



        ttk.Button(

            dialog, 

            text="Guardar Cambios", 

            style="Dark.TButton", 

            width=20, 

            command=guardar

        ).pack(pady=15)



    def eliminar_contacto_seleccionado(self):

        """Elimina el contacto seleccionado de la lista."""

        seleccion = self.tree.selection()

        if not seleccion:

            messagebox.showwarning("Advertencia", "Selecciona un contacto primero")

            return

        

        item = seleccion[0]

        valores = self.tree.item(item, 'values')

        telefono = valores[1]

        nombre = valores[0]

        

        if messagebox.askyesno(

            "Confirmar", 

            f"¿Está seguro de eliminar el contacto '{nombre}'?"

        ):

            try:

                self.logic.eliminar_contacto(telefono)

                self.actualizar_lista()

                messagebox.showinfo("Éxito", "Contacto eliminado correctamente")

            except Exception as e:

                messagebox.showerror("Error", str(e))

