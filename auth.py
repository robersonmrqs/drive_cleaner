import os
import json
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import id_token
from google.auth.transport import requests
from config import Config

class AuthService:
    """Serviço de autenticação para múltiplos provedores de armazenamento."""
    
    @staticmethod
    def get_google_auth_url() -> str:
        """Gera a URL de autenticação OAuth 2.0 para o Google."""
        try:
            flow = InstalledAppFlow.from_client_config(
                Config.get_google_credentials(),
                scopes=Config.GOOGLE_SCOPES,
                redirect_uri=Config.GOOGLE_REDIRECT_URI
            )

            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            return auth_url
            
        except Exception as e:
            raise Exception(f"Erro ao gerar URL de autenticação do Google: {e}")

    @staticmethod
    def validate_google_auth(auth_code: str) -> Credentials:
        """Valida o código de autorização do Google e obtém as credenciais."""
        try:
            flow = InstalledAppFlow.from_client_config(
                Config.get_google_credentials(),
                scopes=Config.GOOGLE_SCOPES,
                redirect_uri=Config.GOOGLE_REDIRECT_URI
            )

            flow.fetch_token(code=auth_code)
            creds = flow.credentials

            # Salva as credenciais no arquivo de tokens
            AuthService._save_tokens({'google': AuthService._credentials_to_dict(creds)})
            return creds
            
        except Exception as e:
            raise Exception(f"Erro na validação da autenticação do Google: {e}")

    @staticmethod
    def get_google_credentials(validate_only: bool = False) -> Optional[Credentials]:
        """Obtém credenciais Google válidas a partir do token armazenado."""
        tokens = AuthService._load_tokens()
        if not tokens or 'google' not in tokens:
            if validate_only:
                raise Exception("Nenhum token Google encontrado")
            return None

        try:
            creds = Credentials.from_authorized_user_info(tokens['google'])
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    tokens['google'] = AuthService._credentials_to_dict(creds)
                    AuthService._save_tokens(tokens)
                else:
                    if validate_only:
                        raise Exception("Credenciais Google inválidas")
                    return None
            return creds
        except Exception as e:
            AuthService._remove_token('google')
            if validate_only:
                raise Exception(f"Erro ao validar credenciais Google: {e}")
            return None

    @staticmethod
    def _credentials_to_dict(creds: Credentials) -> Dict[str, Any]:
        """Converte credenciais Google para dicionário."""
        return {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }

    @staticmethod
    def _save_tokens(tokens: Dict[str, Any]) -> None:
        """Salva todos os tokens no arquivo."""
        os.makedirs(os.path.dirname(Config.TOKEN_PATH), exist_ok=True)
        with open(Config.TOKEN_PATH, 'w') as token_file:
            json.dump(tokens, token_file)

    @staticmethod
    def _load_tokens() -> Dict[str, Any]:
        """Carrega todos os tokens do arquivo."""
        if not os.path.exists(Config.TOKEN_PATH):
            return {}
        with open(Config.TOKEN_PATH, 'r') as token_file:
            return json.load(token_file)

    @staticmethod
    def _remove_token(provider: str) -> None:
        """Remove o token de um provedor específico."""
        tokens = AuthService._load_tokens()
        if provider in tokens:
            del tokens[provider]
            AuthService._save_tokens(tokens)

    @staticmethod
    def logout():
        """Remove todos os tokens de autenticação."""
        if os.path.exists(Config.TOKEN_PATH):
            os.remove(Config.TOKEN_PATH)