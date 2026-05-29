from uuid import UUID


from app.core.exceptions import (
    BadRequestException,
    FieldNotFoundException,
)
from app.models.tasks import Task
from app.models.users import User
from app.repositories.task import TaskRepository
from app.schemas.cursor import CursorPageInfo
from app.schemas.task import TaskCreate, TaskPageResponse, TaskResponse, TaskUpdate
from app.utils.cursor import get_cursor_info


class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def get_tasks_service(
        self, limit: int, cursor: str | None
    ) -> TaskPageResponse:
        tasks = await self.repo.get_tasks(limit=limit, cursor=cursor)

        tasks, has_next, next_cursor = get_cursor_info(tasks, limit)

        return TaskPageResponse(
            items=[TaskResponse.model_validate(task) for task in tasks],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

    async def get_task_service(self, task_id: UUID) -> Task | None:
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise FieldNotFoundException("tasks", str(task_id))

        return task

    async def create_task_service(
        self, form_data: TaskCreate, current_user: User
    ) -> Task:
        try:
            new_task = Task(
                assigned_to_id=form_data.assigned_to_id,
                created_by_id=current_user.id,
                title=form_data.title,
                description=form_data.description,
                status=form_data.status,
                priority=form_data.priority,
                due_date=form_data.due_date,
            )
            return await self.repo.save(new_task)

        except Exception:
            raise BadRequestException("Task could not be created")

    async def update_task_service(
        self,
        task_id: UUID,
        form_data: TaskUpdate,
    ) -> Task:
        task_data = form_data.model_dump(exclude_unset=True)
        if not task_data:
            raise BadRequestException("No fields to update")

        task = await self.repo.get_by_id(task_id)
        if not task:
            raise FieldNotFoundException("tasks", str(task_id))

        for key, val in task_data.items():
            setattr(task, key, val)

        return await self.repo.update(task)

    async def delete_task_service(self, task_id: UUID) -> None:
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise FieldNotFoundException("tasks", str(task_id))

        await self.repo.delete(task)
