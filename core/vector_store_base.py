from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class VectorStoreBase(ABC):
    """
    Interface base para sistemas de armazenamento vetorial no Ziva.
    """

    @abstractmethod
    def add_text(self, text: str, embedding: List[float], metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Adiciona um único texto ao armazenamento.
        """
        pass

    @abstractmethod
    def add_texts(self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict]] = None) -> List[str]:
        """
        Adiciona múltiplos textos em batch ao armazenamento.
        """
        pass

    @abstractmethod
    def search(self, embedding: List[float], limit: int = 5, filters: Optional[Dict] = None, query_text: Optional[str] = None) -> List[Dict]:
        """
        Realiza busca por similaridade.
        Args:
            embedding: Vetor de consulta.
            limit: Limite de resultados.
            filters: Filtros de metadados.
            query_text: Texto original da consulta (para busca híbrida).
        Returns:
            list: Lista de dicionários contendo {'text', 'score', 'metadata'}.
        """
        pass

    @abstractmethod
    def scroll(self, limit: int = 100, offset: Any = None) -> tuple[List[Dict], Any]:
        """
        Itera sobre todos os documentos.
        Returns:
            tuple: (lista de documentos, próxima offset ou None).
        """
        pass

    @abstractmethod
    def delete_old_points(self, days: int) -> int:
        """
        Remove pontos com timestamp mais antigo que X dias.
        Returns:
            int: Número de pontos removidos.
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas operacionais do armazenamento.
        """
        pass

    @abstractmethod
    def exists_similar(self, embedding: List[float], threshold: float = 0.95) -> bool:
        """
        Verifica duplicidade aproximada.
        """
        pass
