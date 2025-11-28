# Arquitetura do Sistema

## Diagrama Simplificado

```
┌─────────────────┐
│     Cliente     │
│   (Postman)     │
└────────┬────────┘
         │ HTTP POST/GET
         ↓
┌─────────────────────────┐
│      API Flask          │
│  ┌──────────────────┐   │
│  │ POST /api/analyze│   │
│  │ GET /api/result  │   │
│  └──────────────────┘   │
└──────┬──────────────────┘
       │
       ↓
┌──────────────────────────┐
│  FUNÇÃO 1               │
│  cadastrar_analise()    │
│  - Gera UUID            │
│  - Salva no banco       │
│  - Enfileira tarefa     │
└──────┬──────────────────┘
       │
       ↓
┌──────────────────────────┐
│   Fila de Tarefas       │
│   (Python Queue)        │
└──────┬──────────────────┘
       │
       ↓
┌──────────────────────────┐
│      Worker             │
│   (Processa Fila)       │
└──────┬──────────────────┘
       │
       ↓
┌──────────────────────────┐
│  FUNÇÃO 2               │
│  processar_fila()       │
│  - Pega da fila         │
│  - Analisa sentimento   │
│  - Atualiza banco       │
└──────┬──────────────────┘
       │
       ↓
┌──────────────────────────┐
│   Banco de Dados        │
│   (SQLite)              │
│  ┌──────────────────┐   │
│  │ Schema 1: users  │   │
│  │ Schema 2: analyses│  │
│  └──────────────────┘   │
└──────┬──────────────────┘
       │
       ↓
┌──────────────────────────┐
│  FUNÇÃO 3               │
│  buscar_resultado()     │
│  - Consulta banco       │
│  - Retorna análise      │
└──────┬──────────────────┘
       │
       ↓
┌─────────────────┐
│   Resposta      │
│   ao Cliente    │
└─────────────────┘
```

## Componentes

### 1. API Flask
- Recebe requisições HTTP
- Valida entrada
- Retorna JSON

### 2. Fila (Queue)
- Armazena tarefas pendentes
- Desacopla API do processamento
- Permite processamento assíncrono

### 3. Worker
- Processa fila continuamente
- Executa análise de sentimento
- Atualiza resultados

### 4. Banco SQLite
- 2 schemas (users e analyses)
- Armazena dados permanentemente
- Relacionamento entre tabelas

## Fluxo de Dados

1. Cliente envia POST com texto
2. API chama **FUNÇÃO 1** (cadastrar_analise)
3. Análise salva no banco com status "pending"
4. Tarefa adicionada à fila
5. Worker pega tarefa da fila
6. Worker chama **FUNÇÃO 2** (processar_fila)
7. Sentimento analisado e salvo no banco
8. Cliente faz GET para resultado
9. API chama **FUNÇÃO 3** (buscar_resultado)
10. Resultado retornado ao cliente

## 3 Funções Principais

```python
# FUNÇÃO 1: Cadastrar Análise
def cadastrar_analise(user_id, texto):
    # 1. Gera ID único
    # 2. Salva no banco (schema: analyses)
    # 3. Adiciona na fila
    # 4. Retorna ID
    pass

# FUNÇÃO 2: Processar Fila
def processar_fila():
    # 1. Pega tarefa da fila
    # 2. Analisa sentimento
    # 3. Calcula score
    # 4. Atualiza banco
    # 5. Retorna resultado
    pass

# FUNÇÃO 3: Buscar Resultado
def buscar_resultado(analysis_id):
    # 1. Consulta banco
    # 2. Retorna dados da análise
    pass
```

## 2 Schemas

```sql
-- SCHEMA 1: Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT UNIQUE,
    password_hash TEXT,
    created_at TIMESTAMP
);

-- SCHEMA 2: Analyses
CREATE TABLE analyses (
    id TEXT PRIMARY KEY,
    user_id INTEGER,
    text TEXT,
    sentiment TEXT,
    score REAL,
    status TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Tecnologias

- **Flask**: API REST
- **SQLite**: Banco de dados
- **Queue**: Fila de processamento
- **Python**: Backend
