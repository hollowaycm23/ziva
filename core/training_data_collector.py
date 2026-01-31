"""
Training Data Collector for Ziva Fine-Tuning System.
"""

import logging
import time
import json
import re
from typing import List, Dict, Optional
from pathlib import Path
from core.database import DatabaseManager

logger = logging.getLogger("TrainingDataCollector")


class TrainingDataCollector:
    """
    Coleta e processa dados de treinamento das sessões da Ziva.
    """

    def __init__(self, db: DatabaseManager = None):
        """
        Inicializa o coletor de dados.
        """
        self.db = db or DatabaseManager()
        self._ensure_training_table()

    def _ensure_training_table(self):
        """Cria tabela de dados de treinamento se não existir"""
        conn = self.db._get_conn()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                instruction TEXT NOT NULL,
                input TEXT,
                output TEXT NOT NULL,
                task_type TEXT,
                quality_score REAL,
                success BOOLEAN,
                created_at REAL NOT NULL,
                used_in_training BOOLEAN DEFAULT 0,
                UNIQUE(instruction, output)
            )
        ''')

        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_task_type ON training_data(task_type)')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_quality ON training_data(quality_score)')
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_used ON training_data(used_in_training)')

        conn.commit()


    def collect_from_sessions(self, min_quality: float = 0.7) -> int:
        """
        Coleta dados de treinamento de sessões completadas.
        """
        conn = self.db._get_conn()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, session_id, role, content, timestamp
            FROM interactions
            WHERE role IN ('user', 'assistant')
            ORDER BY session_id, timestamp
        ''')

        interactions = cursor.fetchall()


        collected = 0
        current_session = None
        user_input = None

        for interaction in interactions:
            _, session_id, role, content, timestamp = interaction
            if session_id != current_session:
                current_session = session_id
                user_input = None
            if role == 'user':
                user_input = content
            elif role == 'assistant' and user_input:
                tool_call = self._extract_tool_call(content)
                if tool_call:
                    quality = self._calculate_quality(
                        user_input, tool_call, content)
                    if quality >= min_quality:
                        self._add_training_example(
                            session_id=session_id,
                            instruction=user_input,
                            output=tool_call,
                            task_type=self._classify_task(
                                user_input, tool_call),
                            quality_score=quality
                        )
                        collected += 1
                user_input = None
        logger.info(f"Coletados {collected} exemplos de treinamento")
        return collected

    def _extract_tool_call(self, content: str) -> Optional[str]:
        """
        Extrai JSON de tool call do conteúdo.
        """
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, content, re.DOTALL)
        if match:
            try:
                json_str = match.group(1)
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                return None
        return None

    def _calculate_quality(self, instruction: str,
                           tool_call: str, full_response: str) -> float:
        """
        Calcula score de qualidade da interação com scoring semântico.
        """
        score = 0.0
        try:
            tool_data = json.loads(tool_call)
            if 'tool' in tool_data and 'args' in tool_data:
                score += 0.25
        except BaseException:
            return 0.0
        if len(instruction.split()) > 3:
            score += 0.15
        error_keywords = [
            'erro', 'error', 'falha', 'failed', 'exception', 'desculpe']
        if not any(kw in full_response.lower() for kw in error_keywords):
            score += 0.25
        if tool_data.get('args') and len(tool_data['args']) > 0:
            score += 0.15
        if 50 < len(full_response) < 2000:
            score += 0.10
        instruction_keywords = set(instruction.lower().split())
        response_keywords = set(full_response.lower().split())
        overlap = len(instruction_keywords & response_keywords)
        if overlap >= 2:
            score += 0.10
        return min(score, 1.0)

    def _classify_task(self, instruction: str, tool_call: str) -> str:
        """
        Classifica tipo de tarefa com suporte para novas categorias.
        """
        try:
            tool_data = json.loads(tool_call)
            tool_name = tool_data.get('tool', '').lower()
            instruction_lower = instruction.lower()

            if 'web_search' in tool_name or 'search_web' in tool_name:
                return 'web-search'
            elif 'get_weather' in tool_name or 'get_air_quality' in tool_name:
                return 'weather-data'
            elif any(kw in tool_name for kw in ['shell', 'bash', 'local_shell']):
                return 'shell'
            elif any(kw in tool_name for kw in ['browser', 'scrape']):
                return 'web-scraping'
            elif any(kw in tool_name for kw in ['search_documentation', 'code_lookup']):
                return 'knowledge-retrieval'
            elif any(kw in tool_name for kw in ['code_writer', 'code_runner']):
                return 'code-generation'
            elif 'file_' in tool_name:
                return 'file-operations'
            elif any(kw in instruction_lower for kw in ['anime', 'filme', 'notícia', 'história']):
                return 'general-knowledge'
            else:
                return 'general'
        except BaseException:
            return 'general'

    def _add_training_example(
            self,
            session_id: int,
            instruction: str,
            output: str,
            task_type: str,
            quality_score: float):
        """Adiciona exemplo ao dataset de treinamento"""
        conn = self.db._get_conn()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO training_data
                (session_id, instruction, output, task_type, quality_score,
                 success, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, instruction, output, task_type, quality_score, True,
                  time.time()))
            conn.commit()
        except Exception as e:
            logger.error(f"Erro ao adicionar exemplo: {e}")
        finally:
            pass


    def get_training_dataset(self, task_type: Optional[str] = None,
                             min_quality: float = 0.7,
                             limit: Optional[int] = None) -> List[Dict]:
        """
        Retorna dataset de treinamento.
        """
        conn = self.db._get_conn()
        cursor = conn.cursor()
        query = '''
            SELECT instruction, input, output, task_type, quality_score
            FROM training_data
            WHERE quality_score >= ? AND success = 1
        '''
        params = [min_quality]
        if task_type:
            query += ' AND task_type = ?'
            params.append(task_type)
        query += ' ORDER BY quality_score DESC'
        if limit:
            query += f' LIMIT {limit}'
        cursor.execute(query, params)
        rows = cursor.fetchall()

        dataset = []
        for row in rows:
            instruction, input_text, output, task_type, quality = row
            dataset.append({
                'instruction': instruction, 'input': input_text or '',
                'output': output, 'task_type': task_type,
                'quality_score': quality})
        return dataset

    def get_diverse_dataset(self, target_size: int = 100,
                            min_quality: float = 0.8) -> List[Dict]:
        """
        Retorna dataset balanceado com diversidade de tipos de tarefa.
        """
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT task_type, COUNT(*) as count
            FROM training_data
            WHERE quality_score >= ? AND success = 1
            GROUP BY task_type
        ''', (min_quality,))
        task_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        if not task_distribution:
    
            return []
        num_types = len(task_distribution)
        quota_per_type = max(1, target_size // num_types)
        diverse_dataset = []
        for task_type, available_count in task_distribution.items():
            limit = min(quota_per_type, available_count)
            cursor.execute('''
                SELECT instruction, input, output, task_type, quality_score
                FROM training_data
                WHERE task_type = ? AND quality_score >= ? AND success = 1
                ORDER BY quality_score DESC
                LIMIT ?
            ''', (task_type, min_quality, limit))
            for row in cursor.fetchall():
                instruction, input_text, output, task_type, quality = row
                diverse_dataset.append({
                    'instruction': instruction, 'input': input_text or '',
                    'output': output, 'task_type': task_type,
                    'quality_score': quality})
        conn.close()
        logger.info(
            f"Dataset diverso gerado: {len(diverse_dataset)} exemplos de "
            f"{num_types} tipos")
        return diverse_dataset

    def export_to_json(self, output_path: str,
                       task_type: Optional[str] = None):
        """
        Exporta dataset para arquivo JSON.
        """
        dataset = self.get_training_dataset(task_type=task_type)
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        logger.info(
            f"Dataset exportado: {output_path} ({len(dataset)} exemplos)")


if __name__ == "__main__":
    collector = TrainingDataCollector()
    count = collector.collect_from_sessions(min_quality=0.7)
    print(f"✅ Coletados {count} exemplos de treinamento")
    dataset = collector.get_training_dataset(limit=10)
    print(f"📊 Dataset: {len(dataset)} exemplos")
    for ex in dataset[:3]:
        print(f"  - {ex['task_type']}: {ex['instruction'][:50]}...")