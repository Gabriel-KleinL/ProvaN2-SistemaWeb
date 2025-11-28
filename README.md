# Sistema de Análise de Sentimentos

Sistema web simples para análise de sentimentos em textos.

## 🎯 Componentes

**3 Funções:**
1. `cadastrar_analise()` - Cadastra texto
2. `processar_fila()` - Processa e analisa
3. `buscar_resultado()` - Retorna resultado

**2 Schemas:**
1. `users` - Usuários
2. `analyses` - Análises

## 📁 Estrutura

```
ProvaN2-SistemaWeb/
├── docs/              # Documentação e arquitetura
├── schema/            # 2 schemas do banco (JSON)
├── src/               # 3 funções principais (Python)
└── tests/             # Testes em Python
```

## 🚀 Como Executar

### 1. Instalar
```bash
pip install -r requirements.txt
```

### 2. Inicializar Banco
```bash
python src/database.py
```

### 3. Executar API (Terminal 1)
```bash
python src/app.py
```

### 4. Executar Worker (Terminal 2)
```bash
python src/worker.py
```

### 5. Testar no Postman

**Cadastrar Análise:**
```
POST http://localhost:5000/api/analyze
Content-Type: application/json

{
  "text": "Este produto é excelente!"
}
```

**Buscar Resultado:**
```
GET http://localhost:5000/api/result/{analysis_id}
```

## 🧪 Executar Testes
```bash
python tests/test_funcoes.py
```

## 📚 Documentação

Ver `docs/README.md` para documentação completa.
