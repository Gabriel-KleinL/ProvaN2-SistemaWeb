"""
Testes das 3 Funções
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import init_db
from funcoes import cadastrar_analise, processar_fila, buscar_resultado


def test_funcao_1_cadastrar():
    """Testa FUNÇÃO 1: Cadastrar Análise"""
    print("\n=== Teste FUNÇÃO 1: Cadastrar Análise ===")

    init_db()

    # Cadastra análise
    analysis_id = cadastrar_analise(1, "Este produto é excelente!")

    assert analysis_id is not None
    print(f"✓ Análise cadastrada: {analysis_id}")


def test_funcao_2_processar():
    """Testa FUNÇÃO 2: Processar Fila"""
    print("\n=== Teste FUNÇÃO 2: Processar Fila ===")

    init_db()

    # Cadastra para ter algo na fila
    cadastrar_analise(1, "Produto ótimo e excelente!")

    # Processa
    resultado = processar_fila()

    assert resultado is not None
    assert resultado['sentiment'] == 'positive'
    print(f"✓ Processado: {resultado['sentiment']} (score: {resultado['score']})")


def test_funcao_3_buscar():
    """Testa FUNÇÃO 3: Buscar Resultado"""
    print("\n=== Teste FUNÇÃO 3: Buscar Resultado ===")

    init_db()

    # Limpa fila de testes anteriores
    from funcoes import fila_analises
    while not fila_analises.empty():
        try:
            fila_analises.get_nowait()
        except:
            break

    # Cadastra e processa
    analysis_id = cadastrar_analise(1, "Produto péssimo e ruim")
    processar_fila()

    # Busca resultado
    resultado = buscar_resultado(analysis_id)

    assert resultado is not None
    assert resultado['sentiment'] == 'negative'
    assert resultado['status'] == 'completed'
    print(f"✓ Resultado encontrado: {resultado['sentiment']}")


def test_sentimentos():
    """Testa diferentes sentimentos"""
    print("\n=== Teste de Sentimentos ===")

    init_db()

    testes = [
        ("Produto excelente e maravilhoso!", "positive"),
        ("Péssimo, horrível e ruim", "negative"),
        ("O produto chegou", "neutral")
    ]

    for texto, esperado in testes:
        analysis_id = cadastrar_analise(1, texto)
        resultado = processar_fila()

        assert resultado['sentiment'] == esperado
        print(f"✓ '{texto[:30]}...' → {esperado}")


if __name__ == '__main__':
    print("="*60)
    print("🧪 Testando 3 Funções")
    print("="*60)

    try:
        test_funcao_1_cadastrar()
        test_funcao_2_processar()
        test_funcao_3_buscar()
        test_sentimentos()

        print("\n" + "="*60)
        print("✅ Todos os testes passaram!")
        print("="*60 + "\n")

    except AssertionError as e:
        print(f"\n❌ Teste falhou: {e}\n")
    except Exception as e:
        print(f"\n❌ Erro: {e}\n")
