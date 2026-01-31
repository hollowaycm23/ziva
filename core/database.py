import sqlite3
import json
import time
import threading
from pathlib import Path
from contextlib import contextmanager

import logging
DB_PATH = Path("/app/data/ziva.db")
if not DB_PATH.parent.exists():
    # Fallback for local execution relative to project root
    DB_PATH = Path(__file__).parent.parent / "data" / "ziva.db"
logger = logging.getLogger("DatabaseManager")


class DatabaseManager:
    """
    Gerenciador de banco de dados SQLite para o sistema Ziva.
    """

    def __init__(self, db_path=DB_PATH):
        """
        Inicializa o gerenciador de banco de dados.
        """
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self):
        """
        Retorna conexão thread-local.
        """
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=10.0,
                check_same_thread=False
            )

            conn.execute('PRAGMA journal_mode=WAL;')
            conn.execute('PRAGMA synchronous=NORMAL;')
            conn.execute('PRAGMA cache_size=-64000;')
            conn.execute('PRAGMA temp_store=MEMORY;')
            conn.execute('PRAGMA mmap_size=268435456;')
            conn.execute('PRAGMA page_size=4096;')
            conn.execute('PRAGMA auto_vacuum=INCREMENTAL;')
            conn.row_factory = sqlite3.Row

            self._local.conn = conn
            logger.debug(
                f"Created DB connection for thread "
                f"{threading.current_thread().name}")

        return self._local.conn

    @contextmanager
    def transaction(self):
        """
        Context manager para transações seguras.
        """
        conn = self._get_conn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def recover_stale_sessions(self):
        """
        Detecta e fecha sessões que ficaram 'active' após um desligamento.
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            logger.info("Verificando integridade de sessões passadas...")
            cursor.execute(
                "UPDATE sessions SET status = 'interrupted', end_time = ? "
                "WHERE status = 'active'",
                (time.time(),)
            )
            if cursor.rowcount > 0:
                logger.warning(
                    f"{cursor.rowcount} sessões interrompidas recuperadas.")

    def _init_db(self):
        """
        Cria o schema inicial do banco de dados se não existir.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL,
                payload TEXT, status TEXT DEFAULT 'pending',
                assigned_node TEXT, result TEXT, created_at REAL,
                updated_at REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY, direction TEXT, sender TEXT,
                receiver TEXT, content TEXT, timestamp REAL,
                status TEXT DEFAULT 'new'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, start_time REAL,
                end_time REAL, summary TEXT, status TEXT DEFAULT 'active'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER,
                role TEXT, content TEXT, timestamp REAL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peers (
                node_id TEXT PRIMARY KEY, public_key TEXT,
                trust_level INTEGER DEFAULT 0, last_seen REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER,
                start_interaction_id INTEGER, end_interaction_id INTEGER,
                summary TEXT, key_insights TEXT, importance INTEGER DEFAULT 0,
                embedding_id TEXT, created_at REAL,
                FOREIGN KEY(session_id) REFERENCES sessions(id)
            )
        ''')

        try:
            cursor.execute(
                'ALTER TABLE interactions ADD COLUMN importance INTEGER DEFAULT 0'
            )
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('ALTER TABLE interactions ADD COLUMN tags TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                'ALTER TABLE interactions ADD COLUMN embedding_id TEXT')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute(
                'ALTER TABLE interactions ADD COLUMN context_summary TEXT')
        except sqlite3.OperationalError:
            pass

        conn.commit()
        self._create_indexes(conn)

    def _create_indexes(self, conn):
        """
        Cria índices estratégicos para otimizar queries frequentes.
        """
        cursor = conn.cursor()
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interactions_session
            ON interactions(session_id, timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_interactions_embedding
            ON interactions(embedding_id) WHERE embedding_id IS NOT NULL
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_episodes_session
            ON episodes(session_id, created_at)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_status
            ON sessions(status, start_time)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_jobs_status
            ON jobs(status, created_at)
        ''')
        conn.commit()
        logger.info("Índices estratégicos criados/verificados")

    def add_trusted_peer(self, node_id, key, trust_level=100):
        import hashlib
        conn = self._get_conn()
        cursor = conn.cursor()
        now = time.time()
        
        # Consistent with BinaryServer validation
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO peers (node_id, public_key, trust_level, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
            public_key=excluded.public_key,
            trust_level=excluded.trust_level,
            last_seen=excluded.last_seen
        ''', (node_id, hashed_key, trust_level, now))
        conn.commit()

    def add_job(self, job_type, payload):
        """
        Adiciona um novo job à fila de processamento.
        """
        with self.transaction() as conn:
            cursor = conn.cursor()
            now = time.time()
            payload_json = json.dumps(payload)
            cursor.execute(
                'INSERT INTO jobs (type, payload, created_at, updated_at) '
                'VALUES (?, ?, ?, ?)',
                (job_type, payload_json, now, now)
            )
            return cursor.lastrowid

    def get_pending_job(self):
        """
        Recupera o próximo job pendente (sem atribuição).
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM jobs WHERE status = "pending" '
            'ORDER BY created_at ASC LIMIT 1')
        row = cursor.fetchone()
        return self._row_to_job(row)

    def get_next_local_job(self, node_id):
        """
        Recupera o próximo job atribuído a este nó específico.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM jobs WHERE status = "assigned" AND '
            'assigned_node = ? ORDER BY created_at ASC LIMIT 1',
            (node_id,)
        )
        row = cursor.fetchone()
        return self._row_to_job(row)

    def _row_to_job(self, row):
        if row:
            return {
                "id": row[0], "type": row[1], "payload": json.loads(row[2]),
                "status": row[3], "assigned_node": row[4], "result": row[5],
                "created_at": row[6], "updated_at": row[7]
            }
        return None

    def update_job_status(self, job_id, status, result=None):
        """Atualiza status de um job (com ou sem resultado)"""
        with self.transaction() as conn:
            cursor = conn.cursor()
            now = time.time()
            if result:
                result_json = json.dumps(result)
                cursor.execute(
                    'UPDATE jobs SET status = ?, result = ?, updated_at = ? '
                    'WHERE id = ?',
                    (status, result_json, now, job_id)
                )
            else:
                cursor.execute(
                    'UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?',
                    (status, now, job_id)
                )

    def add_message(self, msg_id, direction, sender,
                    receiver, content, timestamp):
        """Adiciona mensagem ao banco"""
        with self.transaction() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO messages (id, direction, sender, receiver, '
                    'content, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                    (msg_id, direction, sender, receiver, content, timestamp)
                )
            except sqlite3.IntegrityError:
                pass