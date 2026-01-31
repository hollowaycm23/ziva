import logging
import subprocess
from typing import List, Dict, Optional
from agent.tools import ziva_tool

logger = logging.getLogger("BluetoothTools")


@ziva_tool
def list_bluetooth_devices() -> str:
    """
    Lista todos os dispositivos Bluetooth pareados.

    Returns:
        str: Lista de dispositivos formatada
    """
    try:
        # Usar bluetoothctl para listar dispositivos
        result = subprocess.run(
            ['bluetoothctl', 'devices'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return f"Erro ao listar dispositivos: {result.stderr}"

        devices = result.stdout.strip().split('\n')

        if not devices or devices == ['']:
            return "Nenhum dispositivo Bluetooth pareado encontrado."

        output = "**Dispositivos Bluetooth Pareados:**\n\n"
        for device in devices:
            if device.startswith('Device'):
                # Formato: Device XX:XX:XX:XX:XX:XX Nome
                parts = device.split(maxsplit=2)
                if len(parts) >= 3:
                    mac = parts[1]
                    name = parts[2]

                    # Verificar se está conectado
                    status = _check_device_connection(mac)
                    status_icon = "🟢" if status else "⚪"

                    output += f"{status_icon} **{name}**\n"
                    output += f"   MAC: `{mac}`\n"
                    output += f"   Status: {
                        'Conectado' if status else 'Desconectado'}\n\n"

        return output

    except subprocess.TimeoutExpired:
        return "Timeout ao listar dispositivos Bluetooth"
    except Exception as e:
        logger.error(f"Erro ao listar dispositivos Bluetooth: {e}")
        return f"Erro: {e}"


@ziva_tool
def connect_bluetooth_device(device_mac: str) -> str:
    """
    Conecta a um dispositivo Bluetooth pareado.

    Args:
        device_mac: Endereço MAC do dispositivo (ex: "XX:XX:XX:XX:XX:XX")

    Returns:
        str: Status da conexão
    """
    try:
        # Conectar usando bluetoothctl
        result = subprocess.run(
            ['bluetoothctl', 'connect', device_mac],
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + result.stderr

        if 'Connection successful' in output or 'Connected: yes' in output:
            return f"✅ Conectado com sucesso ao dispositivo {device_mac}"
        elif 'Failed to connect' in output:
            return f"❌ Falha ao conectar: {output}"
        else:
            return f"Status da conexão: {output}"

    except subprocess.TimeoutExpired:
        return f"Timeout ao tentar conectar a {device_mac}"
    except Exception as e:
        logger.error(f"Erro ao conectar dispositivo: {e}")
        return f"Erro: {e}"


@ziva_tool
def disconnect_bluetooth_device(device_mac: str) -> str:
    """
    Desconecta um dispositivo Bluetooth.

    Args:
        device_mac: Endereço MAC do dispositivo

    Returns:
        str: Status da desconexão
    """
    try:
        result = subprocess.run(
            ['bluetoothctl', 'disconnect', device_mac],
            capture_output=True,
            text=True,
            timeout=10
        )

        output = result.stdout + result.stderr

        if 'Successful disconnected' in output or 'Disconnected' in output:
            return f"✅ Desconectado com sucesso de {device_mac}"
        else:
            return f"Status: {output}"

    except Exception as e:
        logger.error(f"Erro ao desconectar dispositivo: {e}")
        return f"Erro: {e}"


@ziva_tool
def scan_bluetooth_devices(duration: int = 10) -> str:
    """
    Escaneia por novos dispositivos Bluetooth disponíveis.

    Args:
        duration: Duração do scan em segundos (default 10)

    Returns:
        str: Dispositivos encontrados
    """
    try:
        # Iniciar scan
        subprocess.run(
            ['bluetoothctl', 'scan', 'on'],
            capture_output=True,
            timeout=2
        )

        # Aguardar duração do scan
        import time
        time.sleep(min(duration, 30))

        # Parar scan
        subprocess.run(
            ['bluetoothctl', 'scan', 'off'],
            capture_output=True,
            timeout=2
        )

        # Listar dispositivos encontrados
        result = subprocess.run(
            ['bluetoothctl', 'devices'],
            capture_output=True,
            text=True,
            timeout=5
        )

        devices = result.stdout.strip().split('\n')

        if not devices or devices == ['']:
            return "Nenhum dispositivo encontrado durante o scan."

        output = f"**Dispositivos Bluetooth Encontrados (scan de {duration}s):**\n\n"
        for device in devices:
            if device.startswith('Device'):
                parts = device.split(maxsplit=2)
                if len(parts) >= 3:
                    mac = parts[1]
                    name = parts[2]
                    output += f"📱 **{name}**\n"
                    output += f"   MAC: `{mac}`\n\n"

        return output

    except Exception as e:
        logger.error(f"Erro ao escanear dispositivos: {e}")
        return f"Erro: {e}"


@ziva_tool
def bluetooth_device_info(device_mac: str) -> str:
    """
    Obtém informações detalhadas sobre um dispositivo Bluetooth.

    Args:
        device_mac: Endereço MAC do dispositivo

    Returns:
        str: Informações do dispositivo
    """
    try:
        result = subprocess.run(
            ['bluetoothctl', 'info', device_mac],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return f"Dispositivo {device_mac} não encontrado"

        info = result.stdout

        # Parsear informações relevantes
        output = f"**Informações do Dispositivo {device_mac}:**\n\n"

        for line in info.split('\n'):
            line = line.strip()
            if line.startswith('Name:'):
                output += f"📱 Nome: {line.split(':', 1)[1].strip()}\n"
            elif line.startswith('Alias:'):
                output += f"🏷️ Alias: {line.split(':', 1)[1].strip()}\n"
            elif line.startswith('Paired:'):
                paired = line.split(':', 1)[1].strip()
                output += f"🔗 Pareado: {paired}\n"
            elif line.startswith('Trusted:'):
                trusted = line.split(':', 1)[1].strip()
                output += f"✅ Confiável: {trusted}\n"
            elif line.startswith('Connected:'):
                connected = line.split(':', 1)[1].strip()
                icon = "🟢" if connected == "yes" else "⚪"
                output += f"{icon} Conectado: {connected}\n"
            elif line.startswith('UUID:'):
                uuid_info = line.split(':', 1)[1].strip()
                if 'Audio' in uuid_info or 'Headset' in uuid_info:
                    output += f"🎧 Tipo: Áudio\n"
                elif 'Input' in uuid_info or 'HID' in uuid_info:
                    output += f"⌨️ Tipo: Entrada (teclado/mouse)\n"

        return output

    except Exception as e:
        logger.error(f"Erro ao obter info do dispositivo: {e}")
        return f"Erro: {e}"


@ziva_tool
def bluetooth_adapter_status() -> str:
    """
    Verifica o status do adaptador Bluetooth.

    Returns:
        str: Status do adaptador
    """
    try:
        result = subprocess.run(
            ['bluetoothctl', 'show'],
            capture_output=True,
            text=True,
            timeout=5
        )

        info = result.stdout

        output = "**Status do Adaptador Bluetooth:**\n\n"

        for line in info.split('\n'):
            line = line.strip()
            if line.startswith('Name:'):
                output += f"📡 Nome: {line.split(':', 1)[1].strip()}\n"
            elif line.startswith('Powered:'):
                powered = line.split(':', 1)[1].strip()
                icon = "🟢" if powered == "yes" else "🔴"
                output += f"{icon} Ligado: {powered}\n"
            elif line.startswith('Discoverable:'):
                discoverable = line.split(':', 1)[1].strip()
                output += f"👁️ Visível: {discoverable}\n"
            elif line.startswith('Pairable:'):
                pairable = line.split(':', 1)[1].strip()
                output += f"🔗 Pareável: {pairable}\n"

        return output

    except Exception as e:
        logger.error(f"Erro ao verificar adaptador: {e}")
        return f"Erro: {e}"


def _check_device_connection(device_mac: str) -> bool:
    """Verifica se um dispositivo está conectado."""
    try:
        result = subprocess.run(
            ['bluetoothctl', 'info', device_mac],
            capture_output=True,
            text=True,
            timeout=3
        )

        return 'Connected: yes' in result.stdout
    except BaseException:
        return False
