// frontend/js/dashboard.js
const API_URL = "http://127.0.0.1:5000";
const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

// --- INICIALIZAÇÃO ---
async function initDashboard(role) {
    checkAuth();

    // Atualiza o nome do usuário no topo
    const userName = localStorage.getItem('user_name');
    if (document.getElementById('user-name') && userName) {
        document.getElementById('user-name').textContent = userName;
    }
    // Atualiza também na aba Perfil
    if (document.getElementById('perfil-nome') && userName) {
        document.getElementById('perfil-nome').textContent = userName;
    }

    // --- LÓGICA DE NAVEGAÇÃO (ABAS) ---
    const navButtons = document.querySelectorAll('.nav-btn');
    const viewSections = document.querySelectorAll('.view-section');

    navButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // 1. Remove a classe 'active' de todos os botões
            navButtons.forEach(b => b.classList.remove('active'));

            // 2. Esconde todas as secções
            viewSections.forEach(s => s.classList.add('hidden'));

            // 3. Identifica o botão clicado (mesmo se clicar no ícone <i>)
            const clickedBtn = e.currentTarget;
            clickedBtn.classList.add('active');

            // 4. Mostra a secção correspondente
            const targetId = clickedBtn.getAttribute('data-target');
            const targetSection = document.getElementById(targetId);

            if (targetSection) {
                targetSection.classList.remove('hidden');
                targetSection.classList.add('fade-in');
            }

            // 5. Carrega dados específicos da aba (se necessário)
            if (targetId === 'view-investir') loadProdutos();
            if (targetId === 'view-clientes') loadAssessorData();
        });
    });

    // Carregamento inicial de dados baseado no tipo de usuário
    if (role === 'cliente') {
        await loadClientData();
    } else if (role === 'assessor') {
        await loadAssessorData();
    }
}

// --- ASSESSOR: Carregar Dados ---
async function loadAssessorData() {
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_URL}/clientes`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) return; // Se der erro, para aqui
        const clientes = await res.json();

        // Atualiza KPIs
        const elTotal = document.getElementById('total-clientes');
        if (elTotal) elTotal.textContent = clientes.length || 0;

        const pendentes = clientes.filter(c => c.StatusCompliance !== 'Aprovado');
        const elPend = document.getElementById('total-pendencias');
        if (elPend) elPend.textContent = pendentes.length || 0;

        // Preenche Tabela de Clientes
        const tbody = document.getElementById('clientes-body');
        if (tbody) {
            tbody.innerHTML = '';
            if (clientes.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem; color:var(--text-muted)">Nenhum cliente na carteira.</td></tr>';
            } else {
                clientes.forEach(c => {
                    let badge = 'badge-gold';
                    if (c.StatusCompliance === 'Aprovado') badge = 'badge-green';
                    if (c.StatusCompliance === 'Reprovado') badge = 'badge-red';

                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td style="color:#fff; font-weight:500">${c.NomeCompleto}</td>
                        <td>${c.CPF_CNPJ}</td>
                        <td>${c.Email}</td>
                        <td><span class="badge ${badge}">${c.StatusCompliance}</span></td>
                        <td><button class="btn-premium" style="padding:4px 10px; font-size:0.7rem;">Ver</button></td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }

        // Preenche Tabela de Compliance
        const compBody = document.getElementById('compliance-body');
        if(compBody) {
            compBody.innerHTML = '';
            if (pendentes.length === 0) {
                 compBody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:1rem; color:var(--text-muted)">Tudo em dia.</td></tr>';
            } else {
                pendentes.forEach(c => {
                    compBody.innerHTML += `
                        <tr>
                            <td style="color:#fff">${c.NomeCompleto}</td>
                            <td style="color:var(--danger)">${c.StatusCompliance}</td>
                            <td><button class="btn-premium" style="padding:4px 12px; font-size:0.7rem;" onclick="alert('Enviado para análise!')">Aprovar</button></td>
                        </tr>`;
                });
            }
        }

    } catch (e) { console.error(e); }
}

// --- CLIENTE: Carregar Dados ---
async function loadClientData() {
    try {
        const token = localStorage.getItem('token');
        const headers = { 'Authorization': `Bearer ${token}` };

        // Busca Saldo e Portfolio em paralelo
        const [resConta, resPort] = await Promise.all([
            fetch(`${API_URL}/portal/minha-conta`, { headers }),
            fetch(`${API_URL}/portal/meu-portfolio`, { headers })
        ]);

        if (resConta.ok) {
            const conta = await resConta.json();
            const elSaldo = document.getElementById('saldo-val');
            if(elSaldo) elSaldo.textContent = moneyFormatter.format(conta.Saldo);
        }

        if (resPort.ok) {
            const portfolio = await resPort.json();

            const elPatr = document.getElementById('patrimonio-val');
            if(elPatr) elPatr.textContent = moneyFormatter.format(portfolio.valor_mercado_total || 0);

            const lucro = parseFloat(portfolio.resultado_total_financeiro || 0);
            const elLucro = document.getElementById('lucro-val');
            if(elLucro) {
                elLucro.textContent = moneyFormatter.format(lucro);
                elLucro.style.color = lucro >= 0 ? 'var(--success)' : 'var(--danger)';
            }

            // Tabela de Carteira
            const tbody = document.getElementById('portfolio-body');
            if(tbody) {
                tbody.innerHTML = '';
                if (portfolio.posicoes && portfolio.posicoes.length > 0) {
                    portfolio.posicoes.forEach(pos => {
                        const rentab = parseFloat(pos.resultado_financeiro);
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td style="color:var(--accent-gold); font-weight:600">${pos.produto.Ticker}</td>
                            <td>${pos.produto.NomeProduto}</td>
                            <td>${parseFloat(pos.Quantidade).toFixed(2)}</td>
                            <td>${moneyFormatter.format(pos.valor_mercado)}</td>
                            <td style="color:${rentab >= 0 ? 'var(--success)' : 'var(--danger)'}">${moneyFormatter.format(rentab)}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem; color:var(--text-muted)">Nenhum ativo na carteira.</td></tr>';
                }
            }
        }
    } catch (e) { console.error(e); }
}

// --- PRODUTOS (Para Investir) ---
async function loadProdutos() {
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_URL}/produtos`, { headers: { 'Authorization': `Bearer ${token}` } });
        const produtos = await res.json();

        const grid = document.getElementById('products-grid');
        if(grid) {
            grid.innerHTML = '';
            produtos.forEach(prod => {
                // Preço simulado para a demo
                const precoSimulado = (Math.random() * 100 + 20).toFixed(2);

                const card = document.createElement('div');
                card.className = 'product-card fade-in';
                card.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items: flex-start;">
                        <span class="badge badge-gold">${prod.ClasseAtivo}</span>
                        <span class="badge" style="border:1px solid var(--text-muted); color:var(--text-muted)">Risco ${prod.NivelRiscoProduto}/5</span>
                    </div>
                    <h3 style="color:#fff; margin-top:1rem; margin-bottom:0.5rem;">${prod.NomeProduto}</h3>
                    <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:1rem;">${prod.Ticker} - ${prod.Emissor || 'Chicoin$'}</p>
                    <p style="color:#fff; font-weight:bold; margin-bottom:1rem;">R$ ${precoSimulado}</p>
                    <button class="btn-premium" style="width:100%; font-size:0.8rem" 
                        onclick="openInvestModal(${prod.ProdutoID}, '${prod.Ticker}', ${precoSimulado})">
                        Investir
                    </button>
                `;
                grid.appendChild(card);
            });
        }
    } catch (e) { console.error(e); }
}

// --- MODAL DE INVESTIMENTO ---
let selectedProdutoId = null;

function openInvestModal(id, ticker, preco) {
    selectedProdutoId = id;
    const modal = document.getElementById('invest-modal');
    if(modal) {
        document.getElementById('modal-titulo').textContent = `Investir em ${ticker}`;
        document.getElementById('modal-preco').value = preco;
        modal.classList.add('open');
    }
}

function closeModal() {
    const modal = document.getElementById('invest-modal');
    if(modal) modal.classList.remove('open');
}

async function confirmInvest() {
    const qtd = document.getElementById('modal-qtd').value;
    const preco = document.getElementById('modal-preco').value;

    try {
        const token = localStorage.getItem('token');
        // 1. Pega ID do Portfolio
        const portRes = await fetch(`${API_URL}/portal/meu-portfolio`, { headers: { 'Authorization': `Bearer ${token}` } });
        const portfolio = await portRes.json();

        // 2. Envia Ordem
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

        if(res.ok) {
            alert('Ordem executada com sucesso!');
            closeModal();
            loadClientData(); // Atualiza saldo e tabela
        } else {
            const json = await res.json();
            alert('Erro: ' + (json.erro || 'Falha ao investir'));
        }
    } catch(e) {
        alert('Erro de conexão.');
    }
}

// --- FUNÇÕES GERAIS ---
async function handleNewClient(e) {
    e.preventDefault();
    const data = {
        NomeCompleto: document.getElementById('novo-nome').value,
        Email: document.getElementById('novo-email').value,
        CPF_CNPJ: document.getElementById('novo-cpf').value
    };
    try {
        const res = await fetch(`${API_URL}/clientes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
            body: JSON.stringify(data)
        });
        if(res.ok) {
            alert('Cliente criado com sucesso!');
            document.getElementById('form-novo-cliente').reset();
            await loadAssessorData(); // Recarrega a lista
            // Volta para a aba de lista
            const btn = document.querySelector('[data-target="view-clientes"]');
            if(btn) btn.click();
        } else {
            alert('Erro ao criar cliente. Verifique os dados.');
        }
    } catch(e) { console.error(e); }
}

function checkAuth() {
    if (!localStorage.getItem('token')) window.location.href = 'login.html';
}

function logout() {
    localStorage.clear();
    window.location.href = 'index.html';
}