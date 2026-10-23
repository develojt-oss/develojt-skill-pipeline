---
paths:
  - "**/*.py"
---

# Python Coding Rules (based on PEP 8 + practical extensions)

## Table of Contents
1. [Naming Rules](#1-naming-rules)
2. [Indentation & Whitespace](#2-indentation--whitespace)
3. [Braces & Blocks](#3-block-structure)
4. [Comments & Docstring](#4-comments--docstring)
5. [Functions & Parameters](#5-functions--parameters)
6. [Import Rules](#6-import-rules)
7. [Type Hints](#7-type-hints)
8. [Exception Handling](#8-exception-handling)
9. [String Handling](#9-string-handling)
10. [File Rules](#10-file-rules)

---

## 1. Naming Rules

| Target | Style | Example |
|------|--------|------|
| Variable | snake_case | `user_name`, `total_count` |
| Function | snake_case | `get_user_by_id()`, `calculate_total()` |
| Class | PascalCase | `UserService`, `DataProcessor` |
| Constant | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| Module/file | snake_case | `data_loader.py`, `user_service.py` |
| Package | snake_case (short) | `utils`, `models`, `core` |
| Private variable | _prefix | `_internal_cache`, `_config` |
| Name mangling | __prefix | `__secret_key` (class-internal only) |
| Magic method | __both sides__ | `__init__`, `__str__`, `__repr__` |
| Boolean variable | is/has/can prefix | `is_active`, `has_permission`, `can_edit` |

```python
# Good example
user_count = 10
max_retry_count = 3
is_authenticated = True

def get_active_users(role: str) -> list[User]:
    ...

class UserRepository:
    _connection_pool = None
    
    def __init__(self, db_url: str):
        self._db_url = db_url

# Bad example
userCount = 10        # no camelCase
MaxRetryCount = 3     # PascalCase is for classes only
authenticated = True  # Booleans should use the is/has prefix
```

---

## 2. Indentation & Whitespace

### Indentation
- **4 spaces** (no tabs)
- Continuation-line alignment: align with the opening parenthesis or use a hanging indent

```python
# Align with the opening parenthesis
result = some_function(arg_one, arg_two,
                       arg_three, arg_four)

# Hanging indent (recommended)
result = some_function(
    arg_one, arg_two,
    arg_three, arg_four,
)

# When the conditional is long
if (first_condition
        and second_condition
        and third_condition):
    do_something()
```

### Whitespace Rules
```python
# Spaces around operators
x = 1 + 2
y = x * 3 - 1

# No spaces around keyword arguments/defaults
def create_user(name: str, role: str = "viewer"):
    ...

# Space after commas
items = [1, 2, 3]
data = {"key": "value", "count": 10}

# No spaces in slices
items[1:3]
items[::2]

# No space before the function-call parenthesis
print("hello")      # O
print ("hello")     # X
```

### Blank Lines
- Between top-level functions/classes: **2 lines**
- Between methods inside a class: **1 line**
- To separate logical sections: **1 line**

---

## 3. Block Structure

Python separates blocks by indentation instead of braces.

```python
# One-line if only when it reads well
if is_valid: return result

# Generally, separating the block is recommended
if is_valid:
    return result
else:
    raise ValueError("Invalid input")

# Ternary operator (short expressions only)
status = "active" if is_enabled else "inactive"

# Context manager
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Multiple context managers (3.10+)
with (
    open("input.txt") as fin,
    open("output.txt", "w") as fout,
):
    fout.write(fin.read())
```

---

## 4. Comments & Docstring

### Inline Comments
```python
# Write above the code (recommended)
# Check the user's active status, then refresh the session
if user.is_active:
    session.refresh()

x = x + 1  # minimize inline comments; keep 2+ spaces from the code
```

### Docstring (Google style recommended)
```python
def fetch_users(
    role: str,
    limit: int = 100,
    include_inactive: bool = False,
) -> list[User]:
    """Retrieve the list of users with the given role.

    Filters users by role from the database and returns them.
    Whether to include inactive users can be selected.

    Args:
        role: The user role to query ("admin", "editor", "viewer").
        limit: Maximum number of results to return. Defaults to 100.
        include_inactive: If True, also include inactive users.

    Returns:
        A list of User objects. Empty list if there are no results.

    Raises:
        ValueError: When role is invalid.
        DatabaseError: On DB connection failure.
    """
    ...


class UserService:
    """Service responsible for user-related business logic.

    Attributes:
        repo: UserRepository instance.
        cache_ttl: Cache time-to-live (seconds).
    """

    def __init__(self, repo: UserRepository, cache_ttl: int = 300):
        ...
```

### TODO / FIXME
```python
# TODO(develojt): need to add cache invalidation logic
# FIXME: intermittent failure due to a concurrency issue
# HACK: temporary workaround; to be refactored in v2.0
```

---

## 5. Functions & Parameters

### Function Design Principles
- A function should do **one thing** only
- Function length: **within 30 lines** recommended
- Parameters: **5 or fewer** recommended; when exceeded, group them into a dataclass/dict

```python
# Good example: a clear signature
def send_notification(
    user_id: int,
    message: str,
    *,                          # force keyword-only
    channel: str = "email",
    priority: int = 1,
) -> bool:
    ...

# Group many settings into a dataclass
@dataclass
class NotificationConfig:
    channel: str = "email"
    priority: int = 1
    retry_count: int = 3
    timeout: float = 5.0

def send_notification(
    user_id: int,
    message: str,
    config: NotificationConfig | None = None,
) -> bool:
    config = config or NotificationConfig()
    ...
```

### Return Values
```python
# Keep a single return type
def find_user(user_id: int) -> User | None:
    ...

# Use NamedTuple for multiple return values
class ParseResult(NamedTuple):
    success: bool
    data: dict
    errors: list[str]

def parse_input(raw: str) -> ParseResult:
    ...
```

---

## 6. Import Rules

### Order (isort default)
```python
# 1. Standard library
import os
import sys
from pathlib import Path

# 2. Third-party
import numpy as np
import pandas as pd
from fastapi import FastAPI, Depends

# 3. Local/project
from app.models import User
from app.services.auth import AuthService
```

### Rules
- **One blank line** between each group
- No `import *` (explicit imports only)
- Prefer absolute-path imports (`from app.models import User`)
- Avoid circular imports: use TYPE_CHECKING

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services import UserService
```

---

## 7. Type Hints

```python
from typing import Any, Optional  # 3.9 or lower
# On 3.10+, built-in types can be used directly

# Basic types
name: str = "Claude"
count: int = 0
ratio: float = 0.5
items: list[str] = []
mapping: dict[str, int] = {}
unique: set[int] = set()
pair: tuple[str, int] = ("a", 1)

# Optional (None allowed)
result: str | None = None       # 3.10+
result: Optional[str] = None    # 3.9 or lower

# Callable
from collections.abc import Callable
handler: Callable[[str, int], bool]

# Generic
from typing import TypeVar, Generic
T = TypeVar("T")

class Repository(Generic[T]):
    def get(self, id: int) -> T | None:
        ...
```

---

## 8. Exception Handling

```python
# Catch specific exceptions
try:
    user = repo.get_user(user_id)
except UserNotFoundError:
    logger.warning("User %d not found", user_id)
    return None
except DatabaseError as e:
    logger.error("DB error: %s", e)
    raise ServiceError("Failed to fetch user") from e

# Custom exceptions
class AppError(Exception):
    """Base application exception."""

class ValidationError(AppError):
    """Input validation failure."""

class NotFoundError(AppError):
    """Resource not found."""

# No bare except
try:
    ...
except:          # X - never do this
    ...

except Exception:  # O - at least Exception
    ...
```

---

## 9. String Handling

```python
# Prefer f-strings (3.6+)
message = f"User {user.name} logged in at {timestamp}"

# Long strings
query = (
    "SELECT u.id, u.name, u.email "
    "FROM users u "
    "WHERE u.role = %s "
    "ORDER BY u.created_at DESC"
)

# Raw string (regex)
pattern = r"\d{4}-\d{2}-\d{2}"

# Multi-line
description = """\
first line
second line
third line\
"""
```

---

## 10. File Rules

### Maximum Line Length
- **88 chars** (Black default) or **120 chars** (team agreement)
- URLs and long strings are allowed as exceptions

### Tool Configuration (pyproject.toml)
```toml
[tool.black]
line-length = 88

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
strict = true
```
