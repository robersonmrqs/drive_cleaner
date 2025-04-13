from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
from drive_service import DriveService
from config import Config
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(Config)

drive_service = DriveService()

@app.route('/')
def index():
    """Página inicial com escolha de pasta e tipo de arquivo"""
    folders = drive_service.list_folders()
    return render_template('index.html', folders=folders)

@app.route('/auth')
def auth():
    """Autenticação Google"""
    try:
        drive_service.__init__()
        flash('Autenticado com sucesso!', 'success')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Erro: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/analisar', methods=['POST'])
def analisar():
    """Executa análise com base na pasta e tipo escolhidos"""
    folder_id = request.form.get('folder_id') or None
    file_type = request.form.get('file_type') or "image"

    try:
        duplicates = drive_service.find_duplicates(folder_id, file_type)
        return render_template('results.html', duplicates=duplicates)
    except Exception as e:
        flash(f'Erro: {e}', 'danger')
        return redirect(url_for('index'))

@app.route('/delete/<file_id>')
def delete_file(file_id):
    """Remove arquivo duplicado"""
    try:
        drive_service.delete_file(file_id)
        flash('Arquivo excluído!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir: {e}', 'danger')
    return redirect(url_for('index'))

@app.route('/progress')
def progress():
    """Retorna progresso detalhado em JSON para uso via AJAX"""
    return jsonify(drive_service.get_detailed_progress())

if __name__ == '__main__':
    os.makedirs('credentials', exist_ok=True)
    print(f"Servidor rodando em http://localhost:{app.config['PORT']}")
    app.run(port=app.config['PORT'], debug=True, use_reloader=False)