# 🚀 Task Manager Pro

Современное веб-приложение для управления задачами с визуализацией дедлайнов и системой уведомлений.

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.23-red.svg)
![JWT](https://img.shields.io/badge/JWT-auth-orange.svg)
![SQLite](https://img.shields.io/badge/SQLite-3.43.0-purple.svg)

## 📋 Содержание

- [Особенности](#особенности)
- [Технологии](#технологии)
- [Установка](#установка)
- [База данных](#база-данных)
- [Автор](#автор)
- [Примеры](#примеры)

## ✨ Особенности

- 🔐 Безопасная аутентификация и авторизация с использованием JWT
- 📝 Полный CRUD для управления задачами
- ⏰ Визуализация дедлайнов с анимированным "горящим фитилем"
- 🔔 Умная система уведомлений о приближающихся дедлайнах
- 👤 Управление профилем пользователя
- 🎨 Современный и отзывчивый интерфейс

## 🛠 Технологии

### Backend
- **FastAPI** - современный асинхронный веб-фреймворк
- **SQLAlchemy** - мощный ORM для работы с базой данных
- **Pydantic** - валидация данных и сериализация
- **JWT** - безопасная аутентификация
- **Bcrypt** - надежное хеширование паролей
- **SQLite** - легкая и быстрая база данных

### Frontend
- **HTML5/CSS3** - современная семантическая верстка
- **JavaScript (ES6+)** - чистый JS без фреймворков
- **CSS Animations** - плавные анимации и визуальные эффекты
- **Responsive Design** - адаптивная верстка

## 💾 База данных

#### Users
| Поле          | Тип      | Описание                    | Ограничения                |
|---------------|----------|-----------------------------| ---------------------------|
| id            | INTEGER  | Первичный ключ             | PRIMARY KEY, AUTOINCREMENT |
| email         | VARCHAR  | Email пользователя         | UNIQUE, NOT NULL          |
| password_hash | VARCHAR  | Хеш пароля                 | NOT NULL                  |
| created_at    | DATETIME | Дата создания              | NOT NULL, DEFAULT NOW     |

#### Tasks
| Поле        | Тип      | Описание                    | Ограничения                |
|-------------|----------|-----------------------------| ---------------------------|
| id          | INTEGER  | Первичный ключ             | PRIMARY KEY, AUTOINCREMENT |
| title       | VARCHAR  | Название задачи            | NOT NULL                  |
| description | TEXT     | Описание задачи            | NULL                      |
| completed   | BOOLEAN  | Статус выполнения          | NOT NULL, DEFAULT FALSE   |
| due_date    | DATETIME | Срок выполнения            | NULL                      |
| created_at  | DATETIME | Дата создания              | NOT NULL, DEFAULT NOW     |
| user_id     | INTEGER  | Внешний ключ на Users      | FOREIGN KEY              |

## 👥 Автор

- [AlibekovAA](https://github.com/AlibekovAA)

## 📄 Примеры

![Login](example/login.jpg)
![Dashboard](example/dashboard.jpg)
![Profile](example/profile.jpg)
![Admin](example/admin.jpg)
![info](example/info.jpg)

---
⭐️ Star на GitHub — это помогает!
