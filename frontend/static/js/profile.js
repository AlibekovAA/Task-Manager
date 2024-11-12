document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/';
        return;
    }

    const userEmail = document.getElementById('userEmail');
    const userCreatedAt = document.getElementById('userCreatedAt');
    const passwordForm = document.getElementById('passwordForm');
    const passwordError = document.getElementById('passwordError');
    const passwordSuccess = document.getElementById('passwordSuccess');
    const logoutBtn = document.getElementById('logoutBtn');

    async function loadUserProfile() {
        try {
            const response = await fetch('/users/me/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                userEmail.textContent = userData.email;
                userCreatedAt.textContent = new Date(userData.created_at).toLocaleString('ru-RU');

                const adminMenuItem = document.getElementById('adminMenuItem');
                if (adminMenuItem) {
                    adminMenuItem.style.display = userData.role === 'admin' ? 'block' : 'none';
                }
            } else if (response.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/';
            }
        } catch (error) {
            console.error('Error loading profile:', error);
        }
    }

    await loadUserProfile();

    passwordForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        passwordError.textContent = '';
        passwordSuccess.textContent = '';
        passwordError.style.display = 'none';
        passwordSuccess.style.display = 'none';

        const submitButton = passwordForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner"></span> Обработка...';

        const currentPassword = passwordForm.currentPassword.value;
        const newPassword = passwordForm.newPassword.value;
        const confirmPassword = passwordForm.confirmPassword.value;

        if (!newPassword.trim()) {
            passwordError.textContent = 'Новый пароль не может быть пустым';
            passwordError.style.display = 'block';
            submitButton.disabled = false;
            submitButton.textContent = 'Сменить пароль';
            return;
        }

        if (newPassword.length < 6) {
            passwordError.textContent = 'Введите корректный пароль';
            passwordError.style.display = 'block';
            submitButton.disabled = false;
            submitButton.textContent = 'Сменить пароль';
            return;
        }

        if (newPassword !== confirmPassword) {
            passwordError.textContent = 'Пароли не совпадают';
            passwordError.style.display = 'block';
            submitButton.disabled = false;
            submitButton.textContent = 'Сменить пароль';
            return;
        }

        try {
            const checkResponse = await fetchWithToken('/users/me/check-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    password: currentPassword
                })
            });

            if (checkResponse.ok) {
                if (currentPassword === newPassword) {
                    passwordError.textContent = 'Новый пароль совпадает с текущим';
                    passwordError.style.display = 'block';
                    submitButton.disabled = false;
                    submitButton.textContent = 'Сменить пароль';
                    return;
                }

                const response = await fetchWithToken('/users/me/password', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        current_password: currentPassword,
                        new_password: newPassword
                    })
                });

                if (response.ok) {
                    passwordSuccess.textContent = 'Пароль успешно изменен';
                    passwordSuccess.style.display = 'block';
                    passwordForm.reset();

                    const formGroups = passwordForm.querySelectorAll('.form-group');
                    formGroups.forEach(group => {
                        group.classList.add('success');
                        setTimeout(() => group.classList.remove('success'), 2000);
                    });
                } else {
                    const data = await response.json();
                    passwordError.textContent = data.detail || 'Ошибка при смене пароля';
                    passwordError.style.display = 'block';

                    const formGroups = passwordForm.querySelectorAll('.form-group');
                    formGroups.forEach(group => {
                        group.classList.add('error');
                        setTimeout(() => group.classList.remove('error'), 2000);
                    });
                }
            } else {
                passwordError.textContent = 'Неверный текущий пароль';
                passwordError.style.display = 'block';
            }
        } catch (error) {
            console.error('Error changing password:', error);
            passwordError.textContent = 'Ошибка соединения с сервером';
            passwordError.style.display = 'block';
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = 'Сменить пароль';
        }
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        window.location.href = '/';
    });

    setInterval(loadUserProfile, 30000);

    document.querySelectorAll('.password-toggle').forEach(button => {
        button.addEventListener('click', (e) => {
            const input = e.currentTarget.previousElementSibling;
            const icon = e.currentTarget.querySelector('i');

            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });
});

async function fetchWithToken(url, options = {}) {
    const token = localStorage.getItem('access_token');
    return fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`
        }
    });
}
