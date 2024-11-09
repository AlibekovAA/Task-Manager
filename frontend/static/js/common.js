async function loadAuthorInfo() {
    try {
        const response = await fetch('/static/templates/author-info.html');
        const html = await response.text();
        const authorModal = document.getElementById('authorModal');
        authorModal.innerHTML = html;
        return true;
    } catch (error) {
        console.error('Ошибка при загрузке информации об авторе:', error);
        return false;
    }
}

async function initializeInfoButton() {
    const infoButton = document.getElementById('infoButton');
    const authorModal = document.getElementById('authorModal');

    if (!infoButton || !authorModal) {
        console.error('Не удалось найти необходимые элементы для кнопки информации об авторе.');
        return;
    }

    const loaded = await loadAuthorInfo();
    if (!loaded) return;

    const closeModal = document.getElementById('closeModal');

    infoButton.addEventListener('click', () => showModal(authorModal));
    closeModal.addEventListener('click', () => hideModal(authorModal));
    window.addEventListener('click', (event) => {
        if (event.target === authorModal) {
            hideModal(authorModal);
        }
    });
}

function showModal(modal) {
    modal.style.display = 'block';
}

function hideModal(modal) {
    modal.style.display = 'none';
}

function initializePasswordToggles() {
    const passwordFields = document.querySelectorAll('input[type="password"]');

    passwordFields.forEach(field => {
        const toggleButton = document.createElement('button');
        toggleButton.type = 'button';
        toggleButton.className = 'password-toggle';
        toggleButton.innerHTML = '<i class="fas fa-eye"></i>';

        const wrapper = document.createElement('div');
        wrapper.className = 'password-field-wrapper';
        field.parentNode.insertBefore(wrapper, field);
        wrapper.appendChild(field);
        wrapper.appendChild(toggleButton);

        toggleButton.addEventListener('click', () => {
            const type = field.type === 'password' ? 'text' : 'password';
            field.type = type;
            toggleButton.innerHTML = type === 'password' ?
                '<i class="fas fa-eye"></i>' :
                '<i class="fas fa-eye-slash"></i>';
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initializeInfoButton();
    initializePasswordToggles();
});
