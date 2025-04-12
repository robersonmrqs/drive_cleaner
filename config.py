import os
import socket
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações globais da aplicação"""
    
    # Autenticação Google
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    CREDENTIALS_PATH = os.path.join('credentials', 'credentials.json')
    TOKEN_PATH = os.path.join('credentials', 'token.json')
    
    # Configuração do servidor
    PORT = self.find_available_port()
    REDIRECT_URIS = [
        f'http://localhost:{PORT}',
        f'http://localhost:{PORT}/auth'
    ]
    
    # Aplicação
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')
    
    @staticmethod
    def find_available_port(start=5000, end=6000):
        """Encontra uma porta disponível dinamicamente"""
        for port in range(start, end + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        raise OSError("Nenhuma porta disponível")