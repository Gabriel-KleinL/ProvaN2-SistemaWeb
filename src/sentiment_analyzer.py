"""
Analisador de Sentimentos
Processa texto e classifica sentimento usando análise léxica
"""

import re
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """Resultado da análise de sentimento"""
    sentiment: str  # 'positive', 'negative', 'neutral'
    score: float  # -1.0 a 1.0
    confidence: float  # 0.0 a 1.0
    keywords: List[str]
    word_count: int
    positive_words: int
    negative_words: int


class SentimentAnalyzer:
    """
    Analisador de sentimentos baseado em léxico
    Em produção, usaríamos modelo de ML (BERT, VADER, etc.)
    """

    def __init__(self):
        # Palavras positivas em português
        self.positive_words = {
            'ótimo', 'excelente', 'bom', 'boa', 'maravilhoso', 'incrível',
            'perfeito', 'adorei', 'amei', 'fantástico', 'espetacular',
            'satisfeito', 'feliz', 'alegre', 'contentamento', 'prazer',
            'qualidade', 'recomendo', 'superou', 'melhor', 'eficiente',
            'rápido', 'prático', 'útil', 'funcional', 'confortável',
            'lindo', 'bonito', 'agradável', 'positivo', 'sucesso',
            'top', 'show', 'legal', 'bacana', 'massa', 'demais',
            'aprovado', 'satisfação', 'encantado', 'impressionado',
            'wow', 'uau', 'demais', 'sensacional', 'magnífico'
        }

        # Palavras negativas em português
        self.negative_words = {
            'ruim', 'péssimo', 'horrível', 'terrível', 'mal', 'má',
            'defeito', 'problema', 'falha', 'erro', 'quebrado', 'quebrou',
            'insatisfeito', 'decepcionado', 'decepção', 'frustrado',
            'frustração', 'raiva', 'ódio', 'detesto', 'odiei',
            'lixo', 'porcaria', 'lento', 'demorado', 'demora',
            'caro', 'custoso', 'desperdício', 'fraco', 'fraca',
            'não recomendo', 'evitem', 'evite', 'não comprem',
            'arrependido', 'arrependimento', 'nunca mais', 'jamais',
            'desastre', 'fracasso', 'incompetente', 'ineficiente',
            'difícil', 'complicado', 'confuso', 'desorganizado',
            'sujo', 'velho', 'usado', 'danificado', 'estragado'
        }

        # Intensificadores
        self.intensifiers = {
            'muito': 1.5,
            'extremamente': 2.0,
            'super': 1.8,
            'mega': 1.8,
            'bastante': 1.3,
            'demais': 1.5,
            'totalmente': 1.7,
            'completamente': 1.7
        }

        # Negações
        self.negations = {
            'não', 'nunca', 'jamais', 'nada', 'nenhum', 'sem'
        }

    def analyze(self, text: str) -> SentimentResult:
        """
        Analisa sentimento do texto

        Args:
            text: Texto a ser analisado

        Returns:
            Resultado da análise
        """
        # Pré-processamento
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        # Análise de sentimento
        score, positive_count, negative_count, keywords = self._calculate_sentiment_score(
            words, text_lower
        )

        # Classificação
        sentiment = self._classify_sentiment(score)

        # Confiança baseada na quantidade de palavras sentimentais
        confidence = self._calculate_confidence(
            len(words), positive_count + negative_count
        )

        return SentimentResult(
            sentiment=sentiment,
            score=round(score, 3),
            confidence=round(confidence, 3),
            keywords=keywords,
            word_count=len(words),
            positive_words=positive_count,
            negative_words=negative_count
        )

    def _calculate_sentiment_score(self, words: List[str], text: str) -> Tuple[float, int, int, List[str]]:
        """Calcula score de sentimento"""
        positive_score = 0
        negative_score = 0
        keywords = []

        for i, word in enumerate(words):
            # Verifica intensificador antes da palavra
            intensity = 1.0
            if i > 0 and words[i - 1] in self.intensifiers:
                intensity = self.intensifiers[words[i - 1]]

            # Verifica negação antes da palavra
            is_negated = False
            if i > 0 and words[i - 1] in self.negations:
                is_negated = True
            elif i > 1 and words[i - 2] in self.negations:
                is_negated = True

            # Palavras positivas
            if word in self.positive_words:
                if is_negated:
                    negative_score += intensity
                    keywords.append(f"não {word}")
                else:
                    positive_score += intensity
                    keywords.append(word)

            # Palavras negativas
            elif word in self.negative_words:
                if is_negated:
                    positive_score += intensity
                    keywords.append(f"não {word}")
                else:
                    negative_score += intensity
                    keywords.append(word)

        # Conta palavras únicas
        positive_count = sum(1 for w in words if w in self.positive_words)
        negative_count = sum(1 for w in words if w in self.negative_words)

        # Score normalizado entre -1 e 1
        total_score = positive_score + negative_score
        if total_score == 0:
            return 0.0, positive_count, negative_count, keywords

        normalized_score = (positive_score - negative_score) / total_score
        return normalized_score, positive_count, negative_count, keywords[:10]

    def _classify_sentiment(self, score: float) -> str:
        """Classifica sentimento baseado no score"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'

    def _calculate_confidence(self, total_words: int, sentiment_words: int) -> float:
        """
        Calcula confiança da análise

        Baseado na proporção de palavras sentimentais no texto
        """
        if total_words == 0:
            return 0.0

        ratio = sentiment_words / total_words

        # Confiança aumenta com a proporção, mas satura em 95%
        confidence = min(ratio * 5, 0.95)

        # Penaliza textos muito curtos
        if total_words < 5:
            confidence *= 0.7
        elif total_words < 10:
            confidence *= 0.85

        return confidence

    def analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Analisa múltiplos textos"""
        return [self.analyze(text) for text in texts]

    def get_sentiment_summary(self, results: List[SentimentResult]) -> Dict[str, Any]:
        """Gera resumo de múltiplas análises"""
        if not results:
            return {
                'total': 0,
                'positive': 0,
                'negative': 0,
                'neutral': 0,
                'average_score': 0.0,
                'average_confidence': 0.0
            }

        sentiment_counts = {
            'positive': sum(1 for r in results if r.sentiment == 'positive'),
            'negative': sum(1 for r in results if r.sentiment == 'negative'),
            'neutral': sum(1 for r in results if r.sentiment == 'neutral')
        }

        average_score = sum(r.score for r in results) / len(results)
        average_confidence = sum(r.confidence for r in results) / len(results)

        return {
            'total': len(results),
            'positive': sentiment_counts['positive'],
            'negative': sentiment_counts['negative'],
            'neutral': sentiment_counts['neutral'],
            'positive_percent': round(sentiment_counts['positive'] / len(results) * 100, 2),
            'negative_percent': round(sentiment_counts['negative'] / len(results) * 100, 2),
            'neutral_percent': round(sentiment_counts['neutral'] / len(results) * 100, 2),
            'average_score': round(average_score, 3),
            'average_confidence': round(average_confidence, 3)
        }


# Instância global do analisador
analyzer = SentimentAnalyzer()


def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Função de conveniência para análise de sentimento

    Args:
        text: Texto a ser analisado

    Returns:
        Dicionário com resultado da análise
    """
    result = analyzer.analyze(text)

    return {
        'sentiment': result.sentiment,
        'score': result.score,
        'confidence': result.confidence,
        'keywords': result.keywords,
        'statistics': {
            'word_count': result.word_count,
            'positive_words': result.positive_words,
            'negative_words': result.negative_words
        }
    }


def analyze_with_context(text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Análise com contexto adicional

    Args:
        text: Texto a analisar
        metadata: Metadados do contexto

    Returns:
        Resultado enriquecido com contexto
    """
    result = analyze_sentiment(text)
    result['metadata'] = metadata
    result['analyzed_at'] = datetime.now().isoformat()

    return result


if __name__ == '__main__':
    # Testes do analisador
    from datetime import datetime

    test_texts = [
        "Este produto é incrível! Estou muito satisfeito com a compra.",
        "Péssimo atendimento, nunca mais volto.",
        "O produto é OK, nada de especial.",
        "Adorei! Super recomendo, qualidade excelente!",
        "Horrível, não funciona direito e quebrou logo."
    ]

    print("=== Teste de Análise de Sentimentos ===\n")

    for text in test_texts:
        result = analyzer.analyze(text)
        print(f"Texto: {text}")
        print(f"Sentimento: {result.sentiment}")
        print(f"Score: {result.score}")
        print(f"Confiança: {result.confidence}")
        print(f"Palavras-chave: {', '.join(result.keywords)}")
        print(f"Estatísticas: {result.positive_words} positivas, {result.negative_words} negativas")
        print("-" * 80)
        print()

    # Resumo
    results = analyzer.analyze_batch(test_texts)
    summary = analyzer.get_sentiment_summary(results)
    print("=== Resumo Geral ===")
    print(f"Total de análises: {summary['total']}")
    print(f"Positivas: {summary['positive']} ({summary['positive_percent']}%)")
    print(f"Negativas: {summary['negative']} ({summary['negative_percent']}%)")
    print(f"Neutras: {summary['neutral']} ({summary['neutral_percent']}%)")
    print(f"Score médio: {summary['average_score']}")
    print(f"Confiança média: {summary['average_confidence']}")
