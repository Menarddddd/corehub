from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from app.schemas.cursor import CursorPageInfo
from app.schemas.enum import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(max_length=100)
    description: str = Field(min_length=1)
    status: TaskStatus
    priority: TaskPriority
    due_date: date = Field(description="2026-05-30")


class TaskCreate(TaskBase):
    assigned_to_id: UUID
    due_date: date = Field(description="2026-05-30")

    @field_validator("due_date")
    @classmethod
    def check_due_date(cls, value: date):
        if value <= date.today():
            raise ValueError("Dute date must be in the future")
        return value


class TaskResponse(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assigned_to_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, min_length=1)
    status: TaskStatus | None = Field(default=None)
    priority: TaskPriority | None = Field(default=None)


class TaskStatusChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: TaskStatus


class TaskDueDateUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    due_date: date = Field(description="2026-05-30")

    @field_validator("due_date")
    @classmethod
    def check_due_date(cls, value: date):
        if value <= date.today():
            raise ValueError("Dute date must be in the future")
        return value


class TaskPageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[TaskResponse]
    page_info: CursorPageInfo
