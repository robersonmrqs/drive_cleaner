/**
 * Controlador da página de resultados
 * Gerencia exclusão de arquivos e seleção
 */
class ResultsController {
    constructor() {
      this.elements = {
        selectAllBtn: document.getElementById('select-all'),
        unselectAllBtn: document.getElementById('unselect-all'),
        batchDeleteBtn: document.getElementById('batch-delete'),
        checkboxes: Array.from(document.querySelectorAll('.duplicate-checkbox')),
        selectedCountEl: document.getElementById('selected-count'),
        deleteButtons: Array.from(document.querySelectorAll('.delete-btn')),
        dupCountEl: document.getElementById('dup-count')
      };
  
      this.init();
    }
  
    /**
     * Inicializa o controlador
     */
    init() {
      this.setupEventListeners();
      this.updateSelectionState();
    }
  
    /**
     * Configura os event listeners
     */
    setupEventListeners() {
      const { selectAllBtn, unselectAllBtn, batchDeleteBtn, checkboxes, deleteButtons } = this.elements;
  
      checkboxes.forEach(cb => {
        cb.addEventListener('change', () => this.updateSelectionState());
      });
  
      selectAllBtn.addEventListener('click', () => this.toggleAllCheckboxes(true));
      unselectAllBtn.addEventListener('click', () => this.toggleAllCheckboxes(false));
      batchDeleteBtn.addEventListener('click', (e) => this.handleBatchDelete(e));
  
      deleteButtons.forEach(btn => {
        btn.addEventListener('click', (e) => this.handleSingleDelete(e));
      });
    }
  
    /**
     * Atualiza o estado da seleção
     */
    updateSelectionState() {
      const selectedCount = this.getSelectedCount();
      this.elements.selectedCountEl.textContent = 
        `${selectedCount} arquivo${selectedCount !== 1 ? 's' : ''} selecionado${selectedCount !== 1 ? 's' : ''}`;
      this.elements.batchDeleteBtn.disabled = selectedCount === 0;
    }
  
    /**
     * Alterna todos os checkboxes
     */
    toggleAllCheckboxes(checked) {
      this.elements.checkboxes.forEach(checkbox => {
        checkbox.checked = checked;
      });
      this.updateSelectionState();
    }
  
    /**
     * Retorna a contagem de selecionados
     */
    getSelectedCount() {
      return this.elements.checkboxes.filter(cb => cb.checked).length;
    }
  
    /**
     * Retorna IDs dos selecionados
     */
    getSelectedIds() {
      return this.elements.checkboxes
        .filter(cb => cb.checked)
        .map(cb => cb.value);
    }
  
    /**
     * Manipula exclusão individual
     */
    async handleSingleDelete(event) {
      const button = event.currentTarget;
      const fileId = button.dataset.fileId;
      const itemBox = button.closest('.duplicate-item');
  
      if (!confirm('Tem certeza que deseja excluir esta duplicata?')) {
        return;
      }
  
      try {
        const response = await fetch(`/delete/${fileId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.ok) {
          itemBox.remove();
          this.updateResultsCount();
          this.showAlert('Arquivo excluído com sucesso.', 'success');
        } else {
          throw new Error('Falha ao excluir');
        }
      } catch (error) {
        console.error('Erro:', error);
        this.showAlert('Erro ao excluir o arquivo.', 'danger');
      }
    }
  
    /**
     * Manipula exclusão em lote
     */
    async handleBatchDelete(event) {
      event.preventDefault();
      const selectedIds = this.getSelectedIds();
  
      if (selectedIds.length === 0) return;
  
      if (!confirm(`Tem certeza que deseja excluir ${selectedIds.length} arquivo${selectedIds.length !== 1 ? 's' : ''}?`)) {
        return;
      }
  
      try {
        const response = await fetch('/delete-multiple', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file_ids: selectedIds })
        });
  
        const data = await response.json();
  
        if (data.success) {
          this.processBatchDeleteSuccess(data, selectedIds);
        } else {
          this.showAlert(`Erro: ${data.error || 'Falha ao excluir'}`, 'danger');
        }
      } catch (error) {
        console.error('Erro:', error);
        this.showAlert('Erro ao processar a solicitação.', 'danger');
      }
    }
  
    /**
     * Processa sucesso na exclusão em lote
     */
    processBatchDeleteSuccess(data, selectedIds) {
      selectedIds.forEach(id => {
        const item = document.querySelector(`#check-${id}`)?.closest('.duplicate-item');
        if (item) item.remove();
      });
  
      this.toggleAllCheckboxes(false);
      this.updateSelectionState();
      this.updateResultsCount();
  
      const message = data.partial
        ? `Excluídos ${data.deleted} de ${selectedIds.length} arquivos.`
        : `${selectedIds.length} arquivo${selectedIds.length !== 1 ? 's' : ''} excluído${selectedIds.length !== 1 ? 's' : ''} com sucesso.`;
      
      this.showAlert(message, data.partial ? 'warning' : 'success');
    }
  
    /**
     * Atualiza contagem de resultados
     */
    updateResultsCount() {
      const remaining = document.querySelectorAll('.duplicate-item').length;
      this.elements.dupCountEl.textContent = remaining;
  
      if (remaining === 0) {
        this.showNoResultsMessage();
      }
    }
  
    /**
     * Mostra mensagem sem resultados
     */
    showNoResultsMessage() {
      document.querySelector('.results-container').innerHTML = `
        <div class="no-results">
          <img src="${document.querySelector('img[alt="Nenhuma duplicata"]')?.src || ''}" 
               alt="Nenhuma duplicata" 
               width="200">
          <h3>Todas as duplicatas foram excluídas!</h3>
          <p>Seus arquivos estão organizados.</p>
          <a href="${document.querySelector('a[href*="voltar"]')?.href || '#'}" class="btn">🔙 Voltar</a>
        </div>
      `;
    }
  
    /**
     * Mostra alerta temporário
     */
    showAlert(msg, category) {
      const alert = document.createElement('div');
      alert.className = `alert alert-${category}`;
      alert.textContent = msg;
  
      const container = document.querySelector('.container');
      container.insertBefore(alert, container.firstChild);
  
      setTimeout(() => alert.remove(), 4000);
    }
  }
  
  // Inicializa quando o DOM estiver pronto
  document.addEventListener('DOMContentLoaded', () => {
    new ResultsController();
  });