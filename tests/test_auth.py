from httpx import AsyncClient
from app.models.users import User
from tests.conftest import get_auth_headers


async def test_logout(client: AsyncClient, member_user: User):
    login_response = await client.post(
        "/auth/login",
        data={
            "username": member_user.username,
            "password": "membermember",
        },
    )

    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    logout_response = await client.post(
        "/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert logout_response.status_code == 204


async def test_refresh(client: AsyncClient, member_user: User):
    login_response = await client.post(
        "/auth/login",
        data={
            "username": member_user.username,
            "password": "membermember",
        },
    )

    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    refresh_response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert refresh_response.status_code == 200
    data = refresh_response.json()
    assert "access_token" in data
    assert "refresh_token" in data
