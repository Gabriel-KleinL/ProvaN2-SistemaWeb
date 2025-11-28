"""
3 Funções Principais do Sistema
"""
import uuid
import queue
from database import get_db


# Fila global simples
fila_analises = queue.Queue()


# ============================================================================
# FUNÇÃO 1: Cadastrar Análise
# ============================================================================
def cadastrar_analise(user_id, texto):
    """
    Cadastra nova análise e adiciona na fila de processamento

    Args:
        user_id: ID do usuário
        texto: Texto a ser analisado

    Returns:
        ID da análise criada
    """
    analysis_id = str(uuid.uuid4())

    # Salva no banco
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO analyses (id, user_id, text, status) VALUES (?, ?, ?, ?)',
        (analysis_id, user_id, texto, 'pending')
    )
    conn.commit()
    conn.close()

    # Adiciona na fila
    fila_analises.put({
        'id': analysis_id,
        'text': texto
    })

    print(f"✓ Análise {analysis_id} cadastrada e enfileirada")
    return analysis_id


# ============================================================================
# FUNÇÃO 2: Processar Fila
# ============================================================================
def processar_fila():
    """
    Processa análises pendentes na fila
    Analisa sentimento e atualiza no banco
    """
    if fila_analises.empty():
        print("Fila vazia")
        return None

    # Pega da fila
    tarefa = fila_analises.get()
    analysis_id = tarefa['id']
    texto = tarefa['text']

    print(f"\n⚡ Processando análise {analysis_id}")
    print(f"Texto: {texto[:50]}...")

    # Análise simples de sentimento
    sentiment, score = analisar_sentimento(texto)

    # Atualiza banco
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''UPDATE analyses
           SET sentiment = ?, score = ?, status = 'completed'
           WHERE id = ?''',
        (sentiment, score, analysis_id)
    )
    conn.commit()
    conn.close()

    print(f"✓ Sentimento: {sentiment} (score: {score})")
    return {
        'id': analysis_id,
        'sentiment': sentiment,
        'score': score
    }


def analisar_sentimento(texto):
    """
    Análise de sentimento simplificada
    Retorna (sentimento, score)
    """
    texto_lower = texto.lower()

    # Palavras positivas e negativas
    positivas = ['bom', 'ótimo', 'excelente', 'amo', 'adorei', 'maravilhoso',
                 'perfeito', 'incrível', 'feliz', 'satisfeito', 'top', 'legal']

    negativas = ['ruim', 'péssimo', 'horrível', 'odeio', 'terrível', 'mal',
                 'pior', 'problema', 'defeito', 'insatisfeito', 'raiva', 'lixo']

    # Conta palavras
    count_pos = sum(1 for p in positivas if p in texto_lower)
    count_neg = sum(1 for n in negativas if n in texto_lower)

    # Calcula score
    total = count_pos + count_neg
    if total == 0:
        return 'neutral', 0.0

    score = (count_pos - count_neg) / total

    # Classifica
    if score > 0.2:
        sentiment = 'positive'
    elif score < -0.2:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'

    return sentiment, round(score, 2)


# ============================================================================
# FUNÇÃO 3: Buscar Resultado
# ============================================================================
def buscar_resultado(analysis_id):
    """
    Busca resultado de uma análise

    Args:
        analysis_id: ID da análise

    Returns:
        Dicionário com dados da análise ou None
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analyses WHERE id = ?', (analysis_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        'id': row['id'],
        'text': row['text'],
        'sentiment': row['sentiment'],
        'score': row['score'],
        'status': row['status'],
        'created_at': row['created_at']
    }
