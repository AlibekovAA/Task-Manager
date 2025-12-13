document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('registered') === 'true') {
    const errorMessage = document.getElementById('errorMessage');
    showSuccessMessage(
      errorMessage,
      'Регистрация успешна! Теперь вы можете войти.',
    );
  }

  const loginForm = document.getElementById('loginForm');
  const errorMessage = document.getElementById('errorMessage');

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideMessage(errorMessage);

    const formData = new FormData(loginForm);
    const email = formData.get('email');
    const password = formData.get('password');

    if (!validateEmail(email)) {
      showErrorMessage(
        errorMessage,
        'Пожалуйста, введите корректный email адрес',
      );
      return;
    }

    if (!validatePassword(password)) {
      showErrorMessage(
        errorMessage,
        'Пароль должен содержать не менее 6 символов',
      );
      return;
    }

    try {
      const response = await fetch('/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `username=${encodeURIComponent(
          email,
        )}&password=${encodeURIComponent(password)}`,
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user_role', data.role);
        window.location.href = '/dashboard.html';
      } else {
        const errorMsg = getErrorMessage(
          data,
          'Ошибка авторизации. Проверьте правильность введенных данных',
        );
        showErrorMessage(errorMessage, errorMsg);
      }
    } catch (error) {
      showErrorMessage(
        errorMessage,
        'Ошибка соединения с сервером. Проверьте подключение к интернету',
      );
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
    const errorMessage = document.getElementById('resetErrorMessage');

    hideMessage(errorMessage);

    if (!validateEmail(email)) {
      showErrorMessage(
        errorMessage,
        'Пожалуйста, введите корректный email адрес',
      );
      return;
    }

    if (!validateSecretWord(secretWord)) {
      showErrorMessage(
        errorMessage,
        'Кодовое слово должно содержать от 3 до 50 символов',
      );
      return;
    }

    try {
      const response = await fetch('/users/verify-reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          secret_word: secretWord,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        resetEmail = email;
        resetSecretWord = secretWord;
        stepOne.style.display = 'none';
        stepTwo.style.display = 'block';
        hideMessage(errorMessage);
      } else {
        let errorMsg = 'Произошла ошибка при проверке данных';

        switch (response.status) {
          case 404:
            errorMsg = 'Пользователь с таким email не найден';
            break;
          case 400:
            errorMsg = 'Неверное кодовое слово';
            break;
          case 422:
            errorMsg = 'Проверьте правильность введенных данных';
            break;
          default:
            errorMsg = getErrorMessage(data, errorMsg);
        }

        showErrorMessage(errorMessage, errorMsg);
        setTimeout(() => hideMessage(errorMessage), 10000);
      }
    } catch (error) {
      showErrorMessage(
        errorMessage,
        'Ошибка соединения с сервером. Проверьте подключение к интернету',
      );
      setTimeout(() => hideMessage(errorMessage), 10000);
    }
  });

  newPasswordForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const newPassword = newPasswordForm.newPassword.value;
    const confirmPassword = newPasswordForm.confirmNewPassword.value;
    const errorMessage = document.getElementById('newPasswordErrorMessage');

    hideMessage(errorMessage);

    if (!validatePassword(newPassword)) {
      showErrorMessage(
        errorMessage,
        'Пароль должен содержать не менее 6 символов',
      );
      return;
    }

    if (newPassword !== confirmPassword) {
      showErrorMessage(errorMessage, 'Пароли не совпадают');
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
          new_password: newPassword,
        }),
      });

      if (response.ok) {
        resetSection.style.display = 'none';
        loginSection.style.display = 'block';
        resetPasswordForm.reset();
        newPasswordForm.reset();
        const loginErrorMessage = document.getElementById('errorMessage');
        showSuccessMessage(
          loginErrorMessage,
          'Пароль успешно изменен! Теперь вы можете войти.',
        );
        resetEmail = '';
        resetSecretWord = '';
      } else {
        const data = await response.json();
        const errorMsg = getErrorMessage(
          data,
          'Ошибка при смене пароля. Попробуйте позже',
        );
        showErrorMessage(errorMessage, errorMsg);
      }
    } catch (error) {
      showErrorMessage(
        errorMessage,
        'Ошибка соединения с сервером. Проверьте подключение к интернету',
      );
    }
  });

  backToStepOne.addEventListener('click', () => {
    stepTwo.style.display = 'none';
    stepOne.style.display = 'block';
    hideMessage(document.getElementById('newPasswordErrorMessage'));
    newPasswordForm.reset();
  });
});
