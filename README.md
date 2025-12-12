# Organization Management Service

> **Backend Intern Assignment** Implementation.

A scalable backend service built with **FastAPI** (Python) and **MongoDB** that implements a multi-tenant architecture. It features **Dynamic Collection Creation** for strong tenant isolation and an efficient **Service-Layer** design.

## 🎯 Objective
To build a RESTful service that manages organizations in a multi-tenant environment. The system maintains a "Master Database" for global metadata and dynamically creates separate MongoDB collections (`org_<name>`) for each organization to ensure data isolation.

## 🚀 Features

-   **Dynamic Multi-Tenancy**: Automatically creates and manages isolated MongoDB collections for every new organization.
-   **Organization Lifecycle**: Full CRUD support including a complex **Update/Rename** flow that performs zero-downtime data migration between collections.
-   **Security**: Admin authentication using **JWT** (JSON Web Tokens) and industry-standard **Bcrypt** password hashing.
-   **Scalability**: Optimized `rename` operations using server-side Aggregation Pipelines to handle large datasets efficiently.

## 🛠️ Tech Stack

-   **Framework**: Python 3.10+ with **FastAPI** (Async, Modern, Fast)
-   **Database**: **MongoDB** with `Motor` (Async Driver)
-   **Authentication**: `Python-Jose` (JWT) & `Passlib` (Bcrypt)
-   **Environment**: `Python-Dotenv`
-   **Testing**: `Httpx` for integration testing

## 📂 Project Structure

```bash
.
├── app
│   ├── routes            # API Controllers (Thin Layer)
│   │   ├── admin.py      # Admin Auth Routes
│   │   └── orgs.py       # Organization CRUD Routes
│   ├── services          # Business Logic Layer
│   │   └── org_service.py # Core logical operations (Transactions)
│   ├── auth.py           # JWT Security
│   ├── db.py             # Database Connection & Aggregation Utils
│   ├── main.py           # App Entry Point
│   ├── models.py         # Pydantic Schemas
│   └── utils.py          # Hashing Helpers
├── .env                  # Configuration
├── requirements.txt      # Dependencies
└── README.md             # Documentation
```

## ⚙️ Setup & Installation

### 1. Prerequisites
-   Python 3.10 or higher
-   MongoDB (Running locally on port 27017 or a cloud URI)

### 2. Clone the Repository
```bash
git clone https://github.com/JukalAdhitya/Organization-Management-Service.git
cd Organization-Management-Service
```

### 3. Configure Environment
Create a `.env` file in the root directory:

**`.env` Content:**
```ini
# Database Connection
MONGO_URI="mongodb://localhost:27017"
MASTER_DB="master_org_db"

# Security
JWT_SECRET="your_generated_secret_key_here"
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Run the Application
```bash
uvicorn app.main:app --reload
```
The API will be accessible at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## 📖 API Documentation

Interactive API documentation is automatically generated:

-   **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
-   **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## 🏗️ Architecture & High-Level Design

### System Diagram
```mermaid
graph TD
    Client[Client / Frontend] -->|HTTP Request| API[FastAPI Application]
    
    subgraph "Application Layer"
        API --> Routes[Routes / Controllers]
        Routes --> Service[Service Layer (Business Logic)]
        Service --> Utils[Auth & Helpers]
    end
    
    subgraph "Data Layer"
        Service --> DB_Master[Master DB (Metadata & Admins)]
        Service --> DB_Dynamic[Dynamic Collections (org_clientA, org_clientB...)]
    end
    
    DB_Master <--> MongoDB[(MongoDB Instance)]
    DB_Dynamic <--> MongoDB
```

### Architecture Analysis & Scalability

#### 1. Is this a good architecture?
**Yes**, for the specified requirements, this is a distinct and modular architecture.
*   **Separation of Concerns**: The **Service Layer** pattern decouples business logic (`OrganizationService`) from HTTP control logic (`Routes`). This makes the codebase **testable**, **maintainable**, and cleaner than adding all logic in the view functions.
*   **Async/Await**: Using FastAPI with `Motor` allows the service to handle thousands of concurrent connections efficiently, making it highly suitable for I/O-bound tasks.

#### 2. Scalability & Trade-offs
The design choice of **Dynamic Collections** (Multi-Tenancy via Database-Level Separation) has specific pros and cons:

*   **Pros (Why it is good)**:
    *   **Isolation**: Strict data separation. It is impossible to accidentally leak Client A's data to Client B via a simple query bug (unlike `WHERE org_id = X`).
    *   **Maintenance**: Easy to backup, restore, or delete a single tenant. Deleting a client is just `drop_collection`, which is instant and reclaims space immediately.

*   **Cons (The Trade-offs)**:
    *   **Namespace Limits**: MongoDB typically has a limit on the number of namespace files. Having 100,000 tenants means 100,000 collections, which can degrade database server performance and increase RAM usage.
    *   **Complexity**: Migrations (schema updates) must be run across *all* dynamic collections, which is operationally complex compared to updating one single table.

#### 3. Alternative Design (Better for massive scale?)
For a system targeting **massive scale** (e.g., millions of tenants), a **Row-Level Tenancy** approach might be "better" depending on the use case:
*   **Design**: Single `Orders` collection with an indexed `org_id` field.
*   **Benefit**: Database remains simple with fixed schema. Excellent for analytics across tenants.
*   **Drawback**: Requires rigorous application-level security to ensure `org_id` is always filtered correctly.

*For this assignment, the Dynamic Collection approach is excellent as it demonstrates strong understanding of database management.*

### Design Choices in this Project

1.  **Service Layer**: I chose to implement a `Service` class to satisfy the "Modular and Class-based" preference. This allows the API routes to remain extremely thin.
2.  **Aggregation for Sync**: Instead of iterating through documents in Python (O(N) network calls), I used the MongoDB Aggregation Pipeline `[{ $match: {} }, { $out: "new_coll" }]`. This performs the copy entirely on the database server, offering **O(1)** network latency and vastly superior performance for large datasets.
3.  **Bcrypt Compatibility**: Explicitly pinned `bcrypt==3.2.0` in `requirements.txt` to solve a known incompatibility with `passlib`, ensuring robust security without runtime errors.
