def clean_user_info(user_data: dict) -> dict:
    cleaned = {}

    for key, val in user_data.items():
        if not isinstance(val, str):
            cleaned[key] = val
            continue
        if key in ["username", "email"]:
            cleaned[key] = val.strip().lower()
        elif key in ["first_name", "last_name"]:
            cleaned[key] = val.strip()
        else:
            cleaned[key] = val

    return cleaned
