document.addEventListener('DOMContentLoaded', async () => {
  if (!checkAuth()) return;

  const userEmail = document.getElementById('userEmail');
  const userCreatedAt = document.getElementById('userCreatedAt');
  const passwordForm = document.getElementById('passwordForm');
  const passwordError = document.getElementById('passwordError');
  const passwordSuccess = document.getElementById('passwordSuccess');
  const logoutBtn = document.getElementById('logoutBtn');

  async function displayUserProfile() {
    const userData = await loadUserProfile();
    if (userData) {
      userEmail.textContent = userData.email;
      userCreatedAt.textContent = new Date(userData.created_at).toLocaleString(
        'ru-RU',
      );

      const adminMenuItem = document.getElementById('adminMenuItem');
      if (adminMenuItem) {
        adminMenuItem.style.display =
          userData.role === 'admin' ? 'block' : 'none';
      }
    }
  }

  await displayUserProfile();

  passwordForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    hideMessage(passwordError);
    hideMessage(passwordSuccess);

    const submitButton = passwordForm.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner"></span> Обработка...';

    const currentPassword = passwordForm.currentPassword.value;
    const newPassword = passwordForm.newPassword.value;
    const confirmPassword = passwordForm.confirmPassword.value;

    if (!newPassword.trim()) {
      showErrorMessage(passwordError, 'Новый пароль не может быть пустым');
      submitButton.disabled = false;
      submitButton.textContent = originalText;
      return;
    }

    if (!validatePassword(newPassword)) {
      showErrorMessage(
        passwordError,
        'Пароль должен содержать не менее 6 символов',
      );
      submitButton.disabled = false;
      submitButton.textContent = originalText;
      return;
    }

    if (newPassword !== confirmPassword) {
      showErrorMessage(passwordError, 'Пароли не совпадают');
      submitButton.disabled = false;
      submitButton.textContent = originalText;
      return;
    }

    try {
      const checkResponse = await fetchWithToken('/users/me/check-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          password: currentPassword,
        }),
      });

      if (checkResponse.ok) {
        if (currentPassword === newPassword) {
          showErrorMessage(
            passwordError,
            'Новый пароль должен отличаться от текущего',
          );
          submitButton.disabled = false;
          submitButton.textContent = originalText;
          return;
        }

        const response = await fetchWithToken('/users/me/password', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            current_password: currentPassword,
            new_password: newPassword,
          }),
        });

        if (response.ok) {
          showSuccessMessage(passwordSuccess, 'Пароль успешно изменен');
          passwordForm.reset();

          const formGroups = passwordForm.querySelectorAll('.form-group');
          formGroups.forEach((group) => {
            group.classList.add('success');
            setTimeout(() => group.classList.remove('success'), 2000);
          });
        } else {
          const data = await response.json();
          const errorMsg = getErrorMessage(
            data,
            'Ошибка при смене пароля. Попробуйте позже',
          );
          showErrorMessage(passwordError, errorMsg);

          const formGroups = passwordForm.querySelectorAll('.form-group');
          formGroups.forEach((group) => {
            group.classList.add('error');
            setTimeout(() => group.classList.remove('error'), 2000);
          });
        }
      } else {
        showErrorMessage(passwordError, 'Неверный текущий пароль');
      }
    } catch (error) {
      console.error('Error changing password:', error);
      showErrorMessage(
        passwordError,
        'Ошибка соединения с сервером. Проверьте подключение к интернету',
      );
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = originalText;
    }
  });

  logoutBtn.addEventListener('click', (e) => {
    e.preventDefault();
    logout();
  });

  setInterval(displayUserProfile, 30000);
});
