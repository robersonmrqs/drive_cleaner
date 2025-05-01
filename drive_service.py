import io
import time
import hashlib
from typing import Optional, List, Dict, Any, Callable, Tuple
from PIL import Image
import imagehash
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from config import Config
from auth import get_google_credentials


class DriveService:
    """Serviço para interação com a API do Google Drive com suporte a análise de duplicatas."""

    # Constantes para tipos de arquivo
    FILE_TYPE_ALL = 'all'
    FILE_TYPE_IMAGE = 'image'
    FILE_TYPE_VIDEO = 'video'
    FILE_TYPE_DOCUMENT = 'document'

    # Limite de similaridade para imagens (0-64)
    IMAGE_SIMILARITY_THRESHOLD = 5

    def __init__(self, creds=None):
        """Inicializa o serviço Drive com credenciais.
        
        Args:
            creds: Credenciais do Google. Se None, tenta obter automaticamente.
            
        Raises:
            Exception: Se não for possível obter credenciais válidas.
        """
        self.creds = creds or get_google_credentials()
        if not self.creds:
            raise Exception("Credenciais do Google inválidas ou não fornecidas")

        self.service = build('drive', 'v3', credentials=self.creds)
        self._reset_analysis_state()

    def _reset_analysis_state(self):
        """Reseta o estado interno da análise."""
        self.progress = 0
        self.total_files = 0
        self.current_index = 0
        self.cancelled = False
        self.paused = False

    def pause(self) -> None:
        """Pausa a execução da análise."""
        self.paused = True

    def resume(self) -> None:
        """Retoma a execução da análise."""
        self.paused = False

    def cancel(self) -> None:
        """Cancela a análise em andamento."""
        self.cancelled = True

    def get_user_info(self) -> Dict[str, str]:
        """Obtém informações básicas do usuário autenticado.
        
        Returns:
            Dicionário com 'email' e 'name' do usuário.
        """
        try:
            oauth_service = build('oauth2', 'v2', credentials=self.creds)
            user_info = oauth_service.userinfo().get().execute()
            return {
                'email': user_info.get('email', 'email-desconhecido@dominio.com'),
                'name': user_info.get('name', 'Usuário')
            }
        except Exception as e:
            print(f"Erro ao obter informações do usuário: {e}")
            return {'email': 'email-desconhecido@dominio.com', 'name': 'Usuário'}

    def list_folders(self) -> List[Dict[str, str]]:
        """Lista todas as pastas do usuário no Google Drive.
        
        Returns:
            Lista de dicionários com 'id' e 'name' de cada pasta.
        """
        results = self.service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)",
            spaces='drive'
        ).execute()
        return results.get('files', [])

    def list_files(self, folder_id: Optional[str] = None, 
                  file_type: str = FILE_TYPE_IMAGE) -> List[Dict[str, Any]]:
        """Lista arquivos do Google Drive com filtros opcionais.
        
        Args:
            folder_id: ID da pasta para filtrar (None para todo o Drive).
            file_type: Tipo de arquivo ('all', 'image', 'video', 'document').
            
        Returns:
            Lista de arquivos com metadados.
        """
        query = self._build_file_query(folder_id, file_type)
        files = []
        page_token = None

        while True:
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, thumbnailLink)",
                pageSize=100,
                pageToken=page_token
            ).execute()

            files.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            if not page_token:
                break

        return files

    def _build_file_query(self, folder_id: Optional[str], file_type: str) -> str:
        """Constrói a query para listagem de arquivos.
        
        Args:
            folder_id: ID da pasta ou None.
            file_type: Tipo de arquivo a filtrar.
            
        Returns:
            String com a query formatada.
        """
        mime_queries = {
            self.FILE_TYPE_IMAGE: "mimeType contains 'image/'",
            self.FILE_TYPE_VIDEO: "mimeType contains 'video/'",
            self.FILE_TYPE_DOCUMENT: "mimeType='application/pdf' or mimeType contains 'officedocument'"
        }

        query = "trashed=false"
        if file_type != self.FILE_TYPE_ALL:
            query += f" and {mime_queries.get(file_type, mime_queries[self.FILE_TYPE_IMAGE])}"

        if folder_id:
            query += f" and '{folder_id}' in parents"

        return query

    def find_duplicates(self, folder_id: Optional[str] = None, 
                       file_type: str = FILE_TYPE_IMAGE) -> Optional[List[Dict[str, Any]]]:
        """Encontra arquivos duplicados no Google Drive.
        
        Args:
            folder_id: ID da pasta para analisar (None para todo o Drive).
            file_type: Tipo de arquivo ('all', 'image', 'video', 'document').
            
        Returns:
            Lista de duplicatas encontradas ou None se cancelado.
        """
        self._reset_analysis_state()
        files = self.list_files(folder_id, file_type)
        self.total_files = len(files)

        seen_hashes = []
        duplicates = []

        for i, file_data in enumerate(files):
            if self._check_cancellation():
                return None

            self._update_progress(i + 1)
            self._wait_if_paused()

            try:
                content = self.download_binary(file_data['id'])
                file_hash, compare_fn = self._get_file_hash(content, file_data, file_type)
                self._check_for_duplicates(file_data, file_hash, compare_fn, seen_hashes, duplicates)
            except Exception as e:
                print(f"Erro ao processar {file_data.get('name')}: {e}")

        self.progress = 100 if not self.cancelled else 0
        return duplicates

    def _check_cancellation(self) -> bool:
        """Verifica se a análise foi cancelada."""
        return self.cancelled

    def _update_progress(self, current_index: int) -> None:
        """Atualiza o progresso da análise."""
        self.current_index = current_index
        self.progress = int((current_index / self.total_files) * 100) if self.total_files > 0 else 0

    def _wait_if_paused(self) -> None:
        """Aguarda se a análise estiver pausada."""
        while self.paused:
            time.sleep(0.5)

    def _get_file_hash(self, content: bytes, file_data: Dict[str, Any], 
                      file_type: str) -> Tuple[Any, Callable[[Any, Any], bool]]:
        """Calcula o hash do arquivo conforme seu tipo.
        
        Args:
            content: Conteúdo binário do arquivo.
            file_data: Metadados do arquivo.
            file_type: Tipo do arquivo.
            
        Returns:
            Tupla com (hash, função de comparação).
        """
        is_image = (file_type == self.FILE_TYPE_IMAGE if file_type != self.FILE_TYPE_ALL 
                   else file_data.get('mimeType', '').startswith('image/'))

        if is_image:
            try:
                with Image.open(io.BytesIO(content)) as image:
                    file_hash = imagehash.phash(image)
                    compare_fn = lambda a, b: (a - b) <= self.IMAGE_SIMILARITY_THRESHOLD
                    return (file_hash, compare_fn)
            except Exception:
                # Fallback para SHA-256 se não for possível processar como imagem
                pass

        file_hash = hashlib.sha256(content).hexdigest()
        return (file_hash, lambda a, b: a == b)

    def _check_for_duplicates(self, file_data: Dict[str, Any], file_hash: Any,
                            compare_fn: Callable[[Any, Any], bool],
                            seen_hashes: List[Dict[str, Any]], 
                            duplicates: List[Dict[str, Any]]) -> None:
        """Verifica se o arquivo é duplicado e atualiza as listas."""
        for entry in seen_hashes:
            if compare_fn(file_hash, entry['hash']):
                similarity = self._calculate_similarity(file_hash, entry['hash'])
                duplicates.append({
                    'original': entry['data'],
                    'duplicate': file_data,
                    'similarity': similarity
                })
                break
        else:
            seen_hashes.append({'hash': file_hash, 'data': file_data})

    def _calculate_similarity(self, hash1: Any, hash2: Any) -> int:
        """Calcula a similaridade entre dois hashes."""
        if isinstance(hash1, imagehash.ImageHash):
            return int(100 - ((hash1 - hash2) / 64) * 100)
        return 100

    def download_binary(self, file_id: str) -> bytes:
        """Baixa o conteúdo binário de um arquivo.
        
        Args:
            file_id: ID do arquivo no Google Drive.
            
        Returns:
            Conteúdo binário do arquivo.
        """
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            _, done = downloader.next_chunk()
            
        return fh.getvalue()

    def delete_file(self, file_id: str) -> None:
        """Exclui um arquivo do Google Drive.
        
        Args:
            file_id: ID do arquivo a ser excluído.
        """
        self.service.files().delete(fileId=file_id).execute()

    def get_progress(self) -> int:
        """Obtém o progresso atual da análise.
        
        Returns:
            Porcentagem de progresso (0-100).
        """
        return self.progress

    def get_detailed_progress(self) -> Dict[str, int]:
        """Obtém o progresso detalhado da análise.
        
        Returns:
            Dicionário com 'percent', 'current' e 'total'.
        """
        return {
            'percent': self.progress,
            'current': self.current_index,
            'total': self.total_files
        }