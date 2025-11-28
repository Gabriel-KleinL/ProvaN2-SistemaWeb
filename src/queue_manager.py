"""
Gerenciador de filas para processamento assíncrono
Simula sistema de filas (RabbitMQ/Celery) usando estruturas em memória
"""

import threading
import queue
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum


class TaskPriority(Enum):
    """Prioridades de tarefas"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0


class TaskStatus(Enum):
    """Status de tarefas"""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'
    RETRY = 'retry'


class Task:
    """Representa uma tarefa na fila"""

    def __init__(self, task_id: str, task_type: str, payload: Dict[str, Any],
                 priority: TaskPriority = TaskPriority.NORMAL):
        self.task_id = task_id
        self.task_type = task_type
        self.payload = payload
        self.priority = priority
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.attempts = 0
        self.max_attempts = 3
        self.error_message = None

    def __lt__(self, other):
        """Comparação para PriorityQueue"""
        return self.priority.value < other.priority.value

    def to_dict(self) -> Dict[str, Any]:
        """Serializa tarefa para dicionário"""
        return {
            'task_id': self.task_id,
            'task_type': self.task_type,
            'payload': self.payload,
            'priority': self.priority.name,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'error_message': self.error_message
        }


class QueueManager:
    """
    Gerenciador de filas de processamento
    Em produção, seria substituído por RabbitMQ/Celery/Redis Queue
    """

    def __init__(self, persistence_dir: Optional[str] = None):
        self.pending_queue = queue.PriorityQueue()
        self.processing = {}  # {task_id: Task}
        self.completed = {}  # {task_id: Task}
        self.failed = {}  # {task_id: Task} - Dead Letter Queue
        self.lock = threading.Lock()

        # Persistência opcional
        self.persistence_dir = persistence_dir
        if persistence_dir and not os.path.exists(persistence_dir):
            os.makedirs(persistence_dir)

        # Estatísticas
        self.stats = {
            'total_enqueued': 0,
            'total_processed': 0,
            'total_failed': 0,
            'total_retried': 0
        }

    def enqueue(self, task: Task) -> bool:
        """
        Adiciona tarefa à fila

        Args:
            task: Tarefa a ser adicionada

        Returns:
            True se adicionada com sucesso
        """
        with self.lock:
            self.pending_queue.put(task)
            self.stats['total_enqueued'] += 1

            # Persiste se configurado
            if self.persistence_dir:
                self._persist_task(task, 'pending')

            return True

    def dequeue(self, timeout: float = 1.0) -> Optional[Task]:
        """
        Remove e retorna próxima tarefa da fila

        Args:
            timeout: Tempo máximo de espera em segundos

        Returns:
            Próxima tarefa ou None se fila vazia
        """
        try:
            task = self.pending_queue.get(timeout=timeout)
            with self.lock:
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.now()
                task.attempts += 1
                self.processing[task.task_id] = task

                if self.persistence_dir:
                    self._persist_task(task, 'processing')

            return task
        except queue.Empty:
            return None

    def mark_completed(self, task_id: str, result: Optional[Dict] = None):
        """Marca tarefa como completada"""
        with self.lock:
            if task_id in self.processing:
                task = self.processing.pop(task_id)
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                if result:
                    task.payload['result'] = result
                self.completed[task_id] = task
                self.stats['total_processed'] += 1

                if self.persistence_dir:
                    self._persist_task(task, 'completed')
                    self._remove_persistence(task_id, 'processing')

    def mark_failed(self, task_id: str, error_message: str, retry: bool = True):
        """
        Marca tarefa como falha

        Args:
            task_id: ID da tarefa
            error_message: Mensagem de erro
            retry: Se deve tentar novamente
        """
        with self.lock:
            if task_id not in self.processing:
                return

            task = self.processing.pop(task_id)
            task.error_message = error_message

            # Verifica se deve retentar
            if retry and task.attempts < task.max_attempts:
                task.status = TaskStatus.RETRY
                self.pending_queue.put(task)
                self.stats['total_retried'] += 1

                if self.persistence_dir:
                    self._persist_task(task, 'pending')
            else:
                # Move para Dead Letter Queue
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                self.failed[task_id] = task
                self.stats['total_failed'] += 1

                if self.persistence_dir:
                    self._persist_task(task, 'failed')

            if self.persistence_dir:
                self._remove_persistence(task_id, 'processing')

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtém status de uma tarefa"""
        with self.lock:
            # Procura em todas as filas
            if task_id in self.processing:
                return self.processing[task_id].to_dict()
            if task_id in self.completed:
                return self.completed[task_id].to_dict()
            if task_id in self.failed:
                return self.failed[task_id].to_dict()

            # Procura na fila pendente (menos eficiente)
            # Em produção, usaríamos Redis para lookup O(1)
            return None

    def get_queue_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da fila"""
        with self.lock:
            return {
                'pending_count': self.pending_queue.qsize(),
                'processing_count': len(self.processing),
                'completed_count': len(self.completed),
                'failed_count': len(self.failed),
                'total_enqueued': self.stats['total_enqueued'],
                'total_processed': self.stats['total_processed'],
                'total_failed': self.stats['total_failed'],
                'total_retried': self.stats['total_retried']
            }

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Lista tarefas pendentes (sem remover da fila)"""
        with self.lock:
            # Copia fila para lista
            tasks = []
            temp_list = []

            while not self.pending_queue.empty():
                task = self.pending_queue.get()
                tasks.append(task.to_dict())
                temp_list.append(task)

            # Restaura fila
            for task in temp_list:
                self.pending_queue.put(task)

            return tasks

    def clear_completed(self):
        """Limpa tarefas completadas (para economizar memória)"""
        with self.lock:
            self.completed.clear()

    def _persist_task(self, task: Task, status: str):
        """Persiste tarefa em arquivo"""
        if not self.persistence_dir:
            return

        filepath = os.path.join(
            self.persistence_dir,
            f"{status}_{task.task_id}.json"
        )

        with open(filepath, 'w') as f:
            json.dump(task.to_dict(), f, indent=2)

    def _remove_persistence(self, task_id: str, status: str):
        """Remove arquivo de persistência"""
        if not self.persistence_dir:
            return

        filepath = os.path.join(
            self.persistence_dir,
            f"{status}_{task_id}.json"
        )

        if os.path.exists(filepath):
            os.remove(filepath)


# Instância global do gerenciador de filas
_queue_dir = os.path.join(os.path.dirname(__file__), '..', 'queue_data')
queue_manager = QueueManager(persistence_dir=_queue_dir)


def enqueue_sentiment_analysis(analysis_id: str, text: str, user_id: int,
                                metadata: Optional[Dict] = None,
                                priority: TaskPriority = TaskPriority.NORMAL) -> Task:
    """
    Adiciona análise de sentimento à fila

    Args:
        analysis_id: ID da análise
        text: Texto a ser analisado
        user_id: ID do usuário
        metadata: Metadados adicionais
        priority: Prioridade da tarefa

    Returns:
        Tarefa criada
    """
    task = Task(
        task_id=analysis_id,
        task_type='sentiment_analysis',
        payload={
            'analysis_id': analysis_id,
            'text': text,
            'user_id': user_id,
            'metadata': metadata or {}
        },
        priority=priority
    )

    queue_manager.enqueue(task)
    return task


def get_next_task(timeout: float = 1.0) -> Optional[Task]:
    """Obtém próxima tarefa da fila"""
    return queue_manager.dequeue(timeout)


def complete_task(task_id: str, result: Optional[Dict] = None):
    """Marca tarefa como completada"""
    queue_manager.mark_completed(task_id, result)


def fail_task(task_id: str, error_message: str, retry: bool = True):
    """Marca tarefa como falha"""
    queue_manager.mark_failed(task_id, error_message, retry)


def get_queue_status() -> Dict[str, Any]:
    """Obtém status da fila"""
    return queue_manager.get_queue_stats()
