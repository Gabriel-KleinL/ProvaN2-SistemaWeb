# Sistema de Análise de Sentimentos em Tempo Real

Sistema web moderno para análise de sentimentos com processamento assíncrono, cache distribuído e arquitetura escalável.

## 🎯 Sobre o Projeto

Este projeto foi desenvolvido como avaliação de Sistemas Web, demonstrando:

- **Arquitetura Moderna**: Microserviços, filas, cache e processamento assíncrono
- **RESTful API**: Flask com autenticação JWT e rate limiting
- **Processamento Inteligente**: Análise de sentimentos em português
- **Sistema de Filas**: Processamento assíncrono de tarefas
- **Webhooks**: Notificações em tempo real
- **Cache**: Sistema de cache para otimização de performance

## 📁 Estrutura do Projeto

```
ProvaN2-SistemaWeb/
├── docs/                  # Documentação completa
│   ├── README.md         # Documentação principal
│   └── arquitetura.md    # Diagramas de arquitetura
├── schema/               # Schema do banco de dados
│   └── database.json     # Definição de tabelas e relacionamentos
├── src/                  # Código fonte
│   ├── app.py           # API Flask principal
│   ├── worker.py        # Worker de processamento
│   ├── auth.py          # Autenticação JWT
│   ├── cache.py         # Sistema de cache
│   ├── database.py      # Modelos e conexão DB
│   ├── queue_manager.py # Gerenciador de filas
│   ├── sentiment_analyzer.py  # Análise de sentimentos
│   └── webhooks.py      # Sistema de webhooks
└── tests/               # Testes
    ├── test_api.py      # Testes da API
    ├── test_sentiment.py # Testes de análise
    └── test_integration.py # Testes de integração
```

## 🚀 Instalação e Execução

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Inicializar banco de dados

```bash
python src/database.py
```

### 3. Executar API (Terminal 1)

```bash
python src/app.py
```

A API estará disponível em: `http://localhost:5000`

### 4. Executar Worker (Terminal 2)

```bash
python src/worker.py
```

### 5. Executar Testes

```bash
# Testes de sentimentos
python tests/test_sentiment.py

# Testes de integração
python tests/test_integration.py

# Testes da API (requer pytest)
pytest tests/test_api.py -v
```

## 📡 Testando com Postman

### 1. Registrar Usuário

```
POST http://localhost:5000/api/auth/register
Content-Type: application/json

{
  "username": "teste",
  "email": "teste@example.com",
  "password": "senha123"
}
```

### 2. Login

```
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
  "email": "teste@example.com",
  "password": "senha123"
}
```

**Resposta:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {...}
}
```

Copie o `access_token` para usar nas próximas requisições.

### 3. Enviar Texto para Análise

```
POST http://localhost:5000/api/sentiment/analyze
Authorization: Bearer SEU_TOKEN_AQUI
Content-Type: application/json

{
  "text": "Este produto é absolutamente incrível! Estou muito satisfeito com a qualidade e o atendimento.",
  "metadata": {
    "product_id": "12345",
    "source": "review"
  }
}
```

**Resposta:**
```json
{
  "message": "Análise submetida com sucesso",
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "estimated_time_seconds": 5
}
```

### 4. Verificar Resultado

Aguarde alguns segundos para o worker processar, então:

```
GET http://localhost:5000/api/sentiment/result/550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer SEU_TOKEN_AQUI
```

**Resposta:**
```json
{
  "analysis": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "Este produto é absolutamente incrível!...",
    "sentiment": "positive",
    "score": 0.875,
    "confidence": 0.92,
    "status": "completed",
    "created_at": "2025-11-28T10:30:00",
    "processed_at": "2025-11-28T10:30:05"
  }
}
```

### 5. Ver Histórico de Análises

```
GET http://localhost:5000/api/sentiment/history
Authorization: Bearer SEU_TOKEN_AQUI
```

### 6. Ver Métricas

```
GET http://localhost:5000/api/metrics/summary
Authorization: Bearer SEU_TOKEN_AQUI
```

**Resposta:**
```json
{
  "metrics": {
    "total_analyses": 15,
    "sentiment_distribution": {
      "positive": 8,
      "negative": 3,
      "neutral": 4
    },
    "average_score": 0.234
  }
}
```

### 7. Configurar Webhook

```
POST http://localhost:5000/api/webhooks/configure
Authorization: Bearer SEU_TOKEN_AQUI
Content-Type: application/json

{
  "url": "https://webhook.site/seu-webhook-id",
  "events": ["analysis_complete", "negative_sentiment"]
}
```

## 🏗️ Arquitetura

O sistema utiliza uma arquitetura moderna em camadas:

- **API Gateway**: Flask com middleware de autenticação e rate limiting
- **Camada de Serviços**: Análise de sentimentos, cache, filas, webhooks
- **Worker Assíncrono**: Processa análises em segundo plano
- **Persistência**: SQLite com índices otimizados

Ver documentação completa em `docs/arquitetura.md`

## 🎯 Componentes Principais

### 1. API REST (Flask)
- Autenticação JWT
- Rate limiting
- CORS habilitado
- Validação de entrada

### 2. Análise de Sentimentos
- Processamento de linguagem natural
- Score de -1 (negativo) a +1 (positivo)
- Confiança da análise
- Detecção de palavras-chave

### 3. Sistema de Filas
- Processamento assíncrono
- Priorização de tarefas
- Retry automático
- Dead letter queue

### 4. Cache Distribuído
- TTL configurável
- Invalidação inteligente
- Estatísticas de hit rate

### 5. Webhooks
- Notificações em tempo real
- Retry com backoff exponencial
- Assinatura de payload

## 📊 Endpoints Principais

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Informações da API |
| `/health` | GET | Health check |
| `/api/auth/register` | POST | Registra usuário |
| `/api/auth/login` | POST | Autentica usuário |
| `/api/sentiment/analyze` | POST | Submete análise |
| `/api/sentiment/result/:id` | GET | Obtém resultado |
| `/api/sentiment/history` | GET | Lista histórico |
| `/api/metrics/summary` | GET | Métricas do usuário |
| `/api/webhooks/configure` | POST | Configura webhook |
| `/api/worker/status` | GET | Status do worker |

## 🧪 Testes

O projeto inclui testes completos:

- **Testes Unitários**: Analisador de sentimentos
- **Testes de API**: Todos os endpoints
- **Testes de Integração**: Fluxo completo

```bash
# Executar todos os testes
python tests/test_sentiment.py
python tests/test_integration.py
pytest tests/test_api.py -v
```

## 🔐 Segurança

- Senhas hasheadas com bcrypt
- Tokens JWT com expiração
- Rate limiting por IP/usuário
- Validação rigorosa de entrada
- Headers de segurança

## 📈 Performance

- Cache de resultados
- Processamento assíncrono
- Índices de banco otimizados
- Thread pool para workers

## 🌟 Diferenciais

1. **Arquitetura Completa**: Todos os componentes de um sistema moderno
2. **Processamento Assíncrono**: Não bloqueia a API
3. **Alta Disponibilidade**: Retry logic e dead letter queue
4. **Observabilidade**: Métricas e health checks
5. **Extensível**: Fácil adicionar novos recursos

## 📝 Casos de Uso

- Análise de reviews de e-commerce
- Monitoramento de redes sociais
- Classificação de tickets de suporte
- Análise de feedback de usuários
- Avaliação de campanhas de marketing

## 👥 Autor

Desenvolvido para avaliação de Sistemas Web Modernos

## 📄 Licença

MIT License - Projeto educacional

---

**Documentação Completa**: Ver `docs/README.md`
**Arquitetura**: Ver `docs/arquitetura.md`
**Schema DB**: Ver `schema/database.json`
