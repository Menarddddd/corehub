# CoreHub API

**CoreHub** is a backend REST API for an **internal company portal** — think of it as the
backend engine for a platform where a company manages its employees, departments, tasks,
announcements, and internal communications all in one place.

Built with **FastAPI** using clean architecture principles, async performance, and
production-ready patterns.

---

## 🧠 What is CoreHub?

CoreHub is designed for companies that need a centralized internal system where:

- **Admins** manage users, departments, and company-wide settings
- **Managers** oversee their teams, assign tasks, and post announcements
- **Employees (Members)** view their tasks, communicate with teammates, and stay
  updated with company announcements

Think of it like a lightweight internal version of **Slack + Asana + an HR portal**,
all powered by one clean backend API.

---

## ⚙️ Tech Stack

| Category             | Technology                    |
| -------------------- | ----------------------------- |
| **Framework**        | FastAPI (Async)               |
| **Database**         | PostgreSQL                    |
| **ORM**              | SQLAlchemy (Async)            |
| **Caching**          | Redis (Upstash)               |
| **Authentication**   | JWT (Access + Refresh Tokens) |
| **Containerization** | Docker + Docker Compose       |
| **Package Manager**  | UV                            |
| **Python**           | 3.12                          |

---

## 🚀 Features

### 🔐 Authentication System

CoreHub uses a **dual-token JWT authentication system** — the industry standard for
secure, stateless authentication.

**How it works:**

- When you log in, the server issues two tokens:
  - **Access Token** (short-lived, e.g. 30 minutes) — used for every API request
  - **Refresh Token** (long-lived, e.g. 7 days) — used only to get a new access token
- When your access token expires, your client sends the refresh token to `/auth/refresh`
  and gets a **brand new pair of tokens** without requiring the user to log in again
- This is called **Refresh Token Rotation** — every refresh issues a new refresh token
  and invalidates the old one, making stolen tokens useless
- On logout, the refresh token is **blacklisted in Redis** so it can never be reused
- The `user-agent` header is tracked on login and refresh for basic session awareness

**Why this is better than a single token:**
A single long-lived token is dangerous. If it gets stolen, the attacker has access
for days. With dual tokens, even if the access token is stolen, it expires in minutes.
The refresh token is only sent to one specific endpoint, reducing its exposure.

---

### 👥 User Management

- Full CRUD for company employees
- **Soft Delete** — deleted users are never permanently removed from the database.
  Their records are kept for audit trails, message history, and task ownership.
  They simply can no longer log in.
- Role-based access control with three roles:
  - `admin` — full system access
  - `manager` — team management, task assignment
  - `member` — personal tasks, messaging, notifications

---

### 🏢 Department Management

- Admins can create, update, and delete departments
- Assign or remove users from departments
- View all users within a specific department
- Department names are unique across the system
- When a department is deleted, users are not deleted — their `department_id`
  is simply set to `NULL`

---

### ✅ Task Management

CoreHub has a full task system with granular permission rules:

- **Admins** can assign tasks to anyone (except themselves) and manage all tasks
- **Managers** can assign tasks to members only (not to other managers or admins)
- **Members** can view and update the status of tasks assigned to them
- Task creators have exclusive rights to edit or delete their own tasks
- Tasks support filtering by **status**, **priority**, and **due date range**
- Members can view tasks **assigned to them** or **created by them** via `task_view`
- Due dates must always be set in the future

**Task Statuses:** `pending`, `in_progress`, `completed`, `cancelled`

**Task Priorities:** `low`, `medium`, `high`, `critical`

---

### 💬 Messaging System

CoreHub has a full messaging system similar to how **Messenger** or **Slack** works:

**Direct Messages (DM)**

- Start a private conversation with any other user
- If a DM already exists between two users, the existing one is returned
  (no duplicate DMs)
- Cannot DM yourself
- Leaving a DM deletes the entire conversation for both users

**Group Conversations**

- Create a group with multiple members
- The creator is automatically set as **group admin**
- Group admins can add or remove members
- Group admins can rename the group
- Regular members can leave at any time
- Only the message sender can delete their own message

**Message History**

- All messages are paginated using **cursor-based pagination**
- Ordered oldest to newest (just like a real chat)
- Unread count is tracked per conversation per user

**Automatic Notifications**

- When a message is sent, every other member of the conversation
  automatically receives a notification

---

### 🔔 Notification System

- Notifications are automatically created for:
  - New messages received in a conversation
  - Task assignments
- Users can:
  - View all notifications (paginated)
  - View only unread notifications
  - Mark a single notification as read
  - Mark all notifications as read at once
  - Delete individual notifications
- Notifications are never shown to the sender — only to recipients

---

### 📢 Announcement System

- Admins can post company-wide announcements
- Announcements support **priority levels** and **status** (active, archived, etc.)
- All authenticated users can view announcements
- Only the announcement creator (Admin) can edit or delete their announcements
- Supports filtering by `user_id`, `status`, and `priority`

---

### ⚡ Performance

**Redis Caching**

Read-heavy endpoints are cached in Redis (Upstash) to reduce database load:

- User list and single user lookups
- Task lists (per user and system-wide)
- Notification lists

Cache is automatically **invalidated** when data changes (create, update, delete).
This means users always see fresh data while getting fast responses on repeated reads.

**Cursor-based Pagination**

All list endpoints use cursor-based pagination instead of traditional
offset pagination.

Offset pagination (`LIMIT 10 OFFSET 100`) becomes slower as data grows because
the database still has to scan all skipped rows. Cursor-based pagination
uses a pointer to the last seen item, making it **consistently fast** regardless
of how much data exists. This is the same approach used by Facebook, Twitter,
and Instagram.

**Fully Async**

Every database query, Redis operation, and I/O call is **non-blocking async**.
This means the server can handle many concurrent requests without waiting for
each one to finish — critical for real-world performance.

---

### 🏗️ Architecture

CoreHub follows a clean layered architecture:
Router → Service → Repository → Database

- **Repository Layer** — handles all database queries. Nothing else touches the DB.
- **Service Layer** — handles all business logic and rules. Talks to repositories.
- **Router Layer** — only handles HTTP concerns (request/response). Talks to services.
- **Dependency Injection** — FastAPI's DI system wires everything together cleanly.

This separation means each layer can be changed independently without breaking others.

---

## 📁 Project Structure

core/ # Database, Redis, Security, Settings
dependencies/ # FastAPI dependency functions
models/ # SQLAlchemy ORM models
repositories/ # Database query logic
routers/ # API route definitions
schemas/ # Pydantic request/response schemas
services/ # Business logic
utils/ # Helper functions (cursor, hashing, etc.)
.env.example
docker-compose.yml
Dockerfile
pyproject.toml

---

## 🛠️ Getting Started

### Requirements

- Docker
- Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/corehub.git
cd corehub
2. Set up environment variables
Bash

cp .env.example .env
Open .env and fill in your values:

env

DATABASE_USER=corehub
DATABASE_PASSWORD=corehub
DATABASE_NAME=corehub_db

# Get from https://upstash.com (free tier available)
REDIS_URL=YOUR_UPSTASH_REDIS_URL

ACCESS_SECRET_KEY=your_access_secret_key
ACCESS_MINUTES_EXPIRES=30

REFRESH_SECRET_KEY=your_refresh_secret_key
REFRESH_DAYS_EXPIRES=7

ALGORITHM=HS256
AUTO_CREATE_TABLES=true
3. Run with Docker Compose
Bash

docker compose up --build
Database tables are created automatically on first run.

4. Open the API docs
http://localhost:8000/docs

5. Login with the default admin account
Username: adminadmin
Password: adminadmin
⚠️ Change the default admin password immediately after first login.

📡 API Overview
Auth
Method	Endpoint	Description	Access
POST	/auth/login	Login and receive access + refresh tokens	Public
POST	/auth/refresh	Get new tokens using refresh token	Public
POST	/auth/logout	Logout and blacklist refresh token	Authenticated

Users
Method	Endpoint	Description	Access
GET	/users	Get all users (paginated, filterable)	Admin, Manager
POST	/users/create	Create a new user	Admin
GET	/users/me	Get current user profile	All
POST	/users/change-password	Change own password	All
GET	/users/{id}	Get user by ID	Admin, Manager
PATCH	/users/{id}	Update user details	Admin, Manager
POST	/users/{id}	Soft delete a user	Admin

Departments
Method	Endpoint	Description	Access
GET	/departments	Get all departments (paginated)	Admin, Manager
POST	/departments	Create a department	Admin
GET	/departments/{id}	Get department by ID	Admin, Manager
PATCH	/departments/{id}	Update department	Admin
DELETE	/departments/{id}	Delete department	Admin
GET	/departments/{id}/users	Get users in a department	Admin, Manager
PATCH	/departments/{id}/assign/{user_id}	Assign user to department	Admin
PATCH	/departments/{id}/remove/{user_id}	Remove user from department	Admin

Tasks
Method	Endpoint	Description	Access
GET	/tasks	Get all tasks (paginated, filterable)	Admin, Manager
POST	/tasks	Create and assign a task	Admin, Manager
GET	/tasks/my	Get my tasks (assigned or created)	All
GET	/tasks/my/{id}	Get single task assigned to me	All
GET	/tasks/{id}	Get any task by ID	Admin, Manager
GET	/tasks/{user_id}/all	Get all tasks of a specific user	Admin, Manager
PATCH	/tasks/{id}	Update task details	Admin, Manager (creator only)
PATCH	/tasks/status/{id}	Update task status	All
PATCH	/tasks/due-date/{id}	Update task due date	Admin, Manager (creator only)
DELETE	/tasks/my/{id}	Delete own task	Admin, Manager (creator only)
DELETE	/tasks/{id}	Hard delete any task	Admin

Conversations & Messaging
Method	Endpoint	Description	Access
GET	/conversations	Get inbox with unread counts	All
POST	/conversations/dm	Start a DM conversation	All
POST	/conversations/group	Create a group conversation	All
GET	/conversations/{id}	Get conversation details	Member
PATCH	/conversations/{id}	Update group name	Group Admin
DELETE	/conversations/{id}	Leave conversation	Member
POST	/conversations/{id}/members	Add member to group	Group Admin
DELETE	/conversations/{id}/members/{user_id}	Remove member from group	Group Admin
GET	/conversations/{id}/messages	Get messages (paginated)	Member
POST	/conversations/{id}/messages	Send a message	Member
DELETE	/conversations/{id}/messages/{msg_id}	Delete own message	Sender
PATCH	/conversations/{id}/read	Mark conversation as read	Member

Notifications
Method	Endpoint	Description	Access
GET	/notifications	Get all notifications (paginated)	All
GET	/notifications/unread	Get unread notifications	All
PATCH	/notifications/{id}/read	Mark notification as read	Owner
PATCH	/notifications/read-all	Mark all notifications as read	All
DELETE	/notifications/{id}	Delete a notification	Owner

Announcements
Method	Endpoint	Description	Access
GET	/announcements	Get all announcements (paginated)	All
POST	/announcements	Create an announcement	Admin
GET	/announcements/{id}	Get announcement by ID	All
PATCH	/announcements/{id}	Update announcement	Admin (creator only)
DELETE	/announcements/{id}	Delete announcement	Admin

🔒 Role Permissions Summary
Feature	Admin	Manager	Member
Manage Users	✅ Full	✅ View only	❌
Manage Departments	✅ Full	✅ View only	❌
Create Tasks	✅	✅	❌
View All Tasks	✅	✅	❌
View Own Tasks	✅	✅	✅
Update Task Status	✅ Any	✅ Any	✅ Own only
Messaging	✅	✅	✅
Notifications	✅	✅	✅
Announcements	✅ Full	✅ View only	✅ View only

🌍 Environment Variables
Variable	Description	Example
DATABASE_USER	PostgreSQL username	corehub
DATABASE_PASSWORD	PostgreSQL password	corehub
DATABASE_NAME	PostgreSQL database name	corehub_db
REDIS_URL	Upstash Redis connection URL	rediss://...
ACCESS_SECRET_KEY	JWT access token signing secret	your_secret
ACCESS_MINUTES_EXPIRES	Access token lifetime in minutes	30
REFRESH_SECRET_KEY	JWT refresh token signing secret	your_secret
REFRESH_DAYS_EXPIRES	Refresh token lifetime in days	7
ALGORITHM	JWT signing algorithm	HS256
AUTO_CREATE_TABLES	Auto create DB tables on startup	true

👨‍💻 Author
Menard Francisco

GitHub: https://github.com/Menarddddd
LinkedIn: https://www.linkedin.com/in/menard-francisco-b21486353/
```
