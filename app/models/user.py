import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

USERS_FILE = Path("users_db.json")


class UserInDB(BaseModel):
    user_id: str
    email: str
    hashed_password: str


def _load_users() -> dict:
    if not USERS_FILE.exists():
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def _save_users(users: dict) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def get_user(email: str) -> Optional[UserInDB]:
    users = _load_users()
    user_data = users.get(email)
    return UserInDB(**user_data) if user_data else None


def create_user(email: str, hashed_password: str) -> UserInDB:
    users = _load_users()
    if email in users:
        raise ValueError("A user with this email already exists.")
    user_id = f"user_{len(users) + 1}"
    user = UserInDB(user_id=user_id, email=email, hashed_password=hashed_password)
    users[email] = user.model_dump()
    _save_users(users)
    return user
