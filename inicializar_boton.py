"""
Script de inicialización del botón físico
Registra el botón de pánico como dispositivo en el sistema
Ejecutar una vez después de iniciar sesión
"""
from data_logic import SecurityLogic

def inicializar_boton_panico():
    """Registra el botón de pánico físico como dispositivo"""
    logic = SecurityLogic()

    if not logic.usuario_actual:
        print("No hay usuario autenticado")
        print("Primero inicia sesión en la aplicación")
        return False
    
    try:
        boton_existente = logic.obtener_dispositivo_por_serie("PICO-BOTON-001")
        
        if boton_existente:
            print("El botón físico ya está registrado")
            print(f"   Serie: {boton_existente.get('serie')}")
            print(f"   Nombre: {boton_existente.get('nombre')}")
            print(f"   Estado: {boton_existente.get('estado')}")
            print(f"   Modo: {boton_existente.get('modo')}")
            return True
        
        logic.registrar_dispositivo(
            serie="PICO-BOTON-001",
            tipo="Botón de Pánico",
            nombre="Botón Físico Pico",
            ubicacion="Raspberry Pi Pico"
        )
        
        print("Botón físico registrado exitosamente")
        print("   Serie: PICO-BOTON-001")
        print("   Tipo: Botón de Pánico")
        print("   Estado: Inactivo (por defecto)")
        print()
        print("💡ara activar el botón:")
        print("   1. Ve a la pestaña 'Dispositivos' en la aplicación")
        print("   2. Busca 'Botón Físico Pico'")
        print("   3. Cambia el modo a 'Activo'")
        print("   4. Cambia el estado a 'Activo'")
        
        return True
        
    except Exception as e:
        print(f"Error al registrar botón: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("INICIALIZACIÓN DE BOTÓN DE PÁNICO FÍSICO")
    print("=" * 70)
    print()
    
    inicializar_boton_panico()
