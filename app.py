from flask import Flask, render_template, redirect, url_for, session, flash
from drive_service import DriveService
from config import Config
import os

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config.from_object(Config())

@app.route('/')
def index():
    """Rota principal da aplicação"""
    if not os.path.exists(app.config['CREDENTIALS_PATH']):
        flash('Configure suas credenciais Google', 'warning')
    return render_template('index.html')

# ... (outras rotas)

if __name__ == '__main__':
    os.makedirs('credentials', exist_ok=True)
    print(f"Servidor rodando em http://localhost:{app.config['PORT']}")
    app.run(
        port=app.config['PORT'],
        debug=True,
        use_reloader=False
    )