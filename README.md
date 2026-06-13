# Corehub API

Corehub is a backend REST API for an internal company portal. It's a backend engine for a platform where a company can manage it's employees, departments, tasks, announcements and internal communication all at once in one place.

It's designed for companies that need a centralized internal system where:

- Admins manage users, departments, and company-wide settings
- Managers oversee their teams, assign tasks, and post announcements
- Members view their tasks, communicate with teammates, and stay updated with company announcements

## Demo Accounts

You can test the live API using these accounts:
Manager Account - username: demo_manager password: demo_manager
Member Account - username: demo_member password: demo_member

You can message me to get a demo admin account

## How to test

- Open the live [API Docs](https://corehub-amber-acorn-510.fly.dev/docs)
- Use the Authorize button on the top right corner
- Use one of the demo account above
- You can now test the endpoints

## Tech stack

- FastAPI
- PostgreSQL
- SQLAlchemy
- Redis
- JWT
- Docker

## Features

### Authentication System

Corehub uses a dual-token JWT authentication system

- Industry standard
- Stateless authentication
- Secure

How it works:

- Server will issues access token (30 mins) and refresh token (7 days) for a successful login
- Client can just send the access token to every request
- Refresh token can be send to /refresh endpoint once the access token is expired, to get new tokens
- Used refresh token is revoked in db to prevent replay attacks

### User Managerment

- Full CRUD for company employees
- Soft deletion for account recover, audit and trails
- RBAC for ADMIN, MANAGER, MEMBER

### Department Management

- Admins can create, update, and delete departments
- Assign or remove users from departments
- View all users within a specific department
- Department names are unique across the system
- When a department is deleted, users are not deleted — their department_id is simply set to NULL

### Task Management

- Admins can assign tasks to anyone (except themselves) and manage all tasks
- Managers can assign tasks to members only (not to other managers or admins)
- Members can view and update the status of tasks assigned to them
- Task creators have exclusive rights to edit or delete their own tasks
- Tasks support filtering by status, priority, and due date range
- Members can view tasks assigned to them or created by them via task_view
- Due dates must always be set in the future

Task Statuses: pending, in_progress, completed, cancelled
Task Priorities: low, medium, high, critical

### Messaging System

CoreHub has a full messaging system similar to how Messenger or Slack works:

Direct Messages (DM)

- Start a private conversation with any other user
- If a DM already exists between two users, the existing one is returned (no duplicate DMs)
- Cannot DM yourself
- Leaving a DM deletes the entire conversation for both users

Group Conversations

- Create a group with multiple members
- The creator is automatically set as group admin
- Group admins can add or remove members
- Group admins can rename the group
- Regular members can leave at any time
- Only the message sender can delete their own message

Message History

- All messages are paginated using cursor-based pagination
- Ordered oldest to newest (just like a real chat)
- Unread count is tracked per conversation per user

### Notification System

Notifications are automatically created for:

- New messages received in a conversation
- Task assignments

Users can:

- View all notifications (paginated)
- View only unread notifications
- Mark a single notification as read
- Mark all notifications as read at once
- Delete individual notifications

### Announcement System

- Admins can post company-wide announcements
- Announcements support priority levels and expiration dates
- All authenticated users can view announcements
- Only the announcement creator (Admin) can edit or delete their announcements
- Supports filtering by user_id, status, and priority

### Dashboard

A single endpoint that returns everything the user needs in one API call:

- User profile — current user's information
- Task summary — counts broken down by status (pending, in progress, completed, cancelled)
- Unread notifications — total count of unread notifications
- Unread messages — total count of unread messages across all conversations
- Recent announcements — latest active company announcements

All data is fetched concurrently using asyncio.gather for maximum performance. Instead of making 4 separate API calls, the frontend only needs one.

### Redis Caching

Read-heavy endpoints are cached in Redis to reduce database load:

- User list and single user lookups
- Task lists (per user and system-wide)
- Notification lists

Cache is automatically invalidated when data changes (create, update, delete)

By default, Docker Compose spins up a local Redis container automatically. If you prefer cloud Redis, you can point REDIS_URL to your Upstash instance instead.

Cursor-based Pagination

All list endpoints use cursor-based pagination instead of traditional offset pagination.

Fully Async

Every database query, Redis operation, and I/O call is non-blocking async. This means the server can handle many concurrent requests without waiting for each one to finish — critical for real-world performance.

### Architecture

Corehub follows a clean layered architecture: API -> Service -> Repository -> Database

- API or router only handles HTTP concerns (request/response). Talks to services.
- Service layer handles all business logic and rules. Talks to repositories.
- Repository layer handles all database queries. Nothing else touches the DB.

I used Dependency Injetction(DI) to wires everything together cleanly

## Clone

You need docker here

### Clone the repository

git clone https://github.com/Menarddddd/corehub.git cd corehub

### Set up environment variables

Copy the env example to your env file:

- cp .env.example .env

Fill in your env values and is already set to use the local Docker Redis container.
If you want to use other service like UPSTASH just replace the value with your UPSTASH URL
Leave the AUTO_CREATE_TABLES=true, you need this on first run

### Run with Docker-Compose

docker-compose up --build

It will set up PostgreSQL database, Redis, FastAPI app all at once

### Open API Docs

http://localhost:8000/docs

Login with the demo account above

## Author

### Menard Francisco

- [GitHub](https://github.com/Menarddddd)
- [LinkedIn](https://linkedin.com/in/menard-francisco-b21486353)
