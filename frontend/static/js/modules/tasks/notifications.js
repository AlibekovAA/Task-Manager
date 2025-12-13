const notificationTracker = {
  shownNotifications: new Set(),
  clearOldNotifications: function () {
    this.shownNotifications.clear();
  },
};

setInterval(() => {
  notificationTracker.clearOldNotifications();
}, 60 * 60 * 1000);

function showNotification(message, type = 'error') {
  const notification = document.getElementById('notification');
  if (!notification) return;

  const notificationKey = `${message}-${type}`;

  if (notificationTracker.shownNotifications.has(notificationKey)) {
    return;
  }

  const content = notification.querySelector('.notification-content');
  const notificationMessage = notification.querySelector(
    '.notification-message',
  );

  if (!content || !notificationMessage) return;

  notificationMessage.textContent = message;

  content.classList.remove('success', 'error', 'urgent');
  content.classList.add(type);
  notification.classList.add('show');

  if (type === 'urgent') {
    const audio = new Audio('/static/sounds/notification.mp3');
    audio.volume = 0.3;
    audio
      .play()
      .catch(() =>
        console.log('Автовоспроизведение звука заблокировано браузером'),
      );
  }

  notificationTracker.shownNotifications.add(notificationKey);

  setTimeout(() => {
    notification.classList.remove('show');
  }, 5000);
}

function hideNotification() {
  const notification = document.getElementById('notification');
  if (notification) {
    notification.classList.remove('show');
  }
}

window.showNotification = showNotification;
window.hideNotification = hideNotification;
