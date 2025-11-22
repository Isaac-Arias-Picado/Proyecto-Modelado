import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

class PanicView:
    """Vista para el botón de pánico y alarma silenciosa (RF12, RF24)."""
    
    def __init__(self, parent, root, logic, styles=None):
        self.parent = parent
        self.root = root
        self.logic = logic
        self.styles = styles or {}

    def mostrar_panel_panico(self):
        """Muestra el panel de emergencia con botones de pánico y alarma silenciosa."""
        for w in self.parent.winfo_children():
            w.destroy()

        tk.Label(
            self.parent, 
            text="Panel de Emergencia", 
            font=("Segoe UI", 24, "bold"), 
            bg=self.styles.get('COLOR_FONDO', '#1F2024'), 
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).pack(pady=20)

        # Advertencia
        warning_frame = tk.Frame(
            self.parent, 
            bg="#8B0000", 
            padx=20, 
            pady=15
        )
        warning_frame.pack(padx=40, pady=10, fill="x")
        
        tk.Label(
            warning_frame,
            text="⚠️ ATENCIÓN: Use estos botones solo en caso de emergencia real",
            font=("Segoe UI", 12, "bold"),
            bg="#8B0000",
            fg="#FFFFFF"
        ).pack()

        # Contenedor principal de botones
        main_container = tk.Frame(self.parent, bg=self.styles.get('COLOR_FONDO', '#1F2024'))
        main_container.pack(expand=True, fill="both", pady=20)

        # Botón de Pánico (rojo grande)
        panic_frame = tk.Frame(
            main_container, 
            bg=self.styles.get('COLOR_CARD', '#4B4952'), 
            padx=30, 
            pady=30
        )
        panic_frame.pack(side="left", expand=True, padx=20)

        tk.Label(
            panic_frame,
            text="BOTÓN DE PÁNICO",
            font=("Segoe UI", 16, "bold"),
            bg=self.styles.get('COLOR_CARD', '#4B4952'),
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).pack(pady=10)

        panic_btn = tk.Button(
            panic_frame,
            text="🚨\nACTIVAR\nPÁNICO",
            font=("Segoe UI", 20, "bold"),
            bg="#DC143C",
            fg="#FFFFFF",
            activebackground="#8B0000",
            activeforeground="#FFFFFF",
            width=15,
            height=8,
            relief="raised",
            borderwidth=5,
            command=self.activar_panico
        )
        panic_btn.pack(pady=10)

        tk.Label(
            panic_frame,
            text="Activa alarma audible y\nnotifica a todos los contactos",
            font=("Segoe UI", 10),
            bg=self.styles.get('COLOR_CARD', '#4B4952'),
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF'),
            justify="center"
        ).pack(pady=5)

        # Botón de Alarma Silenciosa (naranja)
        silent_frame = tk.Frame(
            main_container, 
            bg=self.styles.get('COLOR_CARD', '#4B4952'), 
            padx=30, 
            pady=30
        )
        silent_frame.pack(side="right", expand=True, padx=20)

        tk.Label(
            silent_frame,
            text="ALARMA SILENCIOSA",
            font=("Segoe UI", 16, "bold"),
            bg=self.styles.get('COLOR_CARD', '#4B4952'),
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).pack(pady=10)

        silent_btn = tk.Button(
            silent_frame,
            text="🔇\nACTIVAR\nALARMA\nSILENCIOSA",
            font=("Segoe UI", 18, "bold"),
            bg="#FF8C00",
            fg="#FFFFFF",
            activebackground="#FF6600",
            activeforeground="#FFFFFF",
            width=15,
            height=8,
            relief="raised",
            borderwidth=5,
            command=self.activar_alarma_silenciosa
        )
        silent_btn.pack(pady=10)

        tk.Label(
            silent_frame,
            text="Notifica discretamente sin\nalarma audible",
            font=("Segoe UI", 10),
            bg=self.styles.get('COLOR_CARD', '#4B4952'),
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF'),
            justify="center"
        ).pack(pady=5)

        # Instrucciones
        instructions = tk.Frame(
            self.parent, 
            bg=self.styles.get('COLOR_CARD', '#4B4952'), 
            padx=20, 
            pady=15
        )
        instructions.pack(fill="x", padx=40, pady=10)

        tk.Label(
            instructions,
            text="📱 Instrucciones:",
            font=("Segoe UI", 12, "bold"),
            bg=self.styles.get('COLOR_CARD', '#4B4952'),
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF')
        ).pack(anchor="w")

        instructions_text = """
• PÁNICO: Envía alertas inmediatas con alarma sonora a todos los contactos de emergencia
• ALARMA SILENCIOSA: Envía alertas discretas sin sonido audible
• Ambas opciones registran el evento en el sistema con alta prioridad
• Asegúrese de tener contactos de emergencia configurados en la pestaña "Contactos"
        """

        tk.Label(
            instructions,
            text=instructions_text,
            font=("Segoe UI", 10),
            bg=self.styles.get('COLOR_CARD', '#4B4952'),
            fg=self.styles.get('COLOR_TEXTO', '#FFFFFF'),
            justify="left"
        ).pack(anchor="w", padx=10)

    def activar_panico(self):
        """Activa el botón de pánico (RF12)."""
        # Confirmar la acción
        if not messagebox.askyesno(
            "Confirmar Pánico",
            "¿Está seguro de activar el BOTÓN DE PÁNICO?\n\n"
            "Esto enviará alertas a todos sus contactos de emergencia."
        ):
            return

        try:
            # Activar alarma de pánico en el sistema
            contactos = self.logic.activar_alarma_panico(tipo="manual")

            # Mostrar resultado
            if contactos:
                contactos_str = "\n".join([
                    f"• {c.get('nombre')} - {c.get('telefono')}" 
                    for c in contactos
                ])
                mensaje = (
                    "🚨 ALARMA DE PÁNICO ACTIVADA\n\n"
                    f"Se ha registrado el evento y se notificará a:\n\n{contactos_str}\n\n"
                    "El evento ha sido registrado en el sistema."
                )
            else:
                mensaje = (
                    "🚨 ALARMA DE PÁNICO ACTIVADA\n\n"
                    "⚠️ No hay contactos de emergencia configurados.\n"
                    "Por favor, agregue contactos en la pestaña 'Contactos'.\n\n"
                    "El evento ha sido registrado en el sistema."
                )

            # Simular envío de notificaciones en segundo plano
            self._simular_envio_notificaciones(contactos, tipo="pánico")

            messagebox.showwarning("Pánico Activado", mensaje)

        except Exception as e:
            messagebox.showerror("Error", f"Error al activar pánico: {e}")

    def activar_alarma_silenciosa(self):
        """Activa la alarma silenciosa (RF24)."""
        # Confirmar la acción
        if not messagebox.askyesno(
            "Confirmar Alarma Silenciosa",
            "¿Está seguro de activar la ALARMA SILENCIOSA?\n\n"
            "Esto enviará notificaciones discretas a sus contactos."
        ):
            return

        try:
            # Activar alarma silenciosa en el sistema
            contactos = self.logic.activar_alarma_silenciosa()

            # Mostrar resultado
            if contactos:
                contactos_str = "\n".join([
                    f"• {c.get('nombre')} - {c.get('telefono')}" 
                    for c in contactos
                ])
                mensaje = (
                    "🔇 ALARMA SILENCIOSA ACTIVADA\n\n"
                    f"Se notificará discretamente a:\n\n{contactos_str}\n\n"
                    "El evento ha sido registrado en el sistema."
                )
            else:
                mensaje = (
                    "🔇 ALARMA SILENCIOSA ACTIVADA\n\n"
                    "⚠️ No hay contactos de emergencia configurados.\n"
                    "Por favor, agregue contactos en la pestaña 'Contactos'.\n\n"
                    "El evento ha sido registrado en el sistema."
                )

            # Simular envío de notificaciones en segundo plano
            self._simular_envio_notificaciones(contactos, tipo="silenciosa")

            messagebox.showinfo("Alarma Silenciosa", mensaje)

        except Exception as e:
            messagebox.showerror("Error", f"Error al activar alarma silenciosa: {e}")

    def _simular_envio_notificaciones(self, contactos, tipo="pánico"):
        """Simula el envío de notificaciones en segundo plano.
        
        TODO: Para producción, integrar con servicios reales de notificaciones:
        - SMS: Usar API como Twilio, Nexmo, o servicio local de SMS
        - Push Notifications: Integrar con Firebase Cloud Messaging (FCM) o Apple Push Notification Service (APNs)
        - Email: Usar SMTP o servicios como SendGrid
        - Llamadas de voz: Usar Twilio Voice API para emergencias críticas
        
        La implementación actual solo registra en consola para propósitos de desarrollo.
        """
        def enviar():
            # NOTA: Esta es una simulación para desarrollo
            # En producción, reemplazar con llamadas a APIs de notificación reales
            time.sleep(1)
            print(f"[SIMULACIÓN] Notificaciones de {tipo} enviadas a {len(contactos)} contactos")
            for contacto in contactos:
                print(f"  → {contacto.get('nombre')}: {contacto.get('telefono')}")
                # TODO: Aquí se debe llamar a la API real de notificaciones
                # Ejemplo: send_sms(contacto.get('telefono'), mensaje)
                # Ejemplo: send_push_notification(contacto.get('telefono'), mensaje)

        thread = threading.Thread(target=enviar, daemon=True)
        thread.start()
