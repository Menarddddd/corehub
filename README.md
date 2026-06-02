# CoreHub API

A production-ready backend REST API built with **FastAPI**, featuring real-time messaging,
task management, notifications, and role-based access control.

---

## Tech Stack

| Category             | Technology                    |
| -------------------- | ----------------------------- |
| **Framework**        | FastAPI (Async)               |
| **Database**         | PostgreSQL                    |
| **ORM**              | SQLAlchemy (Async)            |
| **Caching**          | Redis (Upstash)               |
| **Authentication**   | JWT (Access + Refresh Tokens) |
| **Containerization** | Docker + Docker Compose       |
| **Package Manager**  | UV                            |
| **Python Version**   | Python 3.12                   |

---

## Features

### 🔐 Authentication

- JWT-based authentication with **Access** and **Refresh** tokens
- Secure password hashing
- Token blacklisting on logout
- Role-based access control (RBAC)

### 👥 User Management

- Full CRUD for users
- Three roles: **Admin**, **Manager**, **Member**
- Soft delete (users are never permanently removed)
- Password change with current password verification

### ✅ Task Management

- Create, update, and delete tasks
- Filter by **status**, **priority**, and **due date**
- Assign tasks to users
- View tasks **assigned to you** or **created by you**
- Cursor-based pagination

### 💬 Messaging / Conversations

- **Direct Messages (DM)** between two users
- **Group Conversations** with admin controls
- Add and remove members
- Real-time message history with pagination
- Automatic notifications on new messages

### 🔔 Notifications

- Automatic notifications for new messages and task assignments
- Mark notifications as read
- Fetch unread notifications
- Cursor-based pagination

### ⚡ Performance

- **Redis caching** on all read-heavy endpoints
- Cache invalidation on data mutations
- **Cursor-based pagination** for large datasets (scalable)
- Fully **async** database queries

### 🏗️ Architecture

- **Repository Pattern** - Database logic is separated from business logic
- **Service Layer** - Business logic is separated from routes
- **Dependency Injection** - Clean and testable code
- **Soft Deletes** - Data is never permanently lost
- Custom exception handling with consistent error responsestext

---

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/corehub.git
cd corehub
2. Set up environment variables
Bash

cp .env.example .env
Then open .env and fill in your values:

env

# Database
DATABASE_USER=corehub
DATABASE_PASSWORD=corehub
DATABASE_NAME=corehub_db

# Redis (get from https://upstash.com)
REDIS_URL=YOUR_UPSTASH_REDIS_URL

# Auth
ACCESS_SECRET_KEY=your_access_secret_key
ACCESS_MINUTES_EXPIRES=30
REFRESH_SECRET_KEY=your_refresh_secret_key
REFRESH_DAYS_EXPIRES=7
ALGORITHM=HS256

# Development
AUTO_CREATE_TABLES=true
3. Run with Docker Compose
Bash

docker compose up --build
4. Open the API docs
text

http://localhost:8000/docs
That's it. Tables are created automatically on first run.

API Overview

Auth
Method	Endpoint	Description	Access
POST	/auth/login	Login and get tokens	Public
POST	/auth/refresh	Refresh access token	Authenticated
POST	/auth/logout	Logout and blacklist token	Authenticated
Users
Method	Endpoint	Description	Access
GET	/users	Get all users (paginated)	Admin, Manager
POST	/users/create	Create a new user	Admin
GET	/users/me	Get current user profile	All
GET	/users/{id}	Get user by ID	Admin, Manager
PATCH	/users/{id}	Update user	Admin, Manager
POST	/users/{id}	Soft delete user	Admin
POST	/users/change-password	Change password	All

Tasks
Method	Endpoint	Description	Access
GET	/tasks	Get all tasks (paginated)	Admin, Manager
POST	/tasks	Create a task	Admin, Manager
GET	/tasks/me	Get my tasks	All
GET	/tasks/{id}	Get task by ID	Admin, Manager
PATCH	/tasks/{id}	Update task	Admin, Manager
DELETE	/tasks/{id}	Delete task	Admin

Conversations
Method	Endpoint	Description	Access
GET	/conversations	Get inbox	Authenticated
POST	/conversations/dm	Start a DM	Authenticated
POST	/conversations/group	Create a group	Authenticated
GET	/conversations/{id}	Get conversation	Member
PATCH	/conversations/{id}	Update group name	Admin
POST	/conversations/{id}/leave	Leave conversation	Member
GET	/conversations/{id}/messages	Get messages	Member
POST	/conversations/{id}/messages	Send message	Member
DELETE	/conversations/{id}/messages/{id}	Delete message	Sender
Notifications
Method	Endpoint	Description	Access
GET	/notifications	Get all notifications	Authenticated
GET	/notifications/unread	Get unread notifications	Authenticated
POST	/notifications/{id}/read	Mark as read	Authenticated
Default Admin Account
On first run, a default admin account is created automatically:

text

Username: adminadmin
Password: adminadmin

Environment Variables
Variable	Description	Example

DATABASE_USER	PostgreSQL username	corehub

DATABASE_PASSWORD	PostgreSQL password	corehub

DATABASE_NAME	PostgreSQL database name	corehub_db

REDIS_URL	Upstash Redis connection URL	rediss://...

ACCESS_SECRET_KEY	JWT access token secret	your_secret

ACCESS_MINUTES_EXPIRES	Access token expiry (minutes)	30

REFRESH_SECRET_KEY	JWT refresh token secret	your_secret

REFRESH_DAYS_EXPIRES	Refresh token expiry (days)	7

ALGORITHM	JWT algorithm	HS256

AUTO_CREATE_TABLES	Auto create DB tables on startup	true


Design Decisions
Why Cursor-based Pagination?
Offset pagination (LIMIT/OFFSET) becomes very slow on large datasets because the database still has to scan all the skipped rows. Cursor-based pagination is what Facebook, Twitter, and Instagram use because it stays fast regardless of dataset size.

Why Redis Caching?
Read-heavy endpoints (like getting users or tasks) can hit the database thousands of times per minute. Redis caching stores the result in memory so the database is only hit when data actually changes (cache miss).

Why Soft Deletes?
Permanently deleting users can break audit trails, message history, and task assignments. Soft deletes keep the record in the database but mark it as deleted so the app treats it as gone.

Why Repository Pattern?
Mixing database queries directly in routes or services makes the code hard to test and maintain. The Repository Pattern separates database logic into its own layer, making each part easier to understand and change independently.

Author
Menard Francisco

GitHub: https://github.com/Menarddddd
LinkedIn: https://www.linkedin.com/in/menard-francisco-b21486353/
```
