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
        const pendentes = clientes.filter(c => c.StatusCompliance !== 'Aprovado');
        document.getElementById('total-pendencias').textContent = pendentes.length || 0;

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

        // Compliance
        const compBody = document.getElementById('compliance-body');
        if(compBody) {
            compBody.innerHTML = '';
            if(pendentes.length === 0) compBody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:1rem; color:var(--text-muted)">Tudo em dia.</td></tr>';
            pendentes.forEach(c => {
                compBody.innerHTML += `<tr><td style="color:#fff">${c.NomeCompleto}</td><td style="color:var(--danger)">${c.StatusCompliance}</td><td><button class="btn-premium" onclick="updateStatus(${c.ClienteID}, 'Aprovado')">Aprovar</button></td></tr>`;
            });
        }
    } catch (e) { console.error(e); }
}

function openClientModal(nome, doc, email, status) {
    document.getElementById('modal-client-name').textContent = nome;
    document.getElementById('modal-client-doc').textContent = doc;
    document.getElementById('modal-client-email').textContent = email;
    document.getElementById('modal-client-status').textContent = status;

    const statusEl = document.getElementById('modal-client-status');
    statusEl.style.color = status === 'Aprovado' ? 'var(--success)' : 'var(--danger)';

    document.getElementById('client-modal').classList.add('open');
}

function closeClientModal() { document.getElementById('client-modal').classList.remove('open'); }

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
            showToast('Cliente criado com sucesso! Use a senha fornecida para login.', 'success');
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

async function handleNewProduct(e) {
    e.preventDefault();
    const data = {
        Ticker: document.getElementById('prod-ticker').value,
        NomeProduto: document.getElementById('prod-nome').value,
        NivelRiscoProduto: parseInt(document.getElementById('prod-risco').value),
        CNPJ_Empresa: document.getElementById('prod-cnpj').value,
        ClasseAtivo: 'Acao',
        Emissor: document.getElementById('prod-cnpj').value // Usa CNPJ como emissor padrão
    };

    try {
        const res = await fetch(`${API_URL}/produtos`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify(data)
        });
        const json = await res.json();
        if(res.ok) {
            showToast(`Produto ${data.Ticker.toUpperCase()} criado e disponível!`, 'success');
            document.getElementById('form-novo-produto').reset();
            PRECOS_MOCK[data.Ticker.toUpperCase()] = 50.00; // Mocka o preço do novo produto
        } else {
            showToast(`Erro ao criar produto: ${json.erro || json.detalhes}`, 'error');
        }
    } catch(e) { showToast('Erro de conexão.', 'error'); }
}

// ==========================================
// FUNÇÕES DO CLIENTE
// ==========================================

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
        } else {
             const json = await resConta.json();
             showToast('Erro de acesso à conta: ' + (json.erro || 'Autenticação Inválida.'), 'error');
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

async function loadExtratoData() {
    try {
        // Rota de conta simples é usada para simular o extrato
        const resConta = await fetch(`${API_URL}/portal/minha-conta`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
        const resPort = await fetch(`${API_URL}/portal/meu-portfolio`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });

        if (resConta.ok && resPort.ok) {
            const conta = await resConta.json();
            const portfolio = await resPort.json();
            const tbody = document.getElementById('extrato-body');

            if(tbody) {
                tbody.innerHTML = '';
                // 1. Aporte Inicial (Fixo)
                if (parseFloat(conta.Saldo) >= 100000 || portfolio.posicoes.length > 0) {
                     tbody.innerHTML += `<tr><td>${new Date().toLocaleDateString('pt-BR')}</td><td>Aporte</td><td>Transferência Inicial</td><td style="color:var(--success)">+ ${moneyFormatter.format(100000.00)}</td></tr>`;
                }

                // 2. Movimentações (Simulação de Compra - Se a ordem funcionar)
                if (portfolio.posicoes && portfolio.posicoes.length > 0) {
                     portfolio.posicoes.forEach(pos => {
                        // Esta é uma simulação. O valor do custo total é o gasto.
                        const custoTotal = parseFloat(pos.Quantidade) * parseFloat(pos.CustoMedio);
                        if (custoTotal > 0) {
                           tbody.innerHTML += `<tr><td>${new Date().toLocaleDateString('pt-BR')}</td><td>Compra</td><td>${pos.produto.Ticker}</td><td style="color:var(--danger)">- ${moneyFormatter.format(custoTotal)}</td></tr>`;
                        }
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
        } else {
             const json = await res.json();
             showToast('Erro ao carregar perfil: ' + (json.erro || 'Autenticação Inválida.'), 'error');
        }
    } catch(e) { console.error(e); }
}

async function loadProdutos() {
    try {
        const res = await fetch(`${API_URL}/produtos`, { headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` } });
        if (!res.ok) return;

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
    const token = localStorage.getItem('token');

    try {
        const portRes = await fetch(`${API_URL}/portal/meu-portfolio`, { headers: { 'Authorization': `Bearer ${token}` } });

        if (!portRes.ok) {
             const json = await portRes.json();
             showToast('Falha ao investir: ' + (json.erro || 'Autenticação Inválida. Refaça o login.'), 'error');
             closeModal();
             return;
        }
        const portfolio = await portRes.json();

        // Verificação: Se PortfolioID não existe, aborta.
        if (!portfolio.PortfolioID) {
             showToast('Erro: Portfólio do cliente não encontrado. Tente recarregar.', 'error');
             closeModal();
             return;
        }

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