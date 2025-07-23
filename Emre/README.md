# STM32 Traffic Light Simulator

A modular Python application for simulating and controlling traffic lights with STM32 communication.

## Project Structure

The application has been modularized into the following components:

### Core Modules

- **`main_modular.py`** - Main entry point of the application
- **`gui.py`** - User interface components and main application window
- **`traffic_controller.py`** - Traffic light control logic and state management
- **`serial_comm.py`** - Serial communication handling with STM32 device
- **`utils.py`** - Utility functions (Modbus CRC, port selection dialog)

### Legacy Files

- **`main.py`** - Original monolithic version (kept for reference)

### Configuration

- **`requirements.txt`** - Python package dependencies

## Features

- **Real-time Communication**: Serial communication with STM32 devices using Modbus protocol
- **Visual Interface**: Interactive GUI showing traffic lights and car animations
- **Manual Override**: Buttons to manually control traffic light states
- **Logging**: Real-time logging of all communication events
- **Port Management**: Automatic detection and selection of available COM ports
- **Timer Display**: Shows remaining time for current light state

## Installation

1. Install required dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python main_modular.py
   ```

## Module Dependencies

```
main_modular.py
└── gui.py
    ├── traffic_controller.py
    │   └── serial_comm.py
    │       └── utils.py
    └── utils.py (for port selection)
```

## Usage

1. Select a COM port from the dropdown
2. Click "Connect" to establish communication
3. Monitor traffic light states in real-time
4. Use override buttons to manually control lights
5. View communication logs in the bottom panel

## Communication Protocol

The application uses a custom 8-byte Modbus protocol:

- **RED light signal**: `01 02 03 04 05 06 [CRC]`
- **GREEN light signal**: `06 05 04 03 02 01 [CRC]`
- **Override commands**: 8-byte packets with 3rd byte indicating state (0x00=RED, 0x01=GREEN)

## Modular Design Benefits

- **Separation of Concerns**: Each module has a specific responsibility
- **Maintainability**: Easier to modify individual components
- **Testability**: Modules can be tested independently
- **Reusability**: Components can be reused in other projects
- **Readability**: Cleaner, more organized code structure
