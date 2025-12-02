const API_URL = "http://127.0.0.1:5000";
const moneyFormatter = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' });

async function initDashboard(role) {
    checkAuth();
    const userName = localStorage.getItem('user_name');
    if (document.getElementById('user-name')) {
        document.getElementById('user-name').textContent = userName;
    }

    if (role === 'cliente') {
        await loadClientData();
    } else if (role === 'assessor') {
        await loadAssessorData();
    }
}

async function loadClientData() {
    try {
        const token = localStorage.getItem('token');
        const resConta = await fetch(`${API_URL}/portal/minha-conta`, { headers: { 'Authorization': `Bearer ${token}` } });
        const conta = await resConta.json();
        document.getElementById('saldo-val').textContent = moneyFormatter.format(conta.Saldo);

        const resPort = await fetch(`${API_URL}/portal/meu-portfolio`, { headers: { 'Authorization': `Bearer ${token}` } });
        const portfolio = await resPort.json();

        document.getElementById('patrimonio-val').textContent = moneyFormatter.format(portfolio.valor_mercado_total || 0);
        const lucro = parseFloat(portfolio.resultado_total_financeiro || 0);
        const elLucro = document.getElementById('lucro-val');
        elLucro.textContent = moneyFormatter.format(lucro);
        elLucro.style.color = lucro >= 0 ? 'var(--success)' : 'var(--danger)';

        const tbody = document.getElementById('portfolio-body');
        tbody.innerHTML = '';
        if (portfolio.posicoes && portfolio.posicoes.length > 0) {
            portfolio.posicoes.forEach(pos => {
                const rentab = parseFloat(pos.resultado_financeiro);
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight:600; color:#fff;">${pos.produto.Ticker}</td>
                    <td>${pos.produto.NomeProduto}</td>
                    <td>${parseFloat(pos.Quantidade).toFixed(2)}</td>
                    <td>${moneyFormatter.format(pos.valor_mercado)}</td>
                    <td style="color: ${rentab >= 0 ? 'var(--success)' : 'var(--danger)'}">${moneyFormatter.format(rentab)}</td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding: 2rem;">Nenhum investimento encontrado.</td></tr>';
        }
    } catch (error) { console.error(error); }
}

async function loadAssessorData() {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_URL}/clientes`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const clientes = await response.json();

        const tbody = document.getElementById('clientes-body');
        tbody.innerHTML = '';

        if (clientes.length > 0) {
            clientes.forEach(cliente => {
                const tr = document.createElement('tr');
                let badgeClass = 'status-pendente';
                if (cliente.StatusCompliance === 'Aprovado') badgeClass = 'status-aprovado';
                else if (cliente.StatusCompliance === 'Reprovado') badgeClass = 'status-reprovado';

                tr.innerHTML = `
                    <td style="font-weight:500; color:#fff;">${cliente.NomeCompleto}</td>
                    <td>${cliente.CPF_CNPJ}</td>
                    <td>${cliente.Email}</td>
                    <td><span class="status-badge ${badgeClass}">${cliente.StatusCompliance}</span></td>
                    <td><a href="#" style="color:var(--accent-gold); font-size:0.85rem;">Detalhes</a></td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Nenhum cliente na carteira.</td></tr>';
        }
    } catch (error) {
        console.error("Erro ao carregar clientes:", error);
    }
}

function checkAuth() { if (!localStorage.getItem('token')) window.location.href = 'login.html'; }
function logout() { localStorage.clear(); window.location.href = 'index.html'; }