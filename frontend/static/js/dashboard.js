document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/';
        return;
    }

    const tasksList = document.getElementById('tasksList');
    const addTaskBtn = document.getElementById('addTaskBtn');
    const taskModal = document.getElementById('taskModal');
    const taskForm = document.getElementById('taskForm');
    const cancelTaskBtn = document.getElementById('cancelTaskBtn');
    const logoutBtn = document.getElementById('logoutBtn');
    const deleteConfirmModal = document.getElementById('deleteConfirmModal');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    const adminMenuItem = document.getElementById('adminMenuItem');
    let taskToDelete = null;

    const notification = document.getElementById('notification');
    const notificationMessage = notification.querySelector('.notification-message');
    const notificationClose = notification.querySelector('.notification-close');

    const notificationTracker = {
        shownNotifications: new Set(),
        clearOldNotifications: function() {
            this.shownNotifications.clear();
        }
    };

    setInterval(() => {
        notificationTracker.clearOldNotifications();
    }, 60 * 60 * 1000);

    async function loadUserProfile() {
        try {
            const response = await fetch('/users/me/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                if (userData.role === 'admin') {
                    if (adminMenuItem) {
                        adminMenuItem.style.display = 'block';
                    }
                } else {
                    if (adminMenuItem) {
                        adminMenuItem.style.display = 'none';
                    }
                }
            } else if (response.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/';
            }
        } catch (error) {
            console.error('Error loading profile:', error);
        }
    }

    async function loadTasks() {
        try {
            const response = await fetch('/tasks/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const tasks = await response.json();
                renderTasks(tasks);
                checkDeadlines(tasks);
            } else if (response.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/';
            }
        } catch (error) {
            console.error('Error loading tasks:', error);
        }
    }

    function calculateFuseProgress(dueDate) {
        const now = new Date();
        const due = new Date(dueDate);
        const totalTime = due.getTime() - now.getTime();

        if (totalTime <= 0) {
            return 0;
        }

        const maxTime = 7 * 24 * 60 * 60 * 1000;
        const progress = Math.min((totalTime / maxTime) * 100, 100);

        return progress;
    }

    function getFuseClass(progress) {
        if (progress <= 30) return 'urgent';
        if (progress <= 70) return 'medium';
        return 'safe';
    }

    function formatTimeLeft(timeLeft) {
        if (isNaN(timeLeft)) {
            return 'время не задано';
        }

        const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));

        if (days > 0) {
            return `${days} дн. ${hours} ч.`;
        } else if (hours > 0) {
            return `${hours} ч. ${minutes} мин.`;
        } else {
            return `${minutes} мин.`;
        }
    }

    function getFuseLabel(progress, timeLeft) {
        if (timeLeft <= 0) {
            return '⚠️ Просрочено!';
        }

        const timeLeftStr = formatTimeLeft(timeLeft);

        if (progress <= 30) {
            return `⚠️ Срочно!`;
        }
        if (progress <= 70) {
            return `⚡ Внимание`;
        }
        return `✓ В работе`;
    }

    function renderTasks(tasks) {
        tasksList.innerHTML = '';
        tasks.forEach(task => {
            const taskElement = document.createElement('div');
            const isExpired = task.due_date && new Date(task.due_date) < new Date() && !task.completed;
            taskElement.className = `task-item ${task.completed ? 'completed' : ''} ${isExpired ? 'expired' : ''}`;

            let dueDate = '';
            let fuseHtml = '';

            if (task.due_date && !task.completed) {
                try {
                    const date = new Date(task.due_date);
                    dueDate = date.toLocaleString('ru-RU', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });

                    const progress = calculateFuseProgress(task.due_date);
                    const fuseClass = getFuseClass(progress);
                    const timeLeft = new Date(task.due_date) - new Date();
                    const fuseLabel = getFuseLabel(progress, timeLeft);

                    fuseHtml = `
                        <div class="fuse-container">
                            <div class="fuse-label ${fuseClass}">${fuseLabel}</div>
                            <div class="fuse ${fuseClass}" style="width: ${progress}%"></div>
                        </div>
                    `;
                } catch (error) {
                    console.error('Error formatting date:', error);
                }
            }

            taskElement.innerHTML = `
                <div class="task-info">
                    <h3>${task.title}</h3>
                    <p>${task.description || ''}</p>
                    ${dueDate ? `<p class="due-date ${isExpired ? 'expired' : ''}">Срок: ${dueDate}</p>` : ''}
                    ${fuseHtml}
                </div>
                <div class="task-actions">
                    <button class="btn-success ${task.completed ? 'completed' : ''} ${isExpired ? 'disabled' : ''}"
                            onclick="toggleTaskComplete(${task.id}, ${task.completed})"
                            ${isExpired ? 'disabled' : ''}>
                        ${task.completed ? 'Отменить выполнение' : 'Выполнить'}
                    </button>
                    <button class="btn-secondary" onclick="editTask(${task.id})">Изменить</button>
                    <button class="btn-danger" onclick="showDeleteConfirmModal(${task.id})">Удалить</button>
                </div>
            `;
            tasksList.appendChild(taskElement);
        });
    }

    function showNotification(message, type = 'error') {
        const notificationKey = `${message}-${type}`;

        if (notificationTracker.shownNotifications.has(notificationKey)) {
            return;
        }

        const content = notification.querySelector('.notification-content');
        notificationMessage.textContent = message;

        content.classList.remove('success', 'error', 'urgent');
        content.classList.add(type);
        notification.classList.add('show');

        if (type === 'urgent') {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.volume = 0.3;
            audio.play().catch(e => console.log('Автовоспроизведение звука заблокировано браузером'));
        }

        notificationTracker.shownNotifications.add(notificationKey);

        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }

    function hideNotification() {
        notification.classList.remove('show');
    }

    notificationClose.addEventListener('click', hideNotification);

    function showDeleteConfirmModal(taskId) {
        taskToDelete = taskId;
        deleteConfirmModal.classList.add('active');
    }

    function hideDeleteConfirmModal() {
        deleteConfirmModal.classList.remove('active');
        taskToDelete = null;
    }

    cancelDeleteBtn.addEventListener('click', hideDeleteConfirmModal);

    confirmDeleteBtn.addEventListener('click', async () => {
        if (taskToDelete) {
            await deleteTask(taskToDelete);
            hideDeleteConfirmModal();
        }
    });

    async function deleteTask(taskId) {
        try {
            const response = await fetch(`/tasks/${taskId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                await loadTasks();
            } else {
                console.error('Error deleting task:', await response.text());
            }
        } catch (error) {
            console.error('Error deleting task:', error);
        }
    }

    window.showDeleteConfirmModal = showDeleteConfirmModal;

    addTaskBtn.addEventListener('click', () => {
        taskModal.classList.add('active');
    });

    cancelTaskBtn.addEventListener('click', () => {
        taskModal.classList.remove('active');
        taskForm.reset();
    });

    let editingTaskId = null;

    window.editTask = async function(taskId) {
        editingTaskId = taskId;

        try {
            const response = await fetch(`/tasks/${taskId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const task = await response.json();

                taskForm.title.value = task.title;
                taskForm.description.value = task.description || '';
                if (task.due_date) {
                    const date = new Date(task.due_date);
                    const localDateTime = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
                        .toISOString()
                        .slice(0, 16);
                    taskForm.due_date.value = localDateTime;
                } else {
                    taskForm.due_date.value = '';
                }

                document.querySelector('#taskModal h3').textContent = 'Редактировать задачу';
                taskModal.classList.add('active');
            } else {
                showNotification('Ошибка при загрузке задачи', 'error');
            }
        } catch (error) {
            console.error('Error loading task:', error);
            showNotification('Ошибка при загрузке задачи', 'error');
        }
    };

    taskForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(taskForm);
        const dueDate = formData.get('due_date');

        if (dueDate) {
            const selectedDate = new Date(dueDate);
            const now = new Date();

            if (selectedDate < now) {
                showNotification('Дата и время выполнения не могут быть в прошлом', 'error');
                return;
            }
        }

        const taskData = {
            title: formData.get('title'),
            description: formData.get('description'),
            due_date: dueDate || null
        };

        try {
            const url = editingTaskId ? `/tasks/${editingTaskId}` : '/tasks/';
            const method = editingTaskId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(taskData)
            });

            if (response.ok) {
                taskModal.classList.remove('active');
                taskForm.reset();
                await loadTasks();
                showNotification(
                    editingTaskId ? 'Задача успешно обновлена' : 'Задача успешно создана',
                    'success'
                );
                editingTaskId = null;
                document.querySelector('#taskModal h3').textContent = 'Новая задача';
            } else {
                const errorData = await response.json();
                showNotification(errorData.detail || 'Ошибка при сохранении задачи', 'error');
            }
        } catch (error) {
            console.error('Error saving task:', error);
            showNotification('Ошибка при сохранении задачи', 'error');
        }
    });

    await loadUserProfile();
    await loadTasks();

    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('access_token');
        window.location.href = '/';
    });

    window.toggleTaskComplete = async function(taskId, currentStatus) {
        try {
            const response = await fetch(`/tasks/${taskId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    completed: !currentStatus
                })
            });

            if (response.ok) {
                await loadTasks();
                showNotification(
                    currentStatus ? 'Задача отмечена как невыполненная' : 'Задача выполнена!',
                    currentStatus ? 'error' : 'success'
                );
            } else {
                const errorData = await response.json();
                showNotification(errorData.detail || 'Ошибка при обновлении задачи', 'error');
            }
        } catch (error) {
            console.error('Error updating task:', error);
            showNotification('Ошибка при обновлении задачи');
        }
    };

    window.showNotification = showNotification;
    window.loadTasks = loadTasks;

    function checkDeadlines(tasks) {
        tasks.forEach(task => {
            if (task.due_date && !task.completed) {
                const dueDate = new Date(task.due_date);
                const now = new Date();

                if (now > dueDate) {
                    showNotification(
                        `Срок выполнения задачи "${task.title}" истёк!`,
                        'error'
                    );
                }
                else if ((dueDate - now) <= 60 * 60 * 1000) {
                    showNotification(
                        `До окончания срока выполнения задачи "${task.title}" осталось менее часа!`,
                        'urgent'
                    );
                }
            }
        });
    }

    setInterval(async () => {
        await loadUserProfile();
        await loadTasks();
    }, 30000);

    function updateFuse(taskElement, dueDate) {
        const fuseElement = taskElement.querySelector('.fuse');
        if (!fuseElement) return;

        const now = new Date();
        const due = new Date(dueDate);
        const totalTime = due.getTime() - now.getTime();

        if (totalTime <= 0) {
            fuseElement.style.width = '100%';
            fuseElement.style.background = '#ff0000';
            return;
        }

        const timeLeft = totalTime;
        const oneDay = 24 * 60 * 60 * 1000;
        const percentLeft = (timeLeft / oneDay) * 100;

        const width = Math.min(Math.max(100 - percentLeft, 0), 100);
        fuseElement.style.width = `${width}%`;

        if (timeLeft < oneDay * 0.25) {
            fuseElement.style.background = 'linear-gradient(90deg, #ff0000, #ff0000)';
        } else if (timeLeft < oneDay * 0.5) {
            fuseElement.style.background = 'linear-gradient(90deg, #ff0000, #ff5e00)';
        } else {
            fuseElement.style.background = 'linear-gradient(90deg, #ff0000, #ff5e00, #ffcc00)';
        }
    }

    function renderTask(task) {
        const taskElement = document.createElement('div');
        const isExpired = task.due_date && new Date(task.due_date) < new Date() && !task.completed;
        taskElement.className = `task-item ${task.completed ? 'completed' : ''} ${isExpired ? 'expired' : ''}`;
        taskElement.dataset.createdAt = task.created_at;

        let dueDate = '';
        let fuseHtml = '';

        if (task.due_date && !task.completed) {
            try {
                const date = new Date(task.due_date);
                dueDate = date.toLocaleString('ru-RU', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });

                const progress = calculateFuseProgress(task.due_date);
                const fuseClass = getFuseClass(progress);
                const timeLeft = new Date(task.due_date) - new Date();
                const fuseLabel = getFuseLabel(progress, timeLeft);

                fuseHtml = `
                    <div class="fuse-container">
                        <div class="fuse-label ${fuseClass}">${fuseLabel}</div>
                        <div class="fuse ${fuseClass}" style="width: ${progress}%"></div>
                    </div>
                `;
            } catch (error) {
                console.error('Error formatting date:', error);
            }
        }

        taskElement.innerHTML = `
            <div class="task-info">
                <h3>${task.title}</h3>
                <p>${task.description || ''}</p>
                ${dueDate ? `<p class="due-date ${isExpired ? 'expired' : ''}">Срок: ${dueDate}</p>` : ''}
                ${fuseHtml}
            </div>
            <div class="task-actions">
                <button class="btn-success ${task.completed ? 'completed' : ''} ${isExpired ? 'disabled' : ''}"
                        onclick="toggleTaskComplete(${task.id}, ${task.completed})"
                        ${isExpired ? 'disabled' : ''}>
                    ${task.completed ? 'Отменить выполнение' : 'Выполнить'}
                </button>
                <button class="btn-secondary" onclick="editTask(${task.id})">Изменить</button>
                <button class="btn-danger" onclick="showDeleteConfirmModal(${task.id})">Удалить</button>
            </div>
        `;

        return taskElement;
    }

    setInterval(() => {
        document.querySelectorAll('.task-item').forEach(taskElement => {
            const dueDate = taskElement.querySelector('.due-date');
            if (dueDate) {
                const dueDateText = dueDate.textContent.split(': ')[1];
                updateFuse(taskElement, new Date(dueDateText));
            }
        });
    }, 1000);

    const taskDueDate = document.getElementById('taskDueDate');
    if (taskDueDate) {

    function setDefaultDueDate() {
        const now = new Date();
        const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);
        tomorrow.setMinutes(tomorrow.getMinutes() - tomorrow.getTimezoneOffset());
        taskDueDate.value = tomorrow.toISOString().slice(0, 16);
    }

    addTaskBtn.addEventListener('click', () => {
        setDefaultDueDate();
        taskModal.classList.add('active');
    });
    }

});
