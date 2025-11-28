"""
Testes para a API Flask
"""

import sys
import os
import json

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from app import app, initialize_app


@pytest.fixture
def client():
    """Fixture para cliente de testes"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_token(client):
    """Fixture para obter token de autenticação"""
    # Registra usuário de teste
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpass123'
    })

    # Faz login
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })

    data = json.loads(response.data)
    return data['access_token']


class TestHealthEndpoints:
    """Testes de endpoints de saúde"""

    def test_root(self, client):
        """Testa endpoint raiz"""
        response = client.get('/')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'service' in data
        assert data['service'] == 'Sentiment Analysis API'
        print("✓ Teste de endpoint raiz passou")

    def test_health_check(self, client):
        """Testa health check"""
        response = client.get('/health')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'components' in data
        print("✓ Teste de health check passou")


class TestAuthEndpoints:
    """Testes de autenticação"""

    def test_register_success(self, client):
        """Testa registro de usuário com sucesso"""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'pass123'
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'user' in data
        assert data['user']['email'] == 'new@example.com'
        print("✓ Teste de registro passou")

    def test_register_duplicate_email(self, client):
        """Testa registro com email duplicado"""
        # Primeiro registro
        client.post('/api/auth/register', json={
            'username': 'user1',
            'email': 'duplicate@example.com',
            'password': 'pass123'
        })

        # Segundo registro com mesmo email
        response = client.post('/api/auth/register', json={
            'username': 'user2',
            'email': 'duplicate@example.com',
            'password': 'pass456'
        })

        assert response.status_code == 400
        print("✓ Teste de email duplicado passou")

    def test_register_missing_fields(self, client):
        """Testa registro sem campos obrigatórios"""
        response = client.post('/api/auth/register', json={
            'username': 'incomplete'
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'missing_fields' in data
        print("✓ Teste de campos faltando passou")

    def test_login_success(self, client):
        """Testa login com sucesso"""
        # Registra usuário
        client.post('/api/auth/register', json={
            'username': 'loginuser',
            'email': 'login@example.com',
            'password': 'pass123'
        })

        # Faz login
        response = client.post('/api/auth/login', json={
            'email': 'login@example.com',
            'password': 'pass123'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'
        print("✓ Teste de login passou")

    def test_login_wrong_password(self, client):
        """Testa login com senha errada"""
        # Registra usuário
        client.post('/api/auth/register', json={
            'username': 'wrongpass',
            'email': 'wrong@example.com',
            'password': 'correct'
        })

        # Tenta login com senha errada
        response = client.post('/api/auth/login', json={
            'email': 'wrong@example.com',
            'password': 'incorrect'
        })

        assert response.status_code == 401
        print("✓ Teste de senha errada passou")

    def test_get_current_user(self, client, auth_token):
        """Testa obtenção de usuário atual"""
        response = client.get(
            '/api/auth/me',
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'user' in data
        print("✓ Teste de usuário atual passou")

    def test_unauthorized_access(self, client):
        """Testa acesso sem autenticação"""
        response = client.get('/api/auth/me')

        assert response.status_code == 401
        print("✓ Teste de acesso não autorizado passou")


class TestSentimentEndpoints:
    """Testes de análise de sentimentos"""

    def test_analyze_sentiment(self, client, auth_token):
        """Testa submissão de análise"""
        response = client.post(
            '/api/sentiment/analyze',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'text': 'Este produto é incrível!',
                'metadata': {'product_id': '123'}
            }
        )

        assert response.status_code == 202
        data = json.loads(response.data)
        assert 'analysis_id' in data
        assert data['status'] == 'pending'
        print("✓ Teste de análise passou")

    def test_analyze_short_text(self, client, auth_token):
        """Testa análise de texto muito curto"""
        response = client.post(
            '/api/sentiment/analyze',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={'text': 'ab'}
        )

        assert response.status_code == 400
        print("✓ Teste de texto curto passou")

    def test_get_analysis_result(self, client, auth_token):
        """Testa obtenção de resultado"""
        # Submete análise
        response1 = client.post(
            '/api/sentiment/analyze',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={'text': 'Produto excelente!'}
        )
        analysis_id = json.loads(response1.data)['analysis_id']

        # Busca resultado
        response2 = client.get(
            f'/api/sentiment/result/{analysis_id}',
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response2.status_code == 200
        data = json.loads(response2.data)
        assert 'analysis' in data
        print("✓ Teste de resultado passou")

    def test_get_analysis_history(self, client, auth_token):
        """Testa listagem de histórico"""
        response = client.get(
            '/api/sentiment/history',
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'analyses' in data
        assert isinstance(data['analyses'], list)
        print("✓ Teste de histórico passou")


class TestMetricsEndpoints:
    """Testes de métricas"""

    def test_get_metrics_summary(self, client, auth_token):
        """Testa resumo de métricas"""
        response = client.get(
            '/api/metrics/summary',
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'metrics' in data
        print("✓ Teste de métricas passou")

    def test_get_global_metrics(self, client, auth_token):
        """Testa métricas globais"""
        response = client.get(
            '/api/metrics/global',
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'metrics' in data
        print("✓ Teste de métricas globais passou")


class TestWebhookEndpoints:
    """Testes de webhooks"""

    def test_configure_webhook(self, client, auth_token):
        """Testa configuração de webhook"""
        response = client.post(
            '/api/webhooks/configure',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'url': 'https://example.com/webhook',
                'events': ['analysis_complete']
            }
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'config_id' in data
        print("✓ Teste de configuração de webhook passou")

    def test_configure_webhook_invalid_url(self, client, auth_token):
        """Testa webhook com URL inválida"""
        response = client.post(
            '/api/webhooks/configure',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={
                'url': 'invalid-url',
                'events': ['analysis_complete']
            }
        )

        assert response.status_code == 400
        print("✓ Teste de URL inválida passou")

    def test_list_webhooks(self, client, auth_token):
        """Testa listagem de webhooks"""
        response = client.get(
            '/api/webhooks/list',
            headers={'Authorization': f'Bearer {auth_token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'webhooks' in data
        print("✓ Teste de listagem de webhooks passou")


class TestWorkerEndpoints:
    """Testes de worker"""

    def test_worker_status(self, client):
        """Testa status do worker"""
        response = client.get('/api/worker/status')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'queue' in data
        assert 'cache' in data
        print("✓ Teste de status do worker passou")


def run_all_tests():
    """Executa todos os testes"""
    print("=" * 80)
    print("🧪 Executando Testes da API")
    print("=" * 80 + "\n")

    # Inicializa app
    initialize_app()

    # Executa testes com pytest
    import subprocess
    result = subprocess.run(
        ['pytest', __file__, '-v'],
        capture_output=False
    )

    return result.returncode == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
