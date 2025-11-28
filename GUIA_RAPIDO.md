# 🚀 Guia Rápido de Execução

## Passo a Passo para Testar o Sistema

### 1️⃣ Preparação (Execute UMA vez)

```bash
# Instalar dependências
pip install -r requirements.txt

# Inicializar banco de dados
python src/database.py
```

### 2️⃣ Executar o Sistema

Você precisa de **2 terminais** abertos:

#### Terminal 1 - API
```bash
python src/app.py
```

Aguarde até ver:
```
✅ Aplicação inicializada com sucesso!
📡 API disponível em: http://localhost:5000
```

#### Terminal 2 - Worker
```bash
python src/worker.py
```

Aguarde até ver:
```
⚡ Worker de Análise de Sentimentos Iniciado
Aguardando tarefas na fila...
```

### 3️⃣ Testar com Postman

#### Teste 1: Registrar Usuário

```
POST http://localhost:5000/api/auth/register
Content-Type: application/json

{
  "username": "demo",
  "email": "demo@teste.com",
  "password": "senha123"
}
```

#### Teste 2: Fazer Login

```
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
  "email": "demo@teste.com",
  "password": "senha123"
}
```

**IMPORTANTE**: Copie o `access_token` da resposta!

#### Teste 3: Enviar Análise POSITIVA

```
POST http://localhost:5000/api/sentiment/analyze
Authorization: Bearer SEU_TOKEN_AQUI
Content-Type: application/json

{
  "text": "Este produto é absolutamente incrível! Estou muito satisfeito com a compra. Qualidade excelente e atendimento perfeito!"
}
```

Copie o `analysis_id` da resposta.

#### Teste 4: Enviar Análise NEGATIVA

```
POST http://localhost:5000/api/sentiment/analyze
Authorization: Bearer SEU_TOKEN_AQUI
Content-Type: application/json

{
  "text": "Produto péssimo! Total desperdício de dinheiro. Muito insatisfeito, não recomendo."
}
```

#### Teste 5: Enviar Análise NEUTRA

```
POST http://localhost:5000/api/sentiment/analyze
Authorization: Bearer SEU_TOKEN_AQUI
Content-Type: application/json

{
  "text": "O produto chegou hoje. Vou testar amanhã e depois dou feedback."
}
```

#### Teste 6: Ver Resultado

Aguarde 2-3 segundos, depois:

```
GET http://localhost:5000/api/sentiment/result/SEU_ANALYSIS_ID
Authorization: Bearer SEU_TOKEN_AQUI
```

Você verá:
```json
{
  "analysis": {
    "sentiment": "positive",  // ou "negative", "neutral"
    "score": 0.875,           // -1.0 a 1.0
    "confidence": 0.92,       // 0.0 a 1.0
    "status": "completed"
  }
}
```

#### Teste 7: Ver Histórico

```
GET http://localhost:5000/api/sentiment/history
Authorization: Bearer SEU_TOKEN_AQUI
```

#### Teste 8: Ver Métricas

```
GET http://localhost:5000/api/metrics/summary
Authorization: Bearer SEU_TOKEN_AQUI
```

Você verá distribuição de sentimentos e estatísticas!

### 4️⃣ Executar Testes Automatizados

```bash
# Testes do analisador de sentimentos
python tests/test_sentiment.py

# Testes de integração completa
python tests/test_integration.py
```

## 🎥 Para Apresentação em Vídeo

### Demonstração Sugerida (5-7 minutos):

1. **Introdução (30s)**
   - Apresentar o projeto
   - Mostrar arquitetura no arquivo `docs/arquitetura.md`

2. **Executar Sistema (1min)**
   - Iniciar API (Terminal 1)
   - Iniciar Worker (Terminal 2)
   - Mostrar logs de inicialização

3. **Testar API no Postman (3min)**
   - Registrar usuário
   - Fazer login
   - Enviar 3 análises (positiva, negativa, neutra)
   - Mostrar resultados em tempo real
   - Ver histórico e métricas

4. **Mostrar Código (2min)**
   - Estrutura de pastas
   - `src/app.py` - API principal
   - `src/sentiment_analyzer.py` - Algoritmo de análise
   - `src/worker.py` - Processamento assíncrono

5. **Executar Testes (1min)**
   - Rodar testes automatizados
   - Mostrar resultados

6. **Conclusão (30s)**
   - Destacar componentes da arquitetura
   - Mencionar escalabilidade e boas práticas

## 📋 Checklist para Apresentação

- [ ] API rodando sem erros
- [ ] Worker processando análises
- [ ] Postman com requisições salvas
- [ ] 3+ análises de teste (positiva, negativa, neutra)
- [ ] Histórico e métricas funcionando
- [ ] Testes executados com sucesso
- [ ] Arquitetura aberta para mostrar
- [ ] README preparado

## 🐛 Solução de Problemas

### Erro: "Module not found"
```bash
pip install -r requirements.txt
```

### Erro: "Database locked"
- Feche a API e Worker
- Delete o arquivo `sentiment_analysis.db`
- Execute `python src/database.py` novamente

### Worker não processa
- Verifique se ambos (API e Worker) estão rodando
- Veja os logs do Worker no terminal

### Token expirado
- Faça login novamente para obter novo token
- Tokens expiram em 24 horas

## 💡 Dicas para Nota Máxima

1. **Criatividade**: Sistema completo com múltiplas integrações
2. **Complexidade**: Filas, cache, webhooks, autenticação JWT
3. **Arquitetura**: Diagramas detalhados em `docs/arquitetura.md`
4. **Funcionalidade**: Tudo funciona via Postman
5. **Apresentação**: Demonstrar fluxo completo de forma clara

## 📞 Suporte

Se algo não funcionar:
1. Verifique se todas as dependências estão instaladas
2. Confirme que API e Worker estão rodando
3. Veja os logs nos terminais
4. Teste com dados de exemplo acima

Boa apresentação! 🎉
