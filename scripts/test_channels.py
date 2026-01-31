#!/usr/bin/env python3
"""
Script de Verificação de Canais de Comunicação Ziva <-> Gabrielle
Testa todos os canais: Binary (9000), API (8000), SSH, Tailscale
"""
import sys
import os
import socket
import subprocess
import requests
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurações
ZIVA_IP_TAILSCALE = "100.105.168.115"
GABRIELLE_IP_TAILSCALE = "100.114.201.84"
BINARY_PORT = 9000
API_PORT = 8000


class ChannelTester:
    def __init__(self):
        self.results = {}

    def test_binary_listener(self):
        """Testa se a porta 9000 está ouvindo (incoming)"""
        print("\n🔍 [1/6] Testando Binary Channel Listener (Port 9000)...")
        try:
            result = subprocess.run(
                ["ss", "-tuln"],
                capture_output=True,
                text=True
            )
            listening = "0.0.0.0:9000" in result.stdout

            if listening:
                print("   ✅ Porta 9000 está LISTENING em 0.0.0.0")
                self.results['binary_listener'] = 'PASS'
                return True
            else:
                print("   ❌ Porta 9000 NÃO está ouvindo")
                self.results['binary_listener'] = 'FAIL'
                return False
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            self.results['binary_listener'] = 'ERROR'
            return False

    def test_binary_connection(
            self, host=GABRIELLE_IP_TAILSCALE, port=BINARY_PORT):
        """Testa conexão TCP à porta binária de Gabrielle"""
        print(f"\n🔍 [2/6] Testando Binary Connection para {host}:{port}...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                print(f"   ✅ Porta {port} em {host} está ACESSÍVEL")
                self.results['binary_outgoing'] = 'PASS'
                return True
            else:
                print(
                    f"   ⚠️  Porta {port} em {host} está FECHADA ou INACESSÍVEL")
                self.results['binary_outgoing'] = 'FAIL'
                return False
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            self.results['binary_outgoing'] = 'ERROR'
            return False

    def test_api_endpoint(self):
        """Testa API HTTP na porta 8000"""
        print(f"\n🔍 [3/6] Testando API HTTP (Port {API_PORT})...")
        try:
            response = requests.get(f"http://localhost:{API_PORT}/", timeout=3)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ API respondeu: {data}")
                self.results['api_http'] = 'PASS'
                return True
            else:
                print(f"   ❌ API retornou status {response.status_code}")
                self.results['api_http'] = 'FAIL'
                return False
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            self.results['api_http'] = 'ERROR'
            return False

    def test_ssh_connection(self, host=GABRIELLE_IP_TAILSCALE):
        """Testa conexão SSH com Gabrielle"""
        print(f"\n🔍 [4/6] Testando SSH para {host}...")
        try:
            cmd = [
                "ssh",
                "-o", "ConnectTimeout=5",
                "-o", "StrictHostKeyChecking=no",
                f"holloway@{host}",
                "echo 'SSH_OK'"
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and "SSH_OK" in result.stdout:
                print(f"   ✅ SSH conectado com sucesso")
                self.results['ssh_tailscale'] = 'PASS'
                return True
            else:
                print(f"   ❌ SSH falhou: {result.stderr}")
                self.results['ssh_tailscale'] = 'FAIL'
                return False
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            self.results['ssh_tailscale'] = 'ERROR'
            return False

    def test_scp_transfer(self, host=GABRIELLE_IP_TAILSCALE):
        """Testa transferência SCP"""
        print(f"\n🔍 [5/6] Testando SCP File Transfer para {host}...")

        # Criar arquivo de teste
        test_file = "/tmp/ziva_channel_test.txt"
        with open(test_file, 'w') as f:
            f.write(f"Channel Test - {time.time()}")

        try:
            cmd = [
                "scp",
                "-o", "ConnectTimeout=5",
                "-o", "StrictHostKeyChecking=no",
                test_file,
                f"holloway@{host}:/tmp/"
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15)

            if result.returncode == 0:
                print(f"   ✅ SCP transfer bem-sucedido")
                self.results['scp_transfer'] = 'PASS'

                # Limpar arquivo remoto
                subprocess.run([
                    "ssh", "-o", "ConnectTimeout=3", "-o", "StrictHostKeyChecking=no",
                    f"holloway@{host}", "rm -f /tmp/ziva_channel_test.txt"
                ], capture_output=True)

                return True
            else:
                print(f"   ❌ SCP falhou: {result.stderr}")
                self.results['scp_transfer'] = 'FAIL'
                return False
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            self.results['scp_transfer'] = 'ERROR'
            return False
        finally:
            # Limpar arquivo local
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_connection_manager(self):
        """Testa o ConnectionManager"""
        print(f"\n🔍 [6/6] Testando ConnectionManager (Failover Logic)...")
        try:
            from core.connection_manager import ConnectionManager

            cm = ConnectionManager(
                target_host=GABRIELLE_IP_TAILSCALE,
                fallback_ip="192.168.1.8"
            )

            is_connected = cm.check_connectivity()
            active = cm.active_channel

            if is_connected:
                print(
                    f"   ✅ ConnectionManager estabeleceu conexão via: {active}")
                self.results['connection_manager'] = f'PASS ({active})'
                return True
            else:
                print(f"   ❌ ConnectionManager falhou em todos os canais")
                self.results['connection_manager'] = 'FAIL'
                return False
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            self.results['connection_manager'] = 'ERROR'
            return False

    def print_summary(self):
        """Imprime resumo dos testes"""
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)

        for test_name, result in self.results.items():
            status_icon = "✅" if "PASS" in result else (
                "⚠️" if "FAIL" in result else "❌")
            print(f"{status_icon} {test_name:25s} → {result}")

        print("=" * 60)

        # Status geral
        passed = sum(1 for r in self.results.values() if "PASS" in r)
        total = len(self.results)

        print(
            f"\n🎯 Taxa de Sucesso: {passed}/{total} ({100 * passed // total}%)")

        if passed == total:
            print("🎉 Todos os canais estão OPERACIONAIS!")
            return True
        elif passed >= total // 2:
            print(
                "⚠️  Sistema parcialmente operacional. Alguns canais precisam de atenção.")
            return False
        else:
            print("❌ Sistema com problemas críticos de conectividade.")
            return False


def main():
    print("🚀 Iniciando Verificação de Canais de Comunicação Ziva")
    print("=" * 60)

    tester = ChannelTester()

    # Executar todos os testes
    tester.test_binary_listener()
    tester.test_binary_connection()
    tester.test_api_endpoint()
    tester.test_ssh_connection()
    tester.test_scp_transfer()
    tester.test_connection_manager()

    # Resumo
    success = tester.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
