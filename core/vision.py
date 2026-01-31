import logging
import base64
from io import BytesIO
from typing import Optional, List
# Para validação básica de imagem se necessário, mas o principal é passar para o Ollama
# from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VisionHandler")


class VisionHandler:
    """
    Gerencia operações de visão computacional usando LLaVA via Ollama.
    """

    def __init__(self, model_name: str = "llava:7b"):
        self.model_name = model_name
        logger.info(f"👁️ Vision Handler inicializado com modelo: {model_name}")

    def process_image_query(
            self, prompt: str, images: List[str], agent_llm) -> str:
        """
        Processa uma query que contém imagens.

        Args:
            prompt: O texto da pergunta do usuário.
            images: Lista de strings em base64 das imagens.
            agent_llm: A instância do serviço LLM (para usar o método generate/completion).

        Returns:
            A descrição/resposta do modelo.
        """
        if not images:
            logger.warning(
                "Nenhuma imagem fornecida para processamento visual.")
            return "Erro: Nenhuma imagem fornecida."

        logger.info(
            f"👁️ Processando query visual: '{prompt}' com {
                len(images)} imagem(ns)")

        try:
            # Salvar modelo anterior para restaurar depois
            previous_model = agent_llm.model

            # Trocar para modelo de visão
            agent_llm.model = self.model_name

            # Construir payload específico para multimodal no Ollama
            # O método completion do LLMService precisará suportar 'images' no payload
            # Se o LLMService atual não suportar, chamaremos a API diretamente ou ajustaremos o LLMService.
            # Assumindo que vamos passar 'images' como kwarg para o
            # completion/generate

            response = agent_llm.completion(
                prompt=prompt,
                images=images,  # Ollama python lib e requests aceitam isso
                temperature=0.2  # Baixa temperatura para descrições precisas
            )

            # Restaurar modelo anterior
            agent_llm.model = previous_model

            logger.info("✅ Processamento visual concluído com sucesso")
            return response

        except Exception as e:
            logger.error(f"❌ Erro no processamento visual: {e}")
            return f"Não consegui analisar a imagem. Erro: {str(e)}"


# Singleton
_vision_handler = None


def get_vision_handler() -> VisionHandler:
    global _vision_handler
    if _vision_handler is None:
        _vision_handler = VisionHandler()
    return _vision_handler
