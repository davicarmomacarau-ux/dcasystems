const app = {
  hasLoadedLeads: false,
  list: document.getElementById('leadList'),
  total: document.getElementById('totalLeads'),
  status: document.getElementById('statusSystem'),
  email: document.getElementById('email'),
  legacyText: document.getElementById('legacyText'),
  message: document.getElementById('message')
};

function showMessage(messageText, kind = 'success') {
  app.message.className = 'message ' + kind;
  app.message.textContent = messageText;
}

async function loadHealth() {
  try {
    const response = await fetch('/health');
    const data = await response.json();
    if (data.status === 'ok') {
      app.status.textContent = 'online';
      app.status.style.color = 'var(--green)';
    } else {
      app.status.textContent = 'error';
      app.status.style.color = 'var(--red)';
    }
  } catch (error) {
    app.status.textContent = 'offline';
    app.status.style.color = 'var(--red)';
  }
}

async function loadLeads() {
  try {
    const response = await fetch('/api/leads');
    const data = await response.json();
    const rows = data.leads || [];
    app.total.textContent = String(data.total_cadastrados || 0);
    app.list.innerHTML = '';

    if (!rows.length) {
      const row = document.createElement('div');
      row.className = 'lead-row';
      row.innerHTML = '<span class="lead-email">Nenhum lead cadastrado</span><span class="lead-badge">WAIT</span>';
      app.list.appendChild(row);
      return;
    }

    for (const lead of rows) {
      const row = document.createElement('div');
      row.className = 'lead-row';
      row.innerHTML = '<span class="lead-email">' + lead + '</span><span class="lead-badge">OK</span>';
      app.list.appendChild(row);
    }
  } catch (error) {
    showMessage('Não foi possível consultar os leads.', 'error');
  }
}

async function registerLead(event) {
  event.preventDefault();
  const email = app.email.value.trim();
  if (!email) {
    showMessage('Informe um e-mail válido para cadastrar.', 'error');
    return;
  }

  try {
    const response = await fetch('/api/interesse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    const payload = await response.json();
    if (response.ok) {
      showMessage(payload.mensagem || 'Lead cadastrado com sucesso.', 'success');
      app.email.value = '';
    } else {
      showMessage(payload.mensagem || 'Falha ao cadastrar interesse.', 'error');
    }
    await loadLeads();
  } catch (error) {
    showMessage('Falha ao registrar o interesse.', 'error');
  }
}

async function migrateLegacy() {
  const text = app.legacyText.value.trim();
  if (!text) {
    showMessage('Cole o arquivo legado antes de migrar.', 'error');
    return;
  }

  try {
    const response = await fetch('/api/migrar-amostra', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dados_legados: text })
    });
    const payload = await response.json();
    if (response.ok) {
      app.legacyText.value = JSON.stringify(payload, null, 2);
      showMessage('Payload migrado com sucesso.', 'success');
    } else {
      showMessage(payload.mensagem || 'Falha ao migrar a amostra.', 'error');
    }
  } catch (error) {
    showMessage('Erro na conversão do arquivo legado.', 'error');
  }
}

function clearLegacyText() {
  app.legacyText.value = '';
  showMessage('Texto legado limpo.', 'success');
}

function loadDemoText() {
  app.legacyText.value = '001JOAO SILVA                   joao.silva@dca.systems       00000000012345A';
  showMessage('Amostra de legado carregada.', 'success');
}

async function exportLeads() {
  try {
    const response = await fetch('/api/leads');
    const data = await response.json();
    const rows = data.leads || [];
    const text = rows.map((email, idx) => String(idx + 1) + ',' + email).join('\n');
    const blob = new Blob([text], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'dca-systems-leads.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showMessage('Arquivo de leads exportado.', 'success');
  } catch (error) {
    showMessage('Erro ao exportar leads.', 'error');
  }
}

function startListeners() {
  const form = document.getElementById('leadForm');
  const submit = document.getElementById('registerLead');
  const convert = document.getElementById('convertBtn');
  const refresh = document.getElementById('refreshBtn');
  const clear = document.getElementById('clearBtn');
  const demo = document.getElementById('sampleBtn');
  const exportBtn = document.getElementById('exportBtn');

  form.addEventListener('submit', registerLead);
  submit.addEventListener('click', registerLead);
  convert.addEventListener('click', migrateLegacy);
  refresh.addEventListener('click', loadLeads);
  clear.addEventListener('click', clearLegacyText);
  demo.addEventListener('click', loadDemoText);
  exportBtn.addEventListener('click', exportLeads);
}

function init() {
  startListeners();
  loadLeads();
  loadHealth();
}

document.addEventListener('DOMContentLoaded', init);
