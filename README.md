# 🍪 BakeFlow API

A REST API for managing bakery operations, including inventory, cookie cataloging, order processing, role-based access control, and business analytics.

## 🚀 Tech Stack

- **Python 3.9+ / FastAPI** — asynchronous REST API
- **PostgreSQL** — relational database
- **SQLAlchemy 2.0 / AsyncSession** — asynchronous ORM
- **Alembic** — database migrations
- **JWT access & refresh tokens** — authentication
- **RBAC** — baker and admin roles
- **PyTest / HTTPX** — automated API testing
- **Docker / Docker Compose** — containerized development environment

## 📊 Core Features
* Cookie catalog management (CRUD operations, pagination, search, and filtering).
* Baking and sales logic with automated stock control and threshold checking.
* Order processing system with stock availability verification.
* Business analytics endpoints secured with role-based restrictions (`/analytics`).
* Custom middleware for real-time HTTP request logging.

## 🛠️ Running the Project via Docker
1. Clone the repository:
   ```bash
   git clone https://github.com/miaaa1337/bakeflow-api
   cd bakeflow-api

2. Build and run the containers with a single command:
    ```bash
    docker compose up --build

3. Open the interactive API documentation at: 
    ```bash
    http://127.0.0.1:8000/docs

## 🧪 Running Tests Locally

- **46 automated tests**
- **97% code coverage**
- **GitHub Actions CI** for automated test execution

To run the full test suite with coverage reporting:
   ```bash
   pytest --cache-clear --cov=. --cov-report=term-missing
```
    
