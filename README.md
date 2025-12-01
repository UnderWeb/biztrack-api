# 🚀 Biztrack Development Workflow

## 🌟 Project Description

This project is a **Django application** orchestrated with **Docker Compose**.

It uses **Make** as a CLI for all project operations: building containers, managing Django tasks, running tests, and development workflows.

**Poetry** is used as the single source of truth for Python dependencies, ensuring consistency across all environments.

All services run in isolated Docker containers:

- **biztrack-backend** — Django application
- **biztrack-postgres** — PostgreSQL database
- **biztrack-redis** — Redis cache & Celery broker
- **biztrack-mailpit** — SMTP server + web UI for dev
- **biztrack-worker** — Celery worker
- **biztrack-beat** — Celery beat scheduler
- **biztrack-flower** — Flower dashboard (<http://localhost:5555>)

---

## 📋 Prerequisites

Before building and running this project, ensure you have the following tools installed on your host machine:

- **Docker Engine ≥ 20.10**.
- **Docker Compose V2** (docker compose, not docker-compose).
- **GNU Make**.
- **Git**.
- **Poetry**

> Poetry is installed on the host only if you need to manage dependencies outside the container; inside the container, dependencies are handled automatically.

---

## 💻 Installation & Setup

**1. Clone the Repository**:

```bash
clone https://github.com/UnderWeb/biztrack-api.git
cd biztrack-api
```

**2. Configure environment variables**:

Copy the example environment file to create your local configuration:

```bash
cp .env.example .env
```

Edit .env to define:

- PostgreSQL credentials.
- Redis password.
- Django SECRET_KEY.
- Other environment-specific variables for your local setup.

**3. Initial project setup**:

```bash
make setup
```

**What** make setup **does**:

- Installs dependencies via Poetry inside the container.
- Collects static files.

**4. Start full development environment**:

```bash
make run
```

Starts all services (dev-full) and streams logs from biztrack-backend.

---

## 📋 Make Commands Reference

```bash
make help
```

to see all available commands with descriptions.

---

### ⚙️ Quick Start & Core Operations

| Command | Description |
|---|---|
| `make help` | Show all commands. |
| `make run` | Start all services and stream main app logs. |
| `make validate` | Run full QA: lint + tests.|
| `make reset` | Clean environment and start fresh setup.|
| `make setup` | Install dependencies, run migrations, collect static files.|

---

### 🐳 Docker Compose Management

| Command | Description |
| ------- | ----------- |
| `make build` | Build all images using cache |
| `make build-no-cache` | Force rebuild of all images |
| `make up` | Start all containers detached (`-d`) |
| `make up-logs` | Start containers and show continuous logs |
| `make stop` | Stop running containers |
| `make restart` | Restart all containers |
| `make down` | Stop & remove containers, networks, volumes |
| `make logs` | Follow logs from all services |
| `make logs-app` | Follow logs only from `biztrack-backend` |
| `make status` | Show container status |

---

### 🛠️ Development Workflow

| Command | Description |
| ------- | ----------- |
| `make dev` | Start essential services: DB, Redis, Mailpit |
| `make dev-full` | Start all services including backend, optional Celery & Flower |
| `make shell` | Access main container bash shell |
| `make attach` | Attach to main container interactively |
| `make dependencies` | Install Python dependencies via **Poetry** inside container |

---

### 🧪 Testing & QA

| Command | Description |
| ------- | ----------- |
| `make test` | Run Django test suite (`--verbosity=2`) |
| `make test-coverage` | Run tests with coverage report (HTML at `htmlcov/index.html`) |
| `make test-specific APP=app_name` | Run tests for specific app |
| `make test-parallel` | Run tests in parallel |
| `make test-watch` | Auto-run tests on file changes (requires `pytest-watch` installed via Poetry) |
| `make lint` | Run code checks (`flake8`, `black --check`, `isort --check-only`) |
| `make format` | Auto-format code (`black` + `isort`) |
| `make quality-check` | Full QA: lint + coverage |

---

### 🗄️ Database Operations

| Command | Description |
| ------- | ----------- |
| `make migrate` | Apply migrations |
| `make migrations` | Generate new migrations (`makemigrations`) |
| `make migrate-check` | Check for migration conflicts (`--check --dry-run`) |
| `make showmigrations` | Show all migrations & status |
| `make db-shell` | Access PostgreSQL shell |
| `make django-shell` | Access Django shell_plus or default shell |

---

### 📝 Django Management Commands

| Command | Description |
| ------- | ----------- |
| `make collectstatic` | Collect static files |
| `make createsuperuser` | Create superuser interactively |
| `make check` | Run Django system checks |
| `make check-deploy` | Run production deployment checks |

---

### ⏳ Celery Operations

| Command | Description |
| ------- | ----------- |
| `make celery-worker` | Start Celery worker |
| `make celery-beat` | Start Celery beat scheduler |
| `make flower` | Start Flower monitoring dashboard (`http://localhost:5555`) |
| `make celery-logs` | Follow Celery worker logs |

---

### 🧹 Cleanup Operations

| Command | Description |
| ------- | ----------- |
| `make clean` | Remove containers, networks, volumes (-v) |
| `make clean-images` | Remove containers & images |
| `make prune-system` | Remove all unused Docker objects system-wide |

---

## 📋 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
