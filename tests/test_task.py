from datetime import date

from httpx import AsyncClient
from app.models.tasks import Task
from app.schemas.enum import TaskPriority, TaskStatus
from tests.conftest import get_auth_headers
from app.models.users import User


async def test_get_tasks(client: AsyncClient, admin_user: User):
    headers = await get_auth_headers(client, admin_user.username, "adminadmin")

    response = await client.get(
        "/tasks",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page_info" in data


async def test_get_task(client: AsyncClient, admin_user: User, task: Task):
    headers = await get_auth_headers(client, admin_user.username, "adminadmin")

    response = await client.get(
        f"/tasks/{task.id}",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "status" in data
    assert "due_date" in data
    assert "assigned_to_id" in data


async def test_create_task(client: AsyncClient, manager_user: User, employee_user: User, task: Task):
    headers = await get_auth_headers(client, manager_user.username, "managermanager")

    response = await client.post(
        f"/tasks",
        json={
            "assigned_to_id": str(employee_user.id),
            "due_date": str(date(2026, 11, 28)),
            "title": "Surprise",
            "description": "Birthday party",
            "status": TaskStatus.PENDING.value,
            "priority": TaskPriority.HIGH.value
        },
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "status" in data
    assert "due_date" in data
    assert "assigned_to_id" in data


async def test_update_task(client: AsyncClient, manager_user: User, task: Task):
    headers = await get_auth_headers(client, manager_user.username, "managermanager")

    response = await client.patch(
        f"/tasks/{task.id}",
        json={
            "title": "Test",
            "description": "Update Test",
            "priority": TaskPriority.LOW.value
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["title"] == "Test"
    assert data["description"] == "Update Test"
    assert data["priority"] == "low"
    

async def test_update_status_task(client: AsyncClient, manager_user: User, task: Task):
    headers = await get_auth_headers(client, manager_user.username, "managermanager")

    response = await client.patch(
        f"/tasks/status/{task.id}",
        json={
            "status": TaskStatus.COMPLETED.value
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "assigned_to_id" in data
    assert data["status"] == "completed"


async def test_delete_my_task(client: AsyncClient, manager_user: User, task: Task):
    headers = await get_auth_headers(client, manager_user.username, "managermanager")

    response = await client.delete(
        f"/tasks/my/{task.id}",
        headers=headers,
    )

    assert response.status_code == 204

async def test_delete_task(client: AsyncClient, admin_user: User, task: Task):
    headers = await get_auth_headers(client, admin_user.username, "adminadmin")

    response = await client.delete(
        f"/tasks/{task.id}",
        headers=headers,
    )

    assert response.status_code == 204
