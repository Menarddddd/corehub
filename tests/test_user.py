from httpx import AsyncClient
from app.models.users import User
from tests.conftest import get_auth_headers


async def test_login_success(client: AsyncClient, admin_user: User):
    """Admin can login with correct credentials."""
    response = await client.post(
        "/auth/login",
        data={
            "username": "admin_test",
            "password": "adminadmin",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_fail(client: AsyncClient):
    """Login fails with wrong credentials."""
    response = await client.post(
        "/auth/login",
        data={
            "username": "wrong_user",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401


async def test_get_profile(client: AsyncClient, manager_user: User):
    """Authenticated user can view their own profile."""
    headers = await get_auth_headers(client, "manager_test", "managermanager")

    response = await client.get("/users/me", headers=headers)

    assert response.status_code == 200


async def test_get_users_as_manager(client: AsyncClient, manager_user: User):
    """Manager can view the user list."""
    headers = await get_auth_headers(client, "manager_test", "managermanager")

    response = await client.get("/users", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page_info" in data


async def test_get_users_as_member_forbidden(client: AsyncClient, member_user: User):
    """Member cannot view the user list."""
    headers = await get_auth_headers(client, "member_test", "membermember")

    response = await client.get("/users", headers=headers)

    assert response.status_code == 403


async def test_get_user_by_id(client: AsyncClient, member_user: User):
    """Can retrieve a specific user by ID."""
    headers = await get_auth_headers(client, "member_test", "membermember")

    response = await client.get(
        f"/users/{member_user.id}",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "username" in data
    assert "email" in data
    assert "hashed_password" not in data


async def test_change_password_wrong_current(client: AsyncClient, admin_user: User):
    """Change password fails with wrong current password."""
    headers = await get_auth_headers(client, "admin_test", "adminadmin")

    response = await client.post(
        "/users/change-password",
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
        },
        headers=headers,
    )

    assert response.status_code == 401


async def test_change_password_same_value(client: AsyncClient, admin_user: User):
    """Change password fails if new password is same as current."""
    headers = await get_auth_headers(client, "admin_test", "adminadmin")

    response = await client.post(
        "/users/change-password",
        json={
            "current_password": "samesame",
            "new_password": "samesame",
        },
        headers=headers,
    )

    assert response.status_code == 422


async def test_change_password_success(client: AsyncClient, admin_user: User):
    """Change password succeeds with correct current password."""
    headers = await get_auth_headers(client, "admin_test", "adminadmin")

    response = await client.post(
        "/users/change-password",
        json={
            "current_password": "adminadmin",
            "new_password": "newsecurepassword",
        },
        headers=headers,
    )

    assert response.status_code == 204
