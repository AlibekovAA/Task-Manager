document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('registered') === 'true') {
        const errorMessage = document.getElementById('errorMessage');
        errorMessage.style.color = '#388e3c';
        errorMessage.textContent = 'Регистрация успешна! Теперь вы можете войти.';
    }

    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(loginForm);
        const email = formData.get('email');
        const password = formData.get('password');

        try {
            const response = await fetch('/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `username=${encodeURIComponent(email)}&password=${encodeURIComponent(password)}`,
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                localStorage.setItem('user_role', data.role);
                window.location.href = '/dashboard.html';
            } else {
                errorMessage.textContent = data.detail || 'Ошибка авторизации';
            }
        } catch (error) {
            errorMessage.textContent = 'Ошибка соединения с сервером';
            console.error('Error:', error);
        }
    });
});

async function refreshToken() {
    try {
        const refresh_token = localStorage.getItem('refresh_token');
        if (!refresh_token) return false;

        const response = await fetch('/token/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token }),
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            return true;
        }
        return false;
    } catch {
        return false;
    }
}

async function fetchWithToken(url, options = {}) {
    let token = localStorage.getItem('access_token');

    let response = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        }
    });

    if (response.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
            token = localStorage.getItem('access_token');
            response = await fetch(url, {
                ...options,
                headers: {
                    ...options.headers,
                    'Authorization': `Bearer ${token}`
                }
            });
        } else {
            window.location.href = '/';
        }
    }

    return response;
}
