---
paths:
  - "**/*.js"
  - "**/*.jsx"
  - "**/*.mjs"
  - "**/*.cjs"
---

# JavaScript Common Coding Rules

> Based on ES2022+ / JSDoc type annotations / ESLint 9.x flat config
> A version of the TypeScript rules (typescript.md) adapted to the JS environment

## Table of Contents
1. [Naming Rules](#1-naming-rules)
2. [Indentation & Whitespace](#2-indentation--whitespace)
3. [Brace Rules](#3-brace-rules)
4. [Comments & JSDoc](#4-comments--jsdoc)
5. [Functions & Parameters](#5-functions--parameters)
6. [Type Hints (JSDoc)](#6-type-hints-jsdoc)
7. [Error Handling](#7-error-handling)
8. [Async Patterns](#8-async-patterns)
9. [Module & Export](#9-module--export)
10. [File Rules](#10-file-rules)
11. [Configuration & Tooling](#11-configuration--tooling)

---

## 1. Naming Rules

| Target | Style | Example |
|------|--------|------|
| Variable | camelCase | `userName`, `totalCount` |
| Function | camelCase | `getUserById()`, `formatDate()` |
| Class | PascalCase | `UserService`, `HttpClient` |
| Constant | UPPER_SNAKE_CASE | `MAX_RETRY`, `API_URL` |
| Enum-substitute object | PascalCase (keys: PascalCase) | `HttpStatus.NotFound` |
| Boolean | is/has/can/should | `isActive`, `hasError` |
| File (general) | camelCase.js | `userService.js`, `formatters.js` |
| File (class) | PascalCase.js | `UserService.js` |
| Directory | kebab-case | `user-management/`, `api-client/` |
| private member | `#` prefix (ES2022) | `#cache`, `#validate()` |

```javascript
// Good example
const MAX_RETRY_COUNT = 3;

/** @enum {number} */
const HttpStatus = Object.freeze({
  Ok: 200,
  NotFound: 404,
  ServerError: 500,
});

function calculateDiscount(price, rate) {
  return price * rate;
}

class AudioManager {
  #volume = 1.0;
  #muted = false;

  get volume() {
    return this.#volume;
  }
}

// Bad example
const maxRetryCount = 3;          // constants use UPPER_SNAKE
const HTTP_STATUS = { ... };      // Enum-substitute objects use PascalCase
function CalculateDiscount() {}   // functions use camelCase
class audioManager {}             // classes use PascalCase
```

---

## 2. Indentation & Whitespace

### Indentation
- **2 spaces** (frontend standard)
- No tabs

```javascript
// Objects/arrays — trailing comma required
const config = {
  host: "localhost",
  port: 3000,
  options: {
    timeout: 5000,
    retries: 3,
  },
};

const items = [
  "apple",
  "banana",
  "cherry",
];

// Chaining
const result = await fetchData()
  .then((res) => res.json())
  .then((data) => transform(data))
  .catch((err) => handleError(err));
```

### Whitespace Rules
```javascript
// Arrow — spaces on both sides
const add = (a, b) => a + b;

// Ternary operator — spaces on both sides
const status = isActive ? "active" : "inactive";

// Object destructuring — spaces inside braces
const { name, age } = user;

// Generics in JSDoc — no spaces
/** @type {Array<string>} */
/** @type {Map<string, number>} */
```

---

## 3. Brace Rules

### K&R Style
```javascript
// Opening brace on the same line
function processUser(user) {
  if (user.isActive) {
    sendNotification(user);
  } else {
    logInactiveAccess(user);
  }

  for (const item of user.items) {
    process(item);
  }

  switch (user.role) {
    case UserRole.Admin:
      handleAdmin(user);
      break;
    case UserRole.Editor:
      handleEditor(user);
      break;
    default:
      handleDefault(user);
      break;
  }
}

// Class
class UserService {
  constructor(repo) {
    this.repo = repo;
  }

  getUser(id) {
    ...
  }
}
```

### Single-Statement Handling
```javascript
// Arrow functions — omit braces for single-line expressions
const double = (n) => n * 2;
const isActive = (u) => u.isActive;

// Braces required when multi-line
const process = (user) => {
  validate(user);
  return transform(user);
};

// if — always braces (ESLint curly rule)
if (isValid) {
  return result;
}
```

---

## 4. Comments & JSDoc

### JSDoc (required for all classes and public functions)

In a JS project, JSDoc serves as both type hints and documentation at once.
The IDE (VSCode) provides autocompletion and type checking based on JSDoc.

```javascript
/**
 * Filters the user list by role
 *
 * @param {User[]} users - the full array of users
 * @param {string} role - the role to filter by
 * @returns {User[]} the filtered array of users (ascending by name)
 *
 * @spec FR-XX-XXX
 *
 * @example
 * const admins = filterByRole(users, "admin");
 */
function filterByRole(users, role) {
  return users
    .filter((u) => u.role === role)
    .sort((a, b) => a.name.localeCompare(b.name));
}

/**
 * A client that handles HTTP requests
 *
 * @template T - the response data type
 *
 * @spec FR-XX-XXX
 */
class ApiClient {
  ...
}
```

### @spec Tag Placement

Place `@spec` inside the JSDoc block. Separate it from the description with a blank line.

```javascript
/**
 * Handle order saving
 * Records the order in the persistent store
 *
 * @spec FR-05-001
 * @spec NFR-00-004
 */
saveOrder() { ... }
```

### Inline Comments
```javascript
// Business rule: VIP customers get a 2x discount rate
const discountRate = isVip ? baseRate * 2 : baseRate;

// TODO(develojt): cache strategy needs improvement
// FIXME: 1-hour offset occurs during timezone conversion
// HACK: compatibility with the legacy API's date format
```

---

## 5. Functions & Parameters

### Function Declarations
```javascript
// Regular function (can be hoisted)
function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// Arrow function (callbacks, short functions)
const formatPrice = (amount) =>
  new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
  }).format(amount);
```

### More than 5 parameters → group into an object
```javascript
/**
 * Fetches the user list
 *
 * @param {Object} options - query options
 * @param {string} [options.role] - the role to filter by
 * @param {boolean} [options.isActive=true] - active users only
 * @param {number} [options.page=1] - page number
 * @param {number} [options.pageSize=20] - page size
 * @param {string} [options.sortBy] - sort key
 * @param {"asc"|"desc"} [options.sortOrder] - sort direction
 * @returns {Promise<User[]>}
 *
 * @spec FR-XX-XXX
 */
async function fetchUsers(options = {}) {
  const { role, isActive = true, page = 1, pageSize = 20 } = options;
  ...
}
```

### Explicit Return Types (JSDoc)
```javascript
// @returns required for public functions
/** @returns {User|null} */
function getUser(id) { ... }

/** @returns {Promise<ApiResponse>} */
async function fetchData() { ... }

// omission allowed for simple internal functions
const double = (n) => n * 2;
```

---

## 6. Type Hints (JSDoc)

In JS, type safety is secured through JSDoc. Because `jsconfig.json` is set to `checkJs: false`,
no errors are forced, but it greatly aids IDE autocompletion and documentation.

### Type Definitions (typedef)
```javascript
/**
 * @typedef {Object} User
 * @property {number} id - unique user ID
 * @property {string} name - user name
 * @property {string} email - email address
 * @property {boolean} isActive - whether active
 */

/**
 * @typedef {"admin"|"editor"|"viewer"} UserRole
 */

/**
 * @typedef {Object} ApiResponse
 * @property {boolean} success
 * @property {*} data
 * @property {string} [error]
 */
```

### Enum-Substitute Pattern (Object.freeze)
```javascript
/**
 * Screen route keys
 * @enum {string}
 *
 * @spec FR-02-001
 */
const RouteKeys = Object.freeze({
  Home: "home",
  Login: "login",
  Dashboard: "dashboard",
  Settings: "settings",
});

/**
 * Event keys
 * @enum {string}
 */
const EventKeys = Object.freeze({
  OrderCreated: "order:created",
  OrderPaid: "order:paid",
  OrderCancelled: "order:cancelled",
  UserLoggedIn: "user:logged-in",
});
```

### Generics (JSDoc @template)
```javascript
/**
 * Returns the first element in the array that matches the predicate
 *
 * @template T
 * @param {T[]} array - the target array
 * @param {(item: T) => boolean} predicate - the predicate function
 * @returns {T|undefined}
 */
function findFirst(array, predicate) {
  return array.find(predicate);
}
```

### Type Casting / Type Guards
```javascript
/**
 * Checks whether a value is a User object
 *
 * @param {*} value - the value to check
 * @returns {boolean}
 */
function isUser(value) {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    "name" in value
  );
}

// Usage example
const data = JSON.parse(rawText);
if (isUser(data)) {
  console.log(data.name);
}
```

---

## 7. Error Handling

```javascript
/**
 * Base application error class
 *
 * @spec FR-01-003
 */
class AppError extends Error {
  /**
   * @param {string} message - error message
   * @param {string} code - error code
   * @param {number} [statusCode=500] - HTTP status code
   */
  constructor(message, code, statusCode = 500) {
    super(message);
    this.name = "AppError";
    this.code = code;
    this.statusCode = statusCode;
  }
}

/**
 * Resource-not-found error
 *
 * @spec FR-01-001
 */
class NotFoundError extends AppError {
  constructor(resource, id) {
    super(`${resource} not found: ${id}`, "NOT_FOUND", 404);
    this.name = "NotFoundError";
  }
}

// try-catch — type check in catch(err)
try {
  await fetchUser(id);
} catch (err) {
  if (err instanceof NotFoundError) {
    // handle 404
  } else if (err instanceof Error) {
    console.error("Unexpected error", err.message);
  } else {
    console.error("Unknown error", String(err));
  }
}
```

---

## 8. Async Patterns

```javascript
// Prefer async/await (instead of Promise chaining)
async function fetchUserData(userId) {
  const user = await userApi.getById(userId);
  const posts = await postApi.getByUserId(userId);
  return { ...user, posts };
}

// Parallel execution
async function fetchDashboard() {
  const [users, stats, notifications] = await Promise.all([
    userApi.getAll(),
    statsApi.getSummary(),
    notificationApi.getUnread(),
  ]);
  return { users, stats, notifications };
}

// Promise.allSettled (tolerates partial failure)
const results = await Promise.allSettled([
  fetchCritical(),
  fetchOptional(),
]);

for (const result of results) {
  if (result.status === "fulfilled") {
    process(result.value);
  } else {
    console.warn("Failed:", result.reason);
  }
}
```

---

## 9. Module & Export

```javascript
// Prefer named exports (tree-shaking optimization)
export function formatDate(date) { ... }
export function formatCurrency(amount) { ... }

// Default export — only for classes and the main module
export default class UserService { ... }

// Re-export (barrel pattern)
// config/index.js
export { AppConfig } from "./AppConfig.js";
export { ApiEndpoints } from "./ApiEndpoints.js";
export { EventKeys } from "./EventKeys.js";
export { RouteKeys } from "./RouteKeys.js";

// Avoid circular imports
// X: a.js imports b.js, b.js imports a.js
// O: split shared constants/types into shared.js
```

### Import Style
```javascript
// Explicit named import
import { AppConfig } from "@/config/AppConfig.js";
import { UserService } from "@/services/UserService.js";

// Full import of the default export — external libraries
import axios from "axios";

// Import ordering (ESLint import/order)
// 1. External packages (axios, ...)
// 2. Internal absolute paths (@/config, @/services, ...)
// 3. Relative paths (./utils, ../models, ...)
```

---

## 10. File Rules

### File Rules
- General files: **camelCase.js** (`userService.js`, `formatters.js`)
- Class files: **PascalCase.js** (`UserService.js`)
- Directories: **kebab-case** (`user-management/`)
- One file = one class/module (principle)
- Max line length: **100 chars** (Prettier)
- Tests: original name + `.test.js` (`userService.test.js`)

---

## 11. Configuration & Tooling

### jsconfig.json
```json
{
  "compilerOptions": {
    "checkJs": false,
    "target": "ES2022",
    "module": "ES2022",
    "moduleResolution": "bundler",
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src/**/*"]
}
```

### ESLint 9.x flat config (eslint.config.js)
```javascript
import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: { APP_VERSION: "readonly" },
    },
    rules: {
      "no-unused-vars": "warn",
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "curly": ["error", "all"],
      "eqeqeq": ["error", "always"],
      "no-var": "error",
      "prefer-const": "error",
      "prefer-arrow-callback": "warn",
      "no-throw-literal": "error",
    },
  },
];
```

### Prettier (recommended)
```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100
}
```

---

## Summary of Differences from the TypeScript Rules

| Item | TypeScript | JavaScript |
|------|-----------|------------|
| Type declaration | `interface`, `type` | JSDoc `@typedef` |
| Type annotation | `: string`, `: number` | JSDoc `@param {string}` |
| Enum | `enum HttpStatus { ... }` | `Object.freeze({ ... })` |
| Generics | `<T>` syntax | JSDoc `@template T` |
| private member | `private` keyword | `#` prefix (ES2022) |
| Return type | `: ReturnType` | JSDoc `@returns {Type}` |
| Type guard | `value is User` | `typeof` + `in` check function |
| any forbidden | `@typescript-eslint/no-explicit-any` | not applicable (compensated for with JSDoc) |
| Type-only import | `import type { ... }` | N/A |
| Config file | `tsconfig.json` (`strict: true`) | `jsconfig.json` (`checkJs: false`) |
