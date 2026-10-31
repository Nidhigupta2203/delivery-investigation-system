
# Delivery Investigation System

A full-stack web application for managing robotics dataset orders, handling file deliveries, investigating recording quality, and tracking customer acceptance.

## Overview

The Delivery Investigation System helps robotics data providers manage customer orders and deliver recording datasets.

It provides a workflow for:
- Creating and managing customer orders.
- Organizing multiple deliveries for an order.
- Transferring files and verifying their integrity.
- Monitoring delivery progress and failures.
- Investigating recordings using video and sensor data.
- Comparing different delivery versions.
- Recording customer acceptance or rejection.

## Technology Stack

### Frontend
- React
- TypeScript
- Vite
- TanStack Router
- TanStack Query
- Tailwind CSS

### Backend
- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic

### Storage and Background Processing
- S3-compatible object storage
- Python background worker
- File checksum verification

### Testing and Infrastructure
- Vitest
- React Testing Library
- Playwright
- pytest
- Docker Compose

## Core Features

### 1. Order Management
- Create and manage customer orders.
- Track requested and fulfilled quantities.
- Support multiple deliveries per order.
- Track outstanding fulfillment.

### 2. Delivery Management
- Create deliveries using recording manifests.
- Track planned, transferring, transferred, accepted, and rejected states.
- Monitor individual file transfer outcomes.
- Support retries and cancellation.

### 3. File Transfer and Recovery
- Transfer files from source storage to customer storage.
- Verify file integrity using checksums.
- Track transfer progress.
- Handle worker interruptions and failed transfers.
- Support safe retries without duplicate fulfillment.

### 4. Recording Investigation
- Browse delivery manifests.
- Inspect recording metadata and quality reports.
- Play video recordings.
- Visualize timestamped sensor data.
- Investigate missing data and anomalies.

### 5. Delivery Comparison
- Compare two deliveries.
- Identify added, removed, changed, and unchanged recordings.
- Track recording identity and content differences.
- Display differences in quality evidence.

### 6. Customer Review
- Allow authorized reviewers to accept or reject deliveries.
- Record rejection reasons.
- Maintain decision history.
- Enforce customer-level access restrictions.

## Project Structure

```text
delivery-investigation-system/
│
├── frontend/
│   └── src/
│
├── backend/
│   └── app/
│
├── worker/
│
├── docs/
│   ├── architecture.md
│   └── decisions.md
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

Ensure you have the following installed on your machine:
- **Operating System:** Windows (with PowerShell / WSL 2) or Linux / macOS
- **Python:** 3.13+ (managed via `uv`)
- **uv:** Fast Python package and project manager (`https://docs.astral.sh/uv/`)
- **Docker Desktop:** Installed and running (for PostgreSQL container)
- **Git:** Version control
- **Node.js & pnpm:** Node.js 20+ and pnpm 9+ (for future frontend phases)

---

### 1. Environment Configuration

Copy the example environment configuration file to create your local `.env`:

```powershell
# At repository root
Copy-Item .env.example .env
```

The default values configure local development:
```dotenv
APP_NAME="Delivery Investigation System"
APP_ENV=development
DEBUG=True

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=delivery_investigation
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/delivery_investigation
```

> [!NOTE]
> The `.env` file is git-ignored to prevent leaking local credentials.

---

### 2. Start PostgreSQL with Docker Compose

Launch the PostgreSQL 16 container with a persistent volume and automated health check:

```powershell
docker compose up -d
```

Verify the container status:
```powershell
docker compose ps
```
The status should display `Up (healthy)`.

---

### 3. Backend Setup & Dependencies

Navigate to the `backend/` directory and synchronize dependencies using `uv`:

```powershell
cd backend
uv sync
```

This installs FastAPI, Uvicorn, SQLAlchemy, Alembic, Psycopg 3, Pydantic Settings, Pytest, and HTTPX into an isolated virtual environment (`.venv`).

---

### 4. Run Database Migrations

Apply database schema migrations to PostgreSQL using Alembic:

```powershell
uv run alembic upgrade head
```

This creates the core domain tables:
- `organizations`
- `customers`
- `orders`
- `deliveries`
- `recordings`
- `alembic_version`

---

### 5. Run the FastAPI Application

Start the local development server with auto-reload:

```powershell
uv run uvicorn app.main:app --reload --port 8000
```

Access the application in your browser or API client:
- **Root API Status:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Healthcheck & DB Connectivity:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Interactive Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### 6. Run Automated Tests

Execute the backend test suite with Pytest:

```powershell
uv run pytest -v
```

This tests:
- Root endpoint response and metadata.
- Health endpoint database ping (`SELECT 1`).
- Swagger and OpenAPI documentation availability.
- Full domain model persistence and relationship cascade.
- Complete CRUD API operations for Organizations, Customers, Orders, and Deliveries (40 tests total).

---

## API Endpoints

All business APIs are versioned under `/api/v1` and accessible via Swagger UI at `http://127.0.0.1:8000/docs`.

### System & Health
| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `GET` | `/` | API status and root greeting | `200 OK` |
| `GET` | `/health` | API and PostgreSQL connection healthcheck | `200 OK` / `503 Service Unavailable` |

### Organizations (`/api/v1/organizations`)
| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `POST` | `/api/v1/organizations` | Create an organization | `201 Created` / `409 Conflict` |
| `GET` | `/api/v1/organizations` | List organizations (supports `?skip=0&limit=100&is_active=true`) | `200 OK` |
| `GET` | `/api/v1/organizations/{id}` | Get organization by ID | `200 OK` / `404 Not Found` |
| `PATCH` | `/api/v1/organizations/{id}` | Update organization | `200 OK` / `404 Not Found` / `409 Conflict` |
| `DELETE`| `/api/v1/organizations/{id}` | Delete organization and cascade to child records | `204 No Content` / `404 Not Found` |

### Customers (`/api/v1/customers`)
| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `POST` | `/api/v1/customers` | Create a customer under an organization | `201 Created` / `404 Not Found` / `409 Conflict` |
| `GET` | `/api/v1/customers` | List customers (supports `?organization_id=...&skip=0&limit=100`) | `200 OK` |
| `GET` | `/api/v1/customers/{id}` | Get customer by ID | `200 OK` / `404 Not Found` |
| `PATCH` | `/api/v1/customers/{id}` | Update customer | `200 OK` / `404 Not Found` / `409 Conflict` |
| `DELETE`| `/api/v1/customers/{id}` | Delete customer and cascade to child orders | `204 No Content` / `404 Not Found` |

### Orders (`/api/v1/orders`)
| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `POST` | `/api/v1/orders` | Create a dataset order | `201 Created` / `404 Not Found` / `409 Conflict` |
| `GET` | `/api/v1/orders` | List orders (supports `?customer_id=...&status=...&skip=0&limit=100`) | `200 OK` |
| `GET` | `/api/v1/orders/{id}` | Get order by ID | `200 OK` / `404 Not Found` |
| `PATCH` | `/api/v1/orders/{id}/status` | Update order status (`PENDING`, `IN_PROGRESS`, `FULFILLED`, `CANCELLED`) | `200 OK` / `404 Not Found` |

### Deliveries & File Workflow (`/api/v1/deliveries`)
| Method | Endpoint | Description | Status Code |
|---|---|---|---|
| `POST` | `/api/v1/deliveries` | Create a delivery batch for an order (default: `PLANNED`) | `201 Created` / `404 Not Found` |
| `GET` | `/api/v1/deliveries` | List deliveries (supports `?order_id=...&status=...&skip=0&limit=100`) | `200 OK` |
| `GET` | `/api/v1/deliveries/{id}` | Get delivery by ID | `200 OK` / `404 Not Found` |
| `PATCH` | `/api/v1/deliveries/{id}/status` | Update delivery review status (`ACCEPTED` / `REJECTED`) | `200 OK` / `400 Bad Request` / `404 Not Found` |
| `POST` | `/api/v1/deliveries/{id}/manifest` | Register recording manifest with filenames, sizes, and SHA-256 checksums | `201 Created` / `400 Bad Request` / `404 Not Found` |
| `GET` | `/api/v1/deliveries/{id}/manifest` | Inspect registered delivery manifest and recording metadata | `200 OK` / `404 Not Found` |
| `POST` | `/api/v1/deliveries/{id}/transfer` | Start asynchronous file transfer from source storage to customer destination | `202 Accepted` / `400 Bad Request` / `409 Conflict` |
| `GET` | `/api/v1/deliveries/{id}/transfer-status` | Get transfer progress, percentage, byte metrics, and file outcomes | `200 OK` / `404 Not Found` |
| `POST` | `/api/v1/deliveries/{id}/retry-transfer` | Idempotently retry failed transfers without re-transferring completed files | `202 Accepted` / `400 Bad Request` / `409 Conflict` |

> [!TIP]
> - **Checksum Verification**: The transfer worker streams source files and calculates SHA-256 checksums on the fly. If a checksum mismatches the manifest, the file is marked `FAILED` and destination storage is not fulfilled.
> - **Safe Retries**: Retrying a transfer skips already completed and verified files, preventing duplicate fulfillment.

---

### 7. Background Worker

The file transfer worker runs automatically via FastAPI background tasks when transfers are requested. It can also be run as a standalone polling worker process:

```powershell
cd backend
uv run python ../worker/transfer_worker.py
```

### 8. MinIO Object Storage Console

MinIO runs locally via Docker Compose:
- **S3 API Endpoint:** `http://localhost:9000`
- **Web Console:** [http://localhost:9001](http://localhost:9001)
- **Username:** `minioadmin`
- **Password:** `minioadmin`
- **Default Buckets:** `source-bucket` (provider recordings), `customer-bucket` (delivered recordings)

---

## Development Status

**Current Phase:** File Delivery Workflow & Background Processing Implemented (31 October).
- [x] Docker Compose PostgreSQL setup with health checks.
- [x] MinIO S3-compatible local object storage with persistent data.
- [x] `backend/` structured into modular packages (`core`, `models`, `schemas`, `services`, `api`).
- [x] SQLAlchemy 2.0 declarative models with UUID keys, timestamps, and foreign key relations.
- [x] Alembic migration engine applied to PostgreSQL (`transfer_jobs` and `file_transfers`).
- [x] FastAPI application running with `/`, `/health`, and `/docs`.
- [x] Organization & Customer CRUD APIs.
- [x] Order management APIs with status transitions.
- [x] Delivery management APIs with acceptance/rejection validation.
- [x] Recording manifest registration and inspection APIs.
- [x] Background worker for file transfers with on-the-fly SHA-256 checksum validation.
- [x] Progress tracking (percentage, transferred files, transferred bytes).
- [x] Idempotent safe retries without duplicate fulfillment.
- [x] 50 automated Pytest tests passing (100% pass rate).
- [ ] Delivery comparison & diff viewer API.
- [ ] React + Vite + TypeScript frontend with TanStack Router/Query.






