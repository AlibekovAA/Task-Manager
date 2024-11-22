async function loadAuthorInfo() {
    try {
        const response = await fetch('/static/templates/author-info.html');
        if (!response.ok) throw new Error('Не удалось загрузить информацию об авторе');
        const html = await response.text();
        const authorModal = document.getElementById('authorModal');
        if (!authorModal) throw new Error('Элемент authorModal не найден');
        authorModal.innerHTML = html;
        return true;
    } catch (error) {
        console.error(error);
        return false;
    }
}

function toggleModal(modal, show = true) {
    if (!modal) {
        console.error('Модальное окно не найдено');
        return;
    }
    modal.style.display = show ? 'block' : 'none';
    if (show) {
        void modal.offsetWidth;
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    } else {
        modal.classList.remove('active');
        setTimeout(() => document.body.style.overflow = '', 300);
    }
}

async function initializeInfoButton() {
    const infoButton = document.getElementById('infoButton');
    const authorModal = document.getElementById('authorModal');
    const closeModal = document.getElementById('closeModal');

    if (!infoButton || !authorModal || !closeModal) {
        console.error('Не удалось найти необходимые элементы');
        return;
    }

    if (!(await loadAuthorInfo())) {
        console.error('Не удалось загрузить информацию об авторе');
        return;
    }

    infoButton.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleModal(authorModal, true);
    });

    closeModal.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        toggleModal(authorModal, false);
    });

    authorModal.addEventListener('click', (event) => {
        if (event.target === authorModal) {
            toggleModal(authorModal, false);
        }
    });
}

document.addEventListener('DOMContentLoaded', initializeInfoButton);
