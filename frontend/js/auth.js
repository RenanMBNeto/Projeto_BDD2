// frontend/js/auth.js
const API_URL = "http://127.0.0.1:5000";

async function handleLogin(event) {
    event.preventDefault(); // Impede a página de recarregar

    const email = document.getElementById('email').value;
    const senha = document.getElementById('senha').value;

    // Correção: Usa o ID 'error-msg' que está no seu HTML
    const errorMsg = document.getElementById('error-msg');

    // Correção: Seleciona o botão pelo tipo, já que ele não tem ID no HTML
    const btnLogin = document.querySelector('button[type="submit"]');

    // Limpar erros e dar feedback visual
    if (errorMsg) errorMsg.style.display = 'none';
    if (btnLogin) {
        btnLogin.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Autenticando...';
        btnLogin.disabled = true;
    }

    try {
        const response = await fetch(`${API_URL}/unified-login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ Email: email, Senha: senha })
        });

        const data = await response.json();

        if (response.ok) {
            // Sucesso! Salvar Token
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user_role', data.role);
            localStorage.setItem('user_name', data.user.Nome || data.user.NomeCompleto);

            // Feedback de sucesso
            if (btnLogin) {
                btnLogin.innerHTML = 'Sucesso!';
                btnLogin.style.background = 'var(--success)';
                btnLogin.style.color = '#fff';
            }

            // Redirecionar
            setTimeout(() => {
                if (data.role === 'assessor') {
                    window.location.href = 'dashboard-assessor.html';
                } else {
                    window.location.href = 'dashboard-cliente.html';
                }
            }, 500);

        } else {
            // Erro de login (senha errada, etc)
            throw new Error(data.erro || 'Falha no login');
        }

    } catch (error) {
        console.error(error);
        if (errorMsg) {
            errorMsg.innerText = error.message || "Erro ao conectar ao servidor.";
            errorMsg.style.display = 'block';
        }
        // Restaura o botão
        if (btnLogin) {
            btnLogin.innerText = 'Entrar no Portal';
            btnLogin.disabled = false;
        }
    }
}

// Verifica se já está logado
function checkAuth() {
    const token = localStorage.getItem('token');
    // Se não tem token e não está na tela de login ou home, manda pro login
    if (!token && !window.location.pathname.includes('login.html') && !window.location.pathname.includes('index.html')) {
        window.location.href = 'login.html';
    }
}

function logout() {
    localStorage.clear();
    window.location.href = 'index.html';
}