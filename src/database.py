"""
Módulo de gerenciamento de banco de dados
Implementa modelos, conexão e operações CRUD
"""

import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import uuid
import os


DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'sentiment_analysis.db')


@contextmanager
def get_db_connection():
    """Context manager para conexão com banco de dados"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Inicializa o banco de dados com todas as tabelas"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                last_login TIMESTAMP NULL
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')

        # Tabela de análises
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analyses (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                sentiment TEXT NULL,
                score REAL NULL,
                confidence REAL NULL,
                metadata TEXT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP NULL,
                error_message TEXT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_analyses_sentiment ON analyses(sentiment)')

        # Tabela de configurações de webhook
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                events TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                secret TEXT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_webhook_configs_user_id ON webhook_configs(user_id)')

        # Tabela de logs de webhook
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id TEXT NOT NULL,
                webhook_config_id INTEGER NOT NULL,
                webhook_url TEXT NOT NULL,
                payload TEXT NOT NULL,
                status_code INTEGER NULL,
                response_body TEXT NULL,
                attempts INTEGER DEFAULT 1,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT 0,
                FOREIGN KEY (analysis_id) REFERENCES analyses(id),
                FOREIGN KEY (webhook_config_id) REFERENCES webhook_configs(id)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_webhook_logs_analysis_id ON webhook_logs(analysis_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_webhook_logs_sent_at ON webhook_logs(sent_at)')

        # Tabela de métricas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                metric_type TEXT NOT NULL,
                metric_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, metric_type)
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_date_type ON metrics(date, metric_type)')

        # Tabela de rate limiting
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT NOT NULL UNIQUE,
                request_count INTEGER DEFAULT 0,
                window_start TIMESTAMP NOT NULL,
                last_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_rate_limits_identifier ON rate_limits(identifier)')

        conn.commit()
        print("✓ Banco de dados inicializado com sucesso!")


class UserModel:
    """Modelo para operações de usuários"""

    @staticmethod
    def create(username: str, email: str, password_hash: str) -> int:
        """Cria um novo usuário"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por email"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict[str, Any]]:
        """Busca usuário por ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_last_login(user_id: int):
        """Atualiza último login do usuário"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user_id,)
            )


class AnalysisModel:
    """Modelo para operações de análises"""

    @staticmethod
    def create(user_id: int, text: str, metadata: Optional[Dict] = None) -> str:
        """Cria uma nova análise"""
        analysis_id = str(uuid.uuid4())
        metadata_json = json.dumps(metadata) if metadata else None

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO analyses (id, user_id, text, metadata, status)
                   VALUES (?, ?, ?, ?, 'pending')''',
                (analysis_id, user_id, text, metadata_json)
            )
        return analysis_id

    @staticmethod
    def get_by_id(analysis_id: str) -> Optional[Dict[str, Any]]:
        """Busca análise por ID"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                if data.get('metadata'):
                    data['metadata'] = json.loads(data['metadata'])
                return data
            return None

    @staticmethod
    def get_by_user(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Busca análises de um usuário"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT * FROM analyses WHERE user_id = ?
                   ORDER BY created_at DESC LIMIT ? OFFSET ?''',
                (user_id, limit, offset)
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                data = dict(row)
                if data.get('metadata'):
                    data['metadata'] = json.loads(data['metadata'])
                results.append(data)
            return results

    @staticmethod
    def update_result(analysis_id: str, sentiment: str, score: float, confidence: float):
        """Atualiza resultado da análise"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''UPDATE analyses
                   SET sentiment = ?, score = ?, confidence = ?,
                       status = 'completed', processed_at = CURRENT_TIMESTAMP
                   WHERE id = ?''',
                (sentiment, score, confidence, analysis_id)
            )

    @staticmethod
    def update_status(analysis_id: str, status: str, error_message: Optional[str] = None):
        """Atualiza status da análise"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if error_message:
                cursor.execute(
                    'UPDATE analyses SET status = ?, error_message = ? WHERE id = ?',
                    (status, error_message, analysis_id)
                )
            else:
                cursor.execute(
                    'UPDATE analyses SET status = ? WHERE id = ?',
                    (status, analysis_id)
                )

    @staticmethod
    def get_pending() -> List[Dict[str, Any]]:
        """Busca análises pendentes"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM analyses WHERE status = 'pending' ORDER BY created_at ASC"
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                data = dict(row)
                if data.get('metadata'):
                    data['metadata'] = json.loads(data['metadata'])
                results.append(data)
            return results


class WebhookConfigModel:
    """Modelo para configurações de webhook"""

    @staticmethod
    def create(user_id: int, url: str, events: List[str], secret: Optional[str] = None) -> int:
        """Cria configuração de webhook"""
        events_json = json.dumps(events)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO webhook_configs (user_id, url, events, secret)
                   VALUES (?, ?, ?, ?)''',
                (user_id, url, events_json, secret)
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_user(user_id: int) -> List[Dict[str, Any]]:
        """Busca webhooks de um usuário"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM webhook_configs WHERE user_id = ? AND enabled = 1',
                (user_id,)
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                data = dict(row)
                if data.get('events'):
                    data['events'] = json.loads(data['events'])
                results.append(data)
            return results

    @staticmethod
    def update(config_id: int, url: Optional[str] = None, events: Optional[List[str]] = None,
               enabled: Optional[bool] = None):
        """Atualiza configuração de webhook"""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if url:
                cursor.execute('UPDATE webhook_configs SET url = ? WHERE id = ?', (url, config_id))
            if events is not None:
                events_json = json.dumps(events)
                cursor.execute('UPDATE webhook_configs SET events = ? WHERE id = ?', (events_json, config_id))
            if enabled is not None:
                cursor.execute('UPDATE webhook_configs SET enabled = ? WHERE id = ?', (enabled, config_id))


class WebhookLogModel:
    """Modelo para logs de webhook"""

    @staticmethod
    def create(analysis_id: str, webhook_config_id: int, webhook_url: str,
               payload: Dict, status_code: Optional[int] = None,
               response_body: Optional[str] = None, success: bool = False):
        """Cria log de webhook"""
        payload_json = json.dumps(payload)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT INTO webhook_logs
                   (analysis_id, webhook_config_id, webhook_url, payload, status_code,
                    response_body, success)
                   VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (analysis_id, webhook_config_id, webhook_url, payload_json,
                 status_code, response_body, success)
            )
            return cursor.lastrowid


class MetricsModel:
    """Modelo para métricas do sistema"""

    @staticmethod
    def save_daily_metrics(date: str, metric_type: str, metric_data: Dict):
        """Salva métricas diárias"""
        metric_data_json = json.dumps(metric_data)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT OR REPLACE INTO metrics (date, metric_type, metric_data)
                   VALUES (?, ?, ?)''',
                (date, metric_type, metric_data_json)
            )

    @staticmethod
    def get_summary(user_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtém resumo de métricas"""
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Total de análises
            if user_id:
                cursor.execute('SELECT COUNT(*) as total FROM analyses WHERE user_id = ?', (user_id,))
            else:
                cursor.execute('SELECT COUNT(*) as total FROM analyses')
            total_analyses = cursor.fetchone()['total']

            # Distribuição de sentimentos
            if user_id:
                cursor.execute(
                    '''SELECT sentiment, COUNT(*) as count
                       FROM analyses WHERE user_id = ? AND sentiment IS NOT NULL
                       GROUP BY sentiment''',
                    (user_id,)
                )
            else:
                cursor.execute(
                    '''SELECT sentiment, COUNT(*) as count
                       FROM analyses WHERE sentiment IS NOT NULL
                       GROUP BY sentiment'''
                )
            sentiment_dist = {row['sentiment']: row['count'] for row in cursor.fetchall()}

            # Score médio
            if user_id:
                cursor.execute(
                    'SELECT AVG(score) as avg_score FROM analyses WHERE user_id = ? AND score IS NOT NULL',
                    (user_id,)
                )
            else:
                cursor.execute('SELECT AVG(score) as avg_score FROM analyses WHERE score IS NOT NULL')
            avg_score = cursor.fetchone()['avg_score'] or 0

            return {
                'total_analyses': total_analyses,
                'sentiment_distribution': sentiment_dist,
                'average_score': round(avg_score, 3),
                'timestamp': datetime.now().isoformat()
            }


if __name__ == '__main__':
    # Inicializa banco de dados quando executado diretamente
    init_database()
