"""
Testes de integração
Testa o fluxo completo da aplicação
"""

import sys
import os
import time

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import init_database, UserModel, AnalysisModel
from auth import AuthService
from queue_manager import enqueue_sentiment_analysis, get_next_task, complete_task
from sentiment_analyzer import analyzer
from cache import cache, get_cached_analysis, set_cached_analysis


class TestIntegration:
    """Testes de integração do sistema"""

    def setup_method(self):
        """Configuração antes de cada teste"""
        # Limpa cache
        cache.clear()

    def test_complete_analysis_flow(self):
        """Testa fluxo completo de análise"""
        print("\n=== Testando Fluxo Completo de Análise ===\n")

        # 1. Registra usuário
        print("1. Registrando usuário...")
        user = AuthService.register_user(
            username='integrationtest',
            email='integration@test.com',
            password='test123'
        )
        print(f"   ✓ Usuário criado: ID {user['user_id']}")

        # 2. Cria análise
        print("\n2. Criando análise...")
        text = "Este produto é absolutamente incrível! Estou muito satisfeito."
        analysis_id = AnalysisModel.create(
            user_id=user['user_id'],
            text=text,
            metadata={'source': 'test'}
        )
        print(f"   ✓ Análise criada: ID {analysis_id}")

        # 3. Adiciona à fila
        print("\n3. Adicionando à fila...")
        enqueue_sentiment_analysis(
            analysis_id=analysis_id,
            text=text,
            user_id=user['user_id']
        )
        print("   ✓ Tarefa enfileirada")

        # 4. Processa da fila
        print("\n4. Processando da fila...")
        task = get_next_task(timeout=1.0)
        assert task is not None
        assert task.task_id == analysis_id
        print(f"   ✓ Tarefa recuperada: {task.task_id}")

        # 5. Analisa sentimento
        print("\n5. Analisando sentimento...")
        result = analyzer.analyze(text)
        print(f"   ✓ Sentimento: {result.sentiment}")
        print(f"   ✓ Score: {result.score}")
        print(f"   ✓ Confiança: {result.confidence}")

        # 6. Salva resultado
        print("\n6. Salvando resultado...")
        AnalysisModel.update_result(
            analysis_id=analysis_id,
            sentiment=result.sentiment,
            score=result.score,
            confidence=result.confidence
        )
        complete_task(task.task_id)
        print("   ✓ Resultado salvo")

        # 7. Verifica análise completa
        print("\n7. Verificando análise completa...")
        analysis = AnalysisModel.get_by_id(analysis_id)
        assert analysis['status'] == 'completed'
        assert analysis['sentiment'] == result.sentiment
        print(f"   ✓ Análise completada com sucesso")

        print("\n✅ Fluxo completo testado com sucesso!\n")

    def test_cache_integration(self):
        """Testa integração com cache"""
        print("\n=== Testando Integração com Cache ===\n")

        # 1. Cria análise
        print("1. Criando dados de teste...")
        analysis_data = {
            'id': 'test-cache-123',
            'text': 'Teste de cache',
            'sentiment': 'positive',
            'score': 0.8,
            'status': 'completed'
        }

        # 2. Armazena no cache
        print("\n2. Armazenando no cache...")
        set_cached_analysis('test-cache-123', analysis_data, ttl_seconds=10)
        print("   ✓ Dados cacheados")

        # 3. Recupera do cache
        print("\n3. Recuperando do cache...")
        cached = get_cached_analysis('test-cache-123')
        assert cached is not None
        assert cached['sentiment'] == 'positive'
        print("   ✓ Cache hit")

        # 4. Verifica estatísticas
        print("\n4. Verificando estatísticas...")
        stats = cache.get_stats()
        assert stats['hits'] > 0
        print(f"   ✓ Cache hits: {stats['hits']}")
        print(f"   ✓ Cache misses: {stats['misses']}")
        print(f"   ✓ Hit rate: {stats['hit_rate_percent']}%")

        print("\n✅ Integração com cache testada com sucesso!\n")

    def test_user_history(self):
        """Testa histórico de análises do usuário"""
        print("\n=== Testando Histórico de Usuário ===\n")

        # 1. Cria usuário
        print("1. Criando usuário...")
        user = AuthService.register_user(
            username='historytest',
            email='history@test.com',
            password='test123'
        )
        user_id = user['user_id']
        print(f"   ✓ Usuário criado: ID {user_id}")

        # 2. Cria múltiplas análises
        print("\n2. Criando múltiplas análises...")
        texts = [
            "Produto excelente!",
            "Péssimo atendimento.",
            "Produto OK, nada demais."
        ]

        analysis_ids = []
        for text in texts:
            analysis_id = AnalysisModel.create(
                user_id=user_id,
                text=text
            )
            analysis_ids.append(analysis_id)

            # Processa análise
            result = analyzer.analyze(text)
            AnalysisModel.update_result(
                analysis_id=analysis_id,
                sentiment=result.sentiment,
                score=result.score,
                confidence=result.confidence
            )

        print(f"   ✓ {len(analysis_ids)} análises criadas")

        # 3. Busca histórico
        print("\n3. Buscando histórico...")
        history = AnalysisModel.get_by_user(user_id)
        assert len(history) == 3
        print(f"   ✓ {len(history)} análises encontradas")

        # 4. Verifica sentimentos
        print("\n4. Verificando distribuição de sentimentos...")
        sentiments = [a['sentiment'] for a in history]
        print(f"   ✓ Positivos: {sentiments.count('positive')}")
        print(f"   ✓ Negativos: {sentiments.count('negative')}")
        print(f"   ✓ Neutros: {sentiments.count('neutral')}")

        print("\n✅ Histórico testado com sucesso!\n")

    def test_authentication_flow(self):
        """Testa fluxo de autenticação"""
        print("\n=== Testando Fluxo de Autenticação ===\n")

        # 1. Registra usuário
        print("1. Registrando usuário...")
        user = AuthService.register_user(
            username='authtest',
            email='auth@test.com',
            password='secure123'
        )
        print(f"   ✓ Usuário registrado: {user['email']}")

        # 2. Login com credenciais corretas
        print("\n2. Testando login correto...")
        result = AuthService.login_user('auth@test.com', 'secure123')
        assert result is not None
        assert 'access_token' in result
        print(f"   ✓ Token gerado: {result['access_token'][:20]}...")

        # 3. Login com senha errada
        print("\n3. Testando login com senha errada...")
        result_wrong = AuthService.login_user('auth@test.com', 'wrong')
        assert result_wrong is None
        print("   ✓ Login negado corretamente")

        # 4. Verifica token
        print("\n4. Verificando token...")
        payload = AuthService.decode_token(result['access_token'])
        assert payload is not None
        assert payload['email'] == 'auth@test.com'
        print(f"   ✓ Token válido para: {payload['email']}")

        print("\n✅ Autenticação testada com sucesso!\n")

    def test_queue_processing(self):
        """Testa processamento de fila"""
        print("\n=== Testando Processamento de Fila ===\n")

        # 1. Cria múltiplas tarefas
        print("1. Criando múltiplas tarefas...")
        num_tasks = 5
        task_ids = []

        for i in range(num_tasks):
            analysis_id = f"queue-test-{i}"
            task = enqueue_sentiment_analysis(
                analysis_id=analysis_id,
                text=f"Texto de teste {i}",
                user_id=1
            )
            task_ids.append(analysis_id)

        print(f"   ✓ {num_tasks} tarefas enfileiradas")

        # 2. Processa todas as tarefas
        print("\n2. Processando tarefas...")
        processed = 0
        while processed < num_tasks:
            task = get_next_task(timeout=0.5)
            if task:
                complete_task(task.task_id)
                processed += 1
                print(f"   ✓ Tarefa {processed}/{num_tasks} processada")

        print(f"\n   ✓ Todas as {num_tasks} tarefas processadas")

        print("\n✅ Fila testada com sucesso!\n")

    def test_metrics_calculation(self):
        """Testa cálculo de métricas"""
        print("\n=== Testando Cálculo de Métricas ===\n")

        # 1. Cria usuário
        print("1. Criando usuário de teste...")
        user = AuthService.register_user(
            username='metricstest',
            email='metrics@test.com',
            password='test123'
        )
        user_id = user['user_id']
        print(f"   ✓ Usuário criado: ID {user_id}")

        # 2. Cria análises variadas
        print("\n2. Criando análises com sentimentos variados...")
        test_data = [
            ("Excelente produto!", "positive"),
            ("Muito bom!", "positive"),
            ("Péssimo!", "negative"),
            ("OK", "neutral")
        ]

        for text, expected_sentiment in test_data:
            analysis_id = AnalysisModel.create(user_id=user_id, text=text)
            result = analyzer.analyze(text)
            AnalysisModel.update_result(
                analysis_id=analysis_id,
                sentiment=result.sentiment,
                score=result.score,
                confidence=result.confidence
            )

        print(f"   ✓ {len(test_data)} análises criadas")

        # 3. Calcula métricas
        print("\n3. Calculando métricas...")
        from database import MetricsModel
        metrics = MetricsModel.get_summary(user_id)

        print(f"   ✓ Total de análises: {metrics['total_analyses']}")
        print(f"   ✓ Distribuição:")
        for sentiment, count in metrics['sentiment_distribution'].items():
            print(f"      - {sentiment}: {count}")
        print(f"   ✓ Score médio: {metrics['average_score']}")

        assert metrics['total_analyses'] == 4
        print("\n✅ Métricas testadas com sucesso!\n")


def run_all_tests():
    """Executa todos os testes de integração"""
    print("=" * 80)
    print("🧪 Executando Testes de Integração")
    print("=" * 80)

    # Inicializa banco de dados
    print("\n📦 Inicializando banco de dados...")
    init_database()

    test = TestIntegration()

    tests = [
        test.test_complete_analysis_flow,
        test.test_cache_integration,
        test.test_user_history,
        test.test_authentication_flow,
        test.test_queue_processing,
        test.test_metrics_calculation
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test.setup_method()
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ {test_func.__name__} falhou: {e}\n")
            failed += 1
        except Exception as e:
            print(f"\n✗ {test_func.__name__} erro: {e}\n")
            failed += 1

    print("=" * 80)
    print(f"📊 Resultado Final: {passed} passou, {failed} falhou")
    print("=" * 80 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
