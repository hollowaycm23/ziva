import logging
import shutil
import subprocess
import re
import os

logger = logging.getLogger("HardwareValidator")


class HardwareValidator:
    """
    Validador de Especificações de Hardware.
    """

    @staticmethod
    def get_system_specs():
        """
        Coleta informações do sistema.
        """
        specs = {
            'ram_total_gb': 0,
            'cpu_model': 'Unknown',
            'gpu_name': 'None',
            'vram_total_gb': 0,
            'cuda_version': 'None'
        }

        try:
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if 'MemTotal' in line:
                            kb = int(re.search(r'\d+', line).group())
                            specs['ram_total_gb'] = round(kb / (1024 * 1024), 2)
                            break
            elif os.name == 'nt':
                import subprocess
                result = subprocess.run(['wmic', 'memorychip', 'get', 'Capacity'], capture_output=True, text=True)
                total_bytes = sum(int(x) for x in result.stdout.strip().split('\n')[1:] if x.strip())
                specs['ram_total_gb'] = round(total_bytes / (1024**3), 2)
            if os.path.exists('/proc/cpuinfo'):
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            specs['cpu_model'] = line.split(':')[1].strip()
                            break
            elif os.name == 'nt':
                import platform
                specs['cpu_model'] = platform.processor() or 'Unknown'
        except Exception as e:
            logger.error(f"Erro ao ler CPU/RAM: {e}")

        if shutil.which('nvidia-smi'):
            try:
                cmd = [
                    'nvidia-smi',
                    '--query-gpu=name,memory.total',
                    '--format=csv,noheader']
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output:
                        parts = output.split(',')
                        specs['gpu_name'] = parts[0].strip()
                        vram_mib = int(re.search(r'\d+', parts[1]).group())
                        specs['vram_total_gb'] = round(vram_mib / 1024, 2)
                cmd_ver = ['nvidia-smi']
                res_ver = subprocess.run(
                    cmd_ver, capture_output=True, text=True)
                match = re.search(r'CUDA Version: (\d+\.\d+)', res_ver.stdout)
                if match:
                    specs['cuda_version'] = match.group(1)
            except Exception as e:
                logger.error(f"Erro ao ler GPU: {e}")
        return specs

    @staticmethod
    def validate_model_fit(model_path, specs):
        """
        Verifica se o modelo deve caber na memória.
        """
        try:
            file_size_gb = os.path.getsize(model_path) / (1024 ** 3)
            estimated_req = file_size_gb * 1.3
            logger.info(
                f"Modelo: {file_size_gb:.2f} GB. Requisito Estimado: "
                f"{estimated_req:.2f} GB")
            logger.info(
                f"Disponível - VRAM: {specs['vram_total_gb']} GB, "
                f"RAM: {specs['ram_total_gb']} GB")
            if specs['vram_total_gb'] > estimated_req:
                logger.info("Modelo cabe na VRAM (Full GPU Offload).")
                return True
            elif (specs['vram_total_gb'] +
                  specs['ram_total_gb']) > (estimated_req + 2.0):
                logger.info("Modelo cabe na RAM + VRAM (Split Offload).")
                return True
            else:
                logger.warning(
                    "Recursos insuficientes para rodar este modelo.")
                return False
        except Exception as e:
            logger.error(f"Erro na validação do modelo: {e}")
            return True