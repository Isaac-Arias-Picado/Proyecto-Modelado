from typing import Callable, Optional
from DetectorPlacasModule import DetectorPlacasManager
from data_logic import SecurityLogic

class PlatesController:
    def __init__(self, manager: DetectorPlacasManager, logic: SecurityLogic):
        self.manager = manager
        self.logic = logic

    def load_detectores_from_db(self):
        """Cargar detectores persistidos desde la DB en el manager y reanudar monitoreo si aplica."""
        detectores = self.logic.obtener_detectores()
        for serie, info in detectores.items():
            ip = info.get('ip')
            modelo = info.get('nombre', 'Detector Placas')
            self.manager.activar_detector(serie, ip, modelo)
            if info.get('monitoreando'):
                self.manager.iniciar_monitoreo(serie, intervalo=5, callback_evento=None)

    def activar_detector(self, serie: str, ip: str, nombre: str = "Detector Placas") -> bool:
        ok = self.manager.activar_detector(serie, ip, nombre)
        if ok:
            try:
                
                self.logic.guardar_detector(serie, ip, nombre, ubicacion="")
            except Exception:
                pass
        return ok

    def desactivar_detector(self, serie: str) -> bool:
        ok = self.manager.desactivar_detector(serie)
        if ok:
            try:
                self.logic.eliminar_detector(serie)
            except Exception:
                pass
        return ok

    def start_monitoring_all(self, intervalo: int = 5, callback_evento: Optional[Callable] = None):
        count = 0
        for serie in list(self.manager.detectores_activas.keys()):
            started = self.manager.iniciar_monitoreo(serie, intervalo=intervalo, callback_evento=callback_evento)
            if started:
                try:
                    
                    self.logic.db.setdefault('detectores', {}).setdefault(self.logic.usuario_actual, {})
                    self.logic.db['detectores'][self.logic.usuario_actual][serie]['monitoreando'] = True
                    self.logic.guardar()
                except Exception:
                    pass
                count += 1
        return count

    def stop_monitoring_all(self):
        for serie in list(self.manager.detectores_activas.keys()):
            self.manager.detener_monitoreo(serie)
            try:
                self.logic.db.setdefault('detectores', {}).setdefault(self.logic.usuario_actual, {})
                if serie in self.logic.db['detectores'][self.logic.usuario_actual]:
                    self.logic.db['detectores'][self.logic.usuario_actual][serie]['monitoreando'] = False
                self.logic.guardar()
            except Exception:
                pass
        return True

    def detectar_placa_once(self, serie: str):
        return self.manager.detectar_placa_once(serie)

    def obtener_detectores_activas(self):
        return self.manager.detectores_activas
