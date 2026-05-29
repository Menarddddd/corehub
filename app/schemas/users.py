from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.schemas.cursor import CursorPageInfo
from app.schemas.enums import Role


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserBase(BaseModel):
    department_id: UUID | None = None
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=7, max_length=100)
    email: EmailStr = Field(min_length=7, max_length=100)
    role: Role
    profile: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=7)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(default=None, min_length=2, max_length=100)
    last_name: str | None = Field(default=None, min_length=2, max_length=100)
    username: str | None = Field(default=None, min_length=7, max_length=100)
    email: EmailStr | None = Field(default=None, min_length=7, max_length=100)
    profile: str | None = Field(default=None, max_length=255)


class ChangePassword(BaseModel):
    current_password: str = Field(min_length=7)
    new_password: str = Field(min_length=7)

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.current_password == self.new_password:
            raise ValueError("New password cannot be the same as the current password")
        return self


class UserPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[UserResponse]
    page_info: CursorPageInfo
