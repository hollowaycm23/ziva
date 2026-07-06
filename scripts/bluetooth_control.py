#!/usr/bin/env python3
try:
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop
    import gobject
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False

    class DBusGMainLoop:
        def __init__(self, **kwargs): pass

    def dbus_SystemBus(): return None
    sys_modules_mock = True

import sys

# Initialize DBus
try:
    if DBUS_AVAILABLE:
        DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        dev_manager = bus.get_object('org.bluez', '/org/bluez/hci0')
        dev_manager_interface = dbus.Interface(
            dev_manager, 'org.freedesktop.DBus.Properties')
    else:
        raise ImportError("DBus modules not installed")
except Exception as e:
    # If not running on Linux/DBus environment, may fail.
    # Just printing warning as this is a script.
    print(f"Warning: Failed to initialize DBus: {e}")
    bus = None
    dev_manager_interface = None


def list_paired_devices():
    if not dev_manager_interface:
        return
    try:
        paired_devices = dev_manager_interface.Get(
            'org.bluez.Adapter1', 'PairedDevices')
        for device in paired_devices:
            print(device)
    except Exception as e:
        print(f"Error listing devices: {e}")


def connect_device(address):
    if not bus:
        return
    try:
        dev_path = '/org/bluez/hci0/dev_' + address.replace(':', '_').upper()
        dev = bus.get_object('org.bluez', dev_path)
        dev_interface = dbus.Interface(dev, 'org.bluez.Device1')
        dev_interface.Connect()
        print(f"Connecting to {address}...")
    except Exception as e:
        print(f"Error connecting to {address}: {e}")


def disconnect_device(address):
    if not bus:
        return
    try:
        dev_path = '/org/bluez/hci0/dev_' + address.replace(':', '_').upper()
        dev = bus.get_object('org.bluez', dev_path)
        dev_interface = dbus.Interface(dev, 'org.bluez.Device1')
        dev_interface.Disconnect()
        print(f"Disconnecting from {address}...")
    except Exception as e:
        print(f"Error disconnecting from {address}: {e}")


def scan_devices():
    if not dev_manager_interface:
        return
    try:
        dev_manager_interface.Set('org.bluez.Adapter1', 'Discovering', True)
        print('Scanning for devices...')
        loop = gobject.MainLoop()

        # Em um loop real, precisaríamos de um callback para paralisar a busca.
        # Aqui vamos apenas simular um wait ou deixar rodando até user interromper.
        # Simplificação para manter funcionalidade original
        while True:
            paired_devices = dev_manager_interface.Get(
                'org.bluez.Adapter1', 'PairedDevices')
            if len(paired_devices) > 0:
                break
            # gobject iteration pode bloquear. Cuidado.
            # loop.run() seria o correto com callbacks.
            loop.get_context().iteration(True)

        dev_manager_interface.Set('org.bluez.Adapter1', 'Discovering', False)
    except Exception as e:
        print(f"Scan error: {e}")


def check_connection(address):
    if not bus:
        return
    try:
        dev_path = '/org/bluez/hci0/dev_' + address.replace(':', '_').upper()
        dev = bus.get_object('org.bluez', dev_path)
        dev_interface = dbus.Interface(dev, 'org.freedesktop.DBus.Properties')
        connected = dev_interface.Get('org.bluez.Device1', 'Connected')
        print(f'Device {address} is connected: {connected}')
    except Exception as e:
        print(f"Error checking connection for {address}: {e}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python bluetooth_control.py [list|connect <address>|disconnect <address>|scan|check <address>]')
        sys.exit(1)

    command = sys.argv[1]

    if bus is None:
        print("DBus system bus not available. Exiting.")
        sys.exit(1)

    if command == 'list':
        list_paired_devices()
    elif command == 'connect' and len(sys.argv) > 2:
        connect_device(sys.argv[2])
    elif command == 'disconnect' and len(sys.argv) > 2:
        disconnect_device(sys.argv[2])
    elif command == 'scan':
        scan_devices()
    elif command == 'check' and len(sys.argv) > 2:
        check_connection(sys.argv[2])
    else:
        print('Invalid command or missing arguments')
