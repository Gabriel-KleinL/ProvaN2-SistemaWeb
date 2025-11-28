# Sistema de Análise de Sentimentos

Sistema web simples para análise de sentimentos em textos.

## 📊 Estrutura

**3 Funções Principais:**
1. `cadastrar_analise()` - Cadastra texto para análise
2. `processar_fila()` - Processa análise e retorna sentimento
3. `buscar_resultado()` - Busca resultado da análise

**2 Schemas de Banco:**
1. `users` - Usuários do sistema
2. `analyses` - Análises de sentimento

## 🏗️ Arquitetura

```
Cliente (Postman)
    ↓
API Flask
    ↓
FUNÇÃO 1: cadastrar_analise()
    ↓
Fila de Processamento
    ↓
Worker
    ↓
FUNÇÃO 2: processar_fila()
    ↓
Banco de Dados (SQLite)
    ↓
FUNÇÃO 3: buscar_resultado()
    ↓
Cliente recebe resultado
```

## 🚀 Como Usar

### 1. Instalar
```bash
pip install flask flask-cors
```

### 2. Executar API (Terminal 1)
```bash
python src/app.py
```

### 3. Executar Worker (Terminal 2)
```bash
python src/worker.py
```

### 4. Testar no Postman

**Cadastrar Análise:**
```http
POST http://localhost:5000/api/analyze
Content-Type: application/json

{
  "text": "Este produto é excelente!"
}
```

**Resposta:**
```json
{
  "message": "Análise cadastrada",
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

**Buscar Resultado:**
```http
GET http://localhost:5000/api/result/550e8400-e29b-41d4-a716-446655440000
```

**Resposta:**
```json
{
  "analysis": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "text": "Este produto é excelente!",
    "sentiment": "positive",
    "score": 1.0,
    "status": "completed"
  }
}
```

## 🧪 Executar Testes
```bash
python tests/test_funcoes.py
```

## 📁 Estrutura de Arquivos

```
ProvaN2-SistemaWeb/
├── docs/
│   └── README.md          # Documentação
├── schema/
│   └── database.json      # Schema das 2 tabelas
├── src/
│   ├── app.py            # API Flask
│   ├── database.py       # 2 schemas do banco
│   ├── funcoes.py        # 3 funções principais
│   └── worker.py         # Processador de fila
└── tests/
    └── test_funcoes.py   # Testes das 3 funções
```

## 📊 Schemas do Banco

### 1. users
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 2. analyses
```sql
CREATE TABLE analyses (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    sentiment TEXT NULL,          -- positive, negative, neutral
    score REAL NULL,              -- -1.0 a 1.0
    status TEXT DEFAULT 'pending', -- pending, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
```

## ⚙️ Funções Detalhadas

### FUNÇÃO 1: cadastrar_analise(user_id, texto)
**O que faz:**
- Cria UUID único
- Salva no banco (schema: analyses)
- Adiciona na fila de processamento
- Retorna ID da análise

**Exemplo:**
```python
from funcoes import cadastrar_analise

analysis_id = cadastrar_analise(1, "Produto excelente!")
# Retorna: "550e8400-e29b-41d4-a716-446655440000"
```

### FUNÇÃO 2: processar_fila()
**O que faz:**
- Pega análise pendente da fila
- Analisa sentimento do texto
- Calcula score (-1.0 a 1.0)
- Atualiza no banco
- Retorna resultado

**Exemplo:**
```python
from funcoes import processar_fila

resultado = processar_fila()
# Retorna: {'id': '...', 'sentiment': 'positive', 'score': 0.8}
```

### FUNÇÃO 3: buscar_resultado(analysis_id)
**O que faz:**
- Busca análise no banco
- Retorna dados completos
- Retorna None se não encontrado

**Exemplo:**
```python
from funcoes import buscar_resultado

resultado = buscar_resultado("550e8400-...")
# Retorna: {'id': '...', 'text': '...', 'sentiment': 'positive', ...}
```

## 🎯 Análise de Sentimento

**Palavras Positivas:**
- bom, ótimo, excelente, amo, adorei, maravilhoso, perfeito, incrível, feliz, satisfeito, top, legal

**Palavras Negativas:**
- ruim, péssimo, horrível, odeio, terrível, mal, pior, problema, defeito, insatisfeito, raiva, lixo

**Classificação:**
- Score > 0.2 → **positive**
- Score < -0.2 → **negative**
- Caso contrário → **neutral**

## 📈 Endpoints da API

| Endpoint | Método | Descrição | Função |
|----------|--------|-----------|--------|
| `/` | GET | Info do sistema | - |
| `/api/analyze` | POST | Cadastra análise | FUNÇÃO 1 |
| `/api/result/:id` | GET | Busca resultado | FUNÇÃO 3 |
| `/api/status` | GET | Status da fila | - |

## ✅ Checklist de Avaliação

- [x] 3 Funções principais implementadas
- [x] 2 Schemas de banco definidos
- [x] API Flask funcional
- [x] Testável via Postman (sem UI)
- [x] Fila de processamento assíncrono
- [x] Testes em Python
- [x] Documentação completa

## 🎬 Para Apresentação

1. **Mostre a estrutura** (4 pastas: docs, schema, src, tests)
2. **Execute API e Worker** (2 terminais)
3. **Teste no Postman:**
   - POST texto positivo → mostre resultado
   - POST texto negativo → mostre resultado
   - POST texto neutro → mostre resultado
4. **Execute testes:** `python tests/test_funcoes.py`
5. **Mostre código das 3 funções** em `src/funcoes.py`
6. **Mostre schemas** em `schema/database.json`

## 📝 Tecnologias

- **Backend:** Flask (Python)
- **Banco:** SQLite
- **Fila:** Queue (Python nativo)
- **NLP:** Análise léxica simples
