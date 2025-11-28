# 🎨 Como Criar o Diagrama de Arquitetura Estilo AWS

## Opção 1: Gerar Automaticamente com Python ⚡

### Instalar biblioteca:
```bash
pip install diagrams
```

### Gerar imagem:
```bash
python docs/generate_architecture_diagram.py
```

Resultado: `docs/arquitetura_aws.png`

---

## Opção 2: Usar Mermaid Online (Mais Fácil) 🌐

### Passos:

1. **Acesse:** https://mermaid.live

2. **Cole o conteúdo** de `docs/arquitetura.mermaid`

3. **Aguarde renderização** automática

4. **Exporte:**
   - Clique em "Actions" → "Download PNG"
   - Ou "Download SVG" para qualidade vetorial

5. **Salve como:** `docs/arquitetura_aws.png`

---

## Opção 3: Draw.io / Diagrams.net (Mais Controle) 🎨

### Passos:

1. **Acesse:** https://app.diagrams.net

2. **Crie novo diagrama:**
   - Escolha "Blank Diagram"
   - Tamanho: A3 Landscape

3. **Use a biblioteca AWS:**
   - Menu: More Shapes → Clique em "AWS"
   - Ative: AWS19, AWS17, General

4. **Crie as camadas:**

#### Camada 1: Cliente
- Use: "User" ou "Client" icon
- Label: "Postman / HTTP Client"

#### Camada 2: Load Balancer
- Use: AWS → "Elastic Load Balancing"
- Label: "Load Balancer (Nginx)"

#### Camada 3: API Gateway
- Use: AWS → "API Gateway" (3x)
- Labels: "Flask API 1", "Flask API 2", "Flask API 3"
- Agrupe em container "API Layer"

#### Camada 4: Middleware
- Use: General → "Process" (4x)
- Labels:
  - "JWT Auth"
  - "Rate Limiter"
  - "CORS Handler"
  - "Request Validator"
- Agrupe em container "Middleware Layer"

#### Camada 5: Services
- Use: AWS → "Lambda" ou General → "Server"
- Labels:
  - "Auth Service"
  - "Sentiment Analyzer"
  - "Cache Service" (use Redis icon)
  - "Queue Manager" (use SQS icon)
  - "Webhook Service"
  - "Metrics Service"
- Agrupe em container "Service Layer"

#### Camada 6: Workers
- Use: AWS → "EC2" ou "Lambda" (3x)
- Labels: "Worker 1", "Worker 2", "Worker 3"
- Agrupe em container "Worker Layer"

#### Camada 7: Data Layer
- Use:
  - AWS → "RDS" para banco de dados
  - AWS → "ElastiCache" para Redis
  - AWS → "SQS" para fila
- Labels:
  - "PostgreSQL/SQLite"
  - "Redis Cache"
  - "RabbitMQ/SQS"
- Agrupe em container "Data Layer"

#### Camada 8: External
- Use: General → "Server" (2x)
- AWS → "CloudWatch" + "Prometheus"
- Labels:
  - "External Webhook 1"
  - "External Webhook 2"
  - "Prometheus"
  - "Grafana"

5. **Conecte com setas:**
   - Cliente → Load Balancer (laranja, "HTTPS")
   - Load Balancer → APIs (azul)
   - APIs → Middlewares (vermelho)
   - APIs → Services (verde/roxo)
   - Services → Data Layer (roxo)
   - Workers → Services (verde)
   - Workers → Webhooks (laranja)

6. **Estilize:**
   - Cores:
     - Cliente/External: #FF9900 (laranja AWS)
     - APIs: #3B48CC (azul)
     - Middleware: #DD344C (vermelho)
     - Services: #5294CF (azul claro)
     - Workers: #759C3E (verde)
     - Data: #3334B9 (azul escuro)

   - Fontes:
     - Título: Arial Bold, 16pt
     - Labels: Arial, 12pt
     - Notas: Arial, 10pt

7. **Adicione legendas:**
   - Fluxo síncrono: seta sólida
   - Fluxo assíncrono: seta tracejada
   - Cache hit: seta verde
   - Cache miss: seta vermelha

8. **Exporte:**
   - File → Export as → PNG
   - Resolução: 300 DPI
   - Transparência: Desligada
   - Border: 10px

---

## Opção 4: Lucidchart (Profissional) 💼

1. **Acesse:** https://www.lucidchart.com

2. **Use template AWS:**
   - Templates → "AWS Architecture Diagram"

3. **Siga estrutura similar** ao Draw.io

4. **Exporte como PNG** de alta qualidade

---

## Opção 5: Usar Ferramenta CLI (Para Desenvolvedores) 💻

### Usando PlantUML:

```bash
# Instalar
sudo apt-get install plantuml

# Gerar
plantuml docs/arquitetura.puml
```

---

## 🎨 Paleta de Cores AWS

| Componente | Cor | Hex |
|------------|-----|-----|
| Cliente/External | Laranja AWS | #FF9900 |
| Load Balancer | Laranja | #FF9900 |
| API Gateway | Azul | #3B48CC |
| Middleware | Vermelho | #DD344C |
| Services | Azul Claro | #5294CF |
| Workers | Verde | #759C3E |
| Data Layer | Azul Escuro | #3334B9 |
| Monitoring | Cinza | #5A6B7D |

---

## 📐 Layout Recomendado

```
┌─────────────────────────────────────────────┐
│           CLIENTE (Topo)                    │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│        LOAD BALANCER                        │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│        API LAYER (3 instâncias)             │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│        MIDDLEWARE LAYER                     │
└──┬─────────┬──────────┬──────────┬──────────┘
   │         │          │          │
┌──▼─────┐ ┌▼──────┐ ┌▼──────┐ ┌▼──────────┐
│ Auth   │ │ Rate  │ │ Cache │ │ Queue     │
│ Service│ │Limiter│ │Service│ │ Manager   │
└────┬───┘ └───────┘ └───┬───┘ └─────┬─────┘
     │                   │           │
┌────▼───────────────────▼───────────▼─────┐
│           WORKER LAYER                   │
│        (3 workers paralelos)             │
└────────────────┬─────────────────────────┘
                 │
┌────────────────▼─────────────────────────┐
│           DATA LAYER                     │
│     DB │ Cache │ Queue Storage           │
└──────────────────────────────────────────┘
```

---

## 🖼️ Exemplo de Diagrama Pronto

Se quiser usar um exemplo pronto, procure por:
- "AWS Architecture Diagrams"
- "Microservices Architecture AWS"
- "API Gateway Pattern AWS"

E adapte para o nosso sistema.

---

## ⚡ Método Mais Rápido

**Use Mermaid Live Editor:**

1. Copie: `docs/arquitetura.mermaid`
2. Cole em: https://mermaid.live
3. Download PNG
4. Pronto! ✅

**Tempo:** 2 minutos

---

## 📱 Recursos Adicionais

### Ícones AWS Oficiais:
- https://aws.amazon.com/architecture/icons/

### Templates:
- https://github.com/aws-samples/aws-icons-for-plantuml

### Tutoriais:
- AWS Well-Architected Framework
- Cloudcraft (visual 3D)

---

## 💡 Dica para Apresentação

Se não conseguir gerar a imagem, use o diagrama em ASCII da documentação! Ele está em `docs/arquitetura.md` e é visualmente claro.

Ou mostre direto no Mermaid Live Editor durante a apresentação - é interativo e impressionante! 🚀
