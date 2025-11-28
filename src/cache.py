"""
Sistema de cache em memória
Simula funcionalidade de Redis para reduzir latência
"""

from datetime import datetime, timedelta
from typing import Any, Optional
import json
import threading


class CacheService:
    """
    Serviço de cache em memória com TTL
    Em produção, seria substituído por Redis
    """

    def __init__(self):
        self.cache = {}  # {key: {'value': value, 'expires_at': datetime}}
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """
        Armazena valor no cache com TTL

        Args:
            key: Chave do cache
            value: Valor a ser armazenado (será serializado em JSON)
            ttl_seconds: Tempo de vida em segundos (padrão: 5 minutos)
        """
        with self.lock:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at
            }

    def get(self, key: str) -> Optional[Any]:
        """
        Recupera valor do cache

        Args:
            key: Chave do cache

        Returns:
            Valor armazenado ou None se não encontrado/expirado
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            entry = self.cache[key]

            # Verifica expiração
            if datetime.now() > entry['expires_at']:
                del self.cache[key]
                self.misses += 1
                return None

            self.hits += 1
            return entry['value']

    def delete(self, key: str):
        """Remove entrada do cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def clear(self):
        """Limpa todo o cache"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def invalidate_pattern(self, pattern: str):
        """
        Invalida todas as chaves que contém o padrão

        Args:
            pattern: Padrão a ser buscado nas chaves
        """
        with self.lock:
            keys_to_delete = [key for key in self.cache.keys() if pattern in key]
            for key in keys_to_delete:
                del self.cache[key]

    def cleanup_expired(self):
        """Remove entradas expiradas do cache"""
        with self.lock:
            now = datetime.now()
            expired_keys = [
                key for key, entry in self.cache.items()
                if now > entry['expires_at']
            ]
            for key in expired_keys:
                del self.cache[key]

    def get_stats(self) -> dict:
        """Retorna estatísticas do cache"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

            return {
                'total_entries': len(self.cache),
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate_percent': round(hit_rate, 2),
                'total_requests': total_requests
            }

    def get_size_estimate(self) -> dict:
        """Estima tamanho do cache em memória"""
        with self.lock:
            # Serializa cache para estimar tamanho
            cache_json = json.dumps({
                k: v['value'] for k, v in self.cache.items()
            })
            size_bytes = len(cache_json.encode('utf-8'))

            return {
                'size_bytes': size_bytes,
                'size_kb': round(size_bytes / 1024, 2),
                'size_mb': round(size_bytes / (1024 * 1024), 2)
            }


# Instância global do cache
cache = CacheService()


def cache_key_for_analysis(analysis_id: str) -> str:
    """Gera chave de cache para análise"""
    return f"analysis:{analysis_id}"


def cache_key_for_user_history(user_id: int, page: int = 1) -> str:
    """Gera chave de cache para histórico do usuário"""
    return f"user:{user_id}:history:page:{page}"


def cache_key_for_metrics(user_id: Optional[int] = None) -> str:
    """Gera chave de cache para métricas"""
    if user_id:
        return f"metrics:user:{user_id}"
    return "metrics:global"


def get_cached_analysis(analysis_id: str) -> Optional[dict]:
    """Busca análise no cache"""
    key = cache_key_for_analysis(analysis_id)
    return cache.get(key)


def set_cached_analysis(analysis_id: str, data: dict, ttl_seconds: int = 3600):
    """
    Armazena análise no cache
    TTL padrão: 1 hora (análises não mudam após processamento)
    """
    key = cache_key_for_analysis(analysis_id)
    cache.set(key, data, ttl_seconds)


def invalidate_user_cache(user_id: int):
    """Invalida todos os caches relacionados a um usuário"""
    cache.invalidate_pattern(f"user:{user_id}:")


def get_cached_metrics(user_id: Optional[int] = None) -> Optional[dict]:
    """Busca métricas no cache"""
    key = cache_key_for_metrics(user_id)
    return cache.get(key)


def set_cached_metrics(data: dict, user_id: Optional[int] = None, ttl_seconds: int = 60):
    """
    Armazena métricas no cache
    TTL padrão: 1 minuto (métricas mudam frequentemente)
    """
    key = cache_key_for_metrics(user_id)
    cache.set(key, data, ttl_seconds)


class CacheWarmer:
    """
    Aquecedor de cache
    Pré-carrega dados frequentemente acessados
    """

    @staticmethod
    def warm_user_data(user_id: int):
        """Aquece cache com dados do usuário"""
        from database import AnalysisModel, MetricsModel

        # Carrega histórico recente
        history = AnalysisModel.get_by_user(user_id, limit=20)
        key = cache_key_for_user_history(user_id, 1)
        cache.set(key, history, ttl_seconds=300)

        # Carrega métricas
        metrics = MetricsModel.get_summary(user_id)
        set_cached_metrics(metrics, user_id)

    @staticmethod
    def warm_global_metrics():
        """Aquece cache com métricas globais"""
        from database import MetricsModel

        metrics = MetricsModel.get_summary()
        set_cached_metrics(metrics)


def cache_decorator(ttl_seconds: int = 300, key_func=None):
    """
    Decorator para cachear resultados de funções

    Args:
        ttl_seconds: Tempo de vida do cache
        key_func: Função para gerar chave do cache (recebe args e kwargs)
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            # Gera chave do cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Usa nome da função e argumentos como chave
                cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"

            # Tenta buscar no cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Executa função e cacheia resultado
            result = f(*args, **kwargs)
            cache.set(cache_key, result, ttl_seconds)
            return result

        return wrapper
    return decorator


# Thread para limpeza periódica de cache expirado
def start_cache_cleanup_thread():
    """Inicia thread de limpeza de cache"""
    import time

    def cleanup_loop():
        while True:
            time.sleep(300)  # A cada 5 minutos
            cache.cleanup_expired()

    thread = threading.Thread(target=cleanup_loop, daemon=True)
    thread.start()
