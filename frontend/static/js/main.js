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

        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(email)) {
            errorMessage.textContent = 'Пожалуйста, введите корректный email адрес';
            return;
        }

        if (password.length < 6) {
            errorMessage.textContent = 'Пароль должен содержать минимум 6 символов';
            return;
        }

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

    const loginSection = document.getElementById('loginSection');
    const resetSection = document.getElementById('resetSection');
    const forgotPasswordBtn = document.getElementById('forgotPasswordBtn');
    const backToLogin = document.getElementById('backToLogin');
    const resetPasswordForm = document.getElementById('resetPasswordForm');
    const newPasswordForm = document.getElementById('newPasswordForm');
    const stepOne = document.getElementById('stepOne');
    const stepTwo = document.getElementById('stepTwo');

    let resetEmail = '';
    let resetSecretWord = '';

    forgotPasswordBtn.addEventListener('click', (e) => {
        e.preventDefault();
        loginSection.style.display = 'none';
        resetSection.style.display = 'block';
        resetPasswordForm.reset();
        newPasswordForm.reset();
        stepOne.style.display = 'block';
        stepTwo.style.display = 'none';
    });

    backToLogin.addEventListener('click', () => {
        resetSection.style.display = 'none';
        loginSection.style.display = 'block';
        resetPasswordForm.reset();
        newPasswordForm.reset();
        document.getElementById('resetErrorMessage').textContent = '';
        document.getElementById('newPasswordErrorMessage').textContent = '';
    });

    resetPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = resetPasswordForm.resetEmail.value;
        const secretWord = resetPasswordForm.secretWord.value;

        try {
            const response = await fetch('/users/verify-reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: email,
                    secret_word: secretWord
                }),
            });

            const data = await response.json();

            if (response.ok) {
                resetEmail = email;
                resetSecretWord = secretWord;
                stepOne.style.display = 'none';
                stepTwo.style.display = 'block';
                document.getElementById('resetErrorMessage').textContent = '';
            } else {
                const errorMessage = document.getElementById('resetErrorMessage');
                errorMessage.style.color = '#ff3333';

                switch (response.status) {
                    case 404:
                        errorMessage.textContent = 'Пользователь с таким email не найден';
                        break;
                    case 400:
                        errorMessage.textContent = 'Неверное кодовое слово';
                        break;
                    case 422:
                        errorMessage.textContent = 'Проверьте правильность введенных данных';
                        break;
                    default:
                        errorMessage.textContent = data.detail || 'Произошла ошибка при проверке данных';
                }
            }
        } catch (error) {
            const errorMessage = document.getElementById('resetErrorMessage');
            errorMessage.style.color = '#ff3333';
            errorMessage.textContent = 'Ошибка соединения с сервером. Попробуйте позже.';
        }
    });

    newPasswordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const newPassword = newPasswordForm.newPassword.value;
        const confirmPassword = newPasswordForm.confirmNewPassword.value;

        if (newPassword !== confirmPassword) {
            document.getElementById('newPasswordErrorMessage').textContent =
                'Пароли не совпадают';
            return;
        }

        try {
            const response = await fetch('/users/reset-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: resetEmail,
                    secret_word: resetSecretWord,
                    new_password: newPassword
                }),
            });

            if (response.ok) {
                resetSection.style.display = 'none';
                loginSection.style.display = 'block';
                resetPasswordForm.reset();
                newPasswordForm.reset();
                const errorMessage = document.getElementById('errorMessage');
                errorMessage.style.color = '#388e3c';
                errorMessage.textContent = 'Пароль успешно изменен! Теперь вы можете войти.';
                resetEmail = '';
                resetSecretWord = '';
            } else {
                const data = await response.json();
                document.getElementById('newPasswordErrorMessage').textContent =
                    data.detail || 'Ошибка при смене пароля';
            }
        } catch (error) {
            document.getElementById('newPasswordErrorMessage').textContent =
                'Ошибка соединения с сервером';
        }
    });

    backToStepOne.addEventListener('click', () => {
        stepTwo.style.display = 'none';
        stepOne.style.display = 'block';
        document.getElementById('newPasswordErrorMessage').textContent = '';
        newPasswordForm.reset();
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
