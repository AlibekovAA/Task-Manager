document.addEventListener('DOMContentLoaded', () => {
  const registerForm = document.getElementById('registerForm');
  const errorMessage = document.getElementById('errorMessage');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const secretWordInput = document.getElementById('secretWord');

  emailInput.addEventListener('input', () => {
    if (!validateEmail(emailInput.value)) {
      emailInput.setCustomValidity('Введите корректный email адрес');
      showErrorMessage(errorMessage, 'Введите корректный email адрес');
    } else {
      emailInput.setCustomValidity('');
      hideMessage(errorMessage);
    }
  });

  passwordInput.addEventListener('input', () => {
    if (!validatePassword(passwordInput.value)) {
      passwordInput.setCustomValidity(
        'Пароль должен содержать не менее 6 символов',
      );
      showErrorMessage(
        errorMessage,
        'Пароль должен содержать не менее 6 символов',
      );
    } else {
      passwordInput.setCustomValidity('');
      hideMessage(errorMessage);
    }
  });

  secretWordInput.addEventListener('input', () => {
    if (!validateSecretWord(secretWordInput.value)) {
      secretWordInput.setCustomValidity(
        'Кодовое слово должно содержать от 3 до 50 символов',
      );
      showErrorMessage(
        errorMessage,
        'Кодовое слово должно содержать от 3 до 50 символов',
      );
    } else {
      secretWordInput.setCustomValidity('');
      hideMessage(errorMessage);
    }
  });

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideMessage(errorMessage);

    const formData = new FormData(registerForm);
    const email = formData.get('email');
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');
    const secretWord = formData.get('secretWord');

    if (!validateEmail(email)) {
      showErrorMessage(errorMessage, 'Введите корректный email адрес');
      return;
    }

    if (!validatePassword(password)) {
      showErrorMessage(
        errorMessage,
        'Пароль должен содержать не менее 6 символов',
      );
      return;
    }

    if (password !== confirmPassword) {
      showErrorMessage(errorMessage, 'Пароли не совпадают');
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
      const response = await fetch('/users/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.toLowerCase(),
          password: password,
          secret_word: secretWord,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        window.location.href = '/?registered=true';
      } else {
        let errorMsg = 'Ошибка при регистрации';

        if (response.status === 422) {
          const errors = data.detail;
          if (Array.isArray(errors)) {
            const passwordError = errors.find((error) =>
              error.loc?.includes('password'),
            );
            const emailError = errors.find((error) =>
              error.loc?.includes('email'),
            );

            if (passwordError) {
              errorMsg = 'Пароль должен содержать не менее 6 символов';
            } else if (emailError) {
              errorMsg = 'Пользователь с таким email уже существует';
            } else {
              errorMsg = getErrorMessage(
                data,
                'Проверьте правильность введенных данных',
              );
            }
          } else {
            errorMsg = getErrorMessage(data, errorMsg);
          }
        } else {
          errorMsg = getErrorMessage(data, errorMsg);
        }

        showErrorMessage(errorMessage, errorMsg);
      }
    } catch (error) {
      console.error('Error:', error);
      showErrorMessage(
        errorMessage,
        'Ошибка соединения с сервером. Проверьте подключение к интернету',
      );
    }
  });
});
