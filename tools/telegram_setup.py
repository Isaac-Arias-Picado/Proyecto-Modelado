import requests
import time
import json
import os
import sys

# Ajustar ruta al archivo de configuración (subir un nivel desde tools/)
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notification_config.json")

def save_config(token, chat_id):
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    else:
        # Estructura base si no existe
        config = {
            "twilio": {"enabled": False},
            "telegram": {},
            "whatsapp_web": {"enabled": True}
        }
    
    if "telegram" not in config:
        config["telegram"] = {}
        
    config["telegram"]["enabled"] = True
    config["telegram"]["bot_token"] = token
    config["telegram"]["chat_id"] = str(chat_id)
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"✅ Configuración guardada en {CONFIG_FILE}")

def get_chat_id(token):
    print(f"\n⏳ Conectando con el bot...")
    
    # Limpiar actualizaciones previas
    url_updates = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        requests.get(url_updates, params={"offset": -1})
    except:
        pass

    print(f"👉 Ve a Telegram, busca tu bot y envíale un mensaje que diga 'Hola' o dale a 'Iniciar'.")
    print("   Esperando mensaje para detectar tu ID...")
    
    while True:
        try:
            response = requests.get(url_updates)
            data = response.json()
            
            if not data.get("ok"):
                print(f"❌ Error en el token: {data.get('description')}")
                return None

            if data["result"]:
                # Obtener el último mensaje
                last_update = data["result"][-1]
                if "message" in last_update:
                    chat_id = last_update["message"]["chat"]["id"]
                    user = last_update["message"]["from"].get("first_name", "Usuario")
                    print(f"\n✅ ¡Mensaje recibido de {user}!")
                    print(f"🆔 Chat ID encontrado: {chat_id}")
                    return chat_id
            
        except Exception as e:
            print(f"Error conectando: {e}")
            
        time.sleep(2)

def main():
    print("\n=== 🤖 Configuración Automática de Telegram ===")
    print("Este script te ayudará a conectar tu sistema de seguridad con Telegram.\n")
    
    print("PASO 1: Crear el Bot")
    print("  1. Abre Telegram y busca el usuario '@BotFather'")
    print("  2. Envíale el mensaje '/newbot'")
    print("  3. Ponle un nombre (ej: 'Alarma Casa')")
    print("  4. Ponle un usuario (debe terminar en 'bot', ej: 'MiAlarma123_bot')")
    print("  5. BotFather te dará un TOKEN largo (letras y números)")
    print("-" * 60)
    
    token = input("👉 Pega el TOKEN aquí y presiona Enter: ").strip()
    
    if not token:
        print("❌ Token inválido")
        return

    chat_id = get_chat_id(token)
    
    if chat_id:
        save_config(token, chat_id)
        
        # Mensaje de prueba
        print("\n📤 Enviando mensaje de prueba...")
        send_url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            res = requests.post(send_url, data={"chat_id": chat_id, "text": "✅ ¡Configuración exitosa! Tu sistema de seguridad ahora te notificará por aquí."})
            if res.status_code == 200:
                print("✅ ¡Listo! Revisa tu Telegram, deberías haber recibido la confirmación.")
                print("   Ahora puedes cerrar esta ventana y reiniciar la aplicación principal.")
            else:
                print("⚠️ Configuración guardada, pero falló el mensaje de prueba.")
        except Exception as e:
            print(f"⚠️ Error enviando prueba: {e}")

    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
