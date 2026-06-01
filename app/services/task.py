import json

import redis.asyncio as aioredis
from datetime import date, timedelta
from uuid import UUID

from app.core.exceptions import (
    BadRequestException,
    FieldNotFoundException,
    ForbiddenException,
)
from app.models.notifications import Notification
from app.models.tasks import Task
from app.models.users import User
from app.repositories.notification import NotificationRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.schemas.cursor import CursorPageInfo
from app.schemas.enum import (
    NotificationTitle,
    NotificationType,
    Role,
    TaskDue,
    TaskPriority,
    TaskStatus,
    TaskView,
)
from app.schemas.task import (
    TaskCreate,
    TaskPageResponse,
    TaskResponse,
    TaskStatusChange,
    TaskUpdate,
)
from app.utils.cursor import get_cursor_info


class TaskService:
    def __init__(
        self,
        repo: TaskRepository,
        user_repo: UserRepository,
        notif_repo: NotificationRepository,
        redis: aioredis.Redis,
    ):
        self.repo = repo
        self.user_repo = user_repo
        self.notif_repo = notif_repo
        self.redis = redis

    def _build_due_conditions(self, due: TaskDue) -> list:
        """
        Build SQLAlchemy WHERE conditions based on the due date filter.
        OVERDUE: tasks past their due date and not yet completed.
        TODAY: tasks due exactly today.
        THIS_WEEK: tasks due between Monday and Sunday of current week.
        """
        conditions = []
        today = date.today()

        if due == TaskDue.OVERDUE:
            conditions.append(Task.due_date < today)
            conditions.append(Task.status != TaskStatus.COMPLETED.value)

        elif due == TaskDue.TODAY:
            conditions.append(Task.due_date == today)

        elif due == TaskDue.THIS_WEEK:
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            conditions.append(Task.due_date >= start_of_week)
            conditions.append(Task.due_date <= end_of_week)

        return conditions

    def _build_common_conditions(
        self,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due: TaskDue | None = None,
    ) -> list:
        """
        Build shared filter conditions for status, priority, and due date.
        Used by both get_tasks_service and get_my_tasks_service
        to avoid duplicated logic.
        """
        conditions = []

        if status is not None:
            conditions.append(Task.status == status.value)

        if priority is not None:
            conditions.append(Task.priority == priority.value)

        if due is not None:
            conditions.extend(self._build_due_conditions(due))

        return conditions

    async def _build_users_cache_key(
        self,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        due: TaskDue | None,
        limit: int,
        cursor: str | None,
    ) -> str:
        """
        Build a unique cache key based on the query parameters.
        Each unique combination of filters = unique key.
        """
        s = status.value if status else "all"
        p = priority.value if priority else "all"
        d = due.value if due else "all"
        c = cursor if cursor else "none"

        return f"task:status:{s}:priority:{p}:due{d}:limit:{limit}:cursor:{c}"

    async def get_tasks_service(
        self,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        due: TaskDue | None,
        limit: int,
        cursor: str | None,
    ) -> TaskPageResponse:
        """
        Fetch all tasks with optional filters and cursor-based pagination.
        Builds conditions dynamically based on provided filter arguments.
        Implements caching with TTL of 300 or 5 mins
        """
        cache_key = await self._build_users_cache_key(
            status=status, priority=priority, due=due, limit=limit, cursor=cursor
        )
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            data = json.loads(cached_data)
            return TaskPageResponse(**data)

        conditions = self._build_common_conditions(
            status=status,
            priority=priority,
            due=due,
        )

        tasks = await self.repo.get_tasks(*conditions, limit=limit, cursor=cursor)
        tasks, has_next, next_cursor = get_cursor_info(tasks, limit)

        response = TaskPageResponse(
            items=[TaskResponse.model_validate(task) for task in tasks],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

        await self.redis.set(
            cache_key, json.dumps(response.model_dump(), default=str), ex=300
        )

        return response

    async def get_user_tasks_service(
        self,
        user_id: UUID,
        task_view: TaskView | None,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        due: TaskDue | None,
        limit: int,
        cursor: str | None,
    ) -> TaskPageResponse:
        """
        Fetch tasks belonging to the current user with optional filters.
        Defaults to showing tasks ASSIGNED to the user if task_view is not provided.
        task_view=assigned → tasks where assigned_to_id matches current user.
        task_view=created  → tasks where created_by_id matches current user.
        Implements caching with TTL of 180 or 3 mins
        """
        result = await self._build_users_cache_key(
            status=status, priority=priority, due=due, limit=limit, cursor=cursor
        )
        cache_key = result.replace("users:", f"users:{user_id}")

        cached_data = await self.redis.get(cache_key)

        if cached_data:
            data = json.loads(cached_data)
            return TaskPageResponse(**data)

        conditions = self._build_common_conditions(
            status=status, priority=priority, due=due
        )

        # Default to assigned tasks if task_view is None
        if task_view is None or task_view == TaskView.ASSIGNED:
            conditions.append(Task.assigned_to_id == user_id)
        else:
            conditions.append(Task.created_by_id == user_id)

        tasks = await self.repo.get_tasks(*conditions, limit=limit, cursor=cursor)
        tasks, has_next, next_cursor = get_cursor_info(tasks, limit)

        response = TaskPageResponse(
            items=[TaskResponse.model_validate(task) for task in tasks],
            page_info=CursorPageInfo(has_next=has_next, next_cursor=next_cursor),
        )

        await self.redis.set(
            cache_key,
            json.dumps(response.model_dump(), default=str),
            ex=180,
        )

        return response

    async def get_task_service(self, task_id: UUID) -> Task:
        """
        Fetch a single task by its ID.
        Raises 404 if the task does not exist.
        """
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise FieldNotFoundException("tasks", str(task_id))
        return task

    async def get_my_task_service(
        self, task_id: UUID, current_user: User
    ) -> TaskResponse:
        """
        Fetch a single task that is assigned to the current user.
        Raises 404 if the task does not exist.
        Raises 403 if the task is not assigned to the current user.
        Uses caching TTL 5 mins or 300 secs
        """
        cache_key = f"task:{task_id}:user:{current_user.id}"
        cached_data = await self.redis.get(cache_key)

        if cached_data:
            data = json.loads(cached_data)
            return TaskResponse(**data)

        task = await self.repo.get_by_id(task_id)

        if not task:
            raise FieldNotFoundException("tasks", str(task_id))

        if task.assigned_to_id != current_user.id:
            raise ForbiddenException("You are not assigned to this task")

        response = TaskResponse.model_validate(task)

        await self.redis.set(
            cache_key,
            json.dumps(response.model_dump(), default=str),
            ex=300,
        )

        return response

    async def create_task_service(
        self, form_data: TaskCreate, current_user: User
    ) -> Task:
        """
        Create and assign a new task.
        Prevents self-assignment for all roles.
        Managers can only assign tasks to employees.
        Removes broad exception catching to expose real errors during development.
        Notifies assigned user after creating task
        """
        # Prevent self-assignment
        if form_data.assigned_to_id == current_user.id:
            raise BadRequestException("You cannot assign a task to yourself")

        assigned_user = await self.user_repo.get_by_id(form_data.assigned_to_id)
        if not assigned_user:
            raise FieldNotFoundException("users", str(form_data.assigned_to_id))

        if assigned_user.department_id != current_user.department_id:
            raise ForbiddenException(
                "You cannot assign a task to employees outside your department"
            )

        new_task = Task(
            assigned_to_id=form_data.assigned_to_id,
            created_by_id=current_user.id,
            title=form_data.title,
            description=form_data.description,
            status=form_data.status,
            priority=form_data.priority,
            due_date=form_data.due_date,
        )

        notification = Notification(
            user_id=form_data.assigned_to_id,
            type=NotificationType.TASK_ASSIGNED.value,
            title=NotificationTitle.TASK,
            body=form_data.description,
        )

        # Notification for assigned user
        await self.notif_repo.save(notification)

        return await self.repo.save(new_task)

    async def update_status_task_service(
        self, task_id: UUID, form_data: TaskStatusChange, current_user: User
    ) -> Task:
        """
        Update the status of a task.
        Employees can only update tasks assigned to them.
        Admins and Managers can update status of any task regardless of assignment.
        Raises 404 if task does not exist.
        Raises 403 if an employee tries to update a task not assigned to them.
        """
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise FieldNotFoundException("tasks", str(task_id))

        # Admins and Managers can update any task status
        # Only Employees can update their own assigned tasks
        if current_user.role == Role.EMPLOYEE.value:
            if task.assigned_to_id != current_user.id:
                raise ForbiddenException(
                    "You can only update the status of tasks assigned to you"
                )

        task.status = form_data.status
        updated_task = await self.repo.update(task)

        notification = Notification(
            user_id=updated_task.assigned_to_id,
            type=NotificationType.TASK_STATUS_CHANGED.value,
            title=NotificationTitle.UPDATED_TASK.value,
            body=updated_task.description,
        )

        await self.notif_repo.save(notification)

        return updated_task

    async def update_task_service(
        self,
        task: Task,
        form_data: TaskUpdate,
    ) -> Task:
        """
        Update the details of an existing task (title, description, priority, etc).
        Task object is pre-validated by check_task_owner dependency.
        Raises 400 if no fields are provided in the request body.
        """
        task_data = form_data.model_dump(exclude_unset=True)
        if not task_data:
            raise BadRequestException("No fields to update")

        for key, val in task_data.items():
            setattr(task, key, val)

        updated_task = await self.repo.update(task)

        notification = Notification(
            user_id=updated_task.assigned_to_id,
            type=NotificationType.TASK_UPDATE.value,
            title=NotificationTitle.UPDATED_TASK.value,
            body=updated_task.description,
        )

        await self.notif_repo.save(notification)

        return updated_task

    async def update_due_date_service(self, task: Task, due_date: date) -> Task:
        """
        Update the due date of an existing task.
        Task object is pre-validated by check_task_owner dependency.
        Uses repo.update since the task already exists in the database.
        """
        task.due_date = due_date
        updated_task = await self.repo.update(task)

        notification = Notification(
            user_id=updated_task.assigned_to_id,
            type=NotificationType.TASK_DUE_DATE_CHANGED.value,
            title=NotificationTitle.UPDATED_TASK.value,
            body=updated_task.description,
        )

        await self.notif_repo.save(notification)

        return updated_task

    async def delete_task_service(self, task_id: UUID) -> None:
        """
        Hard delete any task by its ID.
        Used by ADMIN for administrative deletion regardless of ownership.
        Raises 404 if the task does not exist.
        """
        task = await self.repo.get_by_id(task_id)
        if not task:
            raise FieldNotFoundException("tasks", str(task_id))
        await self.repo.delete(task)

    async def delete_my_task_service(self, task: Task) -> None:
        """
        Delete a task created by the current user.
        Task object is pre-validated by check_task_owner dependency.
        """
        await self.repo.delete(task)
