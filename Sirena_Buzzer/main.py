"""
Script MicroPython para Raspberry Pi Pico
Activa un buzzer/sirena usando un Timer
Pin GPIO: 0 (Buzzer pasivo)
"""
from machine import Pin, PWM, Timer

# Configurar pin del buzzer (Pin 0)
buzzer_pin = Pin(0, Pin.OUT)
buzzer = PWM(buzzer_pin)
buzzer.freq(2000)

# Variable global para controlar el estado
estado = [True]  # Usar lista para modificar en callback

def toggle_buzzer(timer):
    """Función que se ejecuta periódicamente para alternar el buzzer"""
    if estado[0]:
        buzzer.duty_u16(32768)  # Encender (50% duty cycle)
    else:
        buzzer.duty_u16(0)  # Apagar
    estado[0] = not estado[0]

# Crear un timer que ejecute toggle_buzzer cada 500ms (2 Hz)
timer = Timer()
timer.init(freq=2, mode=Timer.PERIODIC, callback=toggle_buzzer)

print("🔔 Alarma activada con Timer")