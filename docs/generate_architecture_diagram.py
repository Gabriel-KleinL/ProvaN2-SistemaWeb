"""
Gerador de Diagrama de Arquitetura estilo AWS
Requer: pip install diagrams

Execute: python docs/generate_architecture_diagram.py
Resultado: docs/arquitetura_aws.png
"""

try:
    from diagrams import Diagram, Cluster, Edge
    from diagrams.onprem.client import Client
    from diagrams.onprem.compute import Server
    from diagrams.onprem.network import Nginx
    from diagrams.onprem.database import PostgreSQL
    from diagrams.onprem.inmemory import Redis
    from diagrams.onprem.queue import RabbitMQ
    from diagrams.onprem.monitoring import Prometheus, Grafana
    from diagrams.programming.framework import Flask
    from diagrams.generic.device import Mobile, Tablet
    from diagrams.generic.storage import Storage

    print("🎨 Gerando diagrama de arquitetura...")

    # Configurações do diagrama
    graph_attr = {
        "fontsize": "14",
        "bgcolor": "white",
        "pad": "0.5",
        "splines": "ortho",
        "nodesep": "0.8",
        "ranksep": "1.0"
    }

    with Diagram(
        "Sistema de Análise de Sentimentos - Arquitetura AWS-Style",
        filename="docs/arquitetura_aws",
        show=False,
        direction="TB",
        graph_attr=graph_attr,
        outformat="png"
    ):

        # Cliente
        client = Client("Postman/HTTP Client")

        with Cluster("API Gateway Layer"):
            lb = Nginx("Load Balancer")
            with Cluster("Flask API Instances"):
                apis = [
                    Flask("API Flask 1"),
                    Flask("API Flask 2"),
                    Flask("API Flask 3")
                ]

        with Cluster("Middleware Layer"):
            middlewares = [
                Server("JWT Auth"),
                Server("Rate Limiter"),
                Server("CORS Handler"),
                Server("Validator")
            ]

        with Cluster("Service Layer"):
            with Cluster("Core Services"):
                auth_svc = Server("Auth Service")
                sentiment_svc = Server("Sentiment Analyzer")
                webhook_svc = Server("Webhook Service")

            with Cluster("Infrastructure Services"):
                cache_svc = Redis("Cache Service")
                queue_svc = RabbitMQ("Queue Manager")
                metrics_svc = Server("Metrics Service")

        with Cluster("Worker Layer"):
            workers = [
                Server("Worker 1"),
                Server("Worker 2"),
                Server("Worker 3")
            ]

        with Cluster("Data Layer"):
            db = PostgreSQL("Primary Database\n(SQLite/PostgreSQL)")
            cache_store = Redis("Redis Cache\nDistributed")
            queue_store = RabbitMQ("Message Queue\n(RabbitMQ)")

        with Cluster("External Integrations"):
            webhooks = [
                Server("External Webhook 1"),
                Server("External Webhook 2")
            ]
            with Cluster("Monitoring"):
                prometheus = Prometheus("Prometheus")
                grafana = Grafana("Grafana")

        # Fluxos principais
        client >> Edge(label="HTTPS", color="orange") >> lb

        lb >> Edge(color="blue") >> apis[0]
        lb >> Edge(color="blue") >> apis[1]
        lb >> Edge(color="blue") >> apis[2]

        apis[0] >> Edge(label="auth", color="red") >> middlewares[0]
        apis[0] >> Edge(label="limit", color="red") >> middlewares[1]

        middlewares[0] >> Edge(color="purple") >> auth_svc

        apis[0] >> Edge(label="submit", color="green") >> queue_svc
        apis[0] >> Edge(label="cache", color="brown") >> cache_svc
        apis[0] >> Edge(label="metrics", color="pink") >> metrics_svc

        queue_svc >> Edge(color="darkgreen") >> queue_store
        cache_svc >> Edge(color="darkred") >> cache_store

        queue_store >> Edge(label="poll", color="green") >> workers[0]
        queue_store >> Edge(label="poll", color="green") >> workers[1]
        queue_store >> Edge(label="poll", color="green") >> workers[2]

        workers[0] >> Edge(label="analyze", color="blue") >> sentiment_svc
        workers[0] >> Edge(label="save", color="purple") >> db
        workers[0] >> Edge(label="cache", color="brown") >> cache_svc
        workers[0] >> Edge(label="notify", color="orange") >> webhook_svc

        webhook_svc >> Edge(label="HTTP POST", color="orange") >> webhooks[0]
        webhook_svc >> Edge(label="HTTP POST", color="orange") >> webhooks[1]

        auth_svc >> Edge(color="purple") >> db
        metrics_svc >> Edge(color="pink") >> db

        # Monitoramento
        apis[0] >> Edge(style="dashed", color="gray") >> prometheus
        workers[0] >> Edge(style="dashed", color="gray") >> prometheus
        prometheus >> Edge(color="gray") >> grafana

    print("✅ Diagrama gerado com sucesso!")
    print("📄 Arquivo: docs/arquitetura_aws.png")
    print("\nPara visualizar:")
    print("  - Abra docs/arquitetura_aws.png em qualquer visualizador de imagens")
    print("  - Ou use: xdg-open docs/arquitetura_aws.png (Linux)")
    print("  - Ou use: open docs/arquitetura_aws.png (Mac)")

except ImportError:
    print("❌ Biblioteca 'diagrams' não está instalada.")
    print("\nPara instalar:")
    print("  pip install diagrams")
    print("\nOu use a alternativa online:")
    print("  1. Acesse: https://mermaid.live")
    print("  2. Cole o conteúdo de docs/arquitetura.mermaid")
    print("  3. Exporte como PNG")
    print("\nOu use draw.io:")
    print("  1. Acesse: https://app.diagrams.net")
    print("  2. Siga o guia em docs/COMO_CRIAR_DIAGRAMA.md")
