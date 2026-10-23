---
paths:
  - "**/*.cs"
---

# C# Coding Rules (based on Microsoft official guidelines)

## Table of Contents
1. [Naming Rules](#1-naming-rules)
2. [Indentation & Whitespace](#2-indentation--whitespace)
3. [Brace Rules](#3-brace-rules)
4. [Comments & XML Doc](#4-comments--xml-doc)
5. [Functions & Parameters](#5-functions--parameters)
6. [Using & Namespace](#6-using--namespace)
7. [Properties & Fields](#7-properties--fields)
8. [Exception Handling](#8-exception-handling)
9. [Async Patterns](#9-async-patterns)
10. [File Rules](#10-file-rules)

---

## 1. Naming Rules

| Target | Style | Example |
|------|--------|------|
| Class | PascalCase | `UserService`, `DataProcessor` |
| Interface | I + PascalCase | `IUserRepository`, `ILogger` |
| Method | PascalCase | `GetUserById()`, `CalculateTotal()` |
| Property | PascalCase | `FirstName`, `IsActive` |
| Public field | PascalCase | `MaxRetryCount` |
| Private field | _camelCase | `_userRepository`, `_logger` |
| Parameter | camelCase | `userId`, `userName` |
| Local variable | camelCase | `currentUser`, `totalAmount` |
| Constant | PascalCase | `DefaultTimeout`, `MaxBufferSize` |
| Enum | PascalCase | `UserRole.Admin`, `Status.Active` |
| Enum value | PascalCase | `Active`, `Inactive`, `Pending` |
| Event | PascalCase | `OnUserCreated`, `DataReceived` |
| Generic type | T + PascalCase | `TEntity`, `TResult`, `TKey` |
| Namespace | PascalCase | `MyApp.Services.Auth` |
| Boolean | is/has/can prefix | `IsValid`, `HasPermission`, `CanEdit` |

```csharp
// Good example
public class UserService
{
    private readonly IUserRepository _userRepository;
    private readonly ILogger<UserService> _logger;
    private const int DefaultPageSize = 20;

    public string FirstName { get; set; }
    public bool IsActive { get; private set; }

    public async Task<User?> GetUserByIdAsync(int userId)
    {
        var currentUser = await _userRepository.FindAsync(userId);
        return currentUser;
    }
}

// Bad example
public class userService            // lowercase start — X
{
    private IUserRepository repo;    // missing _ prefix
    private const int DEFAULT_SIZE = 20;  // UPPER_SNAKE X → PascalCase
    
    public string firstName;         // public field should be PascalCase
    
    public User get_user(int id)     // snake_case X, missing Async suffix
    {
        ...
    }
}
```

---

## 2. Indentation & Whitespace

### Indentation
- **4 spaces** (no tabs)
- Continuation lines: 4 additional spaces of indentation

```csharp
// Long method call
var result = await userService
    .GetFilteredUsersAsync(
        role: UserRole.Admin,
        isActive: true,
        pageSize: 50
    );

// Long conditional
if (user.IsActive
    && user.HasPermission(Permission.Edit)
    && !user.IsLocked)
{
    ProcessUser(user);
}

// LINQ — align one call per line
var activeAdmins = users
    .Where(u => u.IsActive)
    .Where(u => u.Role == UserRole.Admin)
    .OrderBy(u => u.Name)
    .ToList();
```

### Whitespace Rules
```csharp
// Space on both sides of operators
int total = price * quantity + tax;

// Space after commas
CallMethod(arg1, arg2, arg3);

// Space after control-flow keywords
if (condition)
for (int i = 0; i < count; i++)
while (isRunning)

// Space after a cast
var user = (User) obj;       // X
var user = (User)obj;        // O
```

### Blank Lines
- Between methods: **1 line**
- Between logical sections: **1 line**
- Between field/property/method groups within a class: **1 line**
- End of file: 1 blank line

---

## 3. Brace Rules

### Allman Style (C# standard)
```csharp
// Every brace starts on a new line (Allman style)
public class UserService
{
    public void ProcessUser(User user)
    {
        if (user.IsActive)
        {
            SendNotification(user);
        }
        else
        {
            LogInactiveAccess(user);
        }
    }

    // Same for for, foreach, while
    for (int i = 0; i < items.Count; i++)
    {
        Process(items[i]);
    }

    foreach (var item in collection)
    {
        Process(item);
    }
}
```

### No Brace Omission
```csharp
// Braces required even for a single line
if (isValid)
{
    return result;
}

// X — never omit braces
if (isValid)
    return result;

// Exception: simple switch expression (C# 8+)
var message = status switch
{
    Status.Active => "Active",
    Status.Inactive => "Inactive",
    _ => "Unknown",
};
```

---

## 4. Comments & XML Doc

### XML Documentation (required for public APIs)
```csharp
/// <summary>
/// Retrieves the list of active users with the given role.
/// </summary>
/// <param name="role">The user role to query.</param>
/// <param name="pageSize">Number of results per page. Default 20.</param>
/// <returns>A list of User. Empty list if no results.</returns>
/// <exception cref="ArgumentNullException">
/// When <paramref name="role"/> is null.
/// </exception>
/// <remarks>
/// Returns cached results first; on a cache miss, queries the DB.
/// </remarks>
public async Task<List<User>> GetActiveUsersAsync(
    string role,
    int pageSize = 20)
{
    ...
}

/// <summary>
/// User authentication and authorization management service.
/// </summary>
/// <example>
/// <code>
/// var service = new AuthService(repo, logger);
/// var token = await service.AuthenticateAsync(credentials);
/// </code>
/// </example>
public class AuthService
{
    ...
}
```

### Inline Comments
```csharp
// Business requirement: mark inactive after 30+ days without login
var threshold = DateTime.UtcNow.AddDays(-30);

int retryCount = 0; // retry count (max 3)
```

### TODO / FIXME
```csharp
// TODO: need to implement a cache invalidation strategy
// FIXME: intermittent deadlock from a concurrency issue
// HACK: temporary workaround for legacy API compatibility
```

---

## 5. Functions & Parameters

### Method Design Principles
- One method, **one responsibility**
- Method length: **within 30 lines** recommended
- Parameters: **5 or fewer**; bundle into a DTO/record when exceeded
- Async methods require the **Async suffix**

```csharp
// Good example: clear signature
public async Task<UserDto?> GetUserByIdAsync(
    int userId,
    CancellationToken cancellationToken = default)
{
    ...
}

// When there are many parameters, bundle them into a Request object
public record CreateUserRequest(
    string Name,
    string Email,
    UserRole Role = UserRole.Viewer,
    bool SendWelcomeEmail = true
);

public async Task<UserDto> CreateUserAsync(
    CreateUserRequest request,
    CancellationToken cancellationToken = default)
{
    ...
}
```

### Return Values
```csharp
// Nullable return (when it may not be found)
public async Task<User?> FindUserAsync(int id) { ... }

// Result pattern (carries success/failure info)
public record Result<T>(
    bool IsSuccess,
    T? Data,
    string? ErrorMessage
);

public async Task<Result<User>> TryGetUserAsync(int id)
{
    ...
}
```

---

## 6. Using & Namespace

### using Order
```csharp
// 1. System namespaces
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

// 2. Third-party
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

// 3. Project-internal
using MyApp.Models;
using MyApp.Services;

// static using (rarely)
using static System.Math;
```

### File-scoped namespace (C# 10+, recommended)
```csharp
// O — file-scoped namespace (saves one indent level)
namespace MyApp.Services;

public class UserService
{
    ...
}

// X — block-scoped (legacy)
namespace MyApp.Services
{
    public class UserService
    {
        ...
    }
}
```

### Global using (C# 10+)
```csharp
// Centralize in a GlobalUsings.cs file
global using System;
global using System.Collections.Generic;
global using System.Threading.Tasks;
global using Microsoft.Extensions.Logging;
```

---

## 7. Properties & Fields

```csharp
public class User
{
    // Constants
    private const int MaxNameLength = 100;

    // Static fields
    private static readonly TimeSpan CacheDuration = TimeSpan.FromMinutes(5);

    // Private fields (prefer readonly)
    private readonly ILogger<User> _logger;
    private int _loginCount;

    // Auto-properties
    public int Id { get; init; }
    public string Name { get; set; } = string.Empty;
    public bool IsActive { get; private set; } = true;

    // Computed property
    public string DisplayName => $"{Name} (#{Id})";

    // Constructor
    public User(int id, string name, ILogger<User> logger)
    {
        Id = id;
        Name = name ?? throw new ArgumentNullException(nameof(name));
        _logger = logger;
    }

    // Methods
    public void Deactivate()
    {
        IsActive = false;
        _logger.LogInformation("User {Id} deactivated", Id);
    }
}
```

### Declaration Order (within a class)
1. Constants (const)
2. Static fields
3. Instance fields
4. Properties
5. Constructors
6. Public methods
7. Private methods
8. Nested types

---

## 8. Exception Handling

```csharp
// Catch specific exceptions
try
{
    var user = await _repository.GetByIdAsync(userId);
}
catch (EntityNotFoundException)
{
    _logger.LogWarning("User {UserId} not found", userId);
    return null;
}
catch (DbException ex)
{
    _logger.LogError(ex, "DB error fetching user {UserId}", userId);
    throw new ServiceException("Failed to fetch user", ex);
}

// Custom exception hierarchy
public class AppException : Exception
{
    public string ErrorCode { get; }

    public AppException(string message, string errorCode, Exception? inner = null)
        : base(message, inner)
    {
        ErrorCode = errorCode;
    }
}

public class ValidationException : AppException
{
    public IReadOnlyList<string> Errors { get; }

    public ValidationException(IReadOnlyList<string> errors)
        : base("Validation failed", "VALIDATION_ERROR")
    {
        Errors = errors;
    }
}

// catch (Exception) only at the outermost level
// re-throw with throw; (never throw ex; — loses the stack trace)
catch (Exception ex)
{
    _logger.LogError(ex, "Unexpected error");
    throw;  // O — preserves the stack trace
    // throw ex;  // X — resets the stack trace
}
```

---

## 9. Async Patterns

```csharp
// Always use the Async suffix
public async Task<User> GetUserAsync(int id, CancellationToken ct = default)
{
    return await _repository.FindAsync(id, ct)
        ?? throw new NotFoundException($"User {id} not found");
}

// ConfigureAwait(false) — in library code
public async Task<byte[]> DownloadAsync(string url)
{
    var response = await _httpClient
        .GetAsync(url)
        .ConfigureAwait(false);
    return await response.Content
        .ReadAsByteArrayAsync()
        .ConfigureAwait(false);
}

// Never call async from synchronous code
// X — .Result, .Wait() risk deadlock
var user = GetUserAsync(1).Result;

// Async streams (C# 8+)
public async IAsyncEnumerable<User> GetUsersStreamAsync(
    [EnumeratorCancellation] CancellationToken ct = default)
{
    await foreach (var user in _repository.StreamAllAsync(ct))
    {
        yield return user;
    }
}
```

---

## 10. File Rules

### File Rules
- **One file = one type** (class, interface, enum, etc.)
- File name = type name (`UserService.cs`, `IUserRepository.cs`)
- Max line length: **120 characters** recommended
- Unify team rules via .editorconfig

### .editorconfig Example
```ini
[*.cs]
indent_style = space
indent_size = 4
max_line_length = 120
dotnet_sort_system_directives_first = true
csharp_new_line_before_open_brace = all
csharp_style_var_for_built_in_types = false:suggestion
csharp_style_var_when_type_is_apparent = true:suggestion
```
