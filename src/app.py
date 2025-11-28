"""
API Flask Principal
Sistema de Análise de Sentimentos em Tempo Real
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sys

# Importa módulos locais
from database import init_database, UserModel, AnalysisModel, MetricsModel, WebhookConfigModel
from auth import (
    AuthService, require_auth, rate_limit, validate_request_data,
    rate_limiter
)
from cache import (
    cache, get_cached_analysis, set_cached_analysis,
    get_cached_metrics, set_cached_metrics, start_cache_cleanup_thread
)
from queue_manager import enqueue_sentiment_analysis, get_queue_status, TaskPriority
from webhooks import configure_webhook, webhook_service


# Inicializa Flask
app = Flask(__name__)
CORS(app)

# Configurações
app.config['JSON_SORT_KEYS'] = False


@app.before_request
def before_request():
    """Executado antes de cada requisição"""
    request.start_time = datetime.now()


@app.after_request
def after_request(response):
    """Executado após cada requisição"""
    # Adiciona headers de segurança
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Adiciona tempo de processamento
    if hasattr(request, 'start_time'):
        duration = (datetime.now() - request.start_time).total_seconds()
        response.headers['X-Process-Time'] = f"{duration:.3f}s"

    return response


# ============================================================================
# ROTAS DE SAÚDE E STATUS
# ============================================================================

@app.route('/', methods=['GET'])
def root():
    """Rota raiz com informações da API"""
    return jsonify({
        'service': 'Sentiment Analysis API',
        'version': '1.0.0',
        'status': 'operational',
        'timestamp': datetime.now().isoformat(),
        'endpoints': {
            'auth': '/api/auth/*',
            'sentiment': '/api/sentiment/*',
            'metrics': '/api/metrics/*',
            'webhooks': '/api/webhooks/*',
            'worker': '/api/worker/*'
        },
        'documentation': 'https://github.com/your-repo/docs'
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check para monitoramento"""
    queue_stats = get_queue_status()
    cache_stats = cache.get_stats()

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'database': 'ok',
            'queue': {
                'status': 'ok',
                'pending': queue_stats['pending_count'],
                'processing': queue_stats['processing_count']
            },
            'cache': {
                'status': 'ok',
                'entries': cache_stats['total_entries'],
                'hit_rate': cache_stats['hit_rate_percent']
            }
        }
    })


# ============================================================================
# ROTAS DE AUTENTICAÇÃO
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
@rate_limit
@validate_request_data(['username', 'email', 'password'])
def register():
    """Registra novo usuário"""
    data = request.get_json()

    try:
        user = AuthService.register_user(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )

        return jsonify({
            'message': 'Usuário registrado com sucesso',
            'user': {
                'id': user['user_id'],
                'username': user['username'],
                'email': user['email']
            }
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'Erro ao registrar usuário'}), 500


@app.route('/api/auth/login', methods=['POST'])
@rate_limit
@validate_request_data(['email', 'password'])
def login():
    """Autentica usuário"""
    data = request.get_json()

    result = AuthService.login_user(
        email=data['email'],
        password=data['password']
    )

    if not result:
        return jsonify({'error': 'Credenciais inválidas'}), 401

    return jsonify({
        'message': 'Login realizado com sucesso',
        'access_token': result['access_token'],
        'token_type': result['token_type'],
        'user': {
            'id': result['user_id'],
            'username': result['username'],
            'email': result['email']
        }
    })


@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Retorna informações do usuário autenticado"""
    user = request.current_user

    return jsonify({
        'user': {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'created_at': user['created_at'],
            'last_login': user.get('last_login')
        }
    })


# ============================================================================
# ROTAS DE ANÁLISE DE SENTIMENTOS
# ============================================================================

@app.route('/api/sentiment/analyze', methods=['POST'])
@require_auth
@rate_limit
@validate_request_data(['text'])
def analyze_sentiment():
    """Submete texto para análise de sentimento"""
    data = request.get_json()
    user = request.current_user

    text = data['text']
    metadata = data.get('metadata', {})

    # Validações
    if not text or len(text.strip()) < 3:
        return jsonify({'error': 'Texto muito curto (mínimo 3 caracteres)'}), 400

    if len(text) > 5000:
        return jsonify({'error': 'Texto muito longo (máximo 5000 caracteres)'}), 400

    # Cria análise no banco
    analysis_id = AnalysisModel.create(
        user_id=user['id'],
        text=text,
        metadata=metadata
    )

    # Adiciona à fila de processamento
    # Análises urgentes podem ter prioridade alta
    priority = TaskPriority.HIGH if metadata.get('urgent') else TaskPriority.NORMAL

    enqueue_sentiment_analysis(
        analysis_id=analysis_id,
        text=text,
        user_id=user['id'],
        metadata=metadata,
        priority=priority
    )

    return jsonify({
        'message': 'Análise submetida com sucesso',
        'analysis_id': analysis_id,
        'status': 'pending',
        'estimated_time_seconds': 5,
        'check_result_url': f'/api/sentiment/result/{analysis_id}'
    }), 202


@app.route('/api/sentiment/result/<analysis_id>', methods=['GET'])
@require_auth
def get_analysis_result(analysis_id):
    """Obtém resultado de análise"""
    user = request.current_user

    # Tenta buscar no cache primeiro
    cached = get_cached_analysis(analysis_id)
    if cached:
        return jsonify({
            'analysis': cached,
            'cached': True
        })

    # Busca no banco
    analysis = AnalysisModel.get_by_id(analysis_id)

    if not analysis:
        return jsonify({'error': 'Análise não encontrada'}), 404

    # Verifica permissão
    if analysis['user_id'] != user['id']:
        return jsonify({'error': 'Acesso negado'}), 403

    # Cacheia se completada
    if analysis['status'] == 'completed':
        set_cached_analysis(analysis_id, analysis, ttl_seconds=3600)

    return jsonify({
        'analysis': analysis,
        'cached': False
    })


@app.route('/api/sentiment/history', methods=['GET'])
@require_auth
@rate_limit
def get_analysis_history():
    """Lista histórico de análises do usuário"""
    user = request.current_user

    # Paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    per_page = min(per_page, 100)  # Máximo 100 por página

    offset = (page - 1) * per_page

    # Busca análises
    analyses = AnalysisModel.get_by_user(
        user_id=user['id'],
        limit=per_page,
        offset=offset
    )

    return jsonify({
        'analyses': analyses,
        'page': page,
        'per_page': per_page,
        'total': len(analyses)
    })


# ============================================================================
# ROTAS DE MÉTRICAS
# ============================================================================

@app.route('/api/metrics/summary', methods=['GET'])
@require_auth
def get_metrics_summary():
    """Retorna resumo de métricas"""
    user = request.current_user

    # Tenta buscar do cache
    cached = get_cached_metrics(user['id'])
    if cached:
        return jsonify({
            'metrics': cached,
            'cached': True
        })

    # Calcula métricas
    metrics = MetricsModel.get_summary(user['id'])

    # Cacheia resultado
    set_cached_metrics(metrics, user['id'], ttl_seconds=60)

    return jsonify({
        'metrics': metrics,
        'cached': False
    })


@app.route('/api/metrics/global', methods=['GET'])
@require_auth
def get_global_metrics():
    """Retorna métricas globais do sistema"""
    # Tenta buscar do cache
    cached = get_cached_metrics(None)
    if cached:
        return jsonify({
            'metrics': cached,
            'cached': True
        })

    # Calcula métricas globais
    metrics = MetricsModel.get_summary(None)

    # Cacheia
    set_cached_metrics(metrics, None, ttl_seconds=60)

    return jsonify({
        'metrics': metrics,
        'cached': False
    })


# ============================================================================
# ROTAS DE WEBHOOKS
# ============================================================================

@app.route('/api/webhooks/configure', methods=['POST'])
@require_auth
@validate_request_data(['url', 'events'])
def configure_user_webhook():
    """Configura webhook para usuário"""
    data = request.get_json()
    user = request.current_user

    try:
        config_id = configure_webhook(
            user_id=user['id'],
            url=data['url'],
            events=data['events'],
            secret=data.get('secret')
        )

        return jsonify({
            'message': 'Webhook configurado com sucesso',
            'config_id': config_id,
            'url': data['url'],
            'events': data['events']
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/webhooks/test', methods=['POST'])
@require_auth
@validate_request_data(['url'])
def test_webhook():
    """Testa webhook"""
    data = request.get_json()

    result = webhook_service.test_webhook(
        url=data['url'],
        secret=data.get('secret')
    )

    return jsonify(result)


@app.route('/api/webhooks/list', methods=['GET'])
@require_auth
def list_webhooks():
    """Lista webhooks configurados"""
    user = request.current_user

    webhooks = WebhookConfigModel.get_by_user(user['id'])

    return jsonify({
        'webhooks': webhooks,
        'total': len(webhooks)
    })


# ============================================================================
# ROTAS DE WORKER (ADMIN)
# ============================================================================

@app.route('/api/worker/status', methods=['GET'])
def worker_status():
    """Status do worker e fila"""
    queue_stats = get_queue_status()
    cache_stats = cache.get_stats()

    return jsonify({
        'queue': queue_stats,
        'cache': cache_stats,
        'rate_limiter': {
            'active_identifiers': len(rate_limiter.requests)
        },
        'timestamp': datetime.now().isoformat()
    })


# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Erro 404"""
    return jsonify({
        'error': 'Endpoint não encontrado',
        'status': 404
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Erro 405"""
    return jsonify({
        'error': 'Método HTTP não permitido',
        'status': 405
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Erro 500"""
    return jsonify({
        'error': 'Erro interno do servidor',
        'status': 500
    }), 500


# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

def initialize_app():
    """Inicializa componentes da aplicação"""
    print("=" * 80)
    print("🚀 Iniciando Sistema de Análise de Sentimentos")
    print("=" * 80)

    # Inicializa banco de dados
    print("\n📦 Inicializando banco de dados...")
    init_database()

    # Inicia thread de limpeza de cache
    print("\n🧹 Iniciando limpeza automática de cache...")
    start_cache_cleanup_thread()

    print("\n✅ Aplicação inicializada com sucesso!")
    print("\n" + "=" * 80)
    print("📡 API disponível em: http://localhost:5000")
    print("📚 Documentação: /")
    print("❤️  Health check: /health")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    initialize_app()

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
