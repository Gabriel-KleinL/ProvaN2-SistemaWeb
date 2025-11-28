"""
Worker de Processamento de Análises
Processa fila de análises de sentimento de forma assíncrona
"""

import time
import signal
import sys
from datetime import datetime
from typing import Optional

from database import AnalysisModel, init_database
from queue_manager import get_next_task, complete_task, fail_task, Task
from sentiment_analyzer import analyzer
from webhooks import send_analysis_webhook
from cache import set_cached_analysis


class SentimentWorker:
    """Worker para processar análises de sentimento"""

    def __init__(self):
        self.running = False
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = None

    def start(self):
        """Inicia o worker"""
        self.running = True
        self.start_time = datetime.now()

        print("=" * 80)
        print("⚡ Worker de Análise de Sentimentos Iniciado")
        print("=" * 80)
        print(f"Hora de início: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("Aguardando tarefas na fila...")
        print("=" * 80 + "\n")

        # Registra handler para shutdown gracioso
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Loop principal
        while self.running:
            try:
                self._process_next_task()
            except Exception as e:
                print(f"❌ Erro no loop principal: {e}")
                time.sleep(5)

    def stop(self):
        """Para o worker"""
        self.running = False
        print("\n🛑 Parando worker...")

    def _signal_handler(self, signum, frame):
        """Handler para sinais de shutdown"""
        print(f"\n📡 Recebido sinal {signum}")
        self.stop()

    def _process_next_task(self):
        """Processa próxima tarefa da fila"""
        # Busca próxima tarefa (timeout de 1 segundo)
        task = get_next_task(timeout=1.0)

        if not task:
            # Sem tarefas, aguarda
            time.sleep(0.5)
            return

        # Processa tarefa
        print(f"\n{'='*80}")
        print(f"📝 Processando tarefa: {task.task_id}")
        print(f"Tentativa: {task.attempts}/{task.max_attempts}")
        print(f"Prioridade: {task.priority.name}")
        print(f"Criada em: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            self._process_sentiment_analysis(task)
            print(f"✅ Tarefa completada com sucesso!")
            self.processed_count += 1

        except Exception as e:
            print(f"❌ Erro ao processar tarefa: {e}")
            fail_task(
                task.task_id,
                error_message=str(e),
                retry=True
            )
            self.failed_count += 1

        # Exibe estatísticas
        self._print_stats()

    def _process_sentiment_analysis(self, task: Task):
        """
        Processa análise de sentimento

        Args:
            task: Tarefa a processar
        """
        payload = task.payload
        analysis_id = payload['analysis_id']
        text = payload['text']
        user_id = payload['user_id']
        metadata = payload.get('metadata', {})

        # Atualiza status para processando
        AnalysisModel.update_status(analysis_id, 'processing')

        # Analisa sentimento
        print(f"🔍 Analisando texto: '{text[:50]}...'")
        result = analyzer.analyze(text)

        print(f"📊 Resultado:")
        print(f"   - Sentimento: {result.sentiment}")
        print(f"   - Score: {result.score}")
        print(f"   - Confiança: {result.confidence}")
        print(f"   - Palavras-chave: {', '.join(result.keywords[:5])}")

        # Salva resultado no banco
        AnalysisModel.update_result(
            analysis_id=analysis_id,
            sentiment=result.sentiment,
            score=result.score,
            confidence=result.confidence
        )

        # Busca análise completa
        analysis = AnalysisModel.get_by_id(analysis_id)

        # Cacheia resultado
        set_cached_analysis(analysis_id, analysis, ttl_seconds=3600)

        # Envia webhooks
        try:
            print(f"🔔 Enviando webhooks...")
            send_analysis_webhook(
                analysis_id=analysis_id,
                user_id=user_id,
                sentiment=result.sentiment,
                score=result.score,
                confidence=result.confidence,
                metadata={**metadata, 'text': text}
            )
            print(f"✓ Webhooks enviados")
        except Exception as e:
            print(f"⚠️  Erro ao enviar webhooks: {e}")

        # Marca tarefa como completada
        complete_task(task.task_id, {
            'sentiment': result.sentiment,
            'score': result.score,
            'confidence': result.confidence
        })

    def _print_stats(self):
        """Imprime estatísticas do worker"""
        uptime = datetime.now() - self.start_time
        total = self.processed_count + self.failed_count

        print(f"\n📈 Estatísticas:")
        print(f"   - Processadas: {self.processed_count}")
        print(f"   - Falhas: {self.failed_count}")
        print(f"   - Total: {total}")
        print(f"   - Taxa de sucesso: {(self.processed_count/total*100) if total > 0 else 0:.1f}%")
        print(f"   - Tempo ativo: {uptime}")
        print(f"{'='*80}")


def process_pending_analyses():
    """
    Processa análises pendentes no banco
    Útil para processar análises que ficaram pendentes
    """
    print("🔄 Processando análises pendentes do banco de dados...")

    pending = AnalysisModel.get_pending()
    print(f"Encontradas {len(pending)} análises pendentes")

    for analysis in pending:
        print(f"\nProcessando análise {analysis['id']}...")

        try:
            # Analisa
            result = analyzer.analyze(analysis['text'])

            # Atualiza banco
            AnalysisModel.update_result(
                analysis_id=analysis['id'],
                sentiment=result.sentiment,
                score=result.score,
                confidence=result.confidence
            )

            print(f"✓ Análise {analysis['id']} completada: {result.sentiment}")

        except Exception as e:
            print(f"✗ Erro ao processar {analysis['id']}: {e}")
            AnalysisModel.update_status(
                analysis['id'],
                'failed',
                error_message=str(e)
            )

    print("\n✅ Processamento de análises pendentes concluído!")


if __name__ == '__main__':
    # Inicializa banco de dados
    init_database()

    # Verifica argumentos
    if len(sys.argv) > 1 and sys.argv[1] == '--process-pending':
        # Processa análises pendentes
        process_pending_analyses()
    else:
        # Inicia worker
        worker = SentimentWorker()
        try:
            worker.start()
        except KeyboardInterrupt:
            print("\n⚠️  Interrupção detectada")
        finally:
            worker.stop()
            print(f"\n📊 Resumo Final:")
            print(f"   Total processado: {worker.processed_count}")
            print(f"   Total falhas: {worker.failed_count}")
            print(f"   Tempo de execução: {datetime.now() - worker.start_time}")
            print("\n👋 Worker encerrado. Até logo!")
