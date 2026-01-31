
import logging
from datasets import Dataset
from core.database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatasetLoader")


class DatasetLoader:
    def __init__(self):
        self.db = DatabaseManager()

    def load_from_db(self, limit=1000):
        """
        Carrega dados do banco e converte para HF Dataset.
        """
        conn = self.db._get_conn()
        conn.row_factory = lambda c, r: dict(
            zip([col[0] for col in c.description], r))
        cursor = conn.cursor()

        # Selecionar apenas dados de alta qualidade
        cursor.execute('''
            SELECT instruction, output
            FROM training_data
            WHERE quality_score >= 0.8
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            logger.warning("Nenhum dado de treinamento encontrado no banco.")
            return None

        logger.info(f"Carregados {len(rows)} exemplos do banco de dados.")

        # Formatar para instrução (Alpaca style simplified)
        formatted_data = []
        for row in rows:
            text = f"### Instruction:\n{
                row['instruction']}\n\n### Response:\n{
                row['output']}"
            formatted_data.append({"text": text})

        # Converter para HF Dataset
        hf_dataset = Dataset.from_list(formatted_data)
        return hf_dataset


if __name__ == "__main__":
    loader = DatasetLoader()
    ds = loader.load_from_db()
    if ds:
        print("Example:", ds[0])
