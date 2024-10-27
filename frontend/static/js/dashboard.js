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

    function calculateFuseProgress(dueDate, createdAt) {
        const now = new Date();
        const due = new Date(dueDate);
        const created = new Date(createdAt);

        const totalDuration = due.getTime() - created.getTime();
        const elapsed = now.getTime() - created.getTime();

        return 100 - Math.min(Math.max((elapsed / totalDuration) * 100, 0), 100);
    }

    function getFuseClass(progress) {
        if (progress <= 30) return 'urgent';
        if (progress <= 70) return 'medium';
        return 'safe';
    }

    function formatTimeLeft(timeLeft) {
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
        if (progress <= 30) {
            return `⚠️ Срочно! (${formatTimeLeft(timeLeft)})`;
        }
        if (progress <= 70) {
            return `⚡ Внимание (${formatTimeLeft(timeLeft)})`;
        }
        return `✓ В работе (${formatTimeLeft(timeLeft)})`;
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

                    const progress = calculateFuseProgress(task.due_date, task.created_at);
                    const fuseClass = getFuseClass(progress);
                    const fuseLabel = getFuseLabel(progress);

                    fuseHtml = `
                        <div class="fuse-container">
                            <div class="fuse-label ${fuseClass}">${fuseLabel} (${Math.round(progress)}%)</div>
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
        const fuseContainer = taskElement.querySelector('.fuse-container');
        const fuse = taskElement.querySelector('.fuse');
        const fuseLabel = taskElement.querySelector('.fuse-label');

        if (!dueDate) {
            fuseContainer.style.display = 'none';
            return;
        }

        const now = new Date();
        const due = new Date(dueDate);
        const taskCreatedAt = new Date(taskElement.dataset.createdAt);

        const totalDuration = due - taskCreatedAt;
        const timeLeft = due - now;
        let percentLeft = (timeLeft / totalDuration) * 100;
        percentLeft = Math.max(0, Math.min(100, percentLeft));

        const fuseClass = getFuseClass(percentLeft);
        const fuseLabelText = getFuseLabel(percentLeft, timeLeft);

        fuse.className = `fuse ${fuseClass}`;
        fuseLabel.className = `fuse-label ${fuseClass}`;

        if (percentLeft === 0) {
            taskElement.classList.add('expired');
            fuseLabel.textContent = '❌ Просрочено!';
        } else {
            taskElement.classList.remove('expired');
            fuseLabel.textContent = fuseLabelText;
        }

        fuse.style.width = `${percentLeft}%`;
        fuseContainer.style.display = 'block';
    }

    function renderTask(task) {
        const taskElement = document.createElement('div');
        taskElement.className = `task-item${task.completed ? ' completed' : ''}`;
        taskElement.dataset.createdAt = task.created_at;

        taskElement.innerHTML = `
            <div class="task-info">
                <h3>${task.title}</h3>
                <p>${task.description || ''}</p>
                ${task.due_date ? `<p class="due-date">Срок: ${new Date(task.due_date).toLocaleString('ru-RU')}</p>` : ''}
                <div class="fuse-container">
                    <div class="fuse"></div>
                </div>
            </div>
            <div class="task-actions">
                <button class="btn-success ${task.completed ? 'completed' : ''} ${task.due_date && !task.completed ? 'disabled' : ''}"
                        onclick="toggleTaskComplete(${task.id}, ${task.completed})"
                        ${task.due_date && !task.completed ? 'disabled' : ''}>
                    ${task.completed ? 'Отменить выполнение' : 'Выполнить'}
                </button>
                <button class="btn-secondary" onclick="editTask(${task.id})">Изменить</button>
                <button class="btn-danger" onclick="showDeleteConfirmModal(${task.id})">Удалить</button>
            </div>
        `;

        if (task.due_date) {
            updateFuse(taskElement, task.due_date);
        }

        return taskElement;
    }

    // Обновляем все фитили каждую секунду
    setInterval(() => {
        document.querySelectorAll('.task-item').forEach(taskElement => {
            const dueDate = taskElement.querySelector('.due-date');
            if (dueDate) {
                const dueDateText = dueDate.textContent.split(': ')[1];
                updateFuse(taskElement, new Date(dueDateText));
            }
        });
    }, 1000);

});
