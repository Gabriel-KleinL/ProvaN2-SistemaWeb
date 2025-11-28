"""
Testes para o analisador de sentimentos
"""

import sys
import os

# Adiciona src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sentiment_analyzer import analyzer, SentimentResult


class TestSentimentAnalyzer:
    """Testes do analisador de sentimentos"""

    def test_positive_sentiment(self):
        """Testa detecção de sentimento positivo"""
        text = "Este produto é excelente! Estou muito satisfeito com a qualidade."
        result = analyzer.analyze(text)

        assert result.sentiment == 'positive'
        assert result.score > 0
        assert result.confidence > 0
        print("✓ Teste de sentimento positivo passou")

    def test_negative_sentiment(self):
        """Testa detecção de sentimento negativo"""
        text = "Péssimo produto, total desperdício de dinheiro. Muito insatisfeito."
        result = analyzer.analyze(text)

        assert result.sentiment == 'negative'
        assert result.score < 0
        assert result.confidence > 0
        print("✓ Teste de sentimento negativo passou")

    def test_neutral_sentiment(self):
        """Testa detecção de sentimento neutro"""
        text = "O produto chegou hoje. Vou testar amanhã."
        result = analyzer.analyze(text)

        assert result.sentiment == 'neutral'
        assert -0.1 <= result.score <= 0.1
        print("✓ Teste de sentimento neutro passou")

    def test_intensifier(self):
        """Testa intensificadores"""
        text1 = "Bom produto"
        text2 = "Produto muito bom"

        result1 = analyzer.analyze(text1)
        result2 = analyzer.analyze(text2)

        # Score com intensificador deve ser maior
        assert result2.score > result1.score
        print("✓ Teste de intensificador passou")

    def test_negation(self):
        """Testa negações"""
        text1 = "Produto bom"
        text2 = "Produto não bom"

        result1 = analyzer.analyze(text1)
        result2 = analyzer.analyze(text2)

        # Negação inverte sentimento
        assert result1.score > 0
        assert result2.score < 0
        print("✓ Teste de negação passou")

    def test_keyword_extraction(self):
        """Testa extração de palavras-chave"""
        text = "Produto excelente, qualidade incrível, muito satisfeito!"
        result = analyzer.analyze(text)

        assert len(result.keywords) > 0
        assert any(kw in ['excelente', 'incrível', 'satisfeito'] for kw in result.keywords)
        print("✓ Teste de extração de keywords passou")

    def test_word_count(self):
        """Testa contagem de palavras"""
        text = "Este é um texto com dez palavras para testar contador"
        result = analyzer.analyze(text)

        assert result.word_count == 10
        print("✓ Teste de contagem de palavras passou")

    def test_batch_analysis(self):
        """Testa análise em lote"""
        texts = [
            "Ótimo produto!",
            "Péssimo atendimento.",
            "Produto normal."
        ]

        results = analyzer.analyze_batch(texts)

        assert len(results) == 3
        assert results[0].sentiment == 'positive'
        assert results[1].sentiment == 'negative'
        assert results[2].sentiment == 'neutral'
        print("✓ Teste de análise em lote passou")

    def test_sentiment_summary(self):
        """Testa geração de resumo"""
        texts = [
            "Excelente!",
            "Péssimo!",
            "Bom.",
            "Ótimo!"
        ]

        results = analyzer.analyze_batch(texts)
        summary = analyzer.get_sentiment_summary(results)

        assert summary['total'] == 4
        assert summary['positive'] == 3
        assert summary['negative'] == 1
        assert summary['positive_percent'] == 75.0
        print("✓ Teste de resumo passou")

    def test_confidence_calculation(self):
        """Testa cálculo de confiança"""
        # Texto com muitas palavras sentimentais
        text1 = "Excelente ótimo maravilhoso incrível perfeito"
        # Texto com poucas palavras sentimentais
        text2 = "O produto chegou ontem e excelente"

        result1 = analyzer.analyze(text1)
        result2 = analyzer.analyze(text2)

        # Mais palavras sentimentais = maior confiança
        assert result1.confidence > result2.confidence
        print("✓ Teste de confiança passou")

    def test_empty_text(self):
        """Testa texto vazio"""
        text = ""
        result = analyzer.analyze(text)

        assert result.sentiment == 'neutral'
        assert result.score == 0
        assert result.confidence == 0
        print("✓ Teste de texto vazio passou")


def run_all_tests():
    """Executa todos os testes"""
    print("=" * 80)
    print("🧪 Executando Testes do Analisador de Sentimentos")
    print("=" * 80 + "\n")

    test = TestSentimentAnalyzer()

    tests = [
        test.test_positive_sentiment,
        test.test_negative_sentiment,
        test.test_neutral_sentiment,
        test.test_intensifier,
        test.test_negation,
        test.test_keyword_extraction,
        test.test_word_count,
        test.test_batch_analysis,
        test.test_sentiment_summary,
        test.test_confidence_calculation,
        test.test_empty_text
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} falhou: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} erro: {e}")
            failed += 1

    print("\n" + "=" * 80)
    print(f"📊 Resultado: {passed} passou, {failed} falhou")
    print("=" * 80 + "\n")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
