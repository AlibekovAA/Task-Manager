let userCache = {
  data: null,
  timestamp: null,
  TTL: 30000,
};

async function refreshToken() {
  try {
    const refresh_token = localStorage.getItem('refresh_token');
    if (!refresh_token) return false;

    const response = await fetch('/token/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token }),
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('access_token', data.access_token);
      return true;
    }
    return false;
  } catch {
    return false;
  }
}

async function fetchWithToken(url, options = {}) {
  let token = localStorage.getItem('access_token');

  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    const refreshed = await refreshToken();
    if (refreshed) {
      token = localStorage.getItem('access_token');
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${token}`,
        },
      });
    } else {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_role');
      window.location.href = '/';
      return response;
    }
  }

  return response;
}

function checkAuth() {
  const token = localStorage.getItem('access_token');
  if (!token) {
    window.location.href = '/';
    return false;
  }
  return true;
}

async function loadUserProfile(useCache = true) {
  if (useCache && userCache.data && userCache.timestamp) {
    const now = Date.now();
    if (now - userCache.timestamp < userCache.TTL) {
      return userCache.data;
    }
  }

  try {
    const response = await fetchWithToken('/users/me/');

    if (response.ok) {
      const userData = await response.json();
      userCache.data = userData;
      userCache.timestamp = Date.now();
      return userData;
    } else if (response.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_role');
      window.location.href = '/';
      return null;
    }
    return null;
  } catch (error) {
    console.error('Ошибка при загрузке профиля:', error);
    return null;
  }
}

function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_role');
  localStorage.removeItem('user_email');
  window.location.href = '/';
}

function validateEmail(email) {
  const emailPattern = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
  return emailPattern.test(email);
}

function validatePassword(password) {
  return password && password.length >= 6;
}

function validateSecretWord(secretWord) {
  return secretWord && secretWord.length >= 3 && secretWord.length <= 50;
}

function initializePasswordToggles() {
  document.querySelectorAll('.password-toggle').forEach((button) => {
    button.addEventListener('click', (e) => {
      const input = e.currentTarget.previousElementSibling;
      const icon = e.currentTarget.querySelector('i');

      if (input && icon) {
        if (input.type === 'password') {
          input.type = 'text';
          icon.classList.remove('fa-eye');
          icon.classList.add('fa-eye-slash');
        } else {
          input.type = 'password';
          icon.classList.remove('fa-eye-slash');
          icon.classList.add('fa-eye');
        }
      }
    });
  });
}

function showErrorMessage(element, message) {
  if (!element) return;

  element.textContent = message;
  element.style.display = 'block';
  element.style.color = '#ff3333';
  element.style.backgroundColor = '#ffe6e6';
  element.style.border = '1px solid #ff9999';
  element.style.borderRadius = '4px';
  element.style.padding = '10px';
  element.style.marginTop = '10px';
}

function showSuccessMessage(element, message) {
  if (!element) return;

  element.textContent = message;
  element.style.display = 'block';
  element.style.color = '#388e3c';
  element.style.backgroundColor = '#e8f5e9';
  element.style.border = '1px solid #81c784';
  element.style.borderRadius = '4px';
  element.style.padding = '10px';
  element.style.marginTop = '10px';
}

function hideMessage(element) {
  if (!element) return;
  element.style.display = 'none';
  element.textContent = '';
}

function getErrorMessage(error, defaultMessage = 'Произошла ошибка') {
  if (typeof error === 'string') {
    return error;
  }

  if (error?.detail) {
    if (typeof error.detail === 'string') {
      return error.detail;
    }
    if (Array.isArray(error.detail)) {
      return error.detail.map((e) => e.msg || e).join(', ');
    }
  }

  if (error?.message) {
    return error.message;
  }

  return defaultMessage;
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

async function initializeInfoButton() {
  const infoButton = document.getElementById('infoButton');
  const authorModal = document.getElementById('authorModal');

  if (!infoButton || !authorModal) {
    return;
  }

  const loaded = await loadAuthorInfo();
  if (!loaded) {
    return;
  }

  const closeModal = document.getElementById('closeModal');
  if (!closeModal) {
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

function formatDate(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatTimeLeft(timeLeft) {
  if (isNaN(timeLeft)) {
    return 'время не задано';
  }

  const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
  const hours = Math.floor(
    (timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60),
  );
  const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));

  if (days > 0) {
    return `${days} дн. ${hours} ч.`;
  } else if (hours > 0) {
    return `${hours} ч. ${minutes} мин.`;
  } else {
    return `${minutes + 1} мин.`;
  }
}

function getPriorityLabel(priority) {
  const priorities = {
    1: 'Критический',
    2: 'Высокий',
    3: 'Средний',
    4: 'Низкий',
  };
  return priorities[priority] || 'Средний';
}

function getStatusLabel(status) {
  const statuses = {
    0: 'Не взята в работу',
    1: 'В работе',
    2: 'Завершена',
  };
  return statuses[status] || 'Неизвестно';
}

function getFileIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase();
  const icons = {
    pdf: 'fa-file-pdf',
    doc: 'fa-file-word',
    docx: 'fa-file-word',
    jpg: 'fa-file-image',
    jpeg: 'fa-file-image',
    png: 'fa-file-image',
    gif: 'fa-file-image',
  };
  return icons[ext] || 'fa-file';
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initializeInfoButton();
    initializePasswordToggles();
  });
} else {
  initializeInfoButton();
  initializePasswordToggles();
}
