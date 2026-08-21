# 🍪 BakeFlow API

A robust RESTful API designed to automate bakery operations, including inventory management, cookie cataloging, order processing, role-based access control (RBAC), and business analytics.

## 🚀 Tech Stack
* **Python 3.9+, FastAPI** — High performance and fully asynchronous architecture.
* **SQLAlchemy 2.0 (AsyncSession) + Alembic** — Asynchronous database management and migrations.
* **PostgreSQL** — Reliable relational data storage.
* **JWT (Access & Refresh tokens) + RBAC** — Secure authentication and strict role separation (baker / admin).
* **PyTest + Httpx** — 46 comprehensive unit and integration tests with 97% code coverage.
* **Docker & Docker Compose** — Full containerization for the application and database.

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
To run the full test suite with coverage reporting:
    ```bash
    pytest --cache-clear --cov=main --cov-report=term-missing
    
