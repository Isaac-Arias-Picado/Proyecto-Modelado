"""
Script MicroPython para Raspberry Pi Pico
Activa un buzzer/sirena usando un Timer
Pin GPIO: 0 (Buzzer pasivo)
"""
from machine import Pin, PWM, Timer
import time

# Configurar pin del buzzer (Pin 0)
buzzer_pin = Pin(0, Pin.OUT)
buzzer = PWM(buzzer_pin)
buzzer.freq(2000)

# Variable global para controlar el estado
estado = True

def toggle_buzzer(timer):
    """Función que se ejecuta periódicamente para alternar el buzzer"""
    global estado
    if estado:
        buzzer.duty_u16(32768)  # Encender
    else:
        buzzer.duty_u16(0)  # Apagar
    estado = not estado

# Crear un timer que ejecute toggle_buzzer cada 500ms
timer = Timer()
timer.init(freq=2, mode=Timer.PERIODIC, callback=toggle_buzzer)

print("🔔 Alarma activada con Timer")
