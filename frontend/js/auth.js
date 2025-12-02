// js/auth.js
const API_URL = "http://127.0.0.1:5000"; // Endereço do seu Flask

async function handleLogin(event) {
    event.preventDefault(); // Não recarregar a página

    const email = document.getElementById('email').value;
    const senha = document.getElementById('senha').value;
    const errorMsg = document.getElementById('error-msg');
    const btnLogin = document.querySelector('button');

    // Limpar erros e mudar botão
    errorMsg.style.display = 'none';
    btnLogin.innerText = 'Autenticando...';

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
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user_role', data.role);
            localStorage.setItem('user_name', data.user.Nome || data.user.NomeCompleto);

            if (data.role === 'assessor') {
                window.location.href = 'dashboard-assessor.html';
            } else {
                window.location.href = 'dashboard-cliente.html';
            }
        } else {
            // Erro de login
            throw new Error(data.erro || 'Falha no login');
        }

    } catch (error) {
        errorMsg.innerText = error.message;
        errorMsg.style.display = 'block';
        btnLogin.innerText = 'ENTRAR';
    }
}

// Verifica se já está logado (para proteger páginas internas)
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
    }
}

function logout() {
    localStorage.clear();
    window.location.href = 'index.html';
}