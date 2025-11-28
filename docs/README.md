# Sistema de Análise de Sentimentos em Tempo Real

## 📋 Visão Geral

Sistema web moderno para análise de sentimentos em textos com processamento assíncrono, cache distribuído e arquitetura escalável. Ideal para análise de feedbacks, reviews de produtos, comentários em redes sociais e atendimento ao cliente.

## 🎯 Cenário Principal

Uma empresa de e-commerce recebe milhares de avaliações de produtos diariamente. O sistema permite:

1. **Submissão de Textos**: Envio de reviews/comentários via API REST
2. **Processamento Assíncrono**: Análise de sentimento em fila de processamento
3. **Classificação Inteligente**: Detecta sentimentos (positivo, negativo, neutro)
4. **Métricas em Tempo Real**: Dashboard com estatísticas agregadas
5. **Notificações**: Webhooks para alertar sobre sentimentos negativos
6. **Cache Distribuído**: Respostas rápidas para consultas frequentes

## 🏗️ Arquitetura

```
┌─────────────┐
│   Cliente   │
│  (Postman)  │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────────────┐
│            API Gateway (Flask)                  │
│  ┌──────────────┐  ┌─────────────────────┐    │
│  │ Rate Limiter │  │  JWT Authentication │    │
│  └──────────────┘  └─────────────────────┘    │
└─────────┬───────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────┐
│              Camada de Serviços                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │  Cache   │  │  Queue   │  │  Sentiment   │ │
│  │  Redis   │  │ Manager  │  │   Analyzer   │ │
│  └──────────┘  └──────────┘  └──────────────┘ │
└─────────┬───────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────┐
│         Worker de Processamento                 │
│  ┌──────────────────────────────────────────┐  │
│  │  Processa Fila de Análise de Sentimentos│  │
│  │  - NLP Processing                        │  │
│  │  - Score Calculation                     │  │
│  │  - Webhook Notifications                 │  │
│  └──────────────────────────────────────────┘  │
└─────────┬───────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────┐
│           Camada de Persistência                │
│  ┌──────────────┐  ┌──────────────────────┐    │
│  │   SQLite     │  │  File-based Queue    │    │
│  │  Database    │  │   (Simulated)        │    │
│  └──────────────┘  └──────────────────────┘    │
└─────────────────────────────────────────────────┘
```

## 🔧 Componentes e Integrações

### 1. **API Gateway (Flask)**
- RESTful API endpoints
- Validação de requisições
- Serialização JSON
- CORS habilitado

### 2. **Autenticação JWT**
- Login de usuários
- Tokens com expiração
- Middleware de autenticação
- Refresh tokens

### 3. **Rate Limiting**
- Proteção contra abuso
- Limites por IP/usuário
- Resposta 429 Too Many Requests

### 4. **Sistema de Filas**
- Processamento assíncrono
- Retry logic para falhas
- Priorização de tarefas
- Dead letter queue

### 5. **Análise de Sentimentos**
- Processamento de linguagem natural
- Score de -1 (negativo) a +1 (positivo)
- Detecção de palavras-chave
- Confiança da análise

### 6. **Cache Redis (Simulado)**
- Cache de resultados
- TTL configurável
- Invalidação inteligente
- Redução de latência

### 7. **Banco de Dados**
- Persistência de análises
- Histórico de usuários
- Métricas agregadas
- Índices otimizados

### 8. **Sistema de Webhooks**
- Notificações em tempo real
- Retry automático
- Configuração por usuário
- Payload personalizado

## 📡 Endpoints da API

### Autenticação

#### POST /api/auth/register
Registra novo usuário
```json
{
  "username": "usuario123",
  "email": "usuario@example.com",
  "password": "senha_segura"
}
```

#### POST /api/auth/login
Autentica usuário
```json
{
  "email": "usuario@example.com",
  "password": "senha_segura"
}
```

### Análise de Sentimentos

#### POST /api/sentiment/analyze
Submete texto para análise (requer autenticação)
```json
{
  "text": "Este produto é incrível! Estou muito satisfeito com a compra.",
  "metadata": {
    "product_id": "12345",
    "source": "review"
  }
}
```

#### GET /api/sentiment/result/{analysis_id}
Obtém resultado de análise específica

#### GET /api/sentiment/history
Lista histórico de análises do usuário

### Métricas

#### GET /api/metrics/summary
Retorna estatísticas agregadas
- Total de análises
- Distribuição de sentimentos
- Média de scores
- Análises por período

#### GET /api/metrics/trends
Tendências temporais de sentimentos

### Worker

#### POST /api/worker/process
Processa fila de análises pendentes (uso interno)

#### GET /api/worker/status
Status do worker e fila

### Webhooks

#### POST /api/webhooks/configure
Configura webhook para notificações
```json
{
  "url": "https://seu-servidor.com/webhook",
  "events": ["negative_sentiment", "analysis_complete"],
  "enabled": true
}
```

## 🚀 Como Executar

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Inicializar Banco de Dados
```bash
python src/database.py
```

### 3. Executar API
```bash
python src/app.py
```

### 4. Executar Worker (em terminal separado)
```bash
python src/worker.py
```

### 5. Executar Testes
```bash
pytest tests/ -v
```

## 📦 Estrutura do Projeto

```
ProvaN2-SistemaWeb/
├── docs/
│   ├── README.md          # Documentação principal
│   └── arquitetura.md     # Diagrama detalhado de arquitetura
├── schema/
│   └── database.json      # Schema do banco de dados
├── src/
│   ├── app.py            # Aplicação Flask principal
│   ├── auth.py           # Autenticação e JWT
│   ├── cache.py          # Sistema de cache
│   ├── database.py       # Modelos e conexão DB
│   ├── queue_manager.py  # Gerenciador de filas
│   ├── sentiment_analyzer.py  # Análise de sentimentos
│   ├── webhooks.py       # Sistema de webhooks
│   └── worker.py         # Worker de processamento
└── tests/
    ├── test_api.py       # Testes da API
    ├── test_sentiment.py # Testes de análise
    └── test_integration.py  # Testes de integração
```

## 🧪 Testando com Postman

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

Copie o `access_token` da resposta.

### 3. Enviar Análise
```
POST http://localhost:5000/api/sentiment/analyze
Authorization: Bearer {seu_token_aqui}
Content-Type: application/json

{
  "text": "Produto excelente, superou minhas expectativas!",
  "metadata": {
    "product_id": "12345"
  }
}
```

### 4. Verificar Resultado
```
GET http://localhost:5000/api/sentiment/result/{analysis_id}
Authorization: Bearer {seu_token_aqui}
```

### 5. Ver Métricas
```
GET http://localhost:5000/api/metrics/summary
Authorization: Bearer {seu_token_aqui}
```

## 🎯 Diferenciais Técnicos

1. **Processamento Assíncrono**: Não bloqueia a API durante análises longas
2. **Cache Inteligente**: Reduz latência em consultas repetidas
3. **Rate Limiting**: Previne abuso e garante disponibilidade
4. **Webhooks**: Notificações em tempo real para sistemas externos
5. **JWT Stateless**: Autenticação escalável sem sessões
6. **Retry Logic**: Resiliência em falhas de processamento
7. **Métricas Agregadas**: Insights em tempo real sobre sentimentos
8. **Arquitetura Modular**: Fácil manutenção e extensão

## 📊 Casos de Uso

- **E-commerce**: Análise de reviews de produtos
- **Redes Sociais**: Monitoramento de menções de marca
- **Atendimento**: Classificação automática de tickets
- **Pesquisas**: Análise de feedback de usuários
- **Marketing**: Avaliação de campanhas publicitárias

## 🔐 Segurança

- Senhas hasheadas com bcrypt
- JWT com expiração configurável
- Rate limiting por IP
- Validação de entrada rigorosa
- CORS configurável
- SQL injection prevention

## 📈 Escalabilidade

- Worker pode ser replicado horizontalmente
- Cache pode ser substituído por Redis real
- Fila pode usar RabbitMQ/Celery em produção
- Database pode migrar para PostgreSQL
- API pode usar load balancer

## 🛠️ Tecnologias Utilizadas

- **Flask**: Framework web
- **SQLite**: Banco de dados
- **JWT**: Autenticação
- **NLTK/TextBlob**: Processamento de linguagem natural
- **Pytest**: Testes
- **Werkzeug**: Hashing de senhas
- **Threading**: Processamento paralelo

## 📝 Licença

MIT License - Projeto educacional para avaliação acadêmica
