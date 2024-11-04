function showModal(modal) {
    modal.style.display = 'block';
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

function hideModal(modal) {
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
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
