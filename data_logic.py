# File: data_logic.py
import json
import os
import hashlib
import time
from datetime import datetime

DB_FILE = "database.json"
import os
print(">>> Ruta real del JSON:", os.path.abspath(DB_FILE))

class SecurityLogic:
    def __init__(self):

        self.db = {"usuarios": {}, "dispositivos": {}, "eventos": {}, "contactos": {}}
        self.usuario_actual = None
        self.cargar()

    def cargar(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding='utf-8') as f:
                    self.db = json.load(f)
            except Exception:

                self.db = {"usuarios": {}, "dispositivos": {}, "eventos": {}, "contactos": {}}
                self.guardar()
        else:
            self.guardar()

    def guardar(self):
        with open(DB_FILE, "w", encoding='utf-8') as f:
            json.dump(self.db, f, indent=4, ensure_ascii=False)

    def crear_usuario(self, usuario, contraseña):
        if not usuario or not contraseña:
            raise Exception("Usuario y contraseña requeridos")
        if usuario in self.db["usuarios"]:
            raise Exception("El usuario ya existe.")
        h = hashlib.sha256(contraseña.encode()).hexdigest()
        self.db["usuarios"][usuario] = {"password": h}
        self.db.setdefault("dispositivos", {})
        self.db.setdefault("eventos", {})
        self.db.setdefault("contactos", {})
        self.db["dispositivos"][usuario] = []
        self.db["eventos"][usuario] = []
        self.db["contactos"][usuario] = []
        self.guardar()

    def autenticar(self, usuario, contraseña):
        if usuario not in self.db["usuarios"]:
            return False
        h = hashlib.sha256(contraseña.encode()).hexdigest()
        if self.db["usuarios"][usuario]["password"] == h:
            self.usuario_actual = usuario
            self.registrar_evento("Sistema", "Inicio de sesión")
            return True
        return False

    def registrar_evento(self, dispositivo, descripcion, tipo="Evento"):
        if not self.usuario_actual:
            return
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.setdefault("eventos", {})
        self.db["eventos"].setdefault(self.usuario_actual, [])
        self.db["eventos"][self.usuario_actual].append({
            "dispositivo": dispositivo,
            "descripcion": descripcion,
            "tipo": tipo,
            "fecha": ahora
        })
        self.guardar()

    def obtener_eventos(self):
        if not self.usuario_actual:
            return []
        return list(self.db.get("eventos", {}).get(self.usuario_actual, []))

    def filtrar_eventos(self, dispositivo=None, tipo=None, fecha_inicio=None, fecha_fin=None):
        eventos = self.obtener_eventos()
        def dentro_rango(fecha_str):
            if not fecha_inicio and not fecha_fin:
                return True
            try:
                dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return True
            if fecha_inicio:
                start = datetime.strptime(fecha_inicio + " 00:00:00", "%Y-%m-%d %H:%M:%S")
                if dt < start:
                    return False
            if fecha_fin:
                end = datetime.strptime(fecha_fin + " 23:59:59", "%Y-%m-%d %H:%M:%S")
                if dt > end:
                    return False
            return True
        res = []
        for ev in eventos:
            if dispositivo and ev.get("dispositivo") != dispositivo:
                continue
            if tipo and ev.get("tipo") != tipo:
                continue
            if not dentro_rango(ev.get("fecha", "")):
                continue
            res.append(ev)
        return res

    def eliminar_eventos(self):
        if not self.usuario_actual:
            return
        self.db["eventos"][self.usuario_actual] = []
        self.guardar()

    def obtener_dispositivos(self):
        if not self.usuario_actual:
            return []
        return list(self.db.get("dispositivos", {}).get(self.usuario_actual, []))

    def _serie_existe(self, serie):
        for d in self.obtener_dispositivos():
            if d.get("serie") == serie:
                return True
        return False

    def registrar_dispositivo(self, serie, tipo, nombre, ubicacion):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        if not serie:
            raise Exception("La serie es obligatoria")
        if self._serie_existe(serie):
            raise Exception("Ya existe un dispositivo con esa serie")
        disp = {
            "serie": serie,
            "tipo": tipo,
            "nombre": nombre,
            "ubicacion": ubicacion,
            "estado": "inactivo",
            "modo": "manual",
            "creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.db.setdefault("dispositivos", {})
        self.db["dispositivos"].setdefault(self.usuario_actual, [])
        self.db["dispositivos"][self.usuario_actual].append(disp)
        self.registrar_evento("Sistema", f"Dispositivo registrado: {nombre}", tipo="Registro")
        self.guardar()

    def eliminar_dispositivo(self, serie):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        dispositivos = self.db.get("dispositivos", {}).get(self.usuario_actual, [])
        nuevos = [d for d in dispositivos if d.get("serie") != serie]
        if len(nuevos) == len(dispositivos):
            raise Exception("Dispositivo no encontrado")
        self.db["dispositivos"][self.usuario_actual] = nuevos
        evs = self.db.get("eventos", {}).get(self.usuario_actual, [])
        evs = [e for e in evs if e.get("dispositivo") != serie and e.get("dispositivo") != dispositivos and e.get("dispositivo") != ""]
        self.db["eventos"][self.usuario_actual] = evs
        self.registrar_evento("Sistema", f"Dispositivo eliminado: {serie}", tipo="Eliminación")
        self.guardar()

    def cambiar_modo_dispositivo(self, serie, modo):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        if modo not in ("manual", "automatico", "inactivo"):
            raise Exception("Modo inválido")
        updated = False
        for d in self.db.get("dispositivos", {}).get(self.usuario_actual, []):
            if d.get("serie") == serie:
                d["modo"] = modo
                if modo == "inactivo":
                    d["estado"] = "inactivo"
                updated = True
                break
        if not updated:
            raise Exception("Dispositivo no encontrado")
        self.registrar_evento("Sistema", f"Modo cambiado: {serie} -> {modo}", tipo="Configuración")
        self.guardar()

    def cambiar_estado_dispositivo(self, serie, estado):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        if estado not in ("activo", "inactivo"):
            raise Exception("Estado inválido")
        updated = False
        for d in self.db.get("dispositivos", {}).get(self.usuario_actual, []):
            if d.get("serie") == serie:
                d["estado"] = estado
                updated = True
                break
        if not updated:
            raise Exception("Dispositivo no encontrado")
        self.registrar_evento("Sistema", f"Estado cambiado: {serie} -> {estado}", tipo="Configuración")
        self.guardar()

    def obtener_resumen(self):
        dispositivos = self.obtener_dispositivos()
        eventos = self.obtener_eventos()
        total = len(dispositivos)
        activos = sum(1 for d in dispositivos if d.get("estado") == "activo")
        hoy = len([e for e in eventos if e.get("fecha", "").startswith(datetime.now().strftime("%Y-%m-%d"))])
        return total, activos, hoy