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
    CANCELLED = "cancelled"


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
class NotificationTitle(str, Enum):
    TASK = "New Task Assigned!"
    UPDATED_TASK = "New Updated Task"
    MESSAGE = "New Message Received"
    ANNOUNCEMENT = "New Announcement"


class NotificationType(str, Enum):
    # Tasks
    TASK_ASSIGNED = "task_assigned"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_UPDATE = "task_changed"
    TASK_DUE_DATE_CHANGED = "task_due_date_changed"
    TASK_DELETED = "task_deleted"

    # Messages
    NEW_MESSAGE = "new_message"

    # Department
    DEPARTMENT_ASSIGNED = "department_assigned"
    DEPARTMENT_REMOVED = "department_removed"

    # Account
    ROLE_CHANGED = "role_changed"


# announcements
class AnnouncementPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnnouncementStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
