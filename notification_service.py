import webbrowser
import urllib.parse
import threading
import time

class NotificationService:
    def __init__(self):
        pass

    def notificar_contactos(self, contactos, tipo_alerta="PÁNICO"):
        if not contactos:
            return

        mensaje_base = ""
        if tipo_alerta == "PÁNICO":
            mensaje_base = "🚨 *ALERTA DE SEGURIDAD* 🚨\nSe ha activado el BOTÓN DE PÁNICO en mi ubicación. Por favor ayuda."
        elif tipo_alerta == "SILENCIOSA":
            mensaje_base = "🤫 *ALERTA SILENCIOSA* 🤫\nSituación de riesgo detectada. Por favor monitorear sin llamar."
        else:
            mensaje_base = f"⚠️ *ALERTA DEL SISTEMA*: {tipo_alerta}"

        threading.Thread(target=self._abrir_whatsapp_para_contactos, args=(contactos, mensaje_base), daemon=True).start()

    def _abrir_whatsapp_para_contactos(self, contactos, mensaje):
        print(f"Iniciando envío de alertas a {len(contactos)} contactos...")
        for contacto in contactos:
            nombre = contacto.get("nombre", "Contacto")
            telefono = contacto.get("telefono", "")
            telefono_limpio = "".join(filter(str.isdigit, telefono))
            if not telefono_limpio:
                print(f"Saltando contacto {nombre}: Teléfono inválido")
                continue
            mensaje_final = f"Hola {nombre},\n{mensaje}"
            mensaje_encoded = urllib.parse.quote(mensaje_final)
            url = f"https://wa.me/{telefono_limpio}?text={mensaje_encoded}"
            print(f"Abriendo WhatsApp para {nombre} ({telefono_limpio})...")
            webbrowser.open(url)
            time.sleep(2)
import webbrowser

import urllib.parse

import threading

import time



class NotificationService:

    def __init__(self):

        pass



    def notificar_contactos(self, contactos, tipo_alerta="PÁNICO"):

        """

        Envía notificaciones a la lista de contactos.

        Intenta abrir WhatsApp Web para cada contacto.

        """

        if not contactos:

            return



        mensaje_base = ""

        if tipo_alerta == "PÁNICO":

            mensaje_base = "🚨 *ALERTA DE SEGURIDAD* 🚨\nSe ha activado el BOTÓN DE PÁNICO en mi ubicación. Por favor ayuda."

        elif tipo_alerta == "SILENCIOSA":

            mensaje_base = "🤫 *ALERTA SILENCIOSA* 🤫\nSituación de riesgo detectada. Por favor monitorear sin llamar."

        else:

            mensaje_base = f"⚠️ *ALERTA DEL SISTEMA*: {tipo_alerta}"



                                                                   

        threading.Thread(target=self._abrir_whatsapp_para_contactos, args=(contactos, mensaje_base), daemon=True).start()



    def _abrir_whatsapp_para_contactos(self, contactos, mensaje):

        print(f"Iniciando envío de alertas a {len(contactos)} contactos...")

        

        for contacto in contactos:

            nombre = contacto.get("nombre", "Contacto")

            telefono = contacto.get("telefono", "")

            

                                                                 

            telefono_limpio = "".join(filter(str.isdigit, telefono))

            

            if not telefono_limpio:

                print(f"Saltando contacto {nombre}: Teléfono inválido")

                continue



                                  

            mensaje_final = f"Hola {nombre},\n{mensaje}"

            

                                

            mensaje_encoded = urllib.parse.quote(mensaje_final)

            

                                                    

                                                                                               

                                                                           

            url = f"https://wa.me/{telefono_limpio}?text={mensaje_encoded}"

            

            print(f"Abriendo WhatsApp para {nombre} ({telefono_limpio})...")

            webbrowser.open(url)

            

                                                                         

            time.sleep(2)

