function initializeInfoButton() {
    const infoButton = document.getElementById('infoButton');
    const authorModal = document.getElementById('authorModal');
    const closeModal = document.getElementById('closeModal');

    if (infoButton && authorModal && closeModal) {
        infoButton.addEventListener('click', () => {
            authorModal.style.display = 'block';
        });

        closeModal.addEventListener('click', () => {
            authorModal.style.display = 'none';
        });

        window.addEventListener('click', (event) => {
            if (event.target === authorModal) {
                authorModal.style.display = 'none';
            }
        });
    } else {
        console.error('Не удалось найти элементы для кнопки информации об авторе');
    }
}

document.addEventListener('DOMContentLoaded', initializeInfoButton);
