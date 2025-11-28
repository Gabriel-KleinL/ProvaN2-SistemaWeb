# Sistema de Análise de Sentimentos

Sistema web para análise de sentimentos em textos usando Flask.

## Estrutura

```
├── arquitetura.html    # Visualização da arquitetura
├── schema/            # 2 schemas do banco
├── src/               # 3 funções principais
└── requirements.txt
```

## 3 Funções

1. `cadastrar_analise()` - Cadastra texto
2. `processar_fila()` - Analisa sentimento  
3. `buscar_resultado()` - Retorna resultado

## 2 Schemas

1. `users` - Usuários
2. `analyses` - Análises

## Executar

```bash
# Instalar
pip install -r requirements.txt

# Inicializar banco
python src/database.py

# Terminal 1 - API
python src/app.py

# Terminal 2 - Worker
python src/worker.py
```

## API

**Cadastrar:**
```
POST http://localhost:5000/api/analyze
{"text": "Produto excelente!"}
```

**Buscar:**
```
GET http://localhost:5000/api/result/{id}
```

## Arquitetura

Abra `arquitetura.html` no navegador.
