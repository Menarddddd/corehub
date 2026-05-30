from enum import Enum


# users
class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"


# tasks
class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TaskView(str, Enum):
    ASSIGNED = "assigned"
    CREATED = "created"


class TaskDue(str, Enum):
    OVERDUE = "overdue"
    TODAY = "today"
    THIS_WEEK = "this_week"


# notifications
class NotificationType(str, Enum):
    MESSAGE = "message"
    TASK_ASSIGNED = "task_assigned"
    ANNOUNCEMENT = "announcement"


# announcements
class AnnouncementPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
