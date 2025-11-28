# Arquitetura Detalhada do Sistema

## 🏛️ Visão Geral da Arquitetura

O sistema utiliza uma arquitetura em camadas com processamento assíncrono e separação clara de responsabilidades.

## 📐 Diagrama de Componentes Detalhado

```
┌────────────────────────────────────────────────────────────────────┐
│                        CAMADA DE APRESENTAÇÃO                      │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Postman    │  │  cURL/HTTP   │  │  Aplicações Externas │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                      │                │
│         └─────────────────┴──────────────────────┘                │
│                           │                                        │
└───────────────────────────┼────────────────────────────────────────┘
                            │
                            │ HTTP/REST
                            ↓
┌────────────────────────────────────────────────────────────────────┐
│                      CAMADA DE API (Flask)                         │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Middleware Stack                          │ │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐   │ │
│  │  │   CORS     │→ │Rate Limiter│→ │  JWT Validator      │   │ │
│  │  │  Handler   │  │ (IP-based) │  │  (Token Check)      │   │ │
│  │  └────────────┘  └────────────┘  └─────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                      Controllers                             │ │
│  │  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐   │ │
│  │  │   Auth     │  │ Sentiment  │  │     Metrics         │   │ │
│  │  │ Controller │  │ Controller │  │    Controller       │   │ │
│  │  └────────────┘  └────────────┘  └─────────────────────┘   │ │
│  │  ┌────────────┐  ┌────────────┐                            │ │
│  │  │  Webhook   │  │   Worker   │                            │ │
│  │  │ Controller │  │ Controller │                            │ │
│  │  └────────────┘  └────────────┘                            │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                             ↓
┌────────────────────────────────────────────────────────────────────┐
│                    CAMADA DE SERVIÇOS                              │
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │  Auth Service   │  │ Sentiment       │  │  Cache Service   │  │
│  │                 │  │ Analyzer        │  │                  │  │
│  │ - Register      │  │                 │  │ - Get/Set        │  │
│  │ - Login         │  │ - Analyze Text  │  │ - Invalidate     │  │
│  │ - Generate JWT  │  │ - Calculate     │  │ - TTL Management │  │
│  │ - Validate      │  │   Score         │  │                  │  │
│  │                 │  │ - Classify      │  │ (In-memory Dict) │  │
│  └─────────────────┘  └─────────────────┘  └──────────────────┘  │
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │  Queue Manager  │  │ Webhook Service │  │  Metrics Service │  │
│  │                 │  │                 │  │                  │  │
│  │ - Enqueue       │  │ - Send Webhook  │  │ - Aggregate      │  │
│  │ - Dequeue       │  │ - Retry Logic   │  │ - Calculate      │  │
│  │ - Priority      │  │ - Configure     │  │ - Time Series    │  │
│  │ - Dead Letter   │  │ - Validate URL  │  │ - Statistics     │  │
│  │                 │  │                 │  │                  │  │
│  └─────────────────┘  └─────────────────┘  └──────────────────┘  │
│                                                                    │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                             ↓
┌────────────────────────────────────────────────────────────────────┐
│                  CAMADA DE PROCESSAMENTO                           │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Background Worker                         │ │
│  │                                                              │ │
│  │  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │ │
│  │  │ Queue Poller │  →   │   Process    │  →   │  Persist  │ │ │
│  │  │ (Thread)     │      │   Sentiment  │      │  Results  │ │ │
│  │  └──────────────┘      └──────────────┘      └───────────┘ │ │
│  │         ↓                      ↓                    ↓       │ │
│  │  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │ │
│  │  │ Retry Failed │      │   Notify     │      │  Update   │ │ │
│  │  │   Tasks      │      │   Webhooks   │      │   Cache   │ │ │
│  │  └──────────────┘      └──────────────┘      └───────────┘ │ │
│  │                                                              │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                             ↓
┌────────────────────────────────────────────────────────────────────┐
│                    CAMADA DE PERSISTÊNCIA                          │
│                                                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │  SQLite DB      │  │  File Queue     │  │  In-Memory Cache │  │
│  │                 │  │                 │  │                  │  │
│  │ Tables:         │  │ - Pending Jobs  │  │ - Analysis Cache │  │
│  │ - users         │  │ - Processing    │  │ - User Sessions  │  │
│  │ - analyses      │  │ - Completed     │  │ - Rate Limits    │  │
│  │ - webhooks      │  │ - Failed (DLQ)  │  │                  │  │
│  │ - metrics       │  │                 │  │                  │  │
│  │                 │  │ (JSON Files)    │  │  (Python Dict)   │  │
│  └─────────────────┘  └─────────────────┘  └──────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## 🔄 Fluxo de Processamento de Análise

```
Cliente                API              Queue           Worker          Database
  │                    │                 │                │                │
  │  1. POST /analyze  │                 │                │                │
  │───────────────────→│                 │                │                │
  │                    │                 │                │                │
  │                    │ 2. Validate JWT │                │                │
  │                    │─────────────┐   │                │                │
  │                    │←────────────┘   │                │                │
  │                    │                 │                │                │
  │                    │ 3. Check Cache  │                │                │
  │                    │─────────────────────────────────────────────────┐ │
  │                    │←────────────────────────────────────────────────┘ │
  │                    │                 │                │                │
  │                    │ 4. Enqueue Task │                │                │
  │                    │────────────────→│                │                │
  │                    │                 │                │                │
  │  5. 202 Accepted   │                 │                │                │
  │  (analysis_id)     │                 │                │                │
  │←───────────────────│                 │                │                │
  │                    │                 │                │                │
  │                    │                 │ 6. Poll Queue  │                │
  │                    │                 │←───────────────│                │
  │                    │                 │                │                │
  │                    │                 │ 7. Get Task    │                │
  │                    │                 │───────────────→│                │
  │                    │                 │                │                │
  │                    │                 │        8. Process Sentiment     │
  │                    │                 │                │────────────┐   │
  │                    │                 │                │←───────────┘   │
  │                    │                 │                │                │
  │                    │                 │                │  9. Save Result│
  │                    │                 │                │───────────────→│
  │                    │                 │                │                │
  │                    │                 │                │ 10. Update Cache│
  │                    │                 │                │───────────────→│
  │                    │                 │                │                │
  │                    │                 │                │ 11. Send Webhook│
  │                    │                 │                │────────────┐   │
  │                    │                 │                │←───────────┘   │
  │                    │                 │                │                │
  │  12. GET /result   │                 │                │                │
  │───────────────────→│                 │                │                │
  │                    │                 │                │                │
  │                    │ 13. Check Cache │                │                │
  │                    │─────────────────────────────────────────────────┐ │
  │                    │←────────────────────────────────────────────────┘ │
  │                    │                 │                │                │
  │  14. 200 OK        │                 │                │                │
  │  (result + score)  │                 │                │                │
  │←───────────────────│                 │                │                │
```

## 🔐 Fluxo de Autenticação

```
Cliente              Auth Service         Database
  │                       │                   │
  │  1. POST /register    │                   │
  │──────────────────────→│                   │
  │                       │                   │
  │                       │ 2. Hash Password  │
  │                       │──────────┐        │
  │                       │←─────────┘        │
  │                       │                   │
  │                       │ 3. Save User      │
  │                       │──────────────────→│
  │                       │                   │
  │  4. 201 Created       │                   │
  │←──────────────────────│                   │
  │                       │                   │
  │  5. POST /login       │                   │
  │──────────────────────→│                   │
  │                       │                   │
  │                       │ 6. Get User       │
  │                       │──────────────────→│
  │                       │←──────────────────│
  │                       │                   │
  │                       │ 7. Verify Password│
  │                       │──────────┐        │
  │                       │←─────────┘        │
  │                       │                   │
  │                       │ 8. Generate JWT   │
  │                       │──────────┐        │
  │                       │←─────────┘        │
  │                       │                   │
  │  9. 200 OK            │                   │
  │  (access_token)       │                   │
  │←──────────────────────│                   │
  │                       │                   │
  │  10. API Request      │                   │
  │  (Bearer token)       │                   │
  │──────────────────────→│                   │
  │                       │                   │
  │                       │ 11. Validate JWT  │
  │                       │──────────┐        │
  │                       │←─────────┘        │
  │                       │                   │
  │  12. Authorized       │                   │
  │←──────────────────────│                   │
```

## 📊 Modelo de Dados

### Entidades Principais

```
┌─────────────────────┐
│       Users         │
├─────────────────────┤
│ id (PK)            │
│ username           │
│ email (unique)     │
│ password_hash      │
│ created_at         │
│ is_active          │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ↓
┌─────────────────────┐
│     Analyses        │
├─────────────────────┤
│ id (PK)            │
│ user_id (FK)       │
│ text               │
│ sentiment          │
│ score              │
│ confidence         │
│ metadata (JSON)    │
│ status             │
│ created_at         │
│ processed_at       │
└──────────┬──────────┘
           │
           │ 1:1
           │
           ↓
┌─────────────────────┐
│   Webhook_Logs      │
├─────────────────────┤
│ id (PK)            │
│ analysis_id (FK)   │
│ webhook_url        │
│ payload            │
│ status_code        │
│ attempts           │
│ sent_at            │
└─────────────────────┘

┌─────────────────────┐
│  Webhook_Configs    │
├─────────────────────┤
│ id (PK)            │
│ user_id (FK)       │
│ url                │
│ events (JSON)      │
│ enabled            │
│ created_at         │
└─────────────────────┘
```

## 🎯 Padrões de Projeto Utilizados

### 1. **Repository Pattern**
- Camada de acesso a dados isolada
- Facilita testes unitários
- Permite trocar implementação de persistência

### 2. **Service Layer**
- Lógica de negócio separada dos controllers
- Reutilização de código
- Testabilidade

### 3. **Dependency Injection**
- Inversão de controle
- Acoplamento reduzido
- Facilita mocks em testes

### 4. **Factory Pattern**
- Criação de objetos complexos
- Encapsulamento da lógica de criação

### 5. **Observer Pattern**
- Sistema de webhooks
- Notificações assíncronas

### 6. **Queue Pattern**
- Processamento assíncrono
- Desacoplamento temporal
- Balanceamento de carga

## 🔧 Decisões Arquiteturais

### Por que Flask?
- Lightweight e flexível
- Fácil de entender e manter
- Grande ecossistema de extensões
- Perfeito para APIs RESTful

### Por que SQLite?
- Zero configuração
- Perfeito para desenvolvimento/demonstração
- Fácil migração para PostgreSQL
- ACID compliance

### Por que Processamento Assíncrono?
- Não bloqueia a API
- Escalável horizontalmente
- Retry automático em falhas
- Melhor experiência do usuário

### Por que JWT?
- Stateless (não requer sessões)
- Escalável horizontalmente
- Padrão de mercado
- Fácil integração com frontends

### Por que Cache em Memória?
- Latência mínima
- Simplicidade de implementação
- Fácil migração para Redis
- Suficiente para demonstração

## 📈 Estratégias de Escalabilidade

### Horizontal Scaling

```
┌──────────────┐
│ Load Balancer│
└──────┬───────┘
       │
       ├────────────┬────────────┬────────────┐
       ↓            ↓            ↓            ↓
   ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐
   │ API 1│    │ API 2│    │ API 3│    │ API 4│
   └──┬───┘    └──┬───┘    └──┬───┘    └──┬───┘
      │           │           │           │
      └───────────┴───────────┴───────────┘
                  │
                  ↓
          ┌──────────────┐
          │  Redis Cache │
          └──────────────┘
                  │
                  ↓
          ┌──────────────┐
          │  PostgreSQL  │
          └──────────────┘
```

### Workers Múltiplos

```
┌────────┐    ┌────────┐    ┌────────┐
│Worker 1│    │Worker 2│    │Worker 3│
└───┬────┘    └───┬────┘    └───┬────┘
    │             │             │
    └─────────────┴─────────────┘
                  │
                  ↓
          ┌──────────────┐
          │ RabbitMQ     │
          │ Message Queue│
          └──────────────┘
```

## 🛡️ Segurança em Camadas

```
┌─────────────────────────────────────┐
│  HTTPS/TLS (Transport Security)    │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  Rate Limiting (DoS Protection)     │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  JWT Validation (Authentication)    │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  Input Validation (Injection)       │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  Bcrypt Hashing (Password Security) │
└─────────────────────────────────────┘
```

## 🔍 Monitoramento e Observabilidade

### Métricas Coletadas
- Requisições por segundo
- Latência média/p95/p99
- Taxa de erro
- Queue depth
- Worker throughput
- Cache hit rate
- Análises por sentimento
- Usuários ativos

### Logs Estruturados
```json
{
  "timestamp": "2025-11-28T10:30:00Z",
  "level": "INFO",
  "service": "sentiment-api",
  "endpoint": "/api/sentiment/analyze",
  "user_id": "user_123",
  "duration_ms": 45,
  "status": 202
}
```

## 🚀 Evolução Futura

1. **Machine Learning**: Modelo próprio de NLP
2. **Redis Real**: Cache distribuído
3. **RabbitMQ/Celery**: Filas robustas
4. **PostgreSQL**: Banco relacional escalável
5. **Docker/Kubernetes**: Containerização
6. **GraphQL**: API alternativa
7. **WebSockets**: Notificações em tempo real
8. **Multi-idioma**: Suporte a vários idiomas
9. **A/B Testing**: Experimentação de modelos
10. **Data Lake**: Analytics avançado
