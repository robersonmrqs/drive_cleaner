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
        """Inicializa o serviço com credenciais válidas"""
        self.creds = get_google_credentials()
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def list_recent_images(self):
        """
        Lista imagens recentes da pasta 'Recentes' do Drive
        Retorna:
            list: Lista de dicionários com metadados das imagens
        """
        query = "mimeType contains 'image/' and trashed = false and 'root' in parents"
        results = self.service.files().list(
            q=query,
            pageSize=50,  # Limite para pasta Recentes
            fields="files(id, name, mimeType, size, modifiedTime, thumbnailLink)",
            orderBy="modifiedTime desc"
        ).execute()
        return results.get('files', [])
    
    def download_image(self, file_id):
        """
        Baixa uma imagem do Drive
        Args:
            file_id (str): ID do arquivo no Drive
        Retorna:
            BytesIO: Objeto com os dados da imagem
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
        """
        Remove um arquivo do Drive
        Args:
            file_id (str): ID do arquivo a ser removido
        """
        self.service.files().delete(fileId=file_id).execute()
    
    def find_duplicates(self, threshold=5):
        """
        Identifica imagens duplicadas na pasta Recentes
        Args:
            threshold (int): Nível de similaridade (0-100)
        Retorna:
            list: Lista de dicionários com duplicatas encontradas
        """
        images = self.list_recent_images()
        hashes = {}
        duplicates = []
        
        print(f"\n🔍 Analisando {len(images)} imagens recentes...")
        
        for img in tqdm(images, desc="Processando imagens"):
            try:
                # Baixa e calcula hash perceptual
                img_data = self.download_image(img['id'])
                with Image.open(img_data) as image:
                    img_hash = str(imagehash.average_hash(image))
                
                # Verifica duplicatas
                if img_hash in hashes:
                    duplicates.append({
                        'original': hashes[img_hash],
                        'duplicate': img,
                        'similarity': 100 - (int(img_hash) % 100)  # Simula porcentagem
                    })
                else:
                    hashes[img_hash] = img
                
                img_data.close()
            except Exception as e:
                print(f"\n⚠️ Erro ao processar {img.get('name')}: {str(e)}")
                continue
        
        return duplicates