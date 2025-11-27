import threading
import time
import requests
import json
import os

CONFIG_FILE = "notification_config.json"

class NotificationService:
    def __init__(self):
        self.config = self._cargar_configuracion()

    def _cargar_configuracion(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "twilio": {
                "enabled": False,
                "account_sid": "TU_ACCOUNT_SID",
                "auth_token": "TU_AUTH_TOKEN",
                "from_number": "+1234567890"
            },
            "telegram": {
                "enabled": False,
                "bot_token": "TU_BOT_TOKEN",
                "chat_id": "TU_CHAT_ID" 
            }
        }

    def notificar_contactos(self, contactos, tipo_alerta="PÁNICO"):
        """
        Envía notificaciones a la lista de contactos usando los métodos configurados.
        """
        if not contactos:
            return

        mensaje_base = ""
        if tipo_alerta == "PÁNICO":
            mensaje_base = "*ALERTA DE SEGURIDAD* \nSe ha activado el BOTÓN DE PÁNICO en mi ubicación. Por favor ayuda."
        elif tipo_alerta == "SILENCIOSA":
            mensaje_base = " *ALERTA SILENCIOSA* \nSituación de riesgo detectada. Por favor monitorear sin llamar."
        else:
            mensaje_base = f" *ALERTA DEL SISTEMA*: {tipo_alerta}"

        threading.Thread(target=self._procesar_notificaciones, args=(contactos, mensaje_base), daemon=True).start()

    def _procesar_notificaciones(self, contactos, mensaje):
        if self.config["telegram"]["enabled"]:
            # 1. Enviar al grupo principal configurado
            self._enviar_telegram(self.config["telegram"]["chat_id"], mensaje)
            
            # 2. Enviar a cada contacto individual si tiene telegram_id
            for contacto in contactos:
                tid = contacto.get("telegram_id")
                if tid:
                    self._enviar_telegram(tid, mensaje)

        if self.config["twilio"]["enabled"]:
            self._enviar_sms_masivo(contactos, mensaje)

    def _enviar_telegram(self, chat_id, mensaje):
        """Envía mensaje a un chat/grupo de Telegram"""
        token = self.config["telegram"]["bot_token"]
        
        if token == "TU_BOT_TOKEN" or not chat_id or chat_id == "TU_CHAT_ID":
            return

        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {"chat_id": chat_id, "text": mensaje.replace("*", "")} # Telegram usa markdown diferente o texto plano
            response = requests.post(url, data=data)
        except Exception:
            pass

    def _enviar_sms_masivo(self, contactos, mensaje):
        """Envía SMS usando Twilio"""
        sid = self.config["twilio"]["account_sid"]
        token = self.config["twilio"]["auth_token"]
        origen = self.config["twilio"]["from_number"]

        if sid == "TU_ACCOUNT_SID":
            return

    
        mensaje_sms = mensaje.replace("*", "")
        
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        auth = (sid, token)

        for contacto in contactos:
            telefono = contacto.get("telefono", "")
            if not telefono.startswith("+"):
                telefono = "+506" + telefono 
            
            data = {
                "To": telefono,
                "From": origen,
                "Body": mensaje_sms
            }
            
            try:
                requests.post(url, data=data, auth=auth)
            except Exception:
                pass


