from typing import Callable, Optional



from CamaraModule import CamaraManager

from data_logic import SecurityLogic





class CameraController:

    """Adaptador entre la UI, CamaraManager y SecurityLogic.



    Objetivo: centralizar operaciones relacionadas con cámaras

    para mantener `visual.py` más legible y con responsabilidades claras.

    """



    def __init__(self, camara_manager: CamaraManager, logic: SecurityLogic):

        self.cam = camara_manager

        self.logic = logic



    def load_cameras_from_db(self):
        """Cargar cámaras persistidas desde la base de datos en CamaraManager.

        Solo activa las cámaras. El inicio del monitoreo debe gestionarse vía sync_monitoring_modes.
        """
        camaras = self.logic.obtener_camaras()
        for serie, info in camaras.items():
            ip = info.get('ip')
            modelo = info.get('nombre', 'IP Camera')
            
            self.cam.activar_camara(serie, ip, modelo)



    def get_camaras_activas(self):

        return self.cam.camaras_activas



    def tomar_fotografia(self, serie: str) -> Optional[bytes]:

        return self.cam.tomar_fotografia(serie)



    def detectar_movimiento_once(self, serie: str):

        return self.cam.detectar_movimiento(serie)



    def capturar_foto(self, serie: str) -> bool:

        return self.cam.capturar_foto(serie)



    def activar_camara(self, serie: str, ip: str, modelo: str = "IP Camera") -> bool:

        ok = self.cam.activar_camara(serie, ip, modelo)

        if ok:

            try:

                

                self.logic.guardar_camara(serie, ip, modelo, ubicacion="")

            except Exception:

                pass

        return ok



    def desactivar_camara(self, serie: str) -> bool:

        ok = self.cam.desactivar_camara(serie)

        if ok:

            try:

                self.logic.eliminar_camara(serie)

            except Exception:

                pass

        return ok



    def start_monitoring_all(self, intervalo: int = 1, callback_evento: Optional[Callable] = None):

        """Inicia el monitoreo de todas las cámaras activas. Devuelve cuántas cámaras se iniciaron."""

        count = 0

        for serie in list(self.cam.camaras_activas.keys()):

            started = self.cam.iniciar_monitoreo_movimiento(serie, intervalo=intervalo, callback_evento=callback_evento)

            if started:

                

                try:

                    self.logic.guardar_camara(serie, self.cam.camaras_activas[serie].get('ip', ''), self.cam.camaras_activas[serie].get('modelo', ''), self.logic.obtener_dispositivo_por_serie(serie).get('ubicacion',''))

                    

                    self.logic.db.setdefault('camaras', {}).setdefault(self.logic.usuario_actual, {})

                    self.logic.db['camaras'][self.logic.usuario_actual][serie]['monitoreando'] = True

                    self.logic.guardar()

                except Exception:

                    pass

                count += 1

        return count



    def stop_monitoring_all(self):

        for serie in list(self.cam.camaras_activas.keys()):

            self.cam.detener_monitoreo_movimiento(serie)

            try:

                

                self.logic.db.setdefault('camaras', {}).setdefault(self.logic.usuario_actual, {})

                if serie in self.logic.db['camaras'][self.logic.usuario_actual]:

                    self.logic.db['camaras'][self.logic.usuario_actual][serie]['monitoreando'] = False

                self.logic.guardar()

            except Exception:

                pass

        return True



    def get_camera_info(self, serie: str):

        return self.cam.camaras_activas.get(serie)

    def sync_monitoring_modes(self, event_callback: Callable):
        """Sincroniza el estado de monitoreo de las cámaras con el modo configurado en la BD."""
        for serie in list(self.cam.camaras_activas.keys()):
            dispositivo = self.logic.obtener_dispositivo_por_serie(serie)
            if not dispositivo:
                continue
            
            modo = dispositivo.get('modo')
            info = self.cam.camaras_activas[serie]
            is_monitoring = info.get('monitoreando', False)
            
            if modo == "Detección Movimiento":
                if not is_monitoring:
                    self.cam.iniciar_monitoreo_movimiento(serie, intervalo=0.5, callback_evento=event_callback)
                else:
                    self.cam.detener_monitoreo_movimiento(serie)
                    self.cam.iniciar_monitoreo_movimiento(serie, intervalo=0.5, callback_evento=event_callback)
            elif modo != "Detección Movimiento" and is_monitoring:
                self.cam.detener_monitoreo_movimiento(serie)

