""
"""
HEX Protocol Parser
Sistema de protocolo interno para agentes autônomos
Inspirado no HEX-COM da Annika, expandido para Ziva
"""

import re
import logging
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HEXProtocol")


class HEXCommand(Enum):
    """Comandos disponíveis no protocolo HEX"""
    READ = "READ"
    SAVE = "SAVE"
    EXEC = "EXEC"
    SEARCH = "SEARCH"
    THINK = "THINK"
    TOOL = "TOOL"
    QUERY = "QUERY"


@dataclass
class HEXMessage:
    """Representa uma mensagem HEX parseada"""
    command: HEXCommand
    args: list
    raw: str

    def __str__(self):
        return f"[HEX:{self.command.value}:{':'.join(self.args)}]"


class HEXProtocolParser:
    """
    Parser para protocolo HEX
    """

    HEX_PATTERN = r'[[HEX:(\w+):([^\]]+)\]]'

    @staticmethod
    def parse(text: str) -> Optional[HEXMessage]:
        """
        Parse texto procurando por comandos HEX
        """
        match = re.search(HEXProtocolParser.HEX_PATTERN, text)

        if not match:
            return None

        try:
            command_str = match.group(1).upper()
            args_str = match.group(2)

            try:
                command = HEXCommand[command_str]
            except KeyError:
                logger.warning(f"⚠️ Unknown HEX command: {command_str}")
                return None

            args = [arg.strip() for arg in args_str.split(':')]

            hex_msg = HEXMessage(
                command=command,
                args=args,
                raw=match.group(0)
            )

            logger.debug(f"📨 Parsed HEX: {hex_msg}")
            return hex_msg

        except Exception as e:
            logger.error(f"❌ Error parsing HEX command: {e}")
            return None

    @staticmethod
    def extract_all(text: str) -> list[HEXMessage]:
        """
        Extrai todos os comandos HEX de um texto
        """
        messages = []

        for match in re.finditer(HEXProtocolParser.HEX_PATTERN, text):
            try:
                command_str = match.group(1).upper()
                args_str = match.group(2)

                command = HEXCommand[command_str]
                args = [arg.strip() for arg in args_str.split(':')]

                messages.append(HEXMessage(
                    command=command,
                    args=args,
                    raw=match.group(0)
                ))
            except (KeyError, Exception) as e:
                logger.warning(f"⚠️ Skipping invalid HEX command: {e}")
                continue

        return messages

    @staticmethod
    def remove_hex_commands(text: str) -> str:
        """
        Remove comandos HEX do texto, deixando apenas resposta
        """
        return re.sub(HEXProtocolParser.HEX_PATTERN, '', text).strip()

    @staticmethod
    def validate(hex_msg: HEXMessage) -> Tuple[bool, Optional[str]]:
        """
        Valida se comando HEX tem argumentos corretos
        """
        command = hex_msg.command
        args = hex_msg.args

        validations = {
            HEXCommand.READ: lambda a: len(a) >= 1,
            HEXCommand.SAVE: lambda a: len(a) >= 2,
            HEXCommand.EXEC: lambda a: len(a) >= 1,
            HEXCommand.SEARCH: lambda a: len(a) >= 1,
            HEXCommand.THINK: lambda a: len(a) >= 1,
            HEXCommand.TOOL: lambda a: len(a) >= 2,
            HEXCommand.QUERY: lambda a: len(a) >= 1,
        }

        validator = validations.get(command)
        if not validator:
            return False, f"No validator for {command}"

        if not validator(args):
            return False, f"Invalid arguments for {command}: {args}"

        return True, None


class HEXCommandBuilder:
    """Helper para construir comandos HEX"""

    @staticmethod
    def read(term: str) -> str:
        return f"[HEX:READ:{term}]"

    @staticmethod
    def save(quadrant: str, text: str) -> str:
        return f"[HEX:SAVE:{quadrant}:{text}]"

    @staticmethod
    def exec_cmd(command: str) -> str:
        return f"[HEX:EXEC:{command}]"

    @staticmethod
    def search(query: str) -> str:
        return f"[HEX:SEARCH:{query}]"

    @staticmethod
    def think(thought: str) -> str:
        return f"[HEX:THINK:{thought}]"

    @staticmethod
    def tool(tool_name: str, *args) -> str:
        args_str = ':'.join(str(arg) for arg in args)
        return f"[HEX:TOOL:{tool_name}:{args_str}]"


if __name__ == "__main__":
    print("🧪 HEX Protocol Parser - Test")
    print("=" * 60)

    print("\n1️⃣ Parse READ command:")
    text1 = "Vou buscar na memória: [HEX:READ:otimizações de rede]"
    msg1 = HEXProtocolParser.parse(text1)
    if msg1:
        print(f"   Command: {msg1.command}")
        print(f"   Args: {msg1.args}")
        print(f"   Valid: {HEXProtocolParser.validate(msg1)}")

    print("\n2️⃣ Parse SAVE command:")
    text2 = "[HEX:SAVE:Q2_USER_DATA:Usuário prefere Python]"
    msg2 = HEXProtocolParser.parse(text2)
    if msg2:
        print(f"   Command: {msg2.command}")
        print(f"   Args: {msg2.args}")
        print(f"   Valid: {HEXProtocolParser.validate(msg2)}")

    print("\n3️⃣ Extract multiple commands:")
    text3 = """
    [HEX:THINK:Preciso verificar memória]
    [HEX:READ:último projeto]
    Vou responder agora.
    """
    msgs3 = HEXProtocolParser.extract_all(text3)
    print(f"   Found {len(msgs3)} commands:")
    for msg in msgs3:
        print(f"     - {msg.command}: {msg.args}")

    print("\n4️⃣ Remove HEX commands:")
    text4 = "Primeiro [HEX:READ:dados] depois respondo: A resposta é 42"
    clean4 = HEXProtocolParser.remove_hex_commands(text4)
    print(f"   Original: {text4}")
    print(f"   Cleaned: {clean4}")

    print("\n5️⃣ Command Builder:")
    cmd_read = HEXCommandBuilder.read("otimizações")
    cmd_save = HEXCommandBuilder.save(
        "Q5_SKILLS", "Use gradient checkpointing")
    cmd_tool = HEXCommandBuilder.tool("calculator", "2+2")
    print(f"   READ: {cmd_read}")
    print(f"   SAVE: {cmd_save}")
    print(f"   TOOL: {cmd_tool}")

    print("\n✅ Testes concluídos!")