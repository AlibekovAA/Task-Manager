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

document.addEventListener('DOMContentLoaded', () => {
    initializeInfoButton();
});
