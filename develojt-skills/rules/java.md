---
paths:
  - "**/*.java"
---

# Java Coding Rules (Google Java Style + Spring Boot practice)

## Table of Contents
1. [Naming Rules](#1-naming-rules)
2. [Indentation & Whitespace](#2-indentation--whitespace)
3. [Brace Rules](#3-brace-rules)
4. [Comments & Javadoc](#4-comments--javadoc)
5. [Functions & Parameters](#5-functions--parameters)
6. [Import Rules](#6-import-rules)
7. [Class Design](#7-class-design)
8. [Exception Handling](#8-exception-handling)
9. [Stream & Lambda](#9-stream--lambda)
10. [File Rules](#10-file-rules)

---

## 1. Naming Rules

| Target | Style | Example |
|------|--------|------|
| Class | PascalCase | `UserService`, `DataProcessor` |
| Interface | PascalCase (no I prefix) | `UserRepository`, `Serializable` |
| Method | camelCase | `getUserById()`, `calculateTotal()` |
| Variable | camelCase | `userName`, `totalCount` |
| Constant (static final) | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| Package | lowercase concatenated words | `com.myapp.services`, `com.myapp.models` |
| Enum type | PascalCase | `UserRole`, `OrderStatus` |
| Enum value | UPPER_SNAKE_CASE | `ADMIN`, `ACTIVE`, `PENDING` |
| Generic type | single uppercase letter | `T`, `E`, `K`, `V` |
| Boolean | is/has/can prefix | `isActive`, `hasPermission` |
| Getter/Setter | get/set prefix | `getName()`, `setName()` |
| Boolean Getter | is prefix | `isActive()`, `isEmpty()` |

```java
// Good example
public class UserService {
    private static final int MAX_RETRY_COUNT = 3;
    private static final Duration DEFAULT_TIMEOUT = Duration.ofSeconds(30);
    
    private final UserRepository userRepository;
    private final Logger logger;
    
    public Optional<User> getUserById(long userId) {
        ...
    }
    
    public boolean isUserActive(long userId) {
        ...
    }
}

// Bad example
public class user_service {           // snake_case X
    private static final int maxRetry = 3;  // constants should be UPPER_SNAKE
    private UserRepository _repo;      // _ prefix X (not a Java convention)
    
    public User GetUser(long id) {     // PascalCase X → camelCase
        ...
    }
}
```

---

## 2. Indentation & Whitespace

### Indentation
- **4 spaces** (no tabs)
- Continuation lines: **8 spaces** (or 4 + 4)

```java
// Long method call
var result = userService
        .getFilteredUsers(
                UserRole.ADMIN,
                true,
                PageRequest.of(0, 50)
        );

// Long conditional
if (user.isActive()
        && user.hasPermission(Permission.EDIT)
        && !user.isLocked()) {
    processUser(user);
}

// Method chaining
List<String> names = users.stream()
        .filter(User::isActive)
        .map(User::getName)
        .sorted()
        .collect(Collectors.toList());
```

### Whitespace Rules
```java
// Space on both sides of operators
int total = price * quantity + tax;

// Space after commas
callMethod(arg1, arg2, arg3);

// Space after control-flow keywords
if (condition)
for (int i = 0; i < count; i++)
while (isRunning)

// No space after a cast
User user = (User) obj;

// Generic angle brackets — no spaces
List<String> names;
Map<String, List<User>> grouped;
```

### Blank Lines
- Within a class: **1 line** between methods
- Logical sections within a method: **1 line**
- Between import groups: **1 line**

---

## 3. Brace Rules

### K&R Style (opening brace on the same line)
```java
// Class — same line
public class UserService {

    // Method — same line
    public void processUser(User user) {
        if (user.isActive()) {
            sendNotification(user);
        } else {
            logInactiveAccess(user);
        }

        for (Item item : user.getItems()) {
            process(item);
        }

        switch (user.getRole()) {
            case ADMIN:
                handleAdmin(user);
                break;
            case EDITOR:
                handleEditor(user);
                break;
            default:
                handleDefault(user);
                break;
        }
    }
}
```

### Always Use Braces
```java
// Braces required even for a single statement
if (isValid) {
    return result;
}

// X — never omit
if (isValid)
    return result;

// Empty block: close on the same line
void onEvent() {}

// Or on separate lines
try {
    doSomething();
} catch (Exception e) {
    // Intentionally ignored — when logging is unnecessary
}
```

---

## 4. Comments & Javadoc

### Javadoc (required for public APIs)
```java
/**
 * Retrieves the list of active users with the given role.
 *
 * <p>Returns cached results first; on a cache miss, queries the DB.
 * Pagination uses Spring Data's Pageable.</p>
 *
 * @param role     the user role to query (must not be null)
 * @param pageable pagination info
 * @return a page of users. Empty page if no results.
 * @throws IllegalArgumentException when role is null
 * @throws DataAccessException when the DB connection fails
 * @since 1.2.0
 * @see UserRepository#findByRole
 */
public Page<UserDto> getActiveUsers(
        UserRole role,
        Pageable pageable) {
    ...
}

/**
 * User authentication and authorization management service.
 *
 * <p>Integrates with Spring Security to handle JWT-based authentication.
 * All public methods are thread-safe.</p>
 *
 * @author develojt
 * @version 2.1.0
 */
@Service
public class AuthService {
    ...
}
```

### Inline Comments
```java
// Business requirement: mark inactive after 30+ days without login
LocalDateTime threshold = LocalDateTime.now().minusDays(30);

int retryCount = 0; // retry count (max 3)
```

### TODO / FIXME
```java
// TODO(develojt): need to implement a cache invalidation strategy
// FIXME: intermittent deadlock from a concurrency issue
// HACK: temporary conversion for legacy API compatibility
```

---

## 5. Functions & Parameters

### Method Design
- One method, **one responsibility**
- Method length: **within 30 lines** recommended
- Parameters: **5 or fewer**; bundle into a DTO when exceeded

```java
// Good example
public Optional<UserDto> getUserById(long userId) {
    return userRepository.findById(userId)
            .map(this::toDto);
}

// Many parameters → Request DTO
public record CreateUserRequest(
        @NotBlank String name,
        @Email String email,
        UserRole role,
        boolean sendWelcomeEmail
) {
    public CreateUserRequest {
        role = role != null ? role : UserRole.VIEWER;
    }
}

public UserDto createUser(CreateUserRequest request) {
    ...
}
```

### Return Value Patterns
```java
// Optional (single lookup that may have no result)
public Optional<User> findById(long id) { ... }

// Empty collection (never return null)
public List<User> findAll() {
    return Collections.unmodifiableList(users);
}

// Result wrapper (carries success/failure info)
public record Result<T>(
        boolean success,
        T data,
        String errorMessage
) {
    public static <T> Result<T> ok(T data) {
        return new Result<>(true, data, null);
    }
    public static <T> Result<T> fail(String error) {
        return new Result<>(false, null, error);
    }
}
```

---

## 6. Import Rules

### Order
```java
// 1. java.*
import java.util.List;
import java.util.Optional;

// 2. javax.* / jakarta.*
import jakarta.validation.constraints.NotNull;

// 3. Third-party
import org.springframework.stereotype.Service;
import lombok.RequiredArgsConstructor;

// 4. Project-internal
import com.myapp.models.User;
import com.myapp.repositories.UserRepository;
```

### Rules
- **No wildcard imports** (`import java.util.*` → list individually)
- Remove unused imports immediately
- Keep static imports in a separate group, to a minimum

```java
// static import (keep to a minimum)
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.when;
```

---

## 7. Class Design

### Declaration Order
```java
public class UserService {
    // 1. static constants
    private static final Logger log = LoggerFactory.getLogger(UserService.class);
    private static final int DEFAULT_PAGE_SIZE = 20;

    // 2. static variables
    private static AtomicInteger instanceCount = new AtomicInteger(0);

    // 3. instance fields (prefer final)
    private final UserRepository userRepository;
    private final CacheManager cacheManager;
    private int retryCount;

    // 4. constructors
    public UserService(UserRepository userRepository, CacheManager cacheManager) {
        this.userRepository = userRepository;
        this.cacheManager = cacheManager;
    }

    // 5. public methods
    public UserDto getUser(long id) { ... }
    public UserDto createUser(CreateUserRequest request) { ... }

    // 6. package-private methods
    UserDto toDto(User user) { ... }

    // 7. private methods
    private void validateUser(User user) { ... }

    // 8. nested classes
    private static class CacheEntry { ... }
}
```

### Record (Java 16+, use actively for DTOs)
```java
public record UserDto(
        long id,
        String name,
        String email,
        UserRole role,
        boolean active
) {}
```

---

## 8. Exception Handling

```java
// Catch specific exceptions
try {
    User user = userRepository.findById(userId)
            .orElseThrow(() -> new UserNotFoundException(userId));
    return toDto(user);
} catch (UserNotFoundException e) {
    log.warn("User {} not found", userId);
    throw e;  // propagate as-is
} catch (DataAccessException e) {
    log.error("DB error fetching user {}", userId, e);
    throw new ServiceException("Failed to fetch user", e);
}

// Custom exception hierarchy
public class AppException extends RuntimeException {
    private final String errorCode;
    
    public AppException(String message, String errorCode) {
        super(message);
        this.errorCode = errorCode;
    }
    
    public AppException(String message, String errorCode, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }
}

public class NotFoundException extends AppException {
    public NotFoundException(String resource, Object id) {
        super(
            String.format("%s not found: %s", resource, id),
            "NOT_FOUND"
        );
    }
}

// Spring Boot @ControllerAdvice
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(NotFoundException e) {
        return ResponseEntity.status(404)
                .body(new ErrorResponse(e.getErrorCode(), e.getMessage()));
    }
}

// Absolutely forbidden patterns
catch (Exception e) { }            // no empty catch
catch (Exception e) { e.printStackTrace(); }  // forbidden in production
```

---

## 9. Stream & Lambda

```java
// Stream chaining — align one call per line
List<String> activeAdminNames = users.stream()
        .filter(User::isActive)
        .filter(u -> u.getRole() == UserRole.ADMIN)
        .map(User::getName)
        .sorted()
        .toList();  // Java 16+

// Extract complex logic into a method reference or a separate method
users.stream()
        .filter(this::isEligibleForPromotion)
        .forEach(this::applyPromotion);

// Collectors
Map<UserRole, List<User>> grouped = users.stream()
        .collect(Collectors.groupingBy(User::getRole));

// Optional chaining
String displayName = userRepository.findById(userId)
        .map(User::getName)
        .map(String::toUpperCase)
        .orElse("Unknown");

// Lambda — omit braces for a single line
list.forEach(item -> process(item));

// Use braces for multiple lines
list.forEach(item -> {
    validate(item);
    process(item);
    log(item);
});
```

---

## 10. File Rules

### File Rules
- **One file = one public class**
- File name = class name (`UserService.java`)
- Max line length: **120 characters** (Google: 100)
- File encoding: **UTF-8**
