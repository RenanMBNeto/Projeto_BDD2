// frontend/js/dashboard.js
const API_URL = "http://127.0.0.1:5000";
const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

// --- INICIALIZAÇÃO ---
async function initDashboard(role) {
    checkAuth();

    // Exibir nome do usuário
    const userName = localStorage.getItem('user_name');
    if (document.getElementById('user-name') && userName) {
        document.getElementById('user-name').textContent = userName;
    }

    // --- LÓGICA DE NAVEGAÇÃO (ABAS) ---
    const navButtons = document.querySelectorAll('.nav-btn');
    const viewSections = document.querySelectorAll('.view-section');

    navButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // 1. Remove estado ativo de todos os botões
            navButtons.forEach(b => b.classList.remove('active'));

            // 2. Esconde todas as seções
            viewSections.forEach(s => s.classList.add('hidden'));

            // 3. Ativa o botão clicado
            // (Usa e.currentTarget para garantir que pegamos o botão mesmo se clicar no ícone dentro dele)
            const clickedBtn = e.currentTarget;
            clickedBtn.classList.add('active');

            // 4. Mostra a seção correspondente
            const targetId = clickedBtn.getAttribute('data-target');
            const targetSection = document.getElementById(targetId);

            if (targetSection) {
                targetSection.classList.remove('hidden');
                // Adiciona animação suave se o CSS suportar
                targetSection.classList.add('fade-in');
            }

            // 5. Carrega dados específicos da aba se necessário
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

// --- FUNÇÕES DO ASSESSOR ---
async function loadAssessorData() {
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_URL}/clientes`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) throw new Error("Falha na comunicação com o servidor");

        const clientes = await res.json();

        // Atualiza KPIs (Cards do Topo)
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
                tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem; color: var(--text-muted);">Nenhum cliente encontrado.</td></tr>';
            } else {
                clientes.forEach(c => {
                    // Define a cor do badge baseada no status
                    let badgeClass = 'badge-gold';
                    if (c.StatusCompliance === 'Aprovado') badgeClass = 'badge-green';
                    if (c.StatusCompliance === 'Reprovado') badgeClass = 'badge-red';

                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td style="color:#fff; font-weight:500;">${c.NomeCompleto}</td>
                        <td>${c.CPF_CNPJ}</td>
                        <td>${c.Email}</td>
                        <td><span class="badge ${badgeClass}">${c.StatusCompliance}</span></td>
                        <td><button class="btn-premium" style="padding: 4px 12px; font-size: 0.7rem; width: auto;" onclick="alert('Detalhes do cliente: ${c.NomeCompleto}')">Ver</button></td>
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
                compBody.innerHTML = '<tr><td colspan="3" style="text-align:center; padding:1rem; color: var(--text-muted);">Nenhuma pendência de compliance.</td></tr>';
            } else {
                pendentes.forEach(c => {
                    compBody.innerHTML += `
                        <tr>
                            <td style="color:#fff">${c.NomeCompleto}</td>
                            <td style="color:var(--danger)">${c.StatusCompliance}</td>
                            <td><button class="btn-premium" style="padding:4px 12px; font-size:0.7rem; width: auto;" onclick="alert('Aprovação enviada para análise')">Analisar</button></td>
                        </tr>`;
                });
            }
        }

    } catch (e) {
        console.error("Erro ao carregar dados do assessor:", e);
    }
}

// Lógica para criar novo cliente
async function handleNewClient(e) {
    e.preventDefault(); // Impede o recarregamento da página

    const data = {
        NomeCompleto: document.getElementById('novo-nome').value,
        Email: document.getElementById('novo-email').value,
        CPF_CNPJ: document.getElementById('novo-cpf').value
    };

    try {
        const res = await fetch(`${API_URL}/clientes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(data)
        });

        if(res.ok) {
            alert('Cliente cadastrado com sucesso!');
            document.getElementById('form-novo-cliente').reset();

            // Recarrega a lista de clientes
            await loadAssessorData();

            // Simula clique na aba "Meus Clientes" para voltar para a lista
            const btnList = document.querySelector('[data-target="view-clientes"]');
            if(btnList) btnList.click();
        } else {
            const err = await res.json();
            alert('Erro ao criar: ' + (err.erro || err.detalhes || 'Erro desconhecido'));
        }
    } catch(error) {
        console.error(error);
        alert('Erro de conexão.');
    }
}

// --- FUNÇÕES DO CLIENTE ---
async function loadClientData() {
    try {
        const token = localStorage.getItem('token');
        const headers = { 'Authorization': `Bearer ${token}` };

        // Busca dados em paralelo
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

            // Atualiza Cards
            const elPatr = document.getElementById('patrimonio-val');
            if(elPatr) elPatr.textContent = moneyFormatter.format(portfolio.valor_mercado_total || 0);

            const lucro = parseFloat(portfolio.resultado_total_financeiro || 0);
            const elLucro = document.getElementById('lucro-val');
            if(elLucro) {
                elLucro.textContent = moneyFormatter.format(lucro);
                // Aplica cor verde se lucro >= 0, vermelha se negativo
                elLucro.style.color = lucro >= 0 ? 'var(--success)' : 'var(--danger)';
            }

            // Preenche Tabela
            const tbody = document.getElementById('portfolio-body');
            if(tbody) {
                tbody.innerHTML = '';
                if (portfolio.posicoes && portfolio.posicoes.length > 0) {
                    portfolio.posicoes.forEach(pos => {
                        const rentab = parseFloat(pos.resultado_financeiro);
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td style="color: var(--accent-gold); font-weight:600;">${pos.produto.Ticker}</td>
                            <td>${pos.produto.NomeProduto}</td>
                            <td>${parseFloat(pos.Quantidade).toFixed(2)}</td>
                            <td>${moneyFormatter.format(pos.valor_mercado)}</td>
                            <td style="color:${rentab >= 0 ? 'var(--success)' : 'var(--danger)'}">${moneyFormatter.format(rentab)}</td>
                        `;
                        tbody.appendChild(tr);
                    });
                } else {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem; color: var(--text-muted);">Nenhum ativo em carteira.</td></tr>';
                }
            }
        }
    } catch (e) {
        console.error("Erro ao carregar dados do cliente:", e);
    }
}

// Carrega Produtos para a aba Investir
async function loadProdutos() {
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${API_URL}/produtos`, { headers: { 'Authorization': `Bearer ${token}` } });
        const produtos = await res.json();

        const grid = document.getElementById('products-grid');
        if(grid) {
            grid.innerHTML = '';
            produtos.forEach(prod => {
                const div = document.createElement('div');
                div.className = 'product-card fade-in';
                div.innerHTML = `
                    <div style="display:flex; justify-content:space-between; align-items: flex-start;">
                        <span class="badge badge-gold">${prod.ClasseAtivo}</span>
                        <span class="badge" style="border:1px solid var(--text-muted); color:var(--text-muted)">Risco ${prod.NivelRiscoProduto}/5</span>
                    </div>
                    <h3 style="margin-top:1rem; color:#fff;">${prod.NomeProduto}</h3>
                    <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:1.5rem;">${prod.Ticker} - ${prod.Emissor || 'Chicoin$'}</p>
                    <button class="btn-premium" style="width:100%; font-size:0.8rem" onclick="alert('Ordem de compra enviada para processamento!')">Investir</button>
                `;
                grid.appendChild(div);
            });
        }
    } catch (e) { console.error(e); }
}

// Utilitários
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        // Redireciona apenas se não estiver já na página de login
        if(!window.location.pathname.includes('login.html')) {
            window.location.href = 'login.html';
        }
    }
}

function logout() {
    localStorage.clear();
    window.location.href = 'index.html';
}