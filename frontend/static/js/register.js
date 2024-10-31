document.addEventListener('DOMContentLoaded', () => {
    const registerForm = document.getElementById('registerForm');
    const errorMessage = document.getElementById('errorMessage');

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(registerForm);
        const email = formData.get('email');
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');

        if (password !== confirmPassword) {
            errorMessage.textContent = 'Пароли не совпадают';
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
                    email: email,
                    password: password
                }),
            });

            const data = await response.json();

            if (response.ok) {
                window.location.href = '/?registered=true';
            } else {
                if (response.status === 422) {
                    const errors = data.detail;
                    const passwordError = errors.find(error =>
                        error.loc.includes('password')
                    );
                    const emailError = errors.find(error =>
                        error.loc.includes('email')
                    );

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
            }
        } catch (error) {
            errorMessage.textContent = 'Ошибка соединения с сервером';
            console.error('Error:', error);
        } finally {
            errorMessage.style.display = 'block';
        }
    });
});
