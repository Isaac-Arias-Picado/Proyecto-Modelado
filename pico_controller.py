"""
Módulo para controlar Raspberry Pi Pico mediante comunicación serial
Compatible con MicroPython
"""
import serial
import serial.tools.list_ports
import time
import os
from pathlib import Path


class PicoController:
    """Controlador para Raspberry Pi Pico"""
    
    def __init__(self, port=None, baudrate=115200):
        """
        Inicializa el controlador de Pico
        
        Args:
            port: Puerto COM (ej: 'COM4'). Si es None, se detecta automáticamente
            baudrate: Velocidad de comunicación (default: 115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        
    def detectar_pico(self):
        """
        Detecta automáticamente el puerto COM de la Raspberry Pi Pico
        
        Returns:
            str: Puerto COM detectado o None si no se encuentra
        """
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            description = port.description.lower()
            manufacturer = (port.manufacturer or "").lower()
            
            if any(keyword in description for keyword in ["pico", "raspberry", "rp2040"]):
                return port.device
            if "micropython" in manufacturer or "raspberry" in manufacturer:
                return port.device
                
        for port in ports:
            if "USB" in port.description or "COM" in port.device:
                return port.device
                
        return None
    
    def conectar(self):
        """
        Establece conexión serial con la Pico
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        try:
            if not self.port:
                self.port = self.detectar_pico()
                
            if not self.port:
                print("No se pudo detectar la Raspberry Pi Pico")
                return False
            
            print(f" Conectando a {self.port}...")
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2
            )
            
            time.sleep(2) 
            print(f"Conectado a Raspberry Pi Pico en {self.port}")
            return True
            
        except serial.SerialException as e:
            print(f"Error al conectar: {e}")
            return False
    
    def desconectar(self):
        """Cierra la conexión serial"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("🔌 Desconectado de la Pico")
    
    def enviar_comando(self, comando):
        """
        Envía un comando a la Pico mediante REPL
        
        Args:
            comando: String con el comando Python a ejecutar
            
        Returns:
            str: Respuesta del comando
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            print("❌ No hay conexión activa")
            return None
        
        try:
            self.serial_conn.write(b'\x03')
            time.sleep(0.1)
            
            self.serial_conn.reset_input_buffer()
            
            self.serial_conn.write((comando + '\r\n').encode())
            time.sleep(0.2)

            response = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
            return response
            
        except Exception as e:
            print(f"Error al enviar comando: {e}")
            return None
    
    def cargar_script(self, script_path):
        """
        Carga y ejecuta un script MicroPython en la Pico
        
        Args:
            script_path: Ruta al archivo .py a cargar
            
        Returns:
            bool: True si se cargó exitosamente
        """
        if not os.path.exists(script_path):
            print(f"No se encuentra el archivo: {script_path}")
            return False
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            print(f"Cargando script: {script_path}")
            
           
            self.serial_conn.write(b'\x03\x03')
            time.sleep(0.3)
            self.serial_conn.reset_input_buffer()
            
            self.serial_conn.write(b'\x05')
            time.sleep(0.2)
            
            response = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
            
            self.serial_conn.write(script_content.encode('utf-8'))
            time.sleep(0.2)
            
            self.serial_conn.write(b'\x04')
            time.sleep(0.8)
            
            response = self.serial_conn.read(self.serial_conn.in_waiting).decode('utf-8', errors='ignore')
            
            if response:
                print(f" Respuesta: {response[:200]}")
            
            print(f"Script cargado y ejecutado")
            return True
            
        except Exception as e:
            print(f"Error al cargar script: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def soft_reset(self):
        """Realiza un soft reset de la Pico (Ctrl+D)"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.write(b'\x04')
            time.sleep(1)
            print("Pico reiniciada")


def activar_alarma_pico(port=None, pico_instance=None):
    """
    Función auxiliar para activar la alarma en la Pico
    
    Args:
        port: Puerto COM opcional
        pico_instance: Instancia de PicoController ya conectada (opcional)
        
    Returns:
        bool: True si se activó correctamente
    """
    if pico_instance and pico_instance.serial_conn and pico_instance.serial_conn.is_open:
        pico = pico_instance
    else:
        pico = PicoController(port)
        if not pico.conectar():
            return False
    
    script_path = os.path.abspath("Sirena_Buzzer/main.py")
    resultado = pico.cargar_script(script_path)
    
    if pico_instance is None:
        pass
    
    return resultado


def desactivar_alarma_pico(port=None, pico_instance=None):
    """
    Función auxiliar para desactivar la alarma en la Pico
    
    Args:
        port: Puerto COM opcional
        pico_instance: Instancia de PicoController ya conectada (opcional)
        
    Returns:
        bool: True si se desactivó correctamente
    """
    if pico_instance and pico_instance.serial_conn and pico_instance.serial_conn.is_open:
        pico = pico_instance
    else:
        pico = PicoController(port)
        if not pico.conectar():
            return False
    
    script_path = os.path.abspath("Sirena_Off/main.py")
    resultado = pico.cargar_script(script_path)
    
    if pico_instance is None:
        pico.desconectar()
    
    return resultado


if __name__ == "__main__":
    print("=== Test de Raspberry Pi Pico ===")
    
    pico = PicoController()
    

    if pico.conectar():
        print("\n Activando alarma...")
        activar_alarma_pico(pico.port, pico_instance=pico)
        
        input("\nPresiona Enter para desactivar la alarma...")
        
        print("\n Desactivando alarma...")
        desactivar_alarma_pico(pico.port, pico_instance=pico)
        
        pico.desconectar()
