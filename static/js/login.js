/**
 * Controlador da página de login
 * Gerencia interações simples da página
 */
class LoginController {
  constructor() {
    this.params = new URLSearchParams(window.location.search);
    this.init();
  }

  /**
   * Inicializa o controlador
   */
  init() {
    this.handleURLParams();
  }

  /**
   * Manipula parâmetros da URL
   */
  handleURLParams() {
    if (this.params.has('error')) {
      this.showErrorAlert(this.params.get('error'));
      window.history.replaceState({}, '', window.location.pathname);
    }
  }

  /**
   * Mostra alerta de erro
   */
  showErrorAlert(errorMessage) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger text-center';
    alertDiv.textContent = `Erro: ${errorMessage}`;
    
    const container = document.querySelector('.container');
    if (container) {
      container.insertBefore(alertDiv, container.firstChild);
      setTimeout(() => alertDiv.remove(), 4000);
    }
  }
}

// Inicializa quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
  new LoginController();
});