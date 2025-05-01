import os
import socket
from dotenv import load_dotenv
from typing import List


load_dotenv()


class Config:
    """Configurações globais da aplicação."""
    
    @staticmethod
    def find_available_port(start: int = 5000, end: int = 6000) -> int:
        """Encontra uma porta disponível no intervalo especificado.
        
        Args:
            start: Porta inicial para busca (padrão: 5000).
            end: Porta final para busca (padrão: 6000).
            
        Returns:
            Número da primeira porta disponível encontrada.
            
        Raises:
            OSError: Se nenhuma porta estiver disponível no intervalo.
        """
        for port in range(start, end + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        raise OSError("Nenhuma porta disponível no intervalo especificado")

    # Configurações de rede e autenticação
    PORT: int = find_available_port.__func__()  # type: ignore
    REDIRECT_URIS: List[str] = [
        f'http://localhost:{PORT}',
        f'http://localhost:{PORT}/auth'
    ]
    
    # Escopos da API Google
    SCOPES: List[str] = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/userinfo.profile',
        'https://www.googleapis.com/auth/userinfo.email',
        'openid'
    ]
    
    # Caminhos de arquivos
    CREDENTIALS_PATH: str = os.path.join('credentials', 'credentials.json')
    TOKEN_PATH: str = os.path.join('credentials', 'token.json')
    
    # Chave secreta para sessões Flask
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-key-123')