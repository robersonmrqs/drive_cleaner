import os
from typing import Optional, Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2 import id_token
from google.auth.transport import requests
from config import Config


def get_google_auth_url() -> str:
    """Gera a URL de autenticação OAuth 2.0 para o Google.
    
    Returns:
        URL de autenticação para redirecionamento do usuário.
        
    Raises:
        Exception: Se ocorrer erro ao gerar a URL de autenticação.
    """
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            Config.CREDENTIALS_PATH,
            Config.SCOPES,
            redirect_uri=f'http://localhost:{Config.PORT}/auth'
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return auth_url
        
    except Exception as e:
        raise Exception(f"Erro ao gerar URL de autenticação: {e}")


def validate_google_auth(auth_code: str) -> Credentials:
    """Valida o código de autorização e obtém as credenciais do usuário.
    
    Args:
        auth_code: Código de autorização retornado pelo Google OAuth.
        
    Returns:
        Credentials: Objeto de credenciais do Google.
        
    Raises:
        Exception: Se ocorrer erro na validação ou obtenção de tokens.
    """
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            Config.CREDENTIALS_PATH,
            Config.SCOPES,
            redirect_uri=f'http://localhost:{Config.PORT}/auth'
        )

        flow.fetch_token(code=auth_code)
        creds = flow.credentials

        # Salvar credenciais para uso futuro
        os.makedirs(os.path.dirname(Config.TOKEN_PATH), exist_ok=True)
        with open(Config.TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

        return creds
        
    except Exception as e:
        raise Exception(f"Erro na validação da autenticação: {e}")


def get_google_credentials(validate_only: bool = False) -> Optional[Credentials]:
    """Obtém credenciais Google válidas a partir do token armazenado.
    
    Args:
        validate_only: Se True, apenas valida sem tentar autenticar.
        
    Returns:
        Credentials válidas ou None se não puder obter.
        
    Raises:
        Exception: Se validate_only=True e as credenciais forem inválidas.
    """
    creds = None
    
    # Verifica se existe token salvo
    if os.path.exists(Config.TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(Config.TOKEN_PATH, Config.SCOPES)
        except Exception as e:
            os.remove(Config.TOKEN_PATH)
            if validate_only:
                raise Exception("Credenciais inválidas devido a mudança de escopos")
            return None

    # Valida credenciais existentes
    if creds and creds.valid:
        return creds
        
    # Tenta renovar credenciais expiradas
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            
            # Salva as credenciais atualizadas
            with open(Config.TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
                
            return creds
            
        except Exception as e:
            os.remove(Config.TOKEN_PATH)
            if validate_only:
                raise Exception("Credenciais expiradas")
            return None

    # Se validate_only, não tenta autenticar, apenas verifica
    if validate_only:
        raise Exception("Autenticação necessária")
        
    return None