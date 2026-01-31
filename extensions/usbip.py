import logging
import subprocess
from typing import List, Dict, Optional
from agent.tools import ziva_tool

logger = logging.getLogger("USBIPTools")


@ziva_tool
def list_local_usb_devices() -> str:
    """
    Lista dispositivos USB locais disponíveis para compartilhamento via USB/IP.

    Returns:
        str: Lista de dispositivos USB
    """
    try:
        # Listar dispositivos USB usando lsusb
        result = subprocess.run(
            ['lsusb'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return "Erro ao listar dispositivos USB"

        devices = result.stdout.strip().split('\n')

        if not devices:
            return "Nenhum dispositivo USB encontrado"

        output = "**Dispositivos USB Locais:**\n\n"
        for device in devices:
            # Formato: Bus 001 Device 002: ID 1234:5678 Nome do Dispositivo
            if 'Bus' in device:
                parts = device.split(':', 1)
                if len(parts) >= 2:
                    bus_info = parts[0]
                    device_info = parts[1].strip()

                    output += f"🔌 {device_info}\n"
                    output += f"   {bus_info}\n\n"

        return output

    except Exception as e:
        logger.error(f"Erro ao listar USB: {e}")
        return f"Erro: {e}"


@ziva_tool
def list_usbip_shared_devices() -> str:
    """
    Lista dispositivos USB compartilhados via USB/IP.

    Returns:
        str: Dispositivos compartilhados
    """
    try:
        result = subprocess.run(
            ['usbip', 'list', '-l'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return "Nenhum dispositivo compartilhado ou USB/IP não instalado"

        output = result.stdout.strip()

        if not output or 'usbip' in output.lower() and 'list' in output.lower():
            return "Nenhum dispositivo USB compartilhado no momento"

        return f"**Dispositivos USB Compartilhados:**\n\n{output}"

    except FileNotFoundError:
        return "USB/IP não está instalado. Execute: sudo apt install usbip"
    except Exception as e:
        logger.error(f"Erro ao listar USB/IP: {e}")
        return f"Erro: {e}"


@ziva_tool
def share_usb_device(bus_id: str) -> str:
    """
    Compartilha um dispositivo USB via USB/IP.

    Args:
        bus_id: ID do barramento USB (ex: "1-1", "2-3.1")

    Returns:
        str: Status do compartilhamento
    """
    try:
        # Bind do dispositivo
        result = subprocess.run(
            ['sudo', 'usbip', 'bind', '-b', bus_id],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return f"✅ Dispositivo {bus_id} compartilhado com sucesso via USB/IP"
        else:
            return f"❌ Erro ao compartilhar: {result.stderr}"

    except Exception as e:
        logger.error(f"Erro ao compartilhar USB: {e}")
        return f"Erro: {e}"


@ziva_tool
def unshare_usb_device(bus_id: str) -> str:
    """
    Para de compartilhar um dispositivo USB.

    Args:
        bus_id: ID do barramento USB

    Returns:
        str: Status
    """
    try:
        result = subprocess.run(
            ['sudo', 'usbip', 'unbind', '-b', bus_id],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return f"✅ Dispositivo {bus_id} não está mais compartilhado"
        else:
            return f"Status: {result.stderr}"

    except Exception as e:
        logger.error(f"Erro ao parar compartilhamento: {e}")
        return f"Erro: {e}"


@ziva_tool
def list_remote_usbip_devices(remote_host: str) -> str:
    """
    Lista dispositivos USB disponíveis em um servidor USB/IP remoto.

    Args:
        remote_host: IP ou hostname do servidor USB/IP

    Returns:
        str: Dispositivos disponíveis
    """
    try:
        result = subprocess.run(
            ['usbip', 'list', '-r', remote_host],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return f"Erro ao conectar em {remote_host}: {result.stderr}"

        output = result.stdout.strip()

        if not output:
            return f"Nenhum dispositivo disponível em {remote_host}"

        return f"**Dispositivos USB em {remote_host}:**\n\n{output}"

    except Exception as e:
        logger.error(f"Erro ao listar remoto: {e}")
        return f"Erro: {e}"


@ziva_tool
def attach_remote_usb(remote_host: str, bus_id: str) -> str:
    """
    Conecta a um dispositivo USB remoto via USB/IP.

    Args:
        remote_host: IP ou hostname do servidor
        bus_id: ID do dispositivo remoto

    Returns:
        str: Status da conexão
    """
    try:
        result = subprocess.run(
            ['sudo', 'usbip', 'attach', '-r', remote_host, '-b', bus_id],
            capture_output=True,
            text=True,
            timeout=15
        )

        if result.returncode == 0:
            return f"✅ Conectado ao dispositivo {bus_id} de {remote_host}"
        else:
            return f"❌ Erro ao conectar: {result.stderr}"

    except Exception as e:
        logger.error(f"Erro ao conectar USB remoto: {e}")
        return f"Erro: {e}"


@ziva_tool
def detach_remote_usb(port: str) -> str:
    """
    Desconecta de um dispositivo USB remoto.

    Args:
        port: Número da porta USB/IP (ex: "00", "01")

    Returns:
        str: Status
    """
    try:
        result = subprocess.run(
            ['sudo', 'usbip', 'detach', '-p', port],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return f"✅ Desconectado da porta {port}"
        else:
            return f"Status: {result.stderr}"

    except Exception as e:
        logger.error(f"Erro ao desconectar: {e}")
        return f"Erro: {e}"


@ziva_tool
def usbip_status() -> str:
    """
    Verifica status das conexões USB/IP ativas.

    Returns:
        str: Status das conexões
    """
    try:
        result = subprocess.run(
            ['usbip', 'port'],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout.strip()

        if not output or 'Port' not in output:
            return "Nenhuma conexão USB/IP ativa"

        return f"**Conexões USB/IP Ativas:**\n\n{output}"

    except FileNotFoundError:
        return "USB/IP não instalado"
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        return f"Erro: {e}"
