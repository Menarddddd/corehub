from httpx import AsyncClient
from app.models.users import User
from tests.conftest import get_auth_headers


async def test_get_notifications(client: AsyncClient, member_user: User):
    headers = await get_auth_headers(
        client,
        member_user.username,
        "membermember",
    )

    response = await client.get(
        "/notifications",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page_info" in data


async def test_get_unread_notifications(client: AsyncClient, member_user: User):
    headers = await get_auth_headers(
        client,
        member_user.username,
        "membermember",
    )

    response = await client.get(
        "/notifications/unread",
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "page_info" in data


async def test_get_mark_all_as_read(client: AsyncClient, member_user: User):
    headers = await get_auth_headers(
        client,
        member_user.username,
        "membermember",
    )

    response = await client.patch(
        "/notifications/read-all",
        headers=headers,
    )

    assert response.status_code == 204
