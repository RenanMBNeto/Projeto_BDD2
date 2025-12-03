const API_URL = "http://127.0.0.1:5000";
const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

// PREÇOS FIXOS (Alinhados com o SQL para evitar erro de defasagem)
const PRECOS_MOCK = {
    'PETR4': 35.50,
    'VALE3': 68.20,
    'CDB2027': 1000.00,
    'VERDE': 1500.00,
    'TESOURO2030': 1050.00,
    'FUNDOMOD11': 150.00
};

// --- FUNÇÃO DE UTILIDADE ---
function safeEscape(str) {
    if (!str) return '';
    return str.toString().replace(/\\/g, '\\\\').replace(/'/g, "\\'");
}

async function initDashboard(role) {
    checkAuth();

    const userName = localStorage.getItem('user_name');
    if (userName) {
        document.querySelectorAll('#user-name, #perfil-nome-display').forEach(el => { if(el) el.textContent = userName; });
    }

    const navButtons = document.querySelectorAll('.nav-btn');
    const viewSections = document.querySelectorAll('.view-section');

    navButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const clickedBtn = e.currentTarget;
            const targetId = clickedBtn.getAttribute('data-target');

            navButtons.forEach(b => b.classList.remove('active'));
            viewSections.forEach(s => s.classList.add('hidden'));

            clickedBtn.classList.add('active');
            const targetSection = document.getElementById(targetId);

            if(targetSection) {
                targetSection.classList.remove('hidden');
                targetSection.classList.add('fade-in');
            }

            if (targetId === 'view-investir') loadProdutos();
            if (targetId === 'view-clientes') loadAssessorData();
            if (targetId === 'view-compliance') loadAssessorData();
            if (targetId === 'view-perfil' && role === 'cliente') loadPerfilData();
            if (targetId === 'view-extrato' && role === 'cliente') loadExtratoData();
        });
    });

    if (role === 'cliente') await loadClientData();
    if (role === 'assessor') await loadAssessorData();
}

// --- NOTIFICAÇÕES (TOAST) ---
function showToast(message, type = 'success') {
    const container = document.getElementById('notification-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    const icon = type === 'success' ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-exclamation-circle"></i>';
    toast.innerHTML = `${icon} <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 400); }, 4000);
}

// --- ASSESSOR ---
async function loadAssessorData() {
    try {
        const res = await fetch(`${API_URL}/clientes`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
        if (!res.ok) return;
        const clientes = await res.json();

        document.getElementById('total-clientes').textContent = clientes.length || 0;
        document.getElementById('total-pendencias').textContent = clientes.filter(c => c.StatusCompliance !== 'Aprovado').length || 0;

        const tbody = document.getElementById('clientes-body');
        if(tbody) {
            tbody.innerHTML = '';
            clientes.forEach(c => {
                let badge = c.StatusCompliance === 'Aprovado' ? 'badge-green' : 'badge-gold';
                tbody.innerHTML += `
                    <tr>
                        <td style="color:#fff; font-weight:500">${c.NomeCompleto}</td>
                        <td>${c.CPF_CNPJ}</td>
                        <td>${c.Email}</td>
                        <td><span class="badge ${badge}">${c.StatusCompliance}</span></td>
                        <td><button class="btn-premium" style="padding:6px 12px; font-size:0.7rem;" 
                            onclick="openClientModal('${safeEscape(c.NomeCompleto)}', '${safeEscape(c.CPF_CNPJ)}', '${safeEscape(c.Email)}', '${safeEscape(c.StatusCompliance)}')">
                            Ver
                        </button></td>
                    </tr>`;
            });
        }
    } catch (e) { console.error(e); }
}

async function handleNewClient(e) {
    e.preventDefault();
    const data = {
        NomeCompleto: document.getElementById('novo-nome').value,
        Email: document.getElementById('novo-email').value,
        CPF_CNPJ: document.getElementById('novo-cpf').value,
        Senha: document.getElementById('novo-senha').value
    };
    try {
        const res = await fetch(`${API_URL}/clientes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify(data)
        });
        const json = await res.json();
        if(res.ok) {
            showToast('Cliente criado com sucesso!', 'success');
            const form = document.getElementById('form-novo-cliente');
            if(form) form.reset();
            await loadAssessorData();
            document.querySelector('[data-target="view-clientes"]').click();
        } else {
            const msg = json.detalhes || json.erro;
            showToast(`Falha ao criar: ${msg}. Use CPF/Email ÚNICOS.`, 'error');
        }
    } catch(e) { showToast('Erro de conexão.', 'error'); }
}

// --- CLIENTE ---
async function loadClientData() {
    try {
        const token = localStorage.getItem('token');
        const headers = { 'Authorization': `Bearer ${token}` };

        const [resConta, resPort] = await Promise.all([
            fetch(`${API_URL}/portal/minha-conta`, { headers }),
            fetch(`${API_URL}/portal/meu-portfolio`, { headers })
        ]);

        if (resConta.ok) {
            const conta = await resConta.json();
            document.getElementById('saldo-val').textContent = moneyFormatter.format(conta.Saldo);
        }
        if (resPort.ok) {
            const portfolio = await resPort.json();
            document.getElementById('patrimonio-val').textContent = moneyFormatter.format(portfolio.valor_mercado_total || 0);
            const lucro = parseFloat(portfolio.resultado_total_financeiro || 0);
            const elLucro = document.getElementById('lucro-val');
            elLucro.textContent = moneyFormatter.format(lucro);
            elLucro.style.color = lucro >= 0 ? 'var(--success)' : 'var(--danger)';

            const tbody = document.getElementById('portfolio-body');
            if(tbody) {
                tbody.innerHTML = '';
                if(!portfolio.posicoes || portfolio.posicoes.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem; color:var(--text-muted)">Nenhum ativo.</td></tr>';
                } else {
                    portfolio.posicoes.forEach(pos => {
                        const rentab = parseFloat(pos.resultado_financeiro);
                        tbody.innerHTML += `
                            <tr>
                                <td style="color:var(--accent-gold); font-weight:600">${pos.produto.Ticker}</td>
                                <td>${pos.produto.NomeProduto}</td>
                                <td>${parseFloat(pos.Quantidade).toFixed(2)}</td>
                                <td>${moneyFormatter.format(pos.valor_mercado)}</td>
                                <td style="color:${rentab >= 0 ? 'var(--success)' : 'var(--danger)'}">${moneyFormatter.format(rentab)}</td>
                            </tr>`;
                    });
                }
            }
        }
    } catch (e) { console.error(e); }
}

async function loadPerfilData() {
    try {
        const res = await fetch(`${API_URL}/portal/meu-perfil`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
        if(res.ok) {
            const perfil = await res.json();
            document.getElementById('perfil-email').textContent = perfil.Email;
            document.getElementById('perfil-doc').textContent = perfil.CPF_CNPJ;
            document.getElementById('perfil-status').textContent = perfil.StatusCompliance;
        }
    } catch(e) { console.error(e); }
}

async function loadExtratoData() {
    // Implementação para buscar dados de MovimentacaoConta se a rota existir
    // Por enquanto, mostra um valor padrão.
    const tbody = document.getElementById('extrato-body');
    if(tbody) {
        tbody.innerHTML = `<tr><td>${new Date().toLocaleDateString('pt-BR')}</td><td>Aporte</td><td>Transferência Inicial</td><td style="color:var(--success)">+ ${moneyFormatter.format(100000.00)}</td></tr>`;
    }
}

async function loadProdutos() {
    try {
        const res = await fetch(`${API_URL}/produtos`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
        const produtos = await res.json();
        const grid = document.getElementById('products-grid');

        if(grid) {
            grid.innerHTML = '';
            produtos.forEach(prod => {
                const preco = PRECOS_MOCK[prod.Ticker] || 100.00;
                grid.innerHTML += `
                    <div class="product-card fade-in">
                        <div class="product-header">
                            <span class="badge badge-gold">${prod.ClasseAtivo}</span>
                            <span class="badge" style="border:1px solid var(--text-muted); color:var(--text-muted)">Risco ${prod.NivelRiscoProduto}/5</span>
                        </div>
                        <h3 style="color:#fff; margin-bottom:0.5rem;">${prod.NomeProduto}</h3>
                        <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:1rem;">${prod.Ticker} - ${prod.Emissor || 'Chicoin$'}</p>
                        <p style="color:#fff; font-weight:bold; font-size:1.2rem; margin-bottom:1rem;">R$ ${parseFloat(preco).toFixed(2)}</p>
                        <button class="btn-premium" style="width:100%; font-size:0.8rem" 
                            onclick="openInvestModal(${prod.ProdutoID}, '${prod.Ticker}', ${preco})">
                            Investir
                        </button>
                    </div>`;
            });
        }
    } catch (e) { console.error(e); }
}

let selectedProdutoId = null;
function openInvestModal(id, ticker, preco) {
    selectedProdutoId = id;
    document.getElementById('modal-titulo').textContent = `Investir em ${ticker}`;
    document.getElementById('modal-preco').value = preco;
    document.getElementById('invest-modal').classList.add('open');
}
function closeModal() { document.getElementById('invest-modal').classList.remove('open'); }

async function confirmInvest() {
    const qtd = document.getElementById('modal-qtd').value;
    const preco = document.getElementById('modal-preco').value;
    try {
        const token = localStorage.getItem('token');
        const portRes = await fetch(`${API_URL}/portal/meu-portfolio`, { headers: { 'Authorization': `Bearer ${token}` } });
        const portfolio = await portRes.json();
        const res = await fetch(`${API_URL}/ordem`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({
                portfolio_id: portfolio.PortfolioID,
                produto_id: selectedProdutoId,
                tipo_ordem: 'Compra',
                quantidade: parseFloat(qtd),
                preco_unitario: parseFloat(preco)
            })
        });
        const json = await res.json();
        if(res.ok) {
            showToast('Ordem executada!', 'success');
            closeModal();
            loadClientData();
        } else {
            showToast('Erro: ' + (json.erro || 'Falha'), 'error');
        }
    } catch(e) { showToast('Erro de conexão.', 'error'); }
}

function checkAuth() { if (!localStorage.getItem('token')) window.location.href = 'login.html'; }
function logout() { localStorage.clear(); window.location.href = 'index.html'; }