from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
from drive_service import DriveService
from config import Config
from auth import AuthService
from typing import Optional, Dict, Any, List
import os
import json

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(Config)

# Variável global para o serviço do Drive
drive_service: Optional[DriveService] = None

def get_or_create_drive_service() -> DriveService:
    """Obtém ou cria uma instância do DriveService com credenciais válidas.
    
    Returns:
        DriveService: Instância do serviço do Google Drive
        
    Raises:
        Exception: Se não for possível obter credenciais válidas
    """
    global drive_service
    if drive_service is None:
        creds = AuthService.get_google_credentials()
        if not creds:
            raise Exception("Não foi possível obter as credenciais.")
        drive_service = DriveService(creds)
    return drive_service

def handle_drive_service_error(e: Exception, endpoint: str) -> Any:
    """Trata erros relacionados ao DriveService e redireciona para login.
    
    Args:
        e: Exceção ocorrida
        endpoint: Nome da rota onde ocorreu o erro
        
    Returns:
        Resposta Flask de redirecionamento
    """
    flash(str(e), 'danger')
    return redirect(url_for('login'))

# Rotas de autenticação
@app.route('/')
def index():
    """Rota principal que exibe a interface do Drive Cleaner.
    
    Returns:
        Renderiza template index.html ou redireciona para login em caso de erro
    """
    try:
        if not AuthService.get_google_credentials(validate_only=True):
            return redirect(url_for('login'))

        service = get_or_create_drive_service()
        folders = service.list_folders()
        user_info = service.get_user_info()
        
        return render_template(
            'index.html',
            folders=folders,
            user_name=user_info.get('name', 'Usuário'),
            email=user_info.get('email', '')
        )
    except Exception as e:
        return handle_drive_service_error(e, 'index')

@app.route('/login')
def login():
    """Página de login que redireciona para autenticação Google.
    
    Returns:
        Renderiza template login.html com URL de autenticação
    """
    auth_url = AuthService.get_google_auth_url()
    return render_template('login.html', auth_url=auth_url)

@app.route('/auth')
def auth():
    """Rota de callback para autenticação Google.
    
    Returns:
        Redireciona para index após autenticação bem-sucedida ou para login em caso de erro
    """
    try:
        auth_code = request.args.get('code')
        if not auth_code:
            error = request.args.get('error')
            if error:
                flash(f'Erro de autenticação: {error}', 'danger')
            return redirect(url_for('login'))

        AuthService.validate_google_auth(auth_code)
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Erro: {e}', 'danger')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Realiza logout removendo todos os tokens de autenticação.
    
    Returns:
        Redireciona para login após logout
    """
    AuthService.logout()
    global drive_service
    drive_service = None
    session.pop('user_name', None)
    session['just_logged_out'] = True
    flash('Você foi desconectado com sucesso', 'success')
    return redirect(url_for('login'))

# Rotas de análise e operações
@app.route('/analisar', methods=['POST'])
def analisar():
    """Inicia análise de arquivos duplicados.
    
    Returns:
        Renderiza template results.html com duplicatas encontradas ou redireciona para index em caso de erro
    """
    try:
        folder_id = request.form.get('folder_id') or None
        file_type = request.form.get('file_type') or "image"
        service = get_or_create_drive_service()

        duplicates = service.find_duplicates(folder_id, file_type)
        if duplicates is None:
            flash("Análise cancelada pelo usuário.", "warning")
            return redirect(url_for('index'))

        return render_template('results.html', duplicates=duplicates)
    except Exception as e:
        flash(f'Erro: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/delete-multiple', methods=['POST'])
def delete_multiple():
    """Exclui múltiplos arquivos do Google Drive.
    
    Returns:
        JSON com resultado da operação:
        - success: Booleano indicando sucesso geral
        - deleted: Número de arquivos excluídos com sucesso
        - partial: Booleano indicando exclusão parcial
        - failed: Número de falhas (opcional)
        - failed_ids: Lista de IDs com falha (opcional)
    """
    try:
        data = json.loads(request.data)
        file_ids = data.get('file_ids', [])
        
        if not file_ids:
            return jsonify({'success': False, 'error': 'Nenhum arquivo especificado'}), 400

        service = get_or_create_drive_service()
        success_count = 0
        failed_ids = []

        for file_id in file_ids:
            try:
                service.delete_file(file_id)
                success_count += 1
            except Exception as e:
                print(f"Erro ao excluir arquivo {file_id}: {e}")
                failed_ids.append(file_id)

        response = {'success': True, 'deleted': success_count}
        if failed_ids:
            response.update({
                'partial': True,
                'failed': len(failed_ids),
                'failed_ids': failed_ids
            })
        else:
            response['partial'] = False

        return jsonify(response)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Rotas de controle de análise
@app.route('/progress')
def progress():
    """Retorna o progresso atual da análise.
    
    Returns:
        JSON com:
        - percent: Porcentagem de progresso
        - current: Arquivo atual sendo processado
        - total: Total de arquivos
    """
    global drive_service
    if drive_service:
        return jsonify(drive_service.get_detailed_progress())
    return jsonify({'percent': 0, 'current': 0, 'total': 0})

@app.route('/pausar-analise', methods=['POST'])
def pausar_analise():
    """Pausa a análise em andamento.
    
    Returns:
        Resposta vazia com status 200 (sucesso) ou 400 (falha)
    """
    global drive_service
    if drive_service:
        drive_service.pause()
        return '', 200
    return '', 400

@app.route('/retomar-analise', methods=['POST'])
def retomar_analise():
    """Retoma uma análise pausada.
    
    Returns:
        Resposta vazia com status 200 (sucesso) ou 400 (falha)
    """
    global drive_service
    if drive_service:
        drive_service.resume()
        return '', 200
    return '', 400

@app.route('/cancelar-analise')
def cancelar_analise():
    """Cancela a análise em andamento.
    
    Returns:
        Resposta vazia com status 200 (sucesso) ou 400 (falha)
    """
    global drive_service
    if drive_service:
        drive_service.cancel()
        return '', 200
    return '', 400

@app.route('/voltar')
def voltar():
    """Reseta o estado da análise e retorna à página inicial.
    
    Returns:
        Redireciona para index com parâmetro reset
    """
    global drive_service
    if drive_service:
        drive_service.cancel()
        drive_service = None
    return redirect(url_for('index', reset=1))

if __name__ == '__main__':
    os.makedirs('credentials', exist_ok=True)
    print(f"Servidor rodando em http://localhost:{app.config['PORT']}")
    app.run(port=app.config['PORT'], debug=True, use_reloader=False)