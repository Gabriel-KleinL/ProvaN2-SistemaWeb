"""
FUNÇÃO 1: Cadastrar Análise
"""
import uuid
from database import get_db
from fila import fila_analises


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
