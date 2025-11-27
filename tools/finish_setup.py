import requests
import time
import json
import os

TOKEN = "8023942284:AAHY7N1lzuNYV_ZnwGJSIA_hfU_5TWHLPts"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notification_config.json")

def save_chat_id(chat_id):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    config["telegram"]["enabled"] = True
    config["telegram"]["bot_token"] = TOKEN
    config["telegram"]["chat_id"] = str(chat_id)
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
    print(f"✅ Configuración completada. Chat ID: {chat_id}")

def get_chat_id():
    print(f"⏳ Buscando tu ID de chat con el token proporcionado...")
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    
    # Intentar limpiar updates viejos
    try:
        requests.get(url, params={"offset": -1})
    except:
        pass

    print("👉 Por favor, ve a Telegram y envía un mensaje 'Hola' a tu nuevo bot.")
    print("   Esperando mensaje...")
    
    start_time = time.time()
    while time.time() - start_time < 60: # Intentar por 60 segundos
        try:
            response = requests.get(url)
            data = response.json()
            
            if data.get("result"):
                last_update = data["result"][-1]
                if "message" in last_update:
                    chat_id = last_update["message"]["chat"]["id"]
                    user = last_update["message"]["from"].get("first_name", "Usuario")
                    print(f"✅ ¡Mensaje recibido de {user}!")
                    save_chat_id(chat_id)
                    
                    # Enviar confirmación
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                data={"chat_id": chat_id, "text": "✅ ¡Sistema conectado exitosamente!"})
                    return True
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(2)
    
    print("❌ No se recibió ningún mensaje en 60 segundos.")
    return False

if __name__ == "__main__":
    get_chat_id()
