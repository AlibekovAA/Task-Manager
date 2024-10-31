document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/';
        return;
    }

    async function checkAdminAccess() {
        try {
            const response = await fetch('/users/me/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                if (userData.role !== 'admin') {
                    window.location.href = '/dashboard.html';
                    return;
                }

                localStorage.setItem('user_email', userData.email);
            } else {
                window.location.href = '/';
                return;
            }
        } catch (error) {
            console.error('Error checking admin access:', error);
            window.location.href = '/dashboard.html';
            return;
        }
    }

    checkAdminAccess();

    const usersList = document.getElementById('usersList');
    const logoutBtn = document.getElementById('logoutBtn');
    const notification = document.getElementById('notification');
    const notificationClose = notification.querySelector('.notification-close');

    async function loadUsers() {
        try {
            const response = await fetch('/admin/users/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const users = await response.json();
                renderUsers(users);
            } else if (response.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/';
            } else if (response.status === 403) {
                window.location.href = '/dashboard.html';
            }
        } catch (error) {
            console.error('Error loading users:', error);
            showNotification('Ошибка при загрузке пользователей', 'error');
        }
    }

    function renderUsers(users) {
        usersList.innerHTML = '';
        users.forEach(user => {
            const userElement = document.createElement('div');
            userElement.className = 'user-item';

            const currentUserEmail = localStorage.getItem('user_email');
            const isCurrentUser = user.email === currentUserEmail;
            const isAdmin = user.role === 'admin';

            userElement.innerHTML = `
                <div class="user-info">
                    <h3>${user.email}</h3>
                    <p>Роль: ${user.role}</p>
                    <p>Создан: ${new Date(user.created_at).toLocaleString('ru-RU')}</p>
                    <p>Статус: ${user.is_active ? 'Активен' : 'Заблокирован'}</p>
                </div>
                <div class="user-actions">
                    <select class="role-select" onchange="changeUserRole(${user.id}, this.value)"
                            ${isCurrentUser || isAdmin ? 'disabled' : ''}>
                        <option value="user" ${user.role === 'user' ? 'selected' : ''}>Пользователь</option>
                        <option value="pm" ${user.role === 'pm' ? 'selected' : ''}>Проджект-менеджер</option>
                        ${isAdmin ? `<option value="admin" selected>Администратор</option>` : ''}
                    </select>
                    <button class="btn-${user.is_active ? 'danger' : 'success'}"
                            onclick="toggleUserBlock(${user.id}, ${user.is_active})"
                            ${isCurrentUser || isAdmin ? 'disabled' : ''}>
                        ${user.is_active ? 'Заблокировать' : 'Разблокировать'}
                    </button>
                </div>
            `;
            usersList.appendChild(userElement);
        });
    }

    function showNotification(message, type = 'error') {
        const notificationElement = document.createElement('div');
        notificationElement.className = `notification ${type}`;

        const icon = type === 'success' ? '✅' : '❌';

        notificationElement.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${icon}</span>
                <span class="notification-message">${message}</span>
            </div>
            <button class="notification-close">&times;</button>
        `;

        document.body.appendChild(notificationElement);

        setTimeout(() => {
            notificationElement.classList.add('show');
        }, 10);

        const closeBtn = notificationElement.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            hideNotification(notificationElement);
        });

        setTimeout(() => {
            hideNotification(notificationElement);
        }, 5000);
    }

    function hideNotification(notificationElement) {
        notificationElement.classList.remove('show');
        setTimeout(() => {
            notificationElement.remove();
        }, 300);
    }

    notificationClose.addEventListener('click', () => {
        hideNotification(notification);
    });

    window.toggleUserBlock = async function(userId, currentStatus) {
        try {
            const response = await fetch(`/admin/users/${userId}/block`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    is_active: !currentStatus
                })
            });

            if (response.ok) {
                await loadUsers();
                showNotification(
                    currentStatus ? 'Пользователь заблокирован' : 'Пользователь разблокирован',
                    'success'
                );
            } else {
                const errorData = await response.json();
                showNotification(errorData.detail || 'Ошибка при обновлении статуса пользователя', 'error');
            }
        } catch (error) {
            console.error('Error updating user status:', error);
            showNotification('Ошибка при обновлении статуса пользователя');
        }
    };

    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('access_token');
        window.location.href = '/';
    });

    loadUsers();

    window.changeUserRole = async function(userId, newRole) {
        try {
            const response = await fetch(`/admin/users/${userId}/role`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    role: newRole
                })
            });

            if (response.ok) {
                await loadUsers();
                showNotification(
                    `Роль пользователя изменена на ${newRole}`,
                    'success'
                );
            } else {
                const errorData = await response.json();
                showNotification(errorData.detail || 'Ошибка при изменении роли пользователя', 'error');
            }
        } catch (error) {
            console.error('Error updating user role:', error);
            showNotification('Ошибка при изменении роли пользователя');
        }
    };
});
