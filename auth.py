import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from config import Config

def get_google_credentials():
    """Obtém credenciais Google válidas"""
    creds = None
    config = Config()
    
    # Verifica se já existe token salvo
    if os.path.exists(config.TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(config.TOKEN_PATH, config.SCOPES)
    
    # Se não há credenciais válidas, inicia o fluxo
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.CREDENTIALS_PATH, 
                config.SCOPES,
                redirect_uri=config.REDIRECT_URIS[1]
            )
            creds = flow.run_local_server(
                port=config.PORT,
                authorization_prompt_message='Acesse esta URL: {url}',
                success_message='Autenticação concluída!',
                open_browser=True
            )
        
        # Salva as credenciais para o próximo uso
        with open(config.TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    return creds