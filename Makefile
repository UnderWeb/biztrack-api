# ======================================================
# MAKEFILE — BIZTRACK DEVELOPMENT WORKFLOW
# ======================================================

# ------------------------------
# GLOBAL VARIABLES
# ------------------------------
PROJECT_NAME ?= biztrack-app
MAIN_SERVICE ?= biztrack-backend
COMPOSE := docker compose -p $(PROJECT_NAME)
DOCKER := docker
MANAGE_PY := python manage.py
BUILD_DATE := $(shell date +%Y%m%d%H%M%S)

# Detect dev dependencies
HAS_CELERY := $(shell grep -q "celery" docker-compose.yml && echo true || echo false)

# ======================================================
# HELP TARGET
# ======================================================
help: ## Display available commands with descriptions
	@echo ""
	@echo "🚀 $(PROJECT_NAME) - Django Development Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "} {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "📁 Project: $(PROJECT_NAME)"
	@echo "🐍 Main Service: $(MAIN_SERVICE)"
	@echo "🔧 Django Management: $(MANAGE_PY)"
	@echo ""

# ======================================================
# BOOTSTRAP WORKFLOW
# ======================================================
bootstrap: ## Initialize project with enterprise standards
	@echo "🚀 Enterprise Bootstrap Sequence Initiated"
	@echo "=========================================="
	
	# Phase 1: Build infrastructure
	@echo "📦 Building Docker infrastructure..."
	$(COMPOSE) build --no-cache --build-arg BUILD_DATE=$(BUILD_DATE)
	
	# Phase 2: Host-based tooling installation
	@echo "🔧 Configuring development environment..."
	
	# Check if git repository exists
	@if [ ! -d ".git" ]; then \
		echo "⚠️  Initializing Git repository..."; \
		git init --quiet; \
		git add .; \
		git commit -m "chore: initial commit" --quiet || true; \
	fi
	
	# Install pre-commit on host
	@echo "📝 Installing Git hooks..."
	@command -v pre-commit >/dev/null 2>&1 || { \
		echo "Installing pre-commit..."; \
		pip install pre-commit >/dev/null 2>&1 || pip3 install pre-commit >/dev/null 2>&1 || true; \
	}
	@pre-commit install --hook-type pre-commit --hook-type pre-push 2>/dev/null || \
		echo "⚠️  Pre-commit configuration may need manual setup"
	
	# Phase 3: Validation
	@echo "✅ Enterprise bootstrap completed successfully"

# ======================================================
# DOCKER OPERATIONS
# ======================================================
build: ## Build Docker images (cache enabled)
	$(COMPOSE) build

build-no-cache: ## Build Docker images without cache
	$(COMPOSE) build --no-cache

up: build ## Start all containers in background
	$(COMPOSE) up -d

up-logs: build ## Start all containers in foreground
	$(COMPOSE) up

stop: ## Stop running containers
	$(COMPOSE) stop

restart: ## Restart all services
	$(COMPOSE) restart

down: ## Stop and remove containers, networks, volumes
	$(COMPOSE) down

logs: ## Tail logs of all containers
	$(COMPOSE) logs -f

logs-app: ## Tail logs of main service
	$(COMPOSE) logs -f $(MAIN_SERVICE)

status: ## Show status of all containers
	$(COMPOSE) ps

# ======================================================
# DEVELOPMENT WORKFLOW
# ======================================================
dev: ## Start essential services (DB, Redis, Mailpit)
	$(COMPOSE) up -d biztrack-postgres biztrack-redis biztrack-mailpit
	@echo "⏳ Waiting for services to be ready..."
	@sleep 5
	$(COMPOSE) logs --tail=20

dev-full: ## Start all services including backend
	$(COMPOSE) up -d biztrack-backend biztrack-postgres biztrack-redis biztrack-mailpit
	@echo "⏳ All services started"
	@sleep 5
	$(COMPOSE) logs --tail=20

# ======================================================
# CLEANUP OPERATIONS
# ======================================================
clean: ## Stop and remove containers, networks, volumes
	$(COMPOSE) down -v --remove-orphans

clean-images: ## Remove all images for the project
	$(COMPOSE) down --rmi all

prune-system: ## Remove all unused Docker objects
	$(DOCKER) system prune -a --volumes -f

# ======================================================
# DJANGO DATABASE OPERATIONS
# ======================================================
migrate: ## Apply all migrations manually
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) migrate

migrations: ## Create new migrations
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) makemigrations

migrate-check: ## Check migration conflicts
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) makemigrations --check --dry-run

showmigrations: ## Show migration status
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) showmigrations

db-shell: ## Access PostgreSQL shell
	$(COMPOSE) exec biztrack-postgres psql -U $$(grep DB_USER .env | cut -d '=' -f2) -d $$(grep DB_NAME .env | cut -d '=' -f2)

# ======================================================
# DJANGO MANAGEMENT COMMANDS
# ======================================================
django-shell: ## Access Django shell_plus or fallback shell
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) shell_plus || $(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) shell

collectstatic: ## Collect static files
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) collectstatic --noinput

createsuperuser: ## Create Django superuser
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) createsuperuser

check: ## Run system checks
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) check

check-deploy: ## Run production deployment checks
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) check --deploy

# ======================================================
# POETRY DEPENDENCIES HANDLING
# ======================================================
poetry-add: ## Add a new Python package inside the container (ARG: PACKAGE)
ifeq ($(strip $(PACKAGE)),)
	@echo "⚠️  Please specify a package: make poetry-add PACKAGE=package_name"
else
	$(COMPOSE) run --rm $(MAIN_SERVICE) poetry add $(PACKAGE)
endif

poetry-add-dev: ## Add a new dev package inside the container (ARG: PACKAGE)
ifeq ($(strip $(PACKAGE)),)
	@echo "⚠️  Please specify a package: make poetry-add-dev PACKAGE=package_name"
else
	$(COMPOSE) run --rm $(MAIN_SERVICE) poetry add -D $(PACKAGE)
endif

# ======================================================
# DJANGO TESTING & QA
# ======================================================
test: ## Run Django tests verbose
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) test --verbosity=2

test-specific: ## Run tests for a specific app (APP=name)
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) test $(APP) --verbosity=2

test-parallel: ## Run tests in parallel
	$(COMPOSE) run --rm $(MAIN_SERVICE) $(MANAGE_PY) test --parallel --verbosity=2

test-coverage: ## Run tests with coverage
	$(COMPOSE) run --rm $(MAIN_SERVICE) coverage run --source='.' manage.py test
	$(COMPOSE) run --rm $(MAIN_SERVICE) coverage report
	$(COMPOSE) run --rm $(MAIN_SERVICE) coverage html
	@echo "📊 Coverage report: htmlcov/index.html"

test-watch: ## Run tests on file changes
	$(COMPOSE) run --rm $(MAIN_SERVICE) ptw --runner "$(MANAGE_PY) test --verbosity=2"

lint: ## Run linters and code format check
	$(COMPOSE) run --rm $(MAIN_SERVICE) sh -c "flake8 . && black --check . && isort --check-only ."

format: ## Auto-format code
	@echo "🎨 Formatting code..."
	@CONTAINER_ID=$$(docker ps -q --filter "name=biztrack-backend") && \
	docker exec -u $(shell id -u) $$CONTAINER_ID sh -c "black . && isort ."
	@echo "✅ Code formatted"

quality-check: lint test-coverage ## Full QA pipeline

# ======================================================
# CELERY OPERATIONS
# ======================================================
celery-worker: ## Start Celery worker
ifeq ($(HAS_CELERY),true)
	$(COMPOSE) up -d biztrack-worker
else
	@echo "⚠️  Celery worker not configured, enable service in docker-compose"
endif

celery-beat: ## Start Celery beat
ifeq ($(HAS_CELERY),true)
	$(COMPOSE) up -d biztrack-beat
else
	@echo "⚠️  Celery beat not configured, enable service in docker-compose"
endif

flower: ## Start Flower dashboard
ifeq ($(HAS_CELERY),true)
	$(COMPOSE) up -d biztrack-flower
	@echo "🌸 Flower dashboard: http://localhost:5555"
else
	@echo "⚠️  Flower not configured, enable service in docker-compose"
endif

celery-logs: ## Follow Celery worker logs
ifeq ($(HAS_CELERY),true)
	$(COMPOSE) logs -f biztrack-worker
else
	@echo "⚠️  Celery logs not available, enable service in docker-compose"
endif

# ======================================================
# DEVELOPMENT TOOLS
# ======================================================
shell: ## Open bash shell inside main service container
	$(COMPOSE) exec $(MAIN_SERVICE) bash

attach: ## Attach interactively to main service container
	$(COMPOSE) attach $(MAIN_SERVICE)

health-check: ## Show container health
	$(COMPOSE) ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

dependencies: ## Install dependencies using Poetry
	$(COMPOSE) run --rm $(MAIN_SERVICE) poetry install

# ======================================================
# QUICK DEVELOPMENT COMMANDS
# ======================================================
run: dev-full logs-app ## Start all services and tail logs
reset: clean dev ## Reset development environment
validate: lint test ## Run code quality & tests
setup: dependencies collectstatic ## Setup project (migrations are manual)

# ======================================================
# DEFAULT TARGET
# ======================================================
.DEFAULT_GOAL := help
