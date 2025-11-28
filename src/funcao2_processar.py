"""
FUNÇÃO 2: Processar Fila
"""
from database import get_db
from fila import fila_analises


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
