from httpx import AsyncClient
from app.models.departments import Department
from app.models.users import User
from tests.conftest import get_auth_headers


async def test_gets_department(client: AsyncClient, admin_user: User):
    headers = await get_auth_headers(client, "admin_test", "adminadmin")

    response = await client.get(
        "/departments",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page_info" in data


async def test_create_department(client: AsyncClient, admin_user: User, department: Department):
    headers = await get_auth_headers(client, "admin_test", "adminadmin")

    response = await client.post(
        "/departments",
        json={
            "name": "Test Department"
        },
        headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "name" in data


async def test_get_department(client: AsyncClient, admin_user: User, department: Department):
    headers = await get_auth_headers(client, "admin_test", "adminadmin")

    response = await client.get(
        f"/departments/{department.id}",
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data


async def test_update_department(client: AsyncClient, admin_user: User, department: Department):
    headers = await get_auth_headers(client, "admin_test", "adminadmin")

    response = await client.patch(
        f"/departments/{department.id}",
        json={
            "name": "Updated Department"
        },
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Department" 


async def test_delete_department(client: AsyncClient, admin_user: User, department: Department):
    headers = await get_auth_headers(client, "admin_test", "adminadmin")

    response = await client.delete(
        f"/departments/{department.id}",
        headers=headers
    )

    assert response.status_code == 204