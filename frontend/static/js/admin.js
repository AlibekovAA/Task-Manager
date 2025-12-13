document.addEventListener('DOMContentLoaded', async () => {
  if (!checkAuth()) return;

  async function checkAdminAccess() {
    const userData = await loadUserProfile();
    if (!userData) {
      window.location.href = '/';
      return false;
    }

    if (userData.role !== 'admin') {
      window.location.href = '/dashboard.html';
      return false;
    }

    localStorage.setItem('user_email', userData.email);
    return true;
  }

  const hasAccess = await checkAdminAccess();
  if (!hasAccess) return;

  const usersList = document.getElementById('usersList');
  const logoutBtn = document.getElementById('logoutBtn');

  async function loadUsers() {
    try {
      const response = await fetchWithToken('/admin/users/');

      if (response.ok) {
        const users = await response.json();
        renderUsers(users);
      } else if (response.status === 401) {
        logout();
      } else if (response.status === 403) {
        window.location.href = '/dashboard.html';
      } else {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        showNotification('Ошибка при загрузке пользователей', 'error');
      }
    } catch (error) {
      console.error('Error loading users:', error);
      showNotification(
        'Ошибка при загрузке пользователей. Проверьте подключение к интернету',
        'error',
      );
    }
  }

  function renderUsers(users) {
    usersList.innerHTML = '';
    users.forEach((user) => {
      const userElement = document.createElement('div');
      userElement.className = 'user-item';

      const currentUserEmail = localStorage.getItem('user_email');
      const isCurrentUser = user.email === currentUserEmail;
      const isAdmin = user.role === 'admin';

      userElement.innerHTML = `
                <div class="user-info">
                    <h3>${user.email}</h3>
                    <p>Роль: ${user.role}</p>
                    <p>Создан: ${new Date(user.created_at).toLocaleString(
                      'ru-RU',
                    )}</p>
                    <p>Статус: ${
                      user.is_active ? 'Активен' : 'Заблокирован'
                    }</p>
                </div>
                <div class="user-actions">
                    <select class="role-select" onchange="changeUserRole(${
                      user.id
                    }, this.value)"
                            ${isCurrentUser || isAdmin ? 'disabled' : ''}>
                        <option value="user" ${
                          user.role === 'user' ? 'selected' : ''
                        }>Пользователь</option>
                        <option value="pm" ${
                          user.role === 'pm' ? 'selected' : ''
                        }>Проджект-менеджер</option>
                        ${
                          isAdmin
                            ? `<option value="admin" selected>Администратор</option>`
                            : ''
                        }
                    </select>
                    <div class="toggle-container">
                        <label class="switch">
                            <input type="checkbox" ${
                              user.is_active ? 'checked' : ''
                            }
                                onclick="toggleUserBlock(${user.id}, ${
        user.is_active
      })"
                                ${isCurrentUser || isAdmin ? 'disabled' : ''}>
                            <span class="slider"></span>
                        </label>
                    </div>
                </div>
            `;
      usersList.appendChild(userElement);
    });
  }

  const notification = document.getElementById('notification');
  const notificationMessage = notification.querySelector(
    '.notification-message',
  );
  const notificationClose = notification.querySelector('.notification-close');

  function showNotification(message, type = 'error') {
    const content = notification.querySelector('.notification-content');
    notificationMessage.textContent = message;

    content.classList.remove('success', 'error', 'urgent');
    content.classList.add(type);
    notification.classList.add('show');

    setTimeout(() => {
      notification.classList.remove('show');
    }, 5000);
  }

  function hideNotification() {
    notification.classList.remove('show');
  }

  notificationClose.addEventListener('click', hideNotification);

  window.toggleUserBlock = async function (userId, currentStatus) {
    const newStatus = !currentStatus;
    try {
      const response = await fetchWithToken(`/admin/users/${userId}/block`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          is_active: newStatus,
        }),
      });

      if (response.ok) {
        await loadUsers();
        showNotification(
          newStatus
            ? 'Пользователь успешно разблокирован'
            : 'Пользователь успешно заблокирован',
          'success',
        );
      } else {
        const errorData = await response.json();
        const errorMsg = getErrorMessage(
          errorData,
          'Ошибка при обновлении статуса пользователя',
        );
        showNotification(errorMsg, 'error');
      }
    } catch (error) {
      console.error('Error updating user status:', error);
      showNotification(
        'Ошибка соединения с сервером. Проверьте подключение к интернету',
        'error',
      );
    }
  };

  logoutBtn.addEventListener('click', (e) => {
    e.preventDefault();
    logout();
  });

  loadUsers();

  window.changeUserRole = async function (userId, newRole) {
    try {
      const response = await fetchWithToken(`/admin/users/${userId}/role`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          role: newRole,
        }),
      });

      if (response.ok) {
        await loadUsers();
        const roleNames = {
          user: 'Пользователь',
          pm: 'Проджект-менеджер',
          admin: 'Администратор',
        };
        showNotification(
          `Роль пользователя успешно изменена на "${
            roleNames[newRole] || newRole
          }"`,
          'success',
        );
      } else {
        const errorData = await response.json();
        const errorMsg = getErrorMessage(
          errorData,
          'Ошибка при изменении роли пользователя',
        );
        showNotification(errorMsg, 'error');
      }
    } catch (error) {
      console.error('Error updating user role:', error);
      showNotification(
        'Ошибка соединения с сервером. Проверьте подключение к интернету',
        'error',
      );
    }
  };
});
