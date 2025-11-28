"""
Módulo de autenticação e autorização
Implementa JWT, hashing de senhas e decorators de proteção
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from typing import Optional, Dict, Any
import os

from database import UserModel


# Configurações JWT
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas


class AuthService:
    """Serviço de autenticação"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Gera hash bcrypt de senha"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica senha contra hash"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    @staticmethod
    def create_access_token(user_id: int, email: str) -> str:
        """Cria token JWT"""
        payload = {
            'user_id': user_id,
            'email': email,
            'exp': datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token

    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """Decodifica e valida token JWT"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def register_user(username: str, email: str, password: str) -> Dict[str, Any]:
        """Registra novo usuário"""
        # Verifica se email já existe
        existing_user = UserModel.get_by_email(email)
        if existing_user:
            raise ValueError('Email já cadastrado')

        # Hash da senha
        password_hash = AuthService.hash_password(password)

        # Cria usuário
        user_id = UserModel.create(username, email, password_hash)

        return {
            'user_id': user_id,
            'username': username,
            'email': email
        }

    @staticmethod
    def login_user(email: str, password: str) -> Optional[Dict[str, Any]]:
        """Autentica usuário e retorna token"""
        # Busca usuário
        user = UserModel.get_by_email(email)
        if not user:
            return None

        # Verifica senha
        if not AuthService.verify_password(password, user['password_hash']):
            return None

        # Atualiza último login
        UserModel.update_last_login(user['id'])

        # Gera token
        access_token = AuthService.create_access_token(user['id'], user['email'])

        return {
            'access_token': access_token,
            'token_type': 'bearer',
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email']
        }


def get_current_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """Extrai usuário atual do token"""
    if not token:
        return None

    # Remove 'Bearer ' se presente
    if token.startswith('Bearer '):
        token = token[7:]

    payload = AuthService.decode_token(token)
    if not payload:
        return None

    user_id = payload.get('user_id')
    if not user_id:
        return None

    user = UserModel.get_by_id(user_id)
    return user


def require_auth(f):
    """Decorator para proteger rotas que requerem autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Obtém token do header Authorization
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Token de autenticação não fornecido'}), 401

        # Extrai token
        token = auth_header
        if token.startswith('Bearer '):
            token = token[7:]

        # Valida token
        user = get_current_user_from_token(token)
        if not user:
            return jsonify({'error': 'Token inválido ou expirado'}), 401

        # Adiciona usuário ao request
        request.current_user = user

        return f(*args, **kwargs)

    return decorated_function


class RateLimiter:
    """Rate limiter simples baseado em memória"""

    def __init__(self):
        self.requests = {}  # {identifier: [(timestamp, count)]}
        self.max_requests_per_minute = 60
        self.max_requests_per_hour = 1000

    def is_allowed(self, identifier: str) -> bool:
        """Verifica se requisição é permitida"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)

        # Limpa requisições antigas
        if identifier in self.requests:
            self.requests[identifier] = [
                (ts, count) for ts, count in self.requests[identifier]
                if ts > hour_ago
            ]
        else:
            self.requests[identifier] = []

        # Conta requisições no último minuto e hora
        requests_last_minute = sum(
            count for ts, count in self.requests[identifier]
            if ts > minute_ago
        )
        requests_last_hour = sum(
            count for ts, count in self.requests[identifier]
        )

        # Verifica limites
        if requests_last_minute >= self.max_requests_per_minute:
            return False
        if requests_last_hour >= self.max_requests_per_hour:
            return False

        # Adiciona requisição atual
        self.requests[identifier].append((now, 1))
        return True

    def get_rate_limit_info(self, identifier: str) -> Dict[str, int]:
        """Retorna informações de rate limit"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)

        if identifier not in self.requests:
            return {
                'requests_last_minute': 0,
                'requests_last_hour': 0,
                'limit_per_minute': self.max_requests_per_minute,
                'limit_per_hour': self.max_requests_per_hour
            }

        requests_last_minute = sum(
            count for ts, count in self.requests[identifier]
            if ts > minute_ago
        )
        requests_last_hour = sum(
            count for ts, count in self.requests[identifier]
            if ts > hour_ago
        )

        return {
            'requests_last_minute': requests_last_minute,
            'requests_last_hour': requests_last_hour,
            'limit_per_minute': self.max_requests_per_minute,
            'limit_per_hour': self.max_requests_per_hour
        }


# Instância global do rate limiter
rate_limiter = RateLimiter()


def rate_limit(f):
    """Decorator para aplicar rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Usa user_id se autenticado, senão usa IP
        identifier = None
        if hasattr(request, 'current_user') and request.current_user:
            identifier = f"user_{request.current_user['id']}"
        else:
            identifier = f"ip_{request.remote_addr}"

        # Verifica rate limit
        if not rate_limiter.is_allowed(identifier):
            return jsonify({
                'error': 'Taxa de requisições excedida',
                'message': 'Você excedeu o limite de requisições. Tente novamente mais tarde.'
            }), 429

        return f(*args, **kwargs)

    return decorated_function


def validate_request_data(required_fields: list):
    """Decorator para validar campos obrigatórios no request"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Corpo da requisição vazio'}), 400

            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                return jsonify({
                    'error': 'Campos obrigatórios faltando',
                    'missing_fields': missing_fields
                }), 400

            return f(*args, **kwargs)

        return decorated_function
    return decorator
