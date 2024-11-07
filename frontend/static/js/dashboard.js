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
    const filterBtn = document.getElementById('filterBtn');
    const filterMenu = document.querySelector('.filter-menu');
    const filterTypes = document.querySelectorAll('.filter-type');
    const filterOptions = document.querySelectorAll('.filter-options');
    const exportBtn = document.getElementById('exportBtn');
    const exportMenu = document.querySelector('.export-menu');

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
                adminMenuItem.style.display = userData.role === 'admin' ? 'block' : 'none';
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

    function calculateFuseProgress(DueDate, StartDate) {
        const now = new Date();
        const startDateObj = new Date(StartDate);
        const dueDateObj = new Date(DueDate);

        const differenceInMilliseconds = dueDateObj - startDateObj;
        const differenceInMinutes = Math.floor(differenceInMilliseconds / 60000);
        const initialTotalTime = Math.floor((dueDateObj - now) / 60000);
        const progress = (initialTotalTime / differenceInMinutes) * 100;
        return Math.min(progress, 100);
    }

    function getFuseClass(progress) {
        if (progress <= 30) return 'urgent';
        if (progress <= 60) return 'medium';
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
            return `${minutes + 1} мин.`;
        }
    }

    function getFuseLabel(progress, timeLeft) {
        if (timeLeft <= 0) {
            return '⚠️ Просрочено!';
        }

        const timeLeftStr = formatTimeLeft(timeLeft);

        if (progress <= 30) {
            return `⚠️ Срочно! (${timeLeftStr})`;
        }
        if (progress <= 70) {
            return `⚡ Внимание  (${timeLeftStr})`;
        }
        return `✓ В работе  (${timeLeftStr})`;
    }

    const sortBtn = document.getElementById('sortBtn');
    const sortMenu = document.querySelector('.sort-menu');
    let currentSort = { field: null, order: null };

    sortBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        sortMenu.classList.toggle('active');
        filterMenu.classList.remove('active');
        exportMenu.classList.remove('active');
    });

    document.addEventListener('click', (e) => {
        if (!sortMenu.contains(e.target) && !sortBtn.contains(e.target)) {
            sortMenu.classList.remove('active');
        }
    });

    document.querySelectorAll('.sort-option').forEach(option => {
        option.addEventListener('click', async () => {
            const sortField = option.dataset.sort;
            const sortOrder = option.dataset.order;

            currentSort = { field: sortField, order: sortOrder };
            await loadTasks();
            sortMenu.classList.remove('active');
        });
    });

    function renderTasks(tasks) {
        tasksList.innerHTML = '';

        if (!tasks || tasks.length === 0) {
            tasksList.innerHTML = '<div class="no-tasks-message">Список задач пуст. Нажмите "Добавить задачу" чтобы создать новую задачу.</div>';
            return;
        }

        if (currentSort.field) {
            tasks.sort((a, b) => {
                let comparison = 0;

                if (currentSort.field === 'priority') {
                    comparison = b.priority - a.priority;
                } else if (currentSort.field === 'due_date') {
                    const dateA = a.due_date ? new Date(a.due_date) : new Date(8640000000000000);
                    const dateB = b.due_date ? new Date(b.due_date) : new Date(8640000000000000);
                    comparison = dateA - dateB;
                }

                return currentSort.order === 'desc' ? -comparison : comparison;
            });
        }

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
                    <div class="task-header">
                        <h3>${task.title}</h3>
                        <span class="priority-${task.priority || 3}">${getPriorityLabel(task.priority || 3)}</span>
                    </div>
                    <p>${task.description || ''}</p>
                    ${dueDate ? `<p class="due-date ${isExpired ? 'expired' : ''}">Срок: ${dueDate}</p>` : ''}
                    ${fuseHtml}
                </div>
                <div class="task-actions">
                    <button class="action-btn complete-btn ${task.completed ? 'completed' : ''} ${isExpired ? 'disabled' : ''}"
                            onclick="toggleTaskComplete(${task.id}, ${task.completed})"
                            ${isExpired ? 'disabled' : ''}>
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="action-btn edit-btn" onclick="editTask(${task.id})">
                        <i class="fas fa-pencil-alt"></i>
                    </button>
                    <button class="action-btn delete-btn" onclick="showDeleteConfirmModal(${task.id})">
                        <i class="fas fa-times"></i>
                    </button>
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

    addTaskBtn.addEventListener('click', async () => {
        document.querySelector('#taskModal h3').textContent = 'Новая задача';
        taskForm.reset();

        if (userRole === 'pm') {
            assigneeGroup.style.display = 'block';
            if (defaultUsers.length === 0) {
                await loadDefaultUsers();
            }
        }

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
                taskForm.priority.value = task.priority || 3;

                if (userRole === 'pm' && taskAssignee) {
                    taskAssignee.value = task.user_id || '';
                }

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

        if (userRole === 'pm' && !taskAssignee.value) {
            showNotification('Пожалуйста, выберите пользователя для назначения задачи', 'error');
            return;
        }

        const selectedPriority = parseInt(document.getElementById('taskPriority').value);
        const dueDate = document.getElementById('taskDueDate').value;

        if (dueDate) {
            const selectedDate = new Date(dueDate);
            const now = new Date();

            if (selectedDate < now) {
                showNotification('Дата выполнения не может быть в прошлом', 'error');
                return;
            }
        }

        const formData = {
            title: document.getElementById('taskTitle').value,
            priority: selectedPriority,
            description: document.getElementById('taskDescription').value,
            due_date: dueDate || null
        };

        if (userRole === 'pm' && taskAssignee.value) {
            formData.user_id = parseInt(taskAssignee.value);
        }

        try {
            const url = editingTaskId ? `/tasks/${editingTaskId}` : '/tasks/';
            const method = editingTaskId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const result = await response.json();

                if (result.priority !== selectedPriority) {
                    console.error('Priority mismatch:', {
                        sent: selectedPriority,
                        received: result.priority
                    });
                }

                taskModal.classList.remove('active');
                taskForm.reset();
                await loadTasks();
                showNotification(
                    editingTaskId ? 'Задача успешно обновлена!' : 'Задача успешно создана!',
                    'success'
                );
                editingTaskId = null;
            } else {
                const errorData = await response.json();
                showNotification(errorData.detail || 'Ошибка при сохранении задачи', 'error');
            }
        } catch (error) {
            console.error('Error creating/updating task:', error);
            showNotification('Ошибка при сохранении задачи', 'error');
        }
    });

    let userRole = null;
    let defaultUsers = [];
    const assigneeGroup = document.getElementById('assigneeGroup');
    const taskAssignee = document.getElementById('taskAssignee');

    async function checkUserRole() {
        try {
            const response = await fetch('/users/me/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                userRole = userData.role;
                adminMenuItem.style.display = userData.role === 'admin' ? 'block' : 'none';

                if (userRole === 'pm') {
                    console.log('User is PM, showing assignee field');
                    assigneeGroup.style.display = 'block';
                    await loadDefaultUsers(userData.id);
                }
            } else if (response.status === 401) {
                localStorage.removeItem('access_token');
                window.location.href = '/';
            }
        } catch (error) {
            console.error('Error checking user role:', error);
        }
    }

    async function loadDefaultUsers(currentUserId) {
        try {
            const response = await fetch('/users/', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const users = await response.json();
                defaultUsers = users.filter(user => user.role === 'user' && user.is_active);

                console.log('Loaded users:', defaultUsers);

                const currentPM = users.find(user => user.id === currentUserId);
                if (currentPM) {
                    taskAssignee.innerHTML = `<option value="${currentPM.id}" selected>${currentPM.email} (Вы)</option>` +
                        defaultUsers.map(user =>
                            `<option value="${user.id}">${user.email}</option>`
                        ).join('');
                } else {
                    taskAssignee.innerHTML = '<option value="">Выберите пользователя</option>' +
                        defaultUsers.map(user =>
                            `<option value="${user.id}">${user.email}</option>`
                        ).join('');
                }
            }
        } catch (error) {
            console.error('Error loading users:', error);
            showNotification('Ошибка при загрузке списка пользователей', 'error');
        }
    }

    async function createTask(taskData) {
        try {
            const userId = userRole === 'pm' && taskAssignee.value ?
                parseInt(taskAssignee.value) :
                null;

            const response = await fetch('/tasks/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...taskData,
                    user_id: userId
                })
            });

            if (response.ok) {
                const newTask = await response.json();
                showNotification('Задача успешно создана', 'success');
                return newTask;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Ошибка при создании задачи');
            }
        } catch (error) {
            console.error('Error creating task:', error);
            showNotification(error.message || 'Ошибка при создании задачи', 'error');
            throw error;
        }
    }

    await checkUserRole();
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
                } else if ((dueDate - now) <= 60 * 60 * 1000) {
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

        const percentLeft = (totalTime / (24 * 60 * 60 * 1000)) * 100;
        const width = Math.min(Math.max(100 - percentLeft, 0), 100);
        fuseElement.style.width = `${width}%`;

        if (totalTime < (24 * 60 * 60 * 1000 * 0.25)) {
            fuseElement.style.background = 'linear-gradient(90deg, #ff0000, #ff0000)';
        } else if (totalTime < (24 * 60 * 60 * 1000 * 0.5)) {
            fuseElement.style.background = 'linear-gradient(90deg, #ff0000, #ff5e00)';
        } else {
            fuseElement.style.background = 'linear-gradient(90deg, #ff0000, #ff5e00, #ffcc00)';
        }
    }

    function getPriorityLabel(priority) {
        const priorities = {
            1: 'Критический',
            2: 'Высокий',
            3: 'Средний',
            4: 'Низкий'
        };
        return priorities[priority] || 'Средний';
    }

    setInterval(() => {
        document.querySelectorAll('.task-item').forEach(taskElement => {
            const dueDate = taskElement.querySelector('.due-date');
            if (dueDate) {
                const dueDateText = dueDate.textContent.split(': ')[1];
                updateFuse(taskElement, new Date(dueDateText));
            }
        });
    }, 60000);

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

    let currentFilter = { type: null, value: null };

    filterBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        filterMenu.classList.toggle('active');
        sortMenu.classList.remove('active');
        exportMenu.classList.remove('active');
    });

    filterTypes.forEach(type => {
        type.addEventListener('click', () => {
            const filterType = type.dataset.type;
            filterOptions.forEach(option => {
                option.style.display = option.id === `${filterType}Filter` ? 'block' : 'none';
            });
        });
    });

    document.querySelector('#nameFilter input').addEventListener('input', (e) => {
        currentFilter = { type: 'name', value: e.target.value };
        applyFilters();
    });

    document.querySelector('#priorityFilter select').addEventListener('change', (e) => {
        currentFilter = { type: 'priority', value: e.target.value };
        applyFilters();
    });

    document.querySelector('#statusFilter select').addEventListener('change', (e) => {
        currentFilter = { type: 'status', value: e.target.value };
        applyFilters();
    });

    function applyFilters() {
        const tasks = document.querySelectorAll('.task-item');

        tasks.forEach(task => {
            let show = true;

            if (currentFilter.type === 'name' && currentFilter.value) {
                const title = task.querySelector('h3').textContent.toLowerCase();
                const regex = new RegExp(currentFilter.value.toLowerCase());
                show = regex.test(title);
            }

            if (currentFilter.type === 'priority' && currentFilter.value) {
                const priority = task.querySelector('[class^="priority-"]').className.match(/priority-(\d)/)[1];
                show = priority === currentFilter.value;
            }

            if (currentFilter.type === 'status' && currentFilter.value) {
                const isCompleted = task.classList.contains('completed');
                show = (currentFilter.value === 'completed' && isCompleted) ||
                       (currentFilter.value === 'active' && !isCompleted);
            }

            task.style.display = show ? 'block' : 'none';
        });
    }

    document.addEventListener('click', (e) => {
        if (!filterMenu.contains(e.target) && !filterBtn.contains(e.target)) {
            filterMenu.classList.remove('active');
        }
    });

    exportBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        exportMenu.classList.toggle('active');
        filterMenu.classList.remove('active');
        sortMenu.classList.remove('active');
    });

    document.addEventListener('click', (e) => {
        if (!exportMenu.contains(e.target) && !exportBtn.contains(e.target)) {
            exportMenu.classList.remove('active');
        }
    });

    document.querySelectorAll('.export-option').forEach(option => {
        option.addEventListener('click', async () => {
            const type = option.dataset.type;

            try {
                const response = await fetch('/tasks/', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                    }
                });

                if (!response.ok) {
                    throw new Error('Ошибка получения задач');
                }

                const tasks = await response.json();

                if (tasks.length === 0) {
                    showNotification('Нет задач для экспорта', 'warning');
                    return;
                }

                const tasksData = tasks.map(task => ({
                    'Название': task.title,
                    'Описание': task.description || '',
                    'Приоритет': getPriorityLabel(task.priority),
                    'Срок': task.due_date ? new Date(task.due_date).toLocaleString('ru-RU') : '',
                    'Статус': task.completed ? 'Завершена' : 'В процессе'
                }));

                if (type === 'excel') {
                    exportToExcel(tasksData);
                }

            } catch (error) {
                console.error('Ошибка экспорта:', error);
                showNotification('Ошибка при экспорте данных', 'error');
            }

            exportMenu.classList.remove('active');
        });
    });

    function exportToExcel(data) {
        const worksheet = XLSX.utils.json_to_sheet(data);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, "Задачи");

        const maxWidth = data.reduce((w, r) => Math.max(w, Object.values(r).join('').length), 10);
        const colWidth = Math.min(maxWidth, 50);
        worksheet['!cols'] = Object.keys(data[0]).map(() => ({ wch: colWidth }));

        XLSX.writeFile(workbook, "tasks.xlsx");
        showNotification('Задачи успешно экспортированы в Excel', 'success');
    }

});
