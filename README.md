
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

Setup instructions will be added as the application components are implemented.

The application is intended to run locally using Docker Compose.

## Development Status

**Current Phase:** Initial planning and project setup.

Implementation will proceed incrementally, starting with the backend, database, order management, and delivery workflow.



