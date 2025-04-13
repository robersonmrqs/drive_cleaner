import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
import imagehash
from tqdm import tqdm
from config import Config
from auth import get_google_credentials

class DriveService:
    """Serviço para interação com o Google Drive"""

    def __init__(self):
        self.creds = get_google_credentials()
        self.service = build('drive', 'v3', credentials=self.creds)
        self.progress = 0
        self.total_files = 0
        self.current_index = 0

    def list_folders(self):
        """
        Lista todas as pastas do Drive
        Retorna:
            list: Lista de dicionários com ID e nome da pasta
        """
        results = self.service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed = false",
            fields="files(id, name)",
            spaces='drive'
        ).execute()
        return results.get('files', [])

    def list_files(self, folder_id=None, file_types="image"):
        """
        Lista arquivos de um tipo e pasta especificados
        Args:
            folder_id (str): ID da pasta alvo (ou root)
            file_types (str): 'image', 'video', 'document'
        Retorna:
            list: Lista de arquivos com metadados
        """
        mime_query = {
            'image': "mimeType contains 'image/'",
            'video': "mimeType contains 'video/'",
            'document': "mimeType = 'application/pdf' or mimeType contains 'officedocument'"
        }

        query = f"{mime_query.get(file_types, mime_query['image'])} and trashed = false"
        if folder_id:
            query += f" and '{folder_id}' in parents"

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
            page_token = response.get('nextPageToken', None)
            if not page_token:
                break
        return files

    def download_image(self, file_id):
        """
        Baixa uma imagem do Drive
        """
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        fh.seek(0)
        return fh

    def delete_file(self, file_id):
        """Remove um arquivo do Drive"""
        self.service.files().delete(fileId=file_id).execute()

    def find_duplicates(self, folder_id=None, file_type="image"):
        """
        Identifica arquivos duplicados
        """
        self.progress = 0
        files = self.list_files(folder_id, file_type)
        self.total_files = len(files)
        self.current_index = 0
        hashes = []
        duplicates = []

        for i, f in enumerate(files):
            self.current_index = i + 1
            self.progress = int((self.current_index / self.total_files) * 100)
            try:
                img_data = self.download_image(f['id'])
                with Image.open(img_data) as image:
                    img_hash = imagehash.phash(image)

                for entry in hashes:
                    distance = img_hash - entry['hash']
                    if distance <= 5:
                        duplicates.append({
                            'original': entry['data'],
                            'duplicate': f,
                            'similarity': int(100 - (distance / 64) * 100)
                        })
                        break
                else:
                    hashes.append({'hash': img_hash, 'data': f})

            except Exception as e:
                print(f"Erro ao processar {f.get('name')}: {e}")
                continue

        self.progress = 100
        return duplicates

    def get_progress(self):
        """Retorna progresso da análise atual"""
        return self.progress

    def get_detailed_progress(self):
        """Retorna progresso detalhado com contadores"""
        return {
            'percent': self.progress,
            'current': self.current_index,
            'total': self.total_files
        }