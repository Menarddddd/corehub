import base64
from typing import Sequence
from app.schemas.cursor import CursorPayload


def encode_cursor(payload: CursorPayload) -> str:
    """
    Encode CursorPayload to a URL-safe base64 string.
    Strips trailing = for cleaner URLs.
    """
    json_data = payload.model_dump_json()
    encoded = base64.urlsafe_b64encode(json_data.encode()).decode().rstrip("=")
    return encoded


def decode_cursor(cursor: str) -> CursorPayload:
    """
    Decode cursor and adds back the stripped =
    """
    padding = "=" * (-len(cursor) % 4)
    decoded_bytes = base64.urlsafe_b64decode(cursor + padding)
    decoded_str = decoded_bytes.decode()
    return CursorPayload.model_validate_json(decoded_str)


def get_cursor_info(data: Sequence, limit: int) -> tuple[list, bool, str | None]:
    """
    Determines if a next page exists (using limit + 1 trick)
    and builds the encoded cursor from the last item.
    """
    has_next = len(data) > limit
    items = list(data[:limit]) if has_next else list(data)

    next_cursor = None
    if has_next and items:
        last_item = items[-1]
        next_cursor = encode_cursor(
            CursorPayload(item_id=last_item.id, created_at=last_item.created_at)
        )

    return items, has_next, next_cursor
