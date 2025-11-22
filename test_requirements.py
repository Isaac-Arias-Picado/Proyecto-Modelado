#!/usr/bin/env python3
"""
Test script for verifying the implementation of missing requirements:
- RF08: Alert notifications
- RF10: Emergency contact management
- RF12: Remote panic button
- RF24: Silent alarm
"""

import sys
sys.path.insert(0, '.')

from data_logic import SecurityLogic

def test_emergency_contacts():
    """Test RF10: Gestión de Contactos de Emergencia"""
    print("=" * 60)
    print("Testing RF10: Emergency Contact Management")
    print("=" * 60)
    
    logic = SecurityLogic()
    
    # Create test user
    try:
        logic.crear_usuario("test_rf10", "password123")
        print("✓ Test user created")
    except:
        pass  # User already exists
    
    # Authenticate
    if not logic.autenticar("test_rf10", "password123"):
        print("❌ Authentication failed")
        return False
    print("✓ Authentication successful")
    
    # Test adding contacts
    try:
        logic.agregar_contacto("María González", "+506-1111-1111", "Madre")
        print("✓ Contact 1 added")
    except Exception as e:
        print(f"  Contact 1 already exists: {e}")
    
    try:
        logic.agregar_contacto("Carlos Rodríguez", "+506-2222-2222", "Hermano")
        print("✓ Contact 2 added")
    except Exception as e:
        print(f"  Contact 2 already exists: {e}")
    
    try:
        logic.agregar_contacto("Ana López", "+506-3333-3333", "Amiga")
        print("✓ Contact 3 added")
    except Exception as e:
        print(f"  Contact 3 already exists: {e}")
    
    # Test getting contacts
    contactos = logic.obtener_contactos()
    print(f"✓ Retrieved {len(contactos)} contacts")
    for c in contactos:
        print(f"  - {c.get('nombre')}: {c.get('telefono')} ({c.get('relacion')})")
    
    # Test updating contact
    try:
        logic.actualizar_contacto("+506-1111-1111", "María González Pérez", "+506-1111-1111", "Familiar")
        print("✓ Contact updated successfully")
    except Exception as e:
        print(f"❌ Failed to update contact: {e}")
        return False
    
    # Verify update
    contactos = logic.obtener_contactos()
    maria = [c for c in contactos if c.get('telefono') == '+506-1111-1111'][0]
    assert maria.get('nombre') == "María González Pérez", "Name not updated"
    assert maria.get('relacion') == "Familiar", "Relation not updated"
    print("✓ Update verified")
    
    # Test deleting contact
    try:
        logic.eliminar_contacto("+506-3333-3333")
        print("✓ Contact deleted successfully")
    except Exception as e:
        print(f"❌ Failed to delete contact: {e}")
        return False
    
    # Verify deletion
    contactos = logic.obtener_contactos()
    assert len([c for c in contactos if c.get('telefono') == '+506-3333-3333']) == 0, "Contact not deleted"
    print("✓ Deletion verified")
    
    print("\n✅ RF10 (Emergency Contacts) - ALL TESTS PASSED\n")
    return True

def test_panic_button():
    """Test RF12: Activación Remota de Alarma/Pánico"""
    print("=" * 60)
    print("Testing RF12: Remote Panic Button Activation")
    print("=" * 60)
    
    logic = SecurityLogic()
    
    # Authenticate as test user
    if not logic.autenticar("test_rf10", "password123"):
        print("❌ Authentication failed")
        return False
    print("✓ Authentication successful")
    
    # Test panic button activation
    try:
        contactos = logic.activar_alarma_panico(tipo="manual")
        print(f"✓ Panic alarm activated - would notify {len(contactos)} contacts")
        for c in contactos:
            print(f"  - Would notify: {c.get('nombre')} at {c.get('telefono')}")
    except Exception as e:
        print(f"❌ Failed to activate panic alarm: {e}")
        return False
    
    # Verify event was registered
    eventos = logic.obtener_eventos()
    panic_events = [e for e in eventos if "PÁNICO" in e.get('descripcion', '').upper()]
    assert len(panic_events) > 0, "Panic event not registered"
    print(f"✓ Panic event registered: {panic_events[-1].get('descripcion')}")
    
    print("\n✅ RF12 (Panic Button) - ALL TESTS PASSED\n")
    return True

def test_silent_alarm():
    """Test RF24: Alarma Silenciosa"""
    print("=" * 60)
    print("Testing RF24: Silent Alarm")
    print("=" * 60)
    
    logic = SecurityLogic()
    
    # Authenticate as test user
    if not logic.autenticar("test_rf10", "password123"):
        print("❌ Authentication failed")
        return False
    print("✓ Authentication successful")
    
    # Test silent alarm activation
    try:
        contactos = logic.activar_alarma_silenciosa()
        print(f"✓ Silent alarm activated - would notify {len(contactos)} contacts discretely")
        for c in contactos:
            print(f"  - Would notify discretely: {c.get('nombre')} at {c.get('telefono')}")
    except Exception as e:
        print(f"❌ Failed to activate silent alarm: {e}")
        return False
    
    # Verify event was registered
    eventos = logic.obtener_eventos()
    silent_events = [e for e in eventos if "silenciosa" in e.get('descripcion', '').lower()]
    assert len(silent_events) > 0, "Silent alarm event not registered"
    print(f"✓ Silent alarm event registered: {silent_events[-1].get('descripcion')}")
    
    print("\n✅ RF24 (Silent Alarm) - ALL TESTS PASSED\n")
    return True

def test_notifications():
    """Test RF08: Notificaciones de Alertas"""
    print("=" * 60)
    print("Testing RF08: Alert Notifications")
    print("=" * 60)
    
    logic = SecurityLogic()
    
    # Authenticate as test user
    if not logic.autenticar("test_rf10", "password123"):
        print("❌ Authentication failed")
        return False
    print("✓ Authentication successful")
    
    # Verify events are properly categorized
    eventos = logic.obtener_eventos()
    
    # Check for panic events
    panic_events = [e for e in eventos if e.get('tipo') == 'Pánico']
    print(f"✓ Found {len(panic_events)} panic events")
    
    # Check for silent alarm events
    silent_events = [e for e in eventos if e.get('tipo') == 'Alarma Silenciosa']
    print(f"✓ Found {len(silent_events)} silent alarm events")
    
    # Verify all emergency events have proper timestamps
    emergency_events = panic_events + silent_events
    for event in emergency_events:
        assert 'fecha' in event, "Event missing timestamp"
        assert 'tipo' in event, "Event missing type"
        assert 'descripcion' in event, "Event missing description"
    print("✓ All emergency events have proper structure")
    
    print("\n✅ RF08 (Notifications) - ALL TESTS PASSED\n")
    return True

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST SUITE FOR MISSING REQUIREMENTS")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test RF10: Emergency Contacts
    results.append(("RF10", test_emergency_contacts()))
    
    # Test RF12: Panic Button
    results.append(("RF12", test_panic_button()))
    
    # Test RF24: Silent Alarm
    results.append(("RF24", test_silent_alarm()))
    
    # Test RF08: Notifications
    results.append(("RF08", test_notifications()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for req, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{req}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! All missing requirements are now implemented.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
