function showModal(modal) {
    modal.style.display = 'block';
}

function hideModal(modal) {
    modal.style.display = 'none';
}

function initializeInfoButton() {
    const infoButton = document.getElementById('infoButton');
    const authorModal = document.getElementById('authorModal');
    const closeModal = document.getElementById('closeModal');

    if (!infoButton || !authorModal || !closeModal) {
        console.error('Не удалось найти необходимые элементы для кнопки информации об авторе.');
        return;
    }

    infoButton.addEventListener('click', () => showModal(authorModal));
    closeModal.addEventListener('click', () => hideModal(authorModal));
    window.addEventListener('click', (event) => {
        if (event.target === authorModal) {
            hideModal(authorModal);
        }
    });
}

document.addEventListener('DOMContentLoaded', initializeInfoButton);
