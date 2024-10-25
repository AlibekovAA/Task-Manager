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
