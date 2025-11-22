# Sistema de Seguridad Doméstico

Sistema integral de seguridad para el hogar con gestión de dispositivos IoT, monitoreo en tiempo real, y sistema de emergencias.

## Características Principales

### Gestión de Dispositivos
- Registro y configuración de múltiples tipos de dispositivos
- Soporte para cámaras de seguridad, detectores de placas, sensores, y más
- Cambio de estado y modo por dispositivo
- Vista de estado general del sistema

### Monitoreo de Cámaras
- Detección automática de movimiento
- Captura y almacenamiento de imágenes
- Vista en vivo y galería de capturas
- Configuración de sensibilidad

### Detector de Placas
- Reconocimiento automático de matrículas
- Registro de placas autorizadas
- Alertas para placas no registradas
- Captura fotográfica de vehículos

### Sistema de Emergencias (NUEVO)
- **Gestión de contactos de emergencia** (RF10)
- **Botón de pánico remoto** (RF12)
- **Alarma silenciosa** (RF24)
- **Sistema de notificaciones** (RF08)

### Eventos y Alertas
- Registro completo de eventos del sistema
- Filtros avanzados por dispositivo, tipo, fecha
- Visualización en tiempo real
- Exportación de registros

## Requisitos del Sistema

### Software
- Python 3.8 o superior
- tkinter (incluido en Python estándar)

### Dependencias Python
```bash
pip install opencv-python-headless requests numpy pytesseract pillow
```

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/Isaac-Arias-Picado/Proyecto-Modelado.git
cd Proyecto-Modelado
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```
(Si no existe requirements.txt, instalar manualmente las dependencias listadas arriba)

3. Ejecutar la aplicación:
```bash
python3 visual.py
```

## Uso

### Primera Vez
1. Crear un usuario en la pantalla de login
2. Ingresar con las credenciales creadas
3. Registrar dispositivos en la pestaña "Dispositivos"
4. Configurar contactos de emergencia en "Contactos"

### Operación Normal
- **Estado General**: Vista resumen del sistema
- **Dispositivos**: Gestión de todos los dispositivos IoT
- **Eventos**: Historial y filtrado de eventos
- **Cámaras**: Monitoreo y control de cámaras
- **Detector Placas**: Gestión de detección de matrículas
- **Contactos**: Gestión de contactos de emergencia
- **🚨 Emergencia**: Activación de alarmas de pánico

## Nuevas Funcionalidades

Ver [NUEVAS_FUNCIONALIDADES.md](NUEVAS_FUNCIONALIDADES.md) para detalles sobre las características implementadas recientemente.

## Pruebas

Ejecutar el suite de pruebas:
```bash
python3 test_requirements.py
```

## Arquitectura

```
visual.py                 # Interfaz principal
data_logic.py            # Lógica de negocio y persistencia
CamaraModule.py          # Módulo de cámaras
DetectorPlacasModule.py  # Módulo de detección de placas
contacts_view.py         # Vista de contactos de emergencia (NUEVO)
panic_view.py            # Vista de emergencias (NUEVO)
devices_view.py          # Vista de dispositivos
cameras_view.py          # Vista de cámaras
plates_view.py           # Vista de detector de placas
database.json            # Base de datos local
```

## Seguridad

- Autenticación de usuario con contraseñas hasheadas (SHA-256)
- Validación de entrada en todos los formularios
- Confirmaciones para acciones críticas
- Sin vulnerabilidades detectadas por análisis estático (CodeQL)

## Requerimientos Funcionales Implementados

| ID | Descripción | Estado |
|----|-------------|--------|
| RF01-RF07 | Gestión de dispositivos y eventos | ✅ |
| RF08 | Notificaciones de alertas | ✅ |
| RF09 | Eliminación de eventos | ✅ |
| RF10 | Gestión de contactos de emergencia | ✅ |
| RF11 | Autenticación de usuario | ✅ |
| RF12 | Botón de pánico remoto | ✅ |
| RF13-RF16 | Reconocimiento de dispositivos, estado, capturas | ✅ |
| RF20 | Cámara de seguridad completa | ✅ |
| RF24 | Alarma silenciosa | ✅ |
| RF25 | Detector de placas | ✅ |

Ver documento de especificaciones para detalles de otros requerimientos.

## Contribuir

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto es parte de un trabajo académico.

## Contacto

Isaac Arias Picado - [@Isaac-Arias-Picado](https://github.com/Isaac-Arias-Picado)

Proyecto: [https://github.com/Isaac-Arias-Picado/Proyecto-Modelado](https://github.com/Isaac-Arias-Picado/Proyecto-Modelado)
