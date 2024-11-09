document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    const errorMessage = document.getElementById('errorMessage');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const secretWordInput = document.getElementById('secretWord');

    const validateEmail = (email) => {
        const emailPattern = /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/;
        return emailPattern.test(email.toLowerCase());
    };

    const validatePassword = (password) => {
        return password.length >= 6;
    };

    const validateSecretWord = (secretWord) => {
        return secretWord.length >= 3 && secretWord.length <= 50;
    };

    emailInput.addEventListener('input', () => {
        if (!validateEmail(emailInput.value)) {
            emailInput.setCustomValidity('Введите корректный email адрес');
            errorMessage.textContent = 'Введите корректный email адрес';
            errorMessage.style.display = 'block';
        } else {
            emailInput.setCustomValidity('');
            errorMessage.style.display = 'none';
        }
    });

    passwordInput.addEventListener('input', () => {
        if (!validatePassword(passwordInput.value)) {
            passwordInput.setCustomValidity('Пароль должен содержать не менее 6 символов');
            errorMessage.textContent = 'Пароль должен содержать не менее 6 символов';
            errorMessage.style.display = 'block';
        } else {
            passwordInput.setCustomValidity('');
            errorMessage.style.display = 'none';
        }
    });

    secretWordInput.addEventListener('input', () => {
        if (!validateSecretWord(secretWordInput.value)) {
            secretWordInput.setCustomValidity('Кодовое слово должно содержать от 3 до 50 символов');
            errorMessage.textContent = 'Кодовое слово должно содержать от 3 до 50 символов';
            errorMessage.style.display = 'block';
        } else {
            secretWordInput.setCustomValidity('');
            errorMessage.style.display = 'none';
        }
    });

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        errorMessage.style.display = 'none';
        errorMessage.textContent = '';

        const formData = new FormData(registerForm);
        const email = formData.get('email');
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');
        const secretWord = formData.get('secretWord');

        if (!validateEmail(email)) {
            errorMessage.textContent = 'Введите корректный email адрес';
            errorMessage.style.display = 'block';
            return;
        }

        if (!validatePassword(password)) {
            errorMessage.textContent = 'Пароль должен содержать не менее 6 символов';
            errorMessage.style.display = 'block';
            return;
        }

        if (password !== confirmPassword) {
            errorMessage.textContent = 'Пароли не совпадают';
            errorMessage.style.display = 'block';
            return;
        }

        if (!validateSecretWord(secretWord)) {
            errorMessage.textContent = 'Кодовое слово должно содержать от 3 до 50 символов';
            errorMessage.style.display = 'block';
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
                    secret_word: secretWord
                }),
            });

            const data = await response.json();

            if (response.ok) {
                window.location.href = '/?registered=true';
            } else {
                if (response.status === 422) {
                    const errors = data.detail;
                    const passwordError = errors.find(error => error.loc.includes('password'));
                    const emailError = errors.find(error => error.loc.includes('email'));

                    if (passwordError) {
                        errorMessage.textContent = 'Пароль должен содержать не менее 6 символов';
                    } else if (emailError) {
                        errorMessage.textContent = 'Введите корректный email адрес';
                    } else {
                        errorMessage.textContent = 'Проверьте правильность введенных данных';
                    }
                } else {
                    errorMessage.textContent = data.detail || 'Ошибка при регистрации';
                }
                errorMessage.style.display = 'block';
            }
        } catch (error) {
            console.error('Error:', error);
            errorMessage.textContent = 'Ошибка соединения с сервером';
            errorMessage.style.display = 'block';
        }
    });
});
