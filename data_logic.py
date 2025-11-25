import json
import os
import hashlib
import time
from datetime import datetime

DB_FILE = "database.json"


class SecurityLogic:
    def __init__(self):
        self.db = {"usuarios": {}, "dispositivos": {}, "eventos": {}, "contactos": {}}
        self.usuario_actual = None
        self.observadores_eventos = []
        self.MODOS_POR_TIPO = {
            "Sensor de Movimiento": ["Alta Sensibilidad", "Baja Sensibilidad", "Inactivo"],
            "Cerradura Inteligente": ["Siempre Abierto", "Siempre Cerrado", "Inactivo"],
            "Detector de Humo": ["Alta Sensibilidad", "Baja Sensibilidad", "Inactivo"],
            "Cámara de Seguridad": ["Grabación Continua", "Detección Movimiento", "Inactivo"],
            "Simulador Presencia": ["Automático", "Programado", "Inactivo"],
            "Sensor Puerta": ["Alta Sensibilidad", "Baja Sensibilidad", "Inactivo"],
            "Detector Placas": ["Solo Alertas", "Registro Completo", "Inactivo"],
            "Detector Láser": ["Alta Sensibilidad", "Baja Sensibilidad", "Inactivo"]
        }
        self.cargar()

    def cargar(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding='utf-8') as f:
                    self.db = json.load(f)
                if "camaras" not in self.db:
                    self.db["camaras"] = {}
            except Exception:
                self.db = {"usuarios": {}, "dispositivos": {}, "eventos": {}, "contactos": {}, "camaras": {}}
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

    def agregar_observador_eventos(self, callback):
        if callback not in self.observadores_eventos:
            self.observadores_eventos.append(callback)

    def remover_observador_eventos(self, callback):
        if callback in self.observadores_eventos:
            self.observadores_eventos.remove(callback)

    def notificar_observadores_eventos(self):
        for callback in self.observadores_eventos:
            try:
                callback()
            except Exception as e:
                print(f"Error en observador de eventos: {e}")

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
        self.notificar_observadores_eventos()

    def obtener_eventos(self):
        if not self.usuario_actual:
            return []
        return list(self.db.get("eventos", {}).get(self.usuario_actual, []))

    def filtrar_eventos(self, dispositivo=None, tipo=None, fecha_inicio=None, fecha_fin=None, nombre=None, serie=None, ubicacion=None):
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
        nombre_f = nombre.lower().strip() if nombre else None
        serie_f = serie.strip() if serie else None
        ubic_f = ubicacion.lower().strip() if ubicacion else None
        res = []
        for ev in eventos:
            ev_serie = ev.get("dispositivo")
            if serie_f and ev_serie != serie_f:
                continue
            if dispositivo and ev_serie != dispositivo:
                continue
            dispositivo_info = None
            if nombre_f or ubic_f:
                dispositivo_info = self.obtener_dispositivo_por_serie(ev_serie)
            if tipo and ev.get("tipo") != tipo:
                continue
            if nombre_f:
                dev_name = (dispositivo_info.get("nombre") if dispositivo_info else None) or ""
                if nombre_f not in dev_name.lower():
                    if nombre_f not in (ev.get("descripcion") or "").lower():
                        continue
            if ubic_f:
                dev_ubic = (dispositivo_info.get("ubicacion") if dispositivo_info else None) or ""
                if ubic_f not in dev_ubic.lower():
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

    def obtener_dispositivo_por_serie(self, serie):
        if not self.usuario_actual:
            return None
        dispositivos = self.db.get("dispositivos", {}).get(self.usuario_actual, [])
        for dispositivo in dispositivos:
            if dispositivo.get("serie") == serie:
                return dispositivo
        return None

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
            "modo": "Inactivo",
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
        evs = [e for e in evs if e.get("dispositivo") != serie]
        self.db["eventos"][self.usuario_actual] = evs
        self.registrar_evento("Sistema", f"Dispositivo eliminado: {serie}", tipo="Eliminación")
        self.guardar()

    def cambiar_modo_dispositivo(self, serie, modo):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        dispositivo = None
        for d in self.db.get("dispositivos", {}).get(self.usuario_actual, []):
            if d.get("serie") == serie:
                dispositivo = d
                break
        if not dispositivo:
            raise Exception("Dispositivo no encontrado")
        tipo_dispositivo = dispositivo.get("tipo")
        modos_validos = self.MODOS_POR_TIPO.get(tipo_dispositivo, ["Inactivo"])
        if modo not in modos_validos:
            raise Exception(f"Modo '{modo}' no válido para {tipo_dispositivo}. Modos válidos: {', '.join(modos_validos)}")
        updated = False
        for d in self.db.get("dispositivos", {}).get(self.usuario_actual, []):
            if d.get("serie") == serie:
                d["modo"] = modo
                if modo == "Inactivo":
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
        estado_normalizado = estado.lower()
        if estado_normalizado not in ("activo", "inactivo"):
            raise Exception("Estado inválido. Use 'Activo' o 'Inactivo'")
        updated = False
        for d in self.db.get("dispositivos", {}).get(self.usuario_actual, []):
            if d.get("serie") == serie:
                d["estado"] = estado_normalizado
                updated = True
                break
        if not updated:
            raise Exception("Dispositivo no encontrado")
        self.registrar_evento("Sistema", f"Estado cambiado: {serie} -> {estado}", tipo="Configuración")
        self.guardar()

    def obtener_camaras(self):
        if not self.usuario_actual:
            return {}
        self.db.setdefault("camaras", {})
        self.db["camaras"].setdefault(self.usuario_actual, {})
        return self.db.get("camaras", {}).get(self.usuario_actual, {})

    def guardar_detector(self, serie, ip, nombre, ubicacion):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        self.db.setdefault("detectores", {})
        self.db["detectores"].setdefault(self.usuario_actual, {})
        self.db["detectores"][self.usuario_actual][serie] = {
            'ip': ip,
            'nombre': nombre,
            'ubicacion': ubicacion,
            'estado': 'activa',
            'ultima_deteccion': None,
            'monitoreando': False
        }
        self.guardar()

    def obtener_detectores(self):
        if not self.usuario_actual:
            return {}
        self.db.setdefault("detectores", {})
        self.db["detectores"].setdefault(self.usuario_actual, {})
        return self.db.get("detectores", {}).get(self.usuario_actual, {})

    def eliminar_detector(self, serie):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        if serie in self.db.get("detectores", {}).get(self.usuario_actual, {}):
            del self.db["detectores"][self.usuario_actual][serie]
            self.guardar()

    def guardar_placa(self, placa, propietario=""):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        self.db.setdefault('placas', {})
        self.db['placas'].setdefault(self.usuario_actual, {})
        self.db['placas'][self.usuario_actual][placa] = {
            'propietario': propietario,
            'creado': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.guardar()

    def obtener_placas(self):
        if not self.usuario_actual:
            return {}
        self.db.setdefault('placas', {})
        self.db['placas'].setdefault(self.usuario_actual, {})
        return self.db['placas'][self.usuario_actual]

    def eliminar_placa(self, placa):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        if placa in self.db.get('placas', {}).get(self.usuario_actual, {}):
            del self.db['placas'][self.usuario_actual][placa]
            self.guardar()

    def esta_placa_registrada(self, placa):
        if not self.usuario_actual:
            return False
        return placa in self.db.get('placas', {}).get(self.usuario_actual, {})

    def guardar_camara(self, serie, ip, nombre, ubicacion):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        self.db.setdefault("camaras", {})
        self.db["camaras"].setdefault(self.usuario_actual, {})
        self.db["camaras"][self.usuario_actual][serie] = {
            'ip': ip,
            'nombre': nombre,
            'ubicacion': ubicacion,
            'estado': 'activa',
            'ultima_deteccion': None,
            'monitoreando': False
        }
        self.guardar()

    def eliminar_camara(self, serie):
        if not self.usuario_actual:
            raise Exception("No autenticado")
        if serie in self.db.get("camaras", {}).get(self.usuario_actual, {}):
            del self.db["camaras"][self.usuario_actual][serie]
            self.guardar()

    def obtener_resumen(self):
        dispositivos = self.obtener_dispositivos()
        eventos = self.obtener_eventos()
        total = len(dispositivos)
        activos = sum(1 for d in dispositivos if d.get("estado") == "activo")
        hoy = len([e for e in eventos if e.get("fecha", "").startswith(datetime.now().strftime("%Y-%m-%d"))])
        return total, activos, hoy

    def agregar_contacto(self, nombre, telefono, relacion=""):
        """Agrega un contacto de emergencia para el usuario actual."""
        if not self.usuario_actual:
            raise Exception("No autenticado")
        if not nombre or not telefono:
            raise Exception("Nombre y teléfono son requeridos")
        
        self.db.setdefault("contactos", {})
        self.db["contactos"].setdefault(self.usuario_actual, [])
        
        for contacto in self.db["contactos"][self.usuario_actual]:
            if contacto.get("telefono") == telefono:
                raise Exception("Ya existe un contacto con ese teléfono")
        
        contacto = {
            "nombre": nombre,
            "telefono": telefono,
            "relacion": relacion,
            "creado": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.db["contactos"][self.usuario_actual].append(contacto)
        self.registrar_evento("Sistema", f"Contacto de emergencia agregado: {nombre}", tipo="Configuración")
        self.guardar()

    def obtener_contactos(self):
        """Obtiene todos los contactos de emergencia del usuario actual."""
        if not self.usuario_actual:
            return []
        self.db.setdefault("contactos", {})
        self.db["contactos"].setdefault(self.usuario_actual, [])
        return list(self.db["contactos"][self.usuario_actual])

    def eliminar_contacto(self, telefono):
        """Elimina un contacto de emergencia por su teléfono."""
        if not self.usuario_actual:
            raise Exception("No autenticado")
        
        contactos = self.db.get("contactos", {}).get(self.usuario_actual, [])
        nuevos = [c for c in contactos if c.get("telefono") != telefono]
        
        if len(nuevos) == len(contactos):
            raise Exception("Contacto no encontrado")
        
        self.db["contactos"][self.usuario_actual] = nuevos
        self.registrar_evento("Sistema", f"Contacto de emergencia eliminado: {telefono}", tipo="Configuración")
        self.guardar()

    def actualizar_contacto(self, telefono_original, nuevo_nombre, nuevo_telefono, nueva_relacion=""):
        """Actualiza un contacto de emergencia existente."""
        if not self.usuario_actual:
            raise Exception("No autenticado")
        if not nuevo_nombre or not nuevo_telefono:
            raise Exception("Nombre y teléfono son requeridos")
        
        contactos = self.db.get("contactos", {}).get(self.usuario_actual, [])
        
        if nuevo_telefono != telefono_original:
            for contacto in contactos:
                if contacto.get("telefono") == nuevo_telefono:
                    raise Exception("Ya existe un contacto con ese teléfono")
        
        encontrado = False
        
        for contacto in contactos:
            if contacto.get("telefono") == telefono_original:
                contacto["nombre"] = nuevo_nombre
                contacto["telefono"] = nuevo_telefono
                contacto["relacion"] = nueva_relacion
                encontrado = True
                break
        
        if not encontrado:
            raise Exception("Contacto no encontrado")
        
        self.registrar_evento("Sistema", f"Contacto de emergencia actualizado: {nuevo_nombre}", tipo="Configuración")
        self.guardar()

    def activar_alarma_panico(self, tipo="manual"):
        """Activa la alarma de pánico y registra el evento."""
        if not self.usuario_actual:
            raise Exception("No autenticado")
        
        descripcion = f"¡ALARMA DE PÁNICO ACTIVADA! Tipo: {tipo}"
        self.registrar_evento("Sistema", descripcion, tipo="Pánico")
        
        return self.obtener_contactos()

    def activar_alarma_silenciosa(self):
        """Activa la alarma silenciosa sin sonido audible."""
        if not self.usuario_actual:
            raise Exception("No autenticado")
        
        descripcion = "Alarma silenciosa activada - Notificación enviada a contactos"
        self.registrar_evento("Sistema", descripcion, tipo="Alarma Silenciosa")
        
        return self.obtener_contactos()