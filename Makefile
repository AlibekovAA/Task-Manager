.PHONY: help up down start stop restart rebuild test clean logs down-volumes clean-docker fresh

help:
	@echo Available commands:
	@echo   make up, make start     - Start application via Docker Compose
	@echo   make down, make stop    - Stop containers
	@echo   make down-volumes       - Stop containers and remove volumes
	@echo   make restart            - Restart containers
	@echo   make rebuild            - Rebuild and start containers
	@echo   make clean-docker       - Remove all containers, images, volumes
	@echo   make fresh              - Full cleanup and rebuild from scratch
	@echo   make test               - Run tests
	@echo   make clean               - Clean all cache, logs, etc
	@echo   make logs                - Show container logs

ifeq ($(OS),Windows_NT)
    DOCKER_COMPOSE = docker-compose
    RM = del /Q /F
    RMDIR = rmdir /S /Q
    MKDIR = mkdir
else
    DOCKER_COMPOSE = docker-compose
    RM = rm -f
    RMDIR = rm -rf
    MKDIR = mkdir -p
endif

up start:
	$(DOCKER_COMPOSE) up -d

down stop:
	$(DOCKER_COMPOSE) down

down-volumes:
	$(DOCKER_COMPOSE) down -v

restart:
	$(DOCKER_COMPOSE) restart

rebuild:
	$(DOCKER_COMPOSE) up -d --build

clean-docker:
	@echo Stopping and removing containers...
	$(DOCKER_COMPOSE) down -v
	@echo Removing Docker images...
ifeq ($(OS),Windows_NT)
	@powershell -ExecutionPolicy Bypass -NoProfile -Command "docker images --format '{{.ID}}' -f 'reference=*task_manager*' | ForEach-Object { if ($$_) { docker rmi -f $$_ } }" 2>nul || true
	@powershell -ExecutionPolicy Bypass -NoProfile -Command "docker images --format '{{.ID}}' -f 'reference=fastapi*' | ForEach-Object { if ($$_) { docker rmi -f $$_ } }" 2>nul || true
else
	@docker images -q task_manager* | xargs -r docker rmi -f 2>/dev/null || true
	@docker images -q fastapi* | xargs -r docker rmi -f 2>/dev/null || true
endif
	@echo Removing unused Docker resources...
	@docker system prune -f
	@echo Docker cleanup completed!

fresh: clean-docker
	@echo Building fresh containers...
	$(DOCKER_COMPOSE) build --no-cache
	@echo Starting containers...
	$(DOCKER_COMPOSE) up -d
	@echo Fresh build completed!

test:
	py -m pytest --cov=backend --cov-report=html tests/

clean:
ifeq ($(OS),Windows_NT)
	@echo Cleaning Python cache...
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
	@for /r . %%f in (*.pyc) do @if exist "%%f" del /q /f "%%f" 2>nul
	@if exist .pytest_cache rmdir /s /q .pytest_cache 2>nul
	@if exist htmlcov rmdir /s /q htmlcov 2>nul
	@if exist .coverage del /q /f .coverage 2>nul
	@for /r . %%f in (*.log) do @if exist "%%f" del /q /f "%%f" 2>nul
	@echo Cleanup completed!
else
	@echo Cleaning Python cache...
	@find . -type d -name "__pycache__" -exec $(RMDIR) {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@$(RMDIR) .pytest_cache 2>/dev/null || true
	@$(RMDIR) htmlcov 2>/dev/null || true
	@$(RM) .coverage 2>/dev/null || true
	@find . -type f -name "*.log" -delete 2>/dev/null || true
	@echo Cleanup completed!
endif

logs:
	$(DOCKER_COMPOSE) logs -f
