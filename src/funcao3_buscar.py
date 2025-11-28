"""
FUNÇÃO 3: Buscar Resultado
"""
from database import get_db


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
