/**
 * Controlador da página principal
 * Gerencia análise de arquivos e progresso
 */
class IndexController {
  constructor() {
    this.ANALYSIS_STATES = {
      IDLE: 'idle',
      ANALYZING: 'analyzing',
      PAUSED: 'paused'
    };

    this.elements = {
      form: document.getElementById('analysis-form'),
      analyzeBtn: document.getElementById('analyze-btn'),
      cancelBtn: document.getElementById('cancel-btn'),
      progressBar: document.getElementById('progress-bar'),
      progressText: document.getElementById('progress-text'),
      elapsedTime: document.getElementById('elapsed-time'),
      remainingTime: document.getElementById('remaining-time')
    };

    this.state = {
      current: this.ANALYSIS_STATES.IDLE,
      isPaused: false,
      startTime: null,
      timerInterval: null,
      lastProgress: 0
    };

    this.init();
  }

  /**
   * Inicializa o controlador
   */
  init() {
    this.setupEventListeners();
    if (window.location.search.includes('reset=1')) {
      this.resetProgress();
      window.history.replaceState({}, '', window.location.pathname);
    }
  }

  /**
   * Configura os event listeners
   */
  setupEventListeners() {
    const { analyzeBtn, form, cancelBtn } = this.elements;

    analyzeBtn.addEventListener('mouseover', () => this.handleButtonHover());
    analyzeBtn.addEventListener('mouseout', () => this.handleButtonOut());
    analyzeBtn.addEventListener('click', (e) => this.handleAnalyzeClick(e));
    form.addEventListener('submit', (e) => this.handleFormSubmit(e));
    cancelBtn.addEventListener('click', () => this.handleCancel());
  }

  /**
   * Manipula o hover do botão de análise
   */
  handleButtonHover() {
    if (this.state.current !== this.ANALYSIS_STATES.IDLE) {
      this.updateAnalyzeButtonText();
    }
  }

  /**
   * Manipula a saída do hover do botão
   */
  handleButtonOut() {
    const { analyzeBtn } = this.elements;
    if (this.state.current === this.ANALYSIS_STATES.ANALYZING) {
      analyzeBtn.textContent = '⏳ Em Análise...';
    } else if (this.state.current === this.ANALYSIS_STATES.PAUSED) {
      analyzeBtn.textContent = '⏸️ Análise Pausada';
    }
  }

  /**
   * Atualiza o texto do botão de análise
   */
  updateAnalyzeButtonText() {
    const { analyzeBtn } = this.elements;
    const texts = {
      [this.ANALYSIS_STATES.IDLE]: '🔍 Iniciar Análise',
      [this.ANALYSIS_STATES.ANALYZING]: '⏸️ Pausar Análise',
      [this.ANALYSIS_STATES.PAUSED]: '▶️ Retomar Análise'
    };
    analyzeBtn.textContent = texts[this.state.current];
  }

  /**
   * Manipula o envio do formulário
   */
  async handleFormSubmit(event) {
    if (this.state.current === this.ANALYSIS_STATES.ANALYZING) {
      event.preventDefault();
      alert('Análise já está em andamento.');
      return;
    }

    this.state.current = this.ANALYSIS_STATES.ANALYZING;
    this.state.isPaused = false;
    this.elements.cancelBtn.style.display = 'inline-block';
    this.updateAnalyzeButtonText();
    this.startTimer();
    this.checkProgress();
  }

  /**
   * Verifica o progresso da análise
   */
  async checkProgress() {
    try {
      const response = await fetch('/progress');
      if (!response.ok) throw new Error('Falha ao verificar progresso');
      
      const data = await response.json();
      this.updateProgress(data);
      
      if (data.percent < 100) {
        setTimeout(() => this.checkProgress(), 1000);
      } else {
        this.stopTimer();
      }
    } catch (error) {
      console.error('Erro:', error);
      setTimeout(() => this.checkProgress(), 2000);
    }
  }

  /**
   * Atualiza a exibição do progresso
   */
  updateProgress({ percent, current, total }) {
    const { progressBar, progressText } = this.elements;
    this.state.lastProgress = percent;

    progressBar.style.width = `${percent}%`;
    progressText.textContent = `${current} / ${total} arquivos (${percent}%)`;
    this.updateTimeCounters();
  }

  /**
   * Formata tempo em MM:SS
   */
  formatTime(seconds) {
    const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
    const secs = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${mins}:${secs}`;
  }

  /**
   * Atualiza os contadores de tempo
   */
  updateTimeCounters() {
    if (!this.state.startTime) return;

    const now = new Date();
    const elapsedSeconds = Math.floor((now - this.state.startTime) / 1000);
    const remainingSeconds = this.state.lastProgress > 0 
      ? Math.floor((elapsedSeconds * (100 - this.state.lastProgress)) / this.state.lastProgress)
      : 0;

    this.elements.elapsedTime.textContent = `⏱️ ${this.formatTime(elapsedSeconds)}`;
    this.elements.remainingTime.textContent = `⏳ ${this.formatTime(remainingSeconds)}`;
  }

  /**
   * Inicia o timer
   */
  startTimer() {
    this.state.startTime = new Date();
    this.elements.elapsedTime.style.display = 'inline';
    this.elements.remainingTime.style.display = 'inline';
    this.state.timerInterval = setInterval(() => this.updateTimeCounters(), 1000);
  }

  /**
   * Para o timer
   */
  stopTimer() {
    clearInterval(this.state.timerInterval);
    this.state.timerInterval = null;
    this.elements.elapsedTime.style.display = 'none';
    this.elements.remainingTime.style.display = 'none';
  }

  /**
   * Reseta o progresso
   */
  resetProgress() {
    this.elements.progressBar.style.width = '0%';
    this.elements.progressText.textContent = '0 / 0 arquivos (0%)';
    this.state.lastProgress = 0;
    this.stopTimer();
  }

  /**
   * Manipula o clique no botão de análise
   */
  async handleAnalyzeClick(event) {
    if (this.state.current === this.ANALYSIS_STATES.IDLE) return;
    event.preventDefault();

    try {
      const endpoint = this.state.isPaused ? '/retomar-analise' : '/pausar-analise';
      const response = await fetch(endpoint, { method: 'POST' });
      
      if (response.ok) {
        this.state.isPaused = !this.state.isPaused;
        this.state.current = this.state.isPaused 
          ? this.ANALYSIS_STATES.PAUSED 
          : this.ANALYSIS_STATES.ANALYZING;
        this.updateAnalyzeButtonText();
      }
    } catch (error) {
      console.error('Erro:', error);
    }
  }

  /**
   * Manipula o cancelamento
   */
  async handleCancel() {
    try {
      const response = await fetch('/cancelar-analise');
      
      if (response.ok) {
        this.state.current = this.ANALYSIS_STATES.IDLE;
        this.state.isPaused = false;
        this.elements.cancelBtn.style.display = 'none';
        this.updateAnalyzeButtonText();
        this.resetProgress();
      } else {
        alert('Erro ao cancelar a análise.');
      }
    } catch (error) {
      console.error('Erro:', error);
    }
  }
}

// Inicializa quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
  new IndexController();
});