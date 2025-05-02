import os
import socket
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class Config:
    """Configurações globais da aplicação com suporte a múltiplos provedores."""
    
    @staticmethod
    def find_available_port(start: int = 5000, end: int = 6000) -> int:
        """Encontra uma porta disponível no intervalo especificado."""
        for port in range(start, end + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        raise OSError("Nenhuma porta disponível no intervalo especificado")

    # Configurações gerais
    PORT: int = find_available_port.__func__()  # type: ignore
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-key-123')

    # Configurações do Google Drive
    GOOGLE_CLIENT_ID: str = os.getenv('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET: str = os.getenv('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI: str = os.getenv('GOOGLE_REDIRECT_URI', f'http://localhost:{PORT}/auth')
    
    # Configurações do OneDrive
    ONEDRIVE_CLIENT_ID: str = os.getenv('ONEDRIVE_CLIENT_ID', '')
    ONEDRIVE_CLIENT_SECRET: str = os.getenv('ONEDRIVE_CLIENT_SECRET', '')
    ONEDRIVE_REDIRECT_URI: str = os.getenv('ONEDRIVE_REDIRECT_URI', f'http://localhost:{PORT}/onedrive-auth')

    # Escopos da API Google
    GOOGLE_SCOPES: List[str] = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'
    ]

    # Escopos da API Microsoft
    ONEDRIVE_SCOPES: List[str] = [
        'User.Read',
        'Files.ReadWrite.All',
        'offline_access'
    ]

    # Caminhos de arquivos
    TOKEN_PATH: str = os.path.join('credentials', 'tokens.json')  # Agora armazena todos os tokens

    @staticmethod
    def get_google_credentials() -> Dict[str, Any]:
        """Retorna as credenciais do Google como dicionário."""
        return {
            "web": {
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [Config.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }