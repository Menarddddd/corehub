from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.schemas.cursor import CursorPageInfo


class DepartmentBase(BaseModel):
    name: str = Field(max_length=100)


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class DepartmentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(max_length=100)


class DepartmentPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[DepartmentResponse]
    page_info: CursorPageInfo
