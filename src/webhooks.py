"""
Sistema de Webhooks
Envia notificações HTTP para sistemas externos
"""

import requests
import hashlib
import hmac
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from database import WebhookConfigModel, WebhookLogModel


class WebhookService:
    """Serviço de envio de webhooks"""

    def __init__(self):
        self.timeout = 10  # segundos
        self.max_retries = 3
        self.retry_delays = [1, 5, 15]  # segundos entre tentativas

    def send_webhook(self, url: str, payload: Dict[str, Any],
                     secret: Optional[str] = None,
                     headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Envia webhook para URL

        Args:
            url: URL destino
            payload: Dados a enviar
            secret: Secret para assinar payload
            headers: Headers adicionais

        Returns:
            Resultado do envio
        """
        # Prepara headers
        request_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'SentimentAnalysisWebhook/1.0'
        }

        if headers:
            request_headers.update(headers)

        # Assina payload se secret fornecido
        if secret:
            signature = self._sign_payload(payload, secret)
            request_headers['X-Webhook-Signature'] = signature

        # Tenta enviar com retries
        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=request_headers,
                    timeout=self.timeout
                )

                return {
                    'success': response.status_code < 400,
                    'status_code': response.status_code,
                    'response_body': response.text[:1000],  # Limita tamanho
                    'attempts': attempt + 1,
                    'error': None
                }

            except requests.exceptions.RequestException as e:
                # Se foi a última tentativa, retorna erro
                if attempt == self.max_retries - 1:
                    return {
                        'success': False,
                        'status_code': None,
                        'response_body': None,
                        'attempts': attempt + 1,
                        'error': str(e)
                    }

                # Aguarda antes de retentar
                time.sleep(self.retry_delays[attempt])

        return {
            'success': False,
            'status_code': None,
            'response_body': None,
            'attempts': self.max_retries,
            'error': 'Max retries exceeded'
        }

    def _sign_payload(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Cria assinatura HMAC do payload

        Args:
            payload: Dados a assinar
            secret: Chave secreta

        Returns:
            Assinatura hexadecimal
        """
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    def notify_analysis_complete(self, analysis_id: str, user_id: int,
                                  sentiment: str, score: float, confidence: float,
                                  metadata: Optional[Dict] = None):
        """
        Notifica webhooks sobre análise completa

        Args:
            analysis_id: ID da análise
            user_id: ID do usuário
            sentiment: Sentimento detectado
            score: Score do sentimento
            confidence: Confiança da análise
            metadata: Metadados adicionais
        """
        # Busca webhooks configurados para o usuário
        webhooks = WebhookConfigModel.get_by_user(user_id)

        # Prepara payload
        payload = {
            'event': 'analysis_complete',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'analysis_id': analysis_id,
                'user_id': user_id,
                'sentiment': sentiment,
                'score': score,
                'confidence': confidence,
                'metadata': metadata or {}
            }
        }

        # Envia para cada webhook que está inscrito no evento
        for webhook in webhooks:
            events = webhook.get('events', [])

            # Verifica se webhook está inscrito neste evento
            if 'analysis_complete' not in events and '*' not in events:
                continue

            # Envia webhook
            result = self.send_webhook(
                webhook['url'],
                payload,
                secret=webhook.get('secret')
            )

            # Registra log
            WebhookLogModel.create(
                analysis_id=analysis_id,
                webhook_config_id=webhook['id'],
                webhook_url=webhook['url'],
                payload=payload,
                status_code=result.get('status_code'),
                response_body=result.get('response_body'),
                success=result['success']
            )

    def notify_negative_sentiment(self, analysis_id: str, user_id: int,
                                   text: str, score: float,
                                   metadata: Optional[Dict] = None):
        """
        Notifica sobre sentimento negativo (alerta)

        Args:
            analysis_id: ID da análise
            user_id: ID do usuário
            text: Texto analisado
            score: Score negativo
            metadata: Metadados
        """
        # Busca webhooks configurados
        webhooks = WebhookConfigModel.get_by_user(user_id)

        # Prepara payload de alerta
        payload = {
            'event': 'negative_sentiment',
            'severity': 'high' if score < -0.5 else 'medium',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'analysis_id': analysis_id,
                'user_id': user_id,
                'text_preview': text[:100] + '...' if len(text) > 100 else text,
                'sentiment_score': score,
                'metadata': metadata or {}
            }
        }

        # Envia para webhooks inscritos
        for webhook in webhooks:
            events = webhook.get('events', [])

            if 'negative_sentiment' not in events and '*' not in events:
                continue

            result = self.send_webhook(
                webhook['url'],
                payload,
                secret=webhook.get('secret')
            )

            WebhookLogModel.create(
                analysis_id=analysis_id,
                webhook_config_id=webhook['id'],
                webhook_url=webhook['url'],
                payload=payload,
                status_code=result.get('status_code'),
                response_body=result.get('response_body'),
                success=result['success']
            )

    def test_webhook(self, url: str, secret: Optional[str] = None) -> Dict[str, Any]:
        """
        Testa webhook enviando payload de teste

        Args:
            url: URL do webhook
            secret: Secret opcional

        Returns:
            Resultado do teste
        """
        payload = {
            'event': 'webhook_test',
            'timestamp': datetime.now().isoformat(),
            'message': 'This is a test webhook from Sentiment Analysis API'
        }

        result = self.send_webhook(url, payload, secret)

        return {
            'test_successful': result['success'],
            'status_code': result.get('status_code'),
            'response_preview': result.get('response_body', '')[:200],
            'attempts': result.get('attempts'),
            'error': result.get('error')
        }


# Instância global do serviço
webhook_service = WebhookService()


def configure_webhook(user_id: int, url: str, events: List[str],
                      secret: Optional[str] = None) -> int:
    """
    Configura webhook para usuário

    Args:
        user_id: ID do usuário
        url: URL do webhook
        events: Lista de eventos (ex: ['analysis_complete', 'negative_sentiment'])
        secret: Secret para assinatura

    Returns:
        ID da configuração criada
    """
    # Valida URL
    if not url.startswith('http://') and not url.startswith('https://'):
        raise ValueError('URL deve começar com http:// ou https://')

    # Valida eventos
    valid_events = {'analysis_complete', 'negative_sentiment', '*'}
    for event in events:
        if event not in valid_events:
            raise ValueError(f'Evento inválido: {event}')

    # Cria configuração
    config_id = WebhookConfigModel.create(user_id, url, events, secret)
    return config_id


def send_analysis_webhook(analysis_id: str, user_id: int, sentiment: str,
                          score: float, confidence: float,
                          metadata: Optional[Dict] = None):
    """Envia webhook de análise completa"""
    webhook_service.notify_analysis_complete(
        analysis_id, user_id, sentiment, score, confidence, metadata
    )

    # Se negativo, envia alerta também
    if sentiment == 'negative':
        webhook_service.notify_negative_sentiment(
            analysis_id, user_id,
            metadata.get('text', '') if metadata else '',
            score, metadata
        )
