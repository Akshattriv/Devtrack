"""
Plain-Python OOP domain layer for DevTrack.

These classes are intentionally decoupled from Django's ORM. They encode
the business rules (validation, describe(), to_dict()) required by the
assignment. issues/models.py holds the Django ORM models used for actual
database persistence; views.py bridges the two — it builds one of these
entities to validate/describe incoming data, then persists the result
using the ORM models.
"""

from abc import ABC, abstractmethod
from datetime import datetime

VALID_STATUSES = ('open', 'in_progress', 'resolved', 'closed')
VALID_PRIORITIES = ('low', 'medium', 'high', 'critical')


class BaseEntity(ABC):
    """Abstract base class for all domain entities."""

    @abstractmethod
    def validate(self):
        """Subclasses must implement their own validation rules."""
        pass

    def to_dict(self):
        return {
            key: value
            for key, value in self.__dict__.items()
        }


class Reporter(BaseEntity):
    def __init__(self, id, name, email, team):
        self.id = id
        self.name = name
        self.email = email
        self.team = team

    def validate(self):
        if not self.name:
            raise ValueError('Name cannot be empty')
        if not self.email or '@' not in self.email:
            raise ValueError('Invalid email')
        if not self.team:
            raise ValueError('Team cannot be empty')


class Issue(BaseEntity):
    def __init__(self, id, title, description, status, priority, reporter_id, created_at=None):
        self.id = id
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.reporter_id = reporter_id
        self.created_at = created_at or str(datetime.now())

    def validate(self):
        if not self.title:
            raise ValueError('Title cannot be empty')
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Status must be one of {VALID_STATUSES}")
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of {VALID_PRIORITIES}")
        if self.reporter_id is None:
            raise ValueError('reporter_id is required')

    def describe(self):
        return f"{self.title} [{self.priority}]"


class CriticalIssue(Issue):
    def describe(self):
        return f"[URGENT] {self.title} — needs immediate attention"


class LowPriorityIssue(Issue):
    def describe(self):
        return f"{self.title} — low priority, handle when free"


def build_issue(data):
    """Factory: instantiate the correct Issue subclass based on priority."""
    kwargs = dict(
        id=data.get('id'),
        title=data.get('title'),
        description=data.get('description'),
        status=data.get('status'),
        priority=data.get('priority'),
        reporter_id=data.get('reporter_id'),
    )
    priority = data.get('priority')
    if priority == 'critical':
        return CriticalIssue(**kwargs)
    elif priority == 'low':
        return LowPriorityIssue(**kwargs)
    else:
        return Issue(**kwargs)
