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

                if (userData.role === 'admin') {
                    if (adminMenuItem) {
                        adminMenuItem.style.display = 'block';
                    }
                } else {
                    if (adminMenuItem) {
                        adminMenuItem.style.display = 'none';
                    }
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

        const newPassword = passwordForm.newPassword.value;
        const confirmPassword = passwordForm.confirmPassword.value;

        if (newPassword !== confirmPassword) {
            passwordError.textContent = 'Пароли не совпадают';
            return;
        }

        try {
            const response = await fetchWithToken('/users/me/password', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    current_password: passwordForm.currentPassword.value,
                    new_password: newPassword
                })
            });

            if (response.ok) {
                passwordSuccess.textContent = 'Пароль успешно изменен';
                passwordForm.reset();
            } else {
                const data = await response.json();
                passwordError.textContent = data.detail || 'Ошибка при смене пароля';
            }
        } catch (error) {
            console.error('Error changing password:', error);
            passwordError.textContent = 'Ошибка соединения с сервером';
        }
    });

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_role');
        window.location.href = '/';
    });

    setInterval(loadUserProfile, 30000);
});
