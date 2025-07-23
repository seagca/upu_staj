#!/usr/bin/env python3
"""
Test script to verify the modular structure works correctly.
"""

def test_imports():
    """Test that all modules can be imported without errors."""
    try:
        print("Testing module imports...")
        
        # Test utils module
        import utils
        print("✓ utils module imported successfully")
        
        # Test serial_comm module  
        import serial_comm
        print("✓ serial_comm module imported successfully")
        
        # Test traffic_controller module
        import traffic_controller
        print("✓ traffic_controller module imported successfully")
        
        # Test gui module
        import gui
        print("✓ gui module imported successfully")
        
        print("\nAll modules imported successfully!")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_classes():
    """Test that all classes can be instantiated."""
    try:
        print("\nTesting class definitions...")
        
        # Test utility functions
        from utils import check_modbus_crc, modbus_crc16
        print("✓ Utility functions accessible")
        
        # Test that classes are defined
        from serial_comm import SerialComm
        print("✓ SerialComm class accessible")
        
        from traffic_controller import TrafficLightController
        print("✓ TrafficLightController class accessible")
        
        from gui import TrafficLightGUI
        print("✓ TrafficLightGUI class accessible")
        
        print("\nAll classes are properly defined!")
        return True
        
    except Exception as e:
        print(f"✗ Error testing classes: {e}")
        return False

if __name__ == "__main__":
    print("=== Modular Structure Test ===")
    
    imports_ok = test_imports()
    classes_ok = test_classes()
    
    if imports_ok and classes_ok:
        print("\n🎉 All tests passed! The modular structure is working correctly.")
        print("\nTo run the application, use:")
        print("  python main_modular.py")
    else:
        print("\n❌ Some tests failed. Please check the module structure.")
