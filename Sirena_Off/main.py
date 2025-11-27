"""
Desactiva alarma con soft reset
"""
from machine import Pin, PWM
import machine

# Apagar buzzer
try:
    p = Pin(0, Pin.OUT)
    pwm = PWM(p)
    pwm.duty_u16(0)
    pwm.deinit()
    p.value(0)
except:
    pass

# Soft reset para detener timers
machine.soft_reset()
