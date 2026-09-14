document.addEventListener("DOMContentLoaded", function () {
  
  // 1. Inicializa o Choices.js para buscas avançadas nos Selects (Match 100%)
  const selectsBasicos = document.querySelectorAll('.choices-basico');
  selectsBasicos.forEach(select => {
    new Choices(select, {
      allowHTML: true,
      searchEnabled: true,
      itemSelectText: '', 
      noResultsText: 'Nenhum resultado encontrado!',
      searchPlaceholderValue: 'Buscar...',
      searchFuzzy: false,
      fuseOptions: {
        threshold: 0.0
      }
    });
  }); 

});

// 2. Inicializa o DataTables via jQuery
$(document).ready(function() {
  const configuracaoIdioma = { url: '/static/js/pt-BR.json' };

  // A. Tabelas COM botão de exportação para Excel
  $('#alunos table, #premiacoes table, #turmas table').DataTable({
    language: configuracaoIdioma,
    pageLength: 10,
    ordering: false, // <-- DESATIVA TOTALMENTE A ORDENAÇÃO E AS SETINHAS
    search: { smart: false }, // Força o Match 100% na busca
    layout: {
      topStart: {
        buttons: [{
          extend: 'excelHtml5',
          text: '<i class="bi bi-file-earmark-excel-fill"></i> Exportar para Excel',
          className: 'btn btn-outline-success btn-sm fw-bold mb-3',
          title: 'Relatório Escolar',
          exportOptions: {
            columns: ':not(:last-child)' // Exclui a coluna de ações da planilha
          }
        }]
      },
      topEnd: 'search'
    }
  });

  // B. Tabela SEM botão de exportação (Acessos/Master)
  $('#contas table').DataTable({
    language: configuracaoIdioma,
    pageLength: 10,
    ordering: false, // <-- DESATIVA TOTALMENTE A ORDENAÇÃO E AS SETINHAS
    search: { smart: false }
  });
});

// 3. Memória das Abas (Persistência)
document.addEventListener("DOMContentLoaded", function () {
  const abaAtivaSalva = localStorage.getItem('abaEscolaAtiva');
  
  // Se houver uma aba salva na memória, clica nela automaticamente
  if (abaAtivaSalva) {
    const botaoAba = document.getElementById(abaAtivaSalva);
    if (botaoAba) {
      const tab = new bootstrap.Tab(botaoAba);
      tab.show();
    }
  }

  // Escuta os cliques nas abas e salva o ID da aba atual na memória do navegador
  const botoesAbas = document.querySelectorAll('button[data-bs-toggle="tab"]');
  botoesAbas.forEach(botao => {
    botao.addEventListener('shown.bs.tab', function (event) {
      localStorage.setItem('abaEscolaAtiva', event.target.id);
    });
  });
});

// 4. Lógica de Exclusão Segura (Bootstrap Modal Nativo)
document.addEventListener("DOMContentLoaded", function () {
  const modalElement = document.getElementById('modalConfirmacaoGeral');
  if (!modalElement) return;

  const modalConfirmacao = new bootstrap.Modal(modalElement);
  const btnConfirmar = document.getElementById('btnConfirmarExclusao');
  const textoConfirmacao = document.getElementById('textoConfirmacao');
  let formParaEnviar = null;

  // Usa 'click' globalmente para não se perder com a paginação do DataTables
  document.addEventListener('click', function (e) {
    const btn = e.target.closest('.btn-excluir');
    if (btn) {
      e.preventDefault(); // Evita que clique acione qualquer outra coisa
      formParaEnviar = btn.closest('form'); // Grava qual form acionou
      
      const mensagem = btn.getAttribute('data-msg') || 'Deseja realmente prosseguir com a exclusão?';
      textoConfirmacao.textContent = mensagem; // Troca a mensagem no Modal
      
      modalConfirmacao.show();
    }
  });

  // Botão vermelho de "Sim, excluir" de dentro do modal
  btnConfirmar.addEventListener('click', function () {
    if (formParaEnviar) {
      formParaEnviar.submit(); 
    }
  });
});