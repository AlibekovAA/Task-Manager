async function loadAuthorInfo() {
    try {
        const response = await fetch('/static/templates/author-info.html');
        const html = await response.text();
        const authorModal = document.getElementById('authorModal');
        if (!authorModal) {
            console.error('Элемент authorModal не найден');
            return false;
        }
        authorModal.innerHTML = html;
        return true;
    } catch (error) {
        console.error('Ошибка при загрузке информации об авторе:', error);
        return false;
    }
}

function showModal(modal) {
    if (!modal) {
        console.error('Модальное окно не найдено');
        return;
    }
    modal.style.display = 'block';
    void modal.offsetWidth;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function hideModal(modal) {
    if (!modal) {
        console.error('Модальное окно не найдено');
        return;
    }
    modal.classList.remove('active');
    setTimeout(() => {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }, 300);
}

async function initializeInfoButton() {
    const infoButton = document.getElementById('infoButton');
    const authorModal = document.getElementById('authorModal');

    if (!infoButton || !authorModal) {
        console.error('Не удалось найти необходимые элементы для кнопки информации об авторе.');
        return;
    }

    const loaded = await loadAuthorInfo();
    if (!loaded) {
        console.error('Не удалось загрузить информацию об авторе');
        return;
    }

    const closeModal = document.getElementById('closeModal');
    if (!closeModal) {
        console.error('Не удалось найти кнопку закрытия модального окна.');
        return;
    }

    infoButton.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        showModal(authorModal);
    });

    closeModal.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        hideModal(authorModal);
    });

    authorModal.addEventListener('click', (event) => {
        if (event.target === authorModal) {
            hideModal(authorModal);
        }
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initializeInfoButton();
    });
} else {
    initializeInfoButton();
}
