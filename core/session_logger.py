"""
Advanced Session Logger
Captura interações em tempo real para retreinamento
"""

import os
import json
import time
import sqlite3
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SessionLogger")


@dataclass
class Interaction:
    """Representa uma interação usuário-assistente"""
    session_id: str
    timestamp: float
    user_input: str
    assistant_output: str
    tool_calls: List[Dict]
    success: bool
    error_message: Optional[str]
    execution_time: float
    context: Dict


class SessionLogger:
    """Logger avançado para captura de sessões"""

    def __init__(self, db_path: str = "./ziva_sessions.db"):
        self.db_path = db_path
        self.current_session_id = None
        self.session_start_time = None
        self._init_database()

    def _init_database(self):
        """Inicializa banco de dados de sessões"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time REAL,
                end_time REAL,
                total_interactions INTEGER,
                success_rate REAL,
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp REAL,
                user_input TEXT,
                assistant_output TEXT,
                tool_calls TEXT,
                success INTEGER,
                error_message TEXT,
                execution_time REAL,
                context TEXT,
                quality_score REAL DEFAULT 0.0,
                used_for_training INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id
            ON interactions(session_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_quality
            ON interactions(quality_score DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_training
            ON interactions(used_for_training)
        """)

        conn.commit()
        conn.close()

        logger.info(f"✅ Database initialized: {self.db_path}")

    def start_session(self, metadata: Optional[Dict] = None) -> str:
        """Inicia nova sessão"""
        self.current_session_id = f"session_{int(time.time())}_{os.getpid()}"
        self.session_start_time = time.time()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO sessions (session_id, start_time, total_interactions,
                                  metadata)
            VALUES (?, ?, 0, ?)
        """, (
            self.current_session_id,
            self.session_start_time,
            json.dumps(metadata or {})
        ))

        conn.commit()
        conn.close()

        logger.info(f"📝 Session started: {self.current_session_id}")
        return self.current_session_id

    def log_interaction(self, interaction: Interaction):
        """Registra uma interação"""
        if not self.current_session_id:
            self.start_session()

        interaction.session_id = self.current_session_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO interactions (
                session_id, timestamp, user_input, assistant_output,
                tool_calls, success, error_message, execution_time, context
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            interaction.session_id,
            interaction.timestamp,
            interaction.user_input,
            interaction.assistant_output,
            json.dumps(interaction.tool_calls),
            1 if interaction.success else 0,
            interaction.error_message,
            interaction.execution_time,
            json.dumps(interaction.context)
        ))

        cursor.execute("""
            UPDATE sessions
            SET total_interactions = total_interactions + 1
            WHERE session_id = ?
        """, (self.current_session_id,))

        conn.commit()
        conn.close()

        logger.debug(f"✓ Interaction logged: {interaction.user_input[:50]}...")

    def end_session(self):
        """Finaliza sessão atual"""
        if not self.current_session_id:
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(success) as successful
            FROM interactions
            WHERE session_id = ?
        """, (self.current_session_id,))

        total, successful = cursor.fetchone()
        success_rate = (successful / total) if total > 0 else 0.0

        cursor.execute("""
            UPDATE sessions
            SET end_time = ?, success_rate = ?
            WHERE session_id = ?
        """, (time.time(), success_rate, self.current_session_id))

        conn.commit()
        conn.close()

        logger.info(
            f"✅ Session ended: {self.current_session_id} "
            f"(success rate: {success_rate:.2%})")
        self.current_session_id = None

    def get_unscored_interactions(self, limit: int = 100) -> List[Dict]:
        """Retorna interações que ainda não foram avaliadas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, user_input, assistant_output, tool_calls, success,
                   error_message
            FROM interactions
            WHERE quality_score = 0.0
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))

        interactions = []
        for row in cursor.fetchall():
            interactions.append({
                'id': row[0],
                'user_input': row[1],
                'assistant_output': row[2],
                'tool_calls': json.loads(row[3]),
                'success': bool(row[4]),
                'error_message': row[5]
            })

        conn.close()
        return interactions

    def update_quality_score(self, interaction_id: int, score: float):
        """Atualiza score de qualidade de uma interação"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE interactions
            SET quality_score = ?
            WHERE id = ?
        """, (score, interaction_id))

        conn.commit()
        conn.close()

    def get_high_quality_interactions(
            self, min_score: float = 0.8, limit: int = 1000) -> List[Dict]:
        """Retorna interações de alta qualidade para treinamento"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_input, assistant_output, tool_calls
            FROM interactions
            WHERE quality_score >= ? AND used_for_training = 0
            ORDER BY quality_score DESC
            LIMIT ?
        """, (min_score, limit))

        interactions = []
        for row in cursor.fetchall():
            interactions.append({
                'instruction': row[0],
                'output': row[1],
                'tool_calls': json.loads(row[2])
            })

        conn.close()
        return interactions

    def mark_as_used_for_training(self, interaction_ids: List[int]):
        """Marca interações como usadas no treinamento"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        placeholders = ','.join('?' * len(interaction_ids))
        cursor.execute(f"""
            UPDATE interactions
            SET used_for_training = 1
            WHERE id IN ({placeholders})
        """, interaction_ids)

        conn.commit()
        conn.close()

        logger.info(
            f"✅ Marked {len(interaction_ids)} interactions as used for training")

    def get_statistics(self) -> Dict:
        """Retorna estatísticas do sistema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        total_sessions = cursor.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        total_interactions = cursor.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
        overall_success_rate = cursor.execute(
            "SELECT AVG(success) FROM interactions").fetchone()[0] or 0.0
        high_quality_count = cursor.execute(
            "SELECT COUNT(*) FROM interactions WHERE quality_score >= 0.8").fetchone()[0]
        used_for_training = cursor.execute(
            "SELECT COUNT(*) FROM interactions WHERE used_for_training = 1").fetchone()[0]

        conn.close()

        return {
            'total_sessions': total_sessions,
            'total_interactions': total_interactions,
            'overall_success_rate': overall_success_rate,
            'high_quality_count': high_quality_count,
            'used_for_training': used_for_training,
            'ready_for_training': high_quality_count - used_for_training
        }


if __name__ == "__main__":
    logger_instance = SessionLogger()
    session_id = logger_instance.start_session(
        {'user': 'test', 'mode': 'development'})
    interaction = Interaction(
        session_id=session_id,
        timestamp=time.time(),
        user_input="Como listar arquivos no Linux?",
        assistant_output="Use o comando 'ls' para listar arquivos.",
        tool_calls=[],
        success=True,
        error_message=None,
        execution_time=0.5,
        context={'mode': 'cli'}
    )
    logger_instance.log_interaction(interaction)
    logger_instance.end_session()
    stats = logger_instance.get_statistics()
    print("\n📊 Estatísticas:")
    for key, value in stats.items():
        print(f"  {key}: {value}")