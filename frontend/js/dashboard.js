const API_URL = "http://127.0.0.1:5000";
const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

// --- PREÇOS FIXOS (ALINHADOS COM O BANCO DE DADOS) ---
const PRECOS_MOCK = {
    'PETR4': 35.50,       // Igual ao seed_db.py
    'TESOURO2030': 1050.00,
    'FUNDOMOD11': 150.00,
    'VALE3': 68.20,
    'BTC': 350000.00
};

async function initDashboard(role) {
    checkAuth();

    const userName = localStorage.getItem('user_name');
    if (userName) {
        document.querySelectorAll('#user-name, #perfil-nome-display').forEach(el => {
            if(el) el.textContent = userName;
        });
    }

    // --- NAVEGAÇÃO ---
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
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 400);
    }, 4000);
}

// --- ASSESSOR ---
async function loadAssessorData() {
    try {
        const res = await fetch(`${API_URL}/clientes`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
        if (!res.ok) return;
        const clientes = await res.json();

        const elTotal = document.getElementById('total-clientes');
        if(elTotal) elTotal.textContent = clientes.length;

        const pendentes = clientes.filter(c => c.StatusCompliance !== 'Aprovado');
        const elPend = document.getElementById('total-pendencias');
        if(elPend) elPend.textContent = pendentes.length;

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
                        <td><button class="btn-premium" style="padding:6px 12px; font-size:0.7rem;">Ver</button></td>
                    </tr>`;
            });
        }

        // Compliance
        const compBody = document.getElementById('compliance-body');
        if(compBody) {
            compBody.innerHTML = '';
            if(pendentes.length === 0) compBody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:1rem; color:var(--text-muted)">Sem pendências.</td></tr>';
            pendentes.forEach(c => {
                compBody.innerHTML += `
                    <tr>
                        <td style="color:#fff">${c.NomeCompleto}</td>
                        <td style="color:var(--danger)">${c.StatusCompliance}</td>
                        <td><button class="btn-premium" style="padding:6px 12px; font-size:0.7rem;" onclick="updateStatus(${c.ClienteID}, 'Aprovado')">Aprovar</button></td>
                    </tr>`;
            });
        }
    } catch (e) { console.error(e); }
}

async function updateStatus(id, status) {
    if(!confirm('Aprovar cliente?')) return;
    try {
        const res = await fetch(`${API_URL}/clientes/${id}/status-compliance`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify({ status: status })
        });
        if(res.ok) { showToast('Status atualizado!', 'success'); loadAssessorData(); }
        else { showToast('Erro ao atualizar.', 'error'); }
    } catch(e) { showToast('Erro de conexão.', 'error'); }
}

async function handleNewClient(e) {
    e.preventDefault();

    // Captura os dados
    const nome = document.getElementById('novo-nome').value;
    const email = document.getElementById('novo-email').value;
    const cpf = document.getElementById('novo-cpf').value;

    // Validação básica Frontend
    if (!nome || !email || !cpf) {
        showToast('Preencha todos os campos.', 'error');
        return;
    }

    const data = {
        NomeCompleto: nome,
        Email: email,
        CPF_CNPJ: cpf
    };

    try {
        const res = await fetch(`${API_URL}/clientes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify(data)
        });

        const json = await res.json(); // Sempre lê o JSON para saber o erro exato

        if(res.ok) {
            showToast('Cliente criado com sucesso!', 'success');
            document.getElementById('form-novo-cliente').reset();
            await loadAssessorData();
            document.querySelector('[data-target="view-clientes"]').click();
        } else {
            // Mostra o erro exato que veio do Python (ex: CPF duplicado)
            const msgErro = json.detalhes || json.erro || 'Falha ao criar';
            showToast('Erro: ' + msgErro, 'error');
        }
    } catch(e) { showToast('Erro de conexão com o servidor.', 'error'); }
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
            const el = document.getElementById('saldo-val');
            if(el) el.textContent = moneyFormatter.format(conta.Saldo);
        }

        if (resPort.ok) {
            const portfolio = await resPort.json();
            const elPatr = document.getElementById('patrimonio-val');
            if(elPatr) elPatr.textContent = moneyFormatter.format(portfolio.valor_mercado_total || 0);

            const elLucro = document.getElementById('lucro-val');
            if(elLucro) {
                elLucro.textContent = moneyFormatter.format(portfolio.resultado_total_financeiro || 0);
                const val = parseFloat(portfolio.resultado_total_financeiro || 0);
                elLucro.style.color = val >= 0 ? 'var(--success)' : 'var(--danger)';
            }

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

// --- PRODUTOS ---
async function loadProdutos() {
    try {
        const res = await fetch(`${API_URL}/produtos`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
        const produtos = await res.json();
        const grid = document.getElementById('products-grid');

        if(grid) {
            grid.innerHTML = '';
            produtos.forEach(prod => {
                // USA O PREÇO FIXO DO MOCK PARA EVITAR ERRO DE DEFASAGEM
                const preco = PRECOS_MOCK[prod.Ticker] || 50.00;

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
    const titulo = document.getElementById('modal-titulo');
    if(titulo) titulo.textContent = `Investir em ${ticker}`;

    document.getElementById('modal-preco').value = preco;
    document.getElementById('invest-modal').classList.add('open');
}
function closeModal() { document.getElementById('invest-modal').classList.remove('open'); }

async function confirmInvest() {
    const qtd = document.getElementById('modal-qtd').value;
    const preco = document.getElementById('modal-preco').value;

    try {
        const token = localStorage.getItem('token');
        // Passo 1: Portfolio
        const portRes = await fetch(`${API_URL}/portal/meu-portfolio`, { headers: { 'Authorization': `Bearer ${token}` } });
        const portfolio = await portRes.json();

        // Passo 2: Ordem
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

        const json = await res.json(); // Captura resposta

        if(res.ok) {
            showToast('Ordem de compra realizada com sucesso!', 'success');
            closeModal();
            loadClientData();
        } else {
            // Exibe o erro exato (Ex: Saldo insuficiente ou Perfil Inadequado)
            showToast('Erro: ' + (json.erro || 'Falha ao investir'), 'error');
        }
    } catch(e) { showToast('Erro de conexão.', 'error'); }
}

function checkAuth() { if (!localStorage.getItem('token')) window.location.href = 'login.html'; }
function logout() { localStorage.clear(); window.location.href = 'index.html'; }