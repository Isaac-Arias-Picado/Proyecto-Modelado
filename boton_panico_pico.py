"""
Script MicroPython para Raspberry Pi Pico
Monitorea un botón físico para activar alarma de pánico
Pin GPIO: 14 (Botón con pull-up interno)
Pin GPIO: 0 (Buzzer)
Se comunica con el sistema Python via serial
"""
from machine import Pin, PWM, Timer, ADC, time_pulse_us
import time
import sys
import select


BOTON_PIN = 14  
BOTON_SILENCIOSO_PIN = 15 
BUZZER_PIN = 0
TRIG_PIN = 16
ECHO_PIN = 17
LED_SIMULADOR_PIN = 18
HUMO_PIN = 27
PUERTA_PIN = 1
SERVO_PIN = 2
LASER_PIN = 26

boton = Pin(BOTON_PIN, Pin.IN, Pin.PULL_UP)
boton_silencioso = Pin(BOTON_SILENCIOSO_PIN, Pin.IN, Pin.PULL_UP)
sensor_humo = ADC(HUMO_PIN)
sensor_puerta = Pin(PUERTA_PIN, Pin.IN, Pin.PULL_UP)
sensor_laser = ADC(LASER_PIN)

servo = PWM(Pin(SERVO_PIN))
servo.freq(50)

trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)
trig.value(0)

led_simulador = Pin(LED_SIMULADOR_PIN, Pin.OUT)
led_simulador.value(0)

buzzer_pin = Pin(BUZZER_PIN, Pin.OUT)
buzzer = PWM(buzzer_pin)
buzzer.freq(2000)
buzzer.duty_u16(0)

alarma_activa = False
timer_alarma = Timer()
estado_toggle = [False]

simulador_activo = False
ultimo_cambio_led = 0
patron_led = [200, 200, 200, 1000] # ON, OFF, ON, OFF (ms)
indice_patron = 0
estado_led = False

def medir_distancia():
    """Mide la distancia en cm usando HC-SR04"""
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    
    try:
        duration = time_pulse_us(echo, 1, 30000) # 30ms timeout
        if duration < 0: return None
        
        # Distancia en cm = (duration / 2) / 29.1
        dist = (duration / 2) / 29.1
        return dist
    except:
        return None

def toggle_buzzer(timer):
    """Alterna el buzzer para efecto de sirena"""
    if estado_toggle[0]:
        buzzer.duty_u16(32768)
    else:
        buzzer.duty_u16(0)
    estado_toggle[0] = not estado_toggle[0]

def activar_buzzer():
    """Activa solo el sonido de la alarma"""
    global alarma_activa
    if not alarma_activa:
        alarma_activa = True
        timer_alarma.init(freq=2, mode=Timer.PERIODIC, callback=toggle_buzzer)
        print(" Buzzer activado")

def desactivar_buzzer():
    """Desactiva el sonido de la alarma"""
    global alarma_activa
    if alarma_activa:
        alarma_activa = False
        timer_alarma.deinit()
        buzzer.duty_u16(0)
        print(" Buzzer desactivado")

def procesar_boton_panico():
    """Maneja la lógica del botón de pánico (sonoro)"""
    print("PANIC_BUTTON_PRESSED")

def procesar_boton_silencioso():
    """Maneja la lógica del botón silencioso"""
    print("SILENT_BUTTON_PRESSED")

def procesar_humo():
    """Maneja la detección de humo"""
    print("SMOKE_DETECTED")

def procesar_puerta():
    """Maneja la apertura de puerta"""
    print("DOOR_OPENED")

def activar_simulador():
    global simulador_activo
    simulador_activo = True
    print(" Simulador activado")

def desactivar_simulador():
    global simulador_activo
    simulador_activo = False
    led_simulador.value(0)
    print(" Simulador desactivado")

def mover_servo(angulo):
    """Mueve el servo al ángulo especificado (0-180)"""
    # Mapeo aproximado para SG90 (duty 1638-8192)
    duty = int(1638 + (angulo/180) * (8192-1638))
    servo.duty_u16(duty)

def abrir_cerradura():
    mover_servo(90)
    print(" Cerradura Abierta")

def cerrar_cerradura():
    mover_servo(0)
    print(" Cerradura Cerrada")

ultima_presion = 0
ultima_presion_silencioso = 0
ultima_deteccion_humo = 0
ultimo_estado_humo = -1
ultima_verificacion_humo = 0
ultimo_estado_puerta = -1
DEBOUNCE_MS = 300
ultima_medicion = 0
INTERVALO_MEDICION_MS = 500
DISTANCIA_UMBRAL_CM = 50  # Detectar movimiento si algo está a menos de 50cm

# Configuración Láser
# Asumiendo divisor de voltaje: 3.3V -> LDR -> PIN 26 -> 10k Resistor -> GND
# Luz (Láser) = Resistencia Baja = Voltaje Alto (~50000-65000)
# Oscuridad (Bloqueado) = Resistencia Alta = Voltaje Bajo (< 20000)
UMBRAL_LASER = 30000 
laser_bloqueado = False
ultima_lectura_laser = 0

# Configuración Humo Analógico
# Mayor humo = Mayor voltaje = Mayor valor ADC
# Ajustar este umbral según las lecturas en terminal
UMBRAL_HUMO = 13000 
humo_detectado_analog = False

print(" Sistema de botón de pánico iniciado")
print(f" Botón Pánico: GPIO {BOTON_PIN}, Botón Silencioso: GPIO {BOTON_SILENCIOSO_PIN}")
print(f" Sensor HC-SR04: Trig {TRIG_PIN}, Echo {ECHO_PIN}")
print(f" Simulador Presencia: GPIO {LED_SIMULADOR_PIN}")
print(f" Detector Humo (Analog): ADC {HUMO_PIN}")
print(f" Sensor Puerta: GPIO {PUERTA_PIN}")
print(f" Sensor Láser (LDR): ADC {LASER_PIN}")
print("Esperando comandos o presión de botones...")
time.sleep(1)

while True:
    if select.select([sys.stdin], [], [], 0)[0]:
        linea = sys.stdin.readline().strip()
        if linea == "ALARM_ON":
            activar_buzzer()
        elif linea == "ALARM_OFF":
            desactivar_buzzer()
        elif linea == "SIMULATOR_ON":
            activar_simulador()
        elif linea == "SIMULATOR_OFF":
            desactivar_simulador()
        elif linea == "LOCK_OPEN":
            abrir_cerradura()
        elif linea == "LOCK_CLOSE":
            cerrar_cerradura()
            
    tiempo_actual = time.ticks_ms()

    # Lógica del simulador de presencia (LED)
    if simulador_activo:
        if time.ticks_diff(tiempo_actual, ultimo_cambio_led) > patron_led[indice_patron]:
            ultimo_cambio_led = tiempo_actual
            estado_led = not estado_led
            led_simulador.value(1 if estado_led else 0)
            indice_patron = (indice_patron + 1) % len(patron_led)

    # Medir distancia periódicamente
    if time.ticks_diff(tiempo_actual, ultima_medicion) > INTERVALO_MEDICION_MS:
        ultima_medicion = tiempo_actual
        dist = medir_distancia()
        if dist is not None and dist < DISTANCIA_UMBRAL_CM:
            print("MOTION_DETECTED")

    if boton.value() == 0:
        if time.ticks_diff(tiempo_actual, ultima_presion) > DEBOUNCE_MS:
            ultima_presion = tiempo_actual
            procesar_boton_panico()
            while boton.value() == 0: time.sleep_ms(10)

    if boton_silencioso.value() == 0:
        if time.ticks_diff(tiempo_actual, ultima_presion_silencioso) > DEBOUNCE_MS:
            ultima_presion_silencioso = tiempo_actual
            procesar_boton_silencioso()
            while boton_silencioso.value() == 0: time.sleep_ms(10)
    
    # Lógica detector de humo Analógico (Verificación cada 500ms)
    if time.ticks_diff(tiempo_actual, ultima_verificacion_humo) > 500:
        ultima_verificacion_humo = tiempo_actual
        lectura_humo = sensor_humo.read_u16()
        
        # Enviar valor crudo para depuración
        print(f"SMOKE_VAL:{lectura_humo}")
        
        if lectura_humo > UMBRAL_HUMO:
            if not humo_detectado_analog:
                humo_detectado_analog = True
                print("SMOKE_DETECTED")
        else:
            humo_detectado_analog = False

    # Lógica sensor de puerta (Magnet Near=0, Magnet Far=1)
    val_puerta = sensor_puerta.value()
    if val_puerta != ultimo_estado_puerta:
        time.sleep_ms(50) # Debounce simple
        if sensor_puerta.value() == val_puerta:
            ultimo_estado_puerta = val_puerta
            if val_puerta == 0:
                # print("MAGNET_NEAR") # Silenciado por solicitud
                pass
            else:
                # print("MAGNET_FAR") # Silenciado por solicitud
                pass

    # Lógica Sensor Láser (LDR)
    # Se lee cada 200ms para no saturar
    if time.ticks_diff(tiempo_actual, ultima_lectura_laser) > 200:
        ultima_lectura_laser = tiempo_actual
        lectura = sensor_laser.read_u16()
        
        # Si el voltaje cae por debajo del umbral, significa que la luz se bloqueó
        if lectura < UMBRAL_LASER:
            if not laser_bloqueado:
                laser_bloqueado = True
                # print("LASER_BLOCKED") # Silenciado por solicitud
                pass
        else:
            if laser_bloqueado:
                laser_bloqueado = False
                # print("LASER_OK") # Silenciado por solicitud
                pass

    time.sleep_ms(50)
