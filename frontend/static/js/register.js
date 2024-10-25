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
                errorMessage.textContent = data.detail || 'Ошибка при регистрации';
            }
        } catch (error) {
            errorMessage.textContent = 'Ошибка соединения с сервером';
            console.error('Error:', error);
        }
    });
});
