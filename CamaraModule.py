import threading
import time
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError
import json

class CamaraManager:
    def __init__(self, logic):
        self.logic = logic
        self.camaras_activas = {}
        self.monitoreo_activo = False
        self.thread_monitoreo = None
        self.cargar_camaras_existentes()  # Cargar cámaras existentes al iniciar
        
    def cargar_camaras_existentes(self):
        """Carga las cámaras existentes desde la base de datos"""
        try:
            camaras_db = self.logic.obtener_camaras()
            for serie, camara_data in camaras_db.items():
                self.camaras_activas[serie] = {
                    'ip': camara_data.get('ip', '192.168.0.102'),
                    'nombre': camara_data.get('nombre', 'Cámara Sin Nombre'),
                    'ubicacion': camara_data.get('ubicacion', 'Ubicación Desconocida'),
                    'estado': camara_data.get('estado', 'activa'),
                    'ultima_deteccion': camara_data.get('ultima_deteccion')
                }
            print(f"Cámaras cargadas: {list(self.camaras_activas.keys())}")
        except Exception as e:
            print(f"Error cargando cámaras existentes: {e}")
    
    def registrar_camara(self, serie, nombre, ubicacion, ip_celular):
        try:
            # Verificar si el dispositivo ya existe en la base de datos
            dispositivo_existente = self.logic.obtener_dispositivo_por_serie(serie)
            
            if not dispositivo_existente:
                # Solo registrar en el sistema principal si no existe
                self.logic.registrar_dispositivo(
                    serie=serie,
                    tipo="Cámara de Seguridad", 
                    nombre=nombre,
                    ubicacion=ubicacion
                )
            
            # Registrar/actualizar en el gestor de cámaras
            self.camaras_activas[serie] = {
                'ip': ip_celular,
                'nombre': nombre,
                'ubicacion': ubicacion,
                'estado': 'activa',
                'ultima_deteccion': None
            }

            # Guardar en la base de datos para persistencia
            self.logic.guardar_camara(serie, ip_celular, nombre, ubicacion)

            self.logic.registrar_evento(
                serie, 
                f"Cámara registrada: {nombre} en {ubicacion}", 
                "Registro"
            )
            
            return True
            
        except Exception as e:
            raise Exception(f"Error registrando cámara: {e}")
    
    def verificar_conexion_camara(self, serie):
        if serie not in self.camaras_activas:
            return False
            
        camara = self.camaras_activas[serie]
        try:
            url = f"http://{camara['ip']}:8080/"
            req = Request(url)
            req.add_header('User-Agent', 'SistemaSeguridad/1.0')
            
            with urlopen(req, timeout=5) as response:
                return response.status == 200
        except:
            return False
    
    def capturar_foto(self, serie, tipo="manual"):
        if serie not in self.camaras_activas:
            return False
            
        camara = self.camaras_activas[serie]
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"foto_{serie}_{timestamp}.jpg"
            url = f"http://{camara['ip']}:8080/photo.jpg"
            
            req = Request(url)
            req.add_header('User-Agent', 'SistemaSeguridad/1.0')
            
            with urlopen(req, timeout=10) as response:
                if response.status == 200:
                    with open(nombre_archivo, 'wb') as f:
                        f.write(response.read())
                    
                    descripcion = f"Foto {'automática' if tipo == 'automatico' else 'manual'} capturada: {nombre_archivo}"
                    self.logic.registrar_evento(serie, descripcion, "Captura")
                    
                    return True
            return False
            
        except Exception as e:
            self.logic.registrar_evento(serie, f"Error capturando foto: {e}", "Error")
            return False
    
    def iniciar_monitoreo_automatico(self):
        if self.monitoreo_activo:
            return
            
        self.monitoreo_activo = True
        self.thread_monitoreo = threading.Thread(target=self._monitoreo_loop, daemon=True)
        self.thread_monitoreo.start()
        
        self.logic.registrar_evento("Sistema", "Monitoreo automático de cámaras iniciado", "Sistema")
    
    def detener_monitoreo_automatico(self):
        self.monitoreo_activo = False
        if self.thread_monitoreo:
            self.thread_monitoreo.join(timeout=2)
        
        self.logic.registrar_evento("Sistema", "Monitoreo automático de cámaras detenido", "Sistema")
    
    def _monitoreo_loop(self):
        while self.monitoreo_activo:
            try:
                for serie, camara in self.camaras_activas.items():
                    if not self.monitoreo_activo:
                        break
                        
                    if self._simular_deteccion_movimiento():
                        self.capturar_foto(serie, "automatico")
                        
                        self.logic.registrar_evento(
                            serie, 
                            f"Movimiento detectado en {camara['ubicacion']}", 
                            "Movimiento"
                        )
                
                time.sleep(10)
                
            except Exception as e:
                self.logic.registrar_evento("Sistema", f"Error en monitoreo: {e}", "Error")
                time.sleep(10)
    
    def _simular_deteccion_movimiento(self):
        import random
        return random.random() < 0.3
    
    def obtener_estado_camaras(self):
        estado = {}
        for serie, camara in self.camaras_activas.items():
            estado[serie] = {
                'nombre': camara['nombre'],
                'ubicacion': camara['ubicacion'],
                'conectada': self.verificar_conexion_camara(serie),
                'estado': camara['estado'],
                'ultima_deteccion': camara['ultima_deteccion']
            }
        return estado
    
    def eliminar_camara(self, serie):
        if serie in self.camaras_activas:
            del self.camaras_activas[serie]

        try:
            self.logic.eliminar_camara(serie)
            self.logic.eliminar_dispositivo(serie)
        except Exception as e:
            print(f"Error eliminando cámara: {e}")