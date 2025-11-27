"""
Servicio que monitorea el botón de pánico en la Raspberry Pi Pico
Se ejecuta en segundo plano y escucha eventos del botón físico
"""
import serial
import serial.tools.list_ports
import threading
import time


class MonitorBotonPico:
    """Monitorea el botón de pánico físico en la Raspberry Pi Pico"""
    
    def __init__(self, callback_panico=None, callback_silencioso=None, callback_movimiento=None, callback_humo=None, callback_magnet_on=None, callback_magnet_off=None, callback_laser_blocked=None, callback_laser_ok=None, port=None, baudrate=115200):
        """
        Args:
            callback_panico: Función a llamar cuando se presiona el botón de pánico
            callback_silencioso: Función a llamar cuando se presiona el botón silencioso
            callback_movimiento: Función a llamar cuando se detecta movimiento
            callback_humo: Función a llamar cuando se detecta humo
            callback_magnet_on: Función cuando el imán se pega (alarma on)
            callback_magnet_off: Función cuando el imán se separa (alarma off)
            callback_laser_blocked: Función cuando el láser es interrumpido
            callback_laser_ok: Función cuando el láser se restaura
            port: Puerto COM (auto-detecta si es None)
            baudrate: Velocidad de comunicación
        """
        self.callback_panico = callback_panico
        self.callback_silencioso = callback_silencioso
        self.callback_movimiento = callback_movimiento
        self.callback_humo = callback_humo
        self.callback_magnet_on = callback_magnet_on
        self.callback_magnet_off = callback_magnet_off
        self.callback_laser_blocked = callback_laser_blocked
        self.callback_laser_ok = callback_laser_ok
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.monitor_thread = None
        self.running = False
        
    def detectar_pico(self):
        """Detecta automáticamente el puerto de la Pico"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            description = port.description.lower()
            if any(keyword in description for keyword in ["pico", "raspberry", "rp2040"]):
                return port.device
        for port in ports:
            if "USB" in port.description or "COM" in port.device:
                return port.device
        return None
    
    def conectar(self):
        """Conecta al puerto serial de la Pico"""
        try:
            if not self.port:
                self.port = self.detectar_pico()
            
            if not self.port:
                return False
            
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            time.sleep(2)
            return True
            
        except serial.SerialException:
            return False
    
    def cargar_script_boton(self):
        """Carga el script de monitoreo en la Pico"""
        if not self.serial_conn or not self.serial_conn.is_open:
            return False
        
        try:
            import os
            script_path = os.path.abspath("boton_panico_pico.py")
            
            if not os.path.exists(script_path):
                return False
            
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            self.serial_conn.write(b'\x03')
            time.sleep(0.2)
            self.serial_conn.reset_input_buffer()

            self.serial_conn.write(b'\x05')
            time.sleep(0.1)
            
            self.serial_conn.write(script_content.encode())
            time.sleep(0.1)
            
            self.serial_conn.write(b'\x04')
            time.sleep(0.5)
            
            return True
            
        except Exception:
            return False
    
    def _monitor_loop(self):
        """Loop que escucha eventos del botón"""
        
        while self.running:
            try:
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    linea = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    if "PANIC_BUTTON_PRESSED" in linea:
                        if self.callback_panico:
                            self.callback_panico()
                    
                    elif "SILENT_BUTTON_PRESSED" in linea:
                        if self.callback_silencioso:
                            self.callback_silencioso()

                    elif "MOTION_DETECTED" in linea:
                        if self.callback_movimiento:
                            self.callback_movimiento()

                    elif "SMOKE_DETECTED" in linea:
                        if self.callback_humo:
                            self.callback_humo()

                    elif "SMOKE_VAL:" in linea:
                        try:
                            val = linea.split(":")[1]
                            print(f"Nivel Humo: {val}")
                        except:
                            pass

                    elif "MAGNET_NEAR" in linea:
                        if self.callback_magnet_on:
                            self.callback_magnet_on()
                    
                    elif "MAGNET_FAR" in linea:
                        if self.callback_magnet_off:
                            self.callback_magnet_off()

                    elif "LASER_BLOCKED" in linea:
                        if self.callback_laser_blocked:
                            self.callback_laser_blocked()
                    
                    elif "LASER_OK" in linea:
                        if self.callback_laser_ok:
                            self.callback_laser_ok()
                
                time.sleep(0.1)
                
            except Exception:
                if self.running:
                    time.sleep(1)
    
    def iniciar_monitoreo(self):
        """Inicia el monitoreo del botón en segundo plano"""
        if not self.conectar():
            return False
        
        if not self.cargar_script_boton():
            return False
        
        self.running = True
        if self.serial_conn:
            self.serial_conn.reset_input_buffer()
            
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        return True
    
    def detener_monitoreo(self):
        """Detiene el monitoreo"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()

    def activar_alarma(self):
        """Envía comando para activar alarma"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(b"ALARM_ON\n")
                return True
            except Exception:
                pass
        return False

    def desactivar_alarma(self):
        """Envía comando para desactivar alarma"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(b"ALARM_OFF\n")
                return True
            except Exception:
                pass
        return False

    def activar_simulador(self):
        """Envía comando para activar simulador de presencia"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(b"SIMULATOR_ON\n")
                return True
            except Exception:
                pass
        return False

    def desactivar_simulador(self):
        """Envía comando para desactivar simulador de presencia"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(b"SIMULATOR_OFF\n")
                return True
            except Exception:
                pass
        return False

    def controlar_cerradura(self, abrir=True):
        """Envía comando para controlar la cerradura (servo)"""
        if self.serial_conn and self.serial_conn.is_open:
            try:
                cmd = b"LOCK_OPEN\n" if abrir else b"LOCK_CLOSE\n"
                self.serial_conn.write(cmd)
                return True
            except Exception:
                pass
        return False


if __name__ == "__main__":
    def on_panico():
        print("=" * 60)
        print("¡¡ ALARMA DE PÁNICO ACTIVADA !!!")
        print("=" * 60)
    
    monitor = MonitorBotonPico(callback_panico=on_panico)
    
    if monitor.iniciar_monitoreo():
        print("\nSistema activo. Presiona el botón físico para probar.")
        print("Presiona Ctrl+C para salir\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\nDeteniendo monitor...")
            monitor.detener_monitoreo()
    else:
        print("No se pudo iniciar el monitor")
