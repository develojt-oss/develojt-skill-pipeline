---
paths:
  - "**/*.cpp"
  - "**/*.cc"
  - "**/*.cxx"
  - "**/*.hpp"
  - "**/*.h"
---

# C++ Coding Rules (based on Google C++ Style Guide + Modern C++)

## Table of Contents
1. [Naming Rules](#1-naming-rules)
2. [Indentation & Whitespace](#2-indentation--whitespace)
3. [Brace Rules](#3-brace-rules)
4. [Comments & Documentation](#4-comments--documentation)
5. [Functions & Parameters](#5-functions--parameters)
6. [Include Rules](#6-include-rules)
7. [Memory Management](#7-memory-management)
8. [Modern C++ Patterns](#8-modern-c-patterns)
9. [Exceptions & Error Handling](#9-exceptions--error-handling)
10. [File Rules](#10-file-rules)

---

## 1. Naming Rules

| Target | Style | Example |
|------|--------|------|
| Class/struct | PascalCase | `UserService`, `DataBuffer` |
| Function | PascalCase or camelCase¹ | `GetUserById()`, `calculateTotal()` |
| Variable | snake_case | `user_name`, `total_count` |
| Member variable | snake_case + trailing _ | `user_name_`, `buffer_size_` |
| Constant | k + PascalCase | `kMaxRetryCount`, `kDefaultTimeout` |
| Macro | UPPER_SNAKE_CASE | `MAX_BUFFER_SIZE`, `DEBUG_MODE` |
| Namespace | snake_case | `my_app`, `data_processing` |
| Enum type | PascalCase | `UserRole`, `ConnectionState` |
| Enum value | k + PascalCase | `kAdmin`, `kConnected` |
| Template parameter | PascalCase | `T`, `Container`, `Allocator` |
| Filename | snake_case | `user_service.h`, `data_processor.cpp` |
| Boolean | is/has/can prefix | `is_active`, `has_children` |

> ¹ Google style uses PascalCase; many projects use camelCase. Consistency within the team is required.

```cpp
// Good example
class UserService {
public:
    UserService(std::shared_ptr<ILogger> logger);
    
    std::optional<User> GetUserById(int user_id) const;
    bool IsActive() const { return is_active_; }

private:
    static constexpr int kMaxCacheSize = 1000;
    
    std::shared_ptr<ILogger> logger_;
    std::string connection_string_;
    bool is_active_ = false;
    int retry_count_ = 0;
};

// Bad example
class user_service {          // class should be PascalCase
    string m_connStr;         // no Hungarian notation
    int MaxCacheSize = 1000;  // constants take the k prefix
    bool active;              // members take a trailing _, bools take the is_ prefix
};
```

---

## 2. Indentation & Whitespace

### Indentation
- **4 spaces** (or 2 spaces — Google standard)
- No tabs; consistency within the project is required

```cpp
// Long function call
auto result = ProcessData(
    input_buffer,
    output_buffer,
    ProcessingOptions{
        .max_iterations = 100,
        .tolerance = 0.001
    }
);

// Long conditional — operator at the start of the line
if (first_condition
    && second_condition
    && third_condition) {
    DoSomething();
}

// Long template
template <
    typename T,
    typename Allocator = std::allocator<T>,
    typename Compare = std::less<T>>
class PriorityQueue {
    ...
};
```

### Whitespace Rules
```cpp
// Spaces around operators
int total = price * quantity + tax;

// Pointer/reference — attach to the type (recommended)
int* ptr = nullptr;        // O
const std::string& name;   // O
int *ptr = nullptr;        // X (attached to the variable — not recommended)

// Space after control-flow keywords
if (condition)
for (int i = 0; i < count; ++i)
while (is_running)

// Function call — no space before the parenthesis
DoSomething(arg1, arg2);   // O
DoSomething (arg1, arg2);  // X

// Template angle brackets — no spaces
std::vector<std::string>   // O
std::vector< std::string > // X
```

---

## 3. Brace Rules

### K&R Style (opening brace on the same line)
```cpp
// Function/method — same line or new line (consistent per project)
// Google style: same line
void ProcessUser(const User& user) {
    if (user.IsActive()) {
        SendNotification(user);
    } else {
        LogInactiveAccess(user);
    }

    for (const auto& item : user.GetItems()) {
        Process(item);
    }

    switch (user.GetRole()) {
        case UserRole::kAdmin:
            HandleAdmin(user);
            break;
        case UserRole::kEditor:
            HandleEditor(user);
            break;
        default:
            HandleDefault(user);
            break;
    }
}

// Class/struct also on the same line
class UserService {
public:
    ...
private:
    ...
};  // semicolon required
```

### Omitting Braces
```cpp
// A single statement may omit braces, but the team must agree
// When omitted, it must be on one line
if (is_valid) return result;

// Multiple lines require braces
if (is_valid) {
    LogAccess();
    return result;
}

// Nested if always uses braces
if (condition_a) {
    if (condition_b) {
        DoSomething();
    }
}
```

---

## 4. Comments & Documentation

### Doxygen Style (public API)
```cpp
/**
 * @brief Retrieves the list of users with the given role.
 *
 * Returns cached results first; on a cache miss, queries the DB.
 *
 * @param role      The user role to query.
 * @param max_count Maximum number of results to return. Defaults to 100.
 * @return A vector of users. Empty vector if there are no results.
 * @throws DatabaseException On DB connection failure.
 *
 * @note Thread-safe. Uses a mutex internally.
 * @see UserRepository::FindByRole
 */
std::vector<User> GetActiveUsers(
    UserRole role,
    int max_count = 100) const;

/**
 * @brief User authentication service.
 *
 * Manages resources with the RAII pattern and
 * automatically releases the connection in the destructor.
 */
class AuthService {
    ...
};
```

### Inline Comments
```cpp
// Business requirement: mark inactive after 30+ days without login
auto threshold = std::chrono::system_clock::now() - std::chrono::hours(720);

int retry_count = 0;  // retry count (max 3 times)
```

### TODO / FIXME
```cpp
// TODO(develojt): need to implement a cache invalidation strategy
// FIXME: intermittent crash due to a race condition
// HACK: temporary cast for legacy API compatibility
```

---

## 5. Functions & Parameters

### Parameter Passing Rules
```cpp
// Input only: const reference
void Process(const std::string& input);

// Primitive types: pass by value
void SetCount(int count);

// Output: pointer (nullptr allowed) or reference
bool TryParse(const std::string& input, int* result);
void GetSize(int& width, int& height);

// Ownership transfer: move a unique_ptr
void TakeOwnership(std::unique_ptr<Resource> resource);

// Shared ownership: copy a shared_ptr
void ShareResource(std::shared_ptr<Resource> resource);

// Sink parameter (copy + move optimization)
void SetName(std::string name) {    // take by value
    name_ = std::move(name);         // move
}
```

### Function Design
```cpp
// Max line length: 80–120 chars; wrap if exceeded
std::optional<User> FindUser(
    int user_id,
    const SearchOptions& options = {}) const;

// Return value: use optional (instead of nullptr)
std::optional<User> FindUser(int user_id) const {
    auto it = cache_.find(user_id);
    if (it != cache_.end()) {
        return it->second;
    }
    return std::nullopt;
}

// Use nodiscard to prevent ignoring the return value
[[nodiscard]] ErrorCode Initialize();
```

---

## 6. Include Rules

### Order (Google style)
```cpp
// user_service.cpp

// 1. Corresponding header (catch build errors early)
#include "user_service.h"

// 2. C system headers
#include <cstdlib>
#include <cstring>

// 3. C++ standard library
#include <memory>
#include <string>
#include <vector>

// 4. Third-party libraries
#include <spdlog/spdlog.h>
#include <nlohmann/json.hpp>

// 5. Project-internal
#include "models/user.h"
#include "repositories/user_repository.h"
```

### Include Guard
```cpp
// #pragma once (recommended — concise, supported by most compilers)
#pragma once

// or a traditional include guard
#ifndef MYAPP_SERVICES_USER_SERVICE_H_
#define MYAPP_SERVICES_USER_SERVICE_H_

...

#endif  // MYAPP_SERVICES_USER_SERVICE_H_
```

### Using Forward Declarations
```cpp
// If the header uses only pointers/references, reduce dependencies with forward declarations
class User;  // instead of #include "user.h"
class ILogger;

class UserService {
public:
    void Process(const User& user);
private:
    std::unique_ptr<ILogger> logger_;
};
```

---

## 7. Memory Management

```cpp
// RAII principle: resource acquisition is initialization
// No raw new/delete — use smart pointers

// Sole ownership
auto user = std::make_unique<User>("Alice");
ProcessUser(std::move(user));  // transfer ownership

// Shared ownership
auto config = std::make_shared<Config>();
service_a.SetConfig(config);
service_b.SetConfig(config);

// Observation only (no ownership)
void Display(const User& user);       // reference (recommended)
void Display(const User* user);       // pointer (when nullable)

// Array
auto buffer = std::make_unique<char[]>(1024);

// Forbidden patterns
User* user = new User();              // X - raw new
delete user;                           // X - raw delete
char* buf = (char*)malloc(1024);      // X - C-style memory
```

---

## 8. Modern C++ Patterns

```cpp
// auto (when the type is clear)
auto user = GetUser(id);               // return type is clear
auto count = static_cast<int>(size);   // cast makes the type clear
auto it = container.begin();           // iterator

// Range-based for
for (const auto& item : collection) {
    Process(item);
}

// Structured bindings (C++17)
auto [name, age] = GetUserInfo(id);
for (const auto& [key, value] : map) {
    ...
}

// enum class (scoped enum)
enum class UserRole : uint8_t {
    kAdmin = 0,
    kEditor = 1,
    kViewer = 2,
};

// constexpr
constexpr int kMaxSize = 1024;
constexpr int Square(int x) { return x * x; }

// std::string_view (read-only string)
void PrintName(std::string_view name);

// std::span (array view, C++20)
void ProcessData(std::span<const int> data);

// Lambda
auto is_active = [](const User& u) { return u.IsActive(); };
std::ranges::sort(users, {}, &User::GetName);  // C++20

// if constexpr (compile-time branching)
template <typename T>
void Process(const T& value) {
    if constexpr (std::is_integral_v<T>) {
        ProcessInt(value);
    } else {
        ProcessGeneric(value);
    }
}
```

---

## 9. Exceptions & Error Handling

```cpp
// Exception hierarchy (based on std::exception)
class AppError : public std::runtime_error {
public:
    explicit AppError(const std::string& msg)
        : std::runtime_error(msg) {}
};

class NotFoundError : public AppError {
public:
    explicit NotFoundError(const std::string& msg)
        : AppError(msg) {}
};

// Using exceptions
void GetUser(int id) {
    auto user = repository_.Find(id);
    if (!user) {
        throw NotFoundError(
            fmt::format("User {} not found", id));
    }
}

// Declare noexcept
void Swap(User& a, User& b) noexcept;
int GetSize() const noexcept { return size_; }

// Projects that do not use exceptions (game engines, etc.)
// std::expected (C++23) or the Result pattern
template <typename T>
struct Result {
    bool success;
    T value;
    std::string error;
};

Result<User> TryGetUser(int id) noexcept;
```

---

## 10. File Rules

### File Rules
- Header: `.h` (`.hpp` also allowed for C++-only)
- Source: `.cpp`
- One file = one class (principle)
- Filename = the class name converted to snake_case

### .clang-format Example
```yaml
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 120
AllowShortFunctionsOnASingleLine: Inline
BreakBeforeBraces: Attach
PointerAlignment: Left
SortIncludes: CaseSensitive
```
