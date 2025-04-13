import os
import socket
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações globais da aplicação"""

    @staticmethod
    def find_available_port(start=5000, end=6000):
        """
        Encontra uma porta disponível dinamicamente entre os intervalos especificados.
        """
        for port in range(start, end + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('localhost', port)) != 0:
                    return port
        raise OSError("Nenhuma porta disponível")

# Executa fora da classe (chamada correta de método estático)
Config.PORT = Config.find_available_port()
Config.REDIRECT_URIS = [
    f'http://localhost:{Config.PORT}',
    f'http://localhost:{Config.PORT}/auth'
]

# Outras configurações dentro da classe
Config.SCOPES = ['https://www.googleapis.com/auth/drive']
Config.CREDENTIALS_PATH = os.path.join('credentials', 'credentials.json')
Config.TOKEN_PATH = os.path.join('credentials', 'token.json')
Config.SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-123')