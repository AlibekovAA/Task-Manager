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
    const adminMenuItem = document.getElementById('adminMenuItem');

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

        const submitButton = passwordForm.querySelector('button[type="submit"]');
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner"></span> Обработка...';

        const currentPassword = passwordForm.currentPassword.value;
        const newPassword = passwordForm.newPassword.value;
        const confirmPassword = passwordForm.confirmPassword.value;

        if (!newPassword.trim()) {
            passwordError.textContent = 'Новый пароль не может быть пустым';
            submitButton.disabled = false;
            submitButton.textContent = 'Сменить пароль';
            return;
        }

        if (newPassword.length < 6) {
            passwordError.textContent = 'Новый пароль должен содержать минимум 6 символов';
            submitButton.disabled = false;
            submitButton.textContent = 'Сменить пароль';
            return;
        }

        if (newPassword !== confirmPassword) {
            passwordError.textContent = 'Пароли не совпадают';
            submitButton.disabled = false;
            submitButton.textContent = 'Сменить пароль';
            return;
        }

        try {
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
                passwordForm.reset();

                const formGroups = passwordForm.querySelectorAll('.form-group');
                formGroups.forEach(group => {
                    group.classList.add('success');
                    setTimeout(() => group.classList.remove('success'), 2000);
                });
            } else {
                const data = await response.json();
                if (response.status === 401) {
                    passwordError.textContent = 'Неверный текущий пароль';
                } else {
                    passwordError.textContent = data.detail || 'Ошибка при смене пароля';
                }

                const formGroups = passwordForm.querySelectorAll('.form-group');
                formGroups.forEach(group => {
                    group.classList.add('error');
                    setTimeout(() => group.classList.remove('error'), 2000);
                });
            }
        } catch (error) {
            console.error('Error changing password:', error);
            passwordError.textContent = 'Ошибка соединения с сервером';
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
