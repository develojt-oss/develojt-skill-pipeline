---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# TypeScript Common Coding Rules

## Table of Contents
1. [Naming Rules](#1-naming-rules)
2. [Indentation & Whitespace](#2-indentation--whitespace)
3. [Brace Rules](#3-brace-rules)
4. [Comments & TSDoc](#4-comments--tsdoc)
5. [Functions & Parameters](#5-functions--parameters)
6. [Type System](#6-type-system)
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
| Interface | PascalCase (no I prefix) | `UserDto`, `ApiConfig` |
| Type alias | PascalCase | `UserId`, `RequestHandler` |
| Enum | PascalCase | `UserRole`, `HttpStatus` |
| Enum value | PascalCase | `Admin`, `NotFound` |
| Constant | UPPER_SNAKE_CASE | `MAX_RETRY`, `API_URL` |
| Generic | T / single uppercase letter or PascalCase | `T`, `TResult`, `TKey` |
| Boolean | is/has/can/should | `isActive`, `hasError` |
| File (general) | camelCase.ts | `userService.ts`, `formatters.ts` |
| File (class) | PascalCase.ts | `UserService.ts` |
| Directory | kebab-case | `user-management/`, `api-client/` |

```typescript
// Good example
const MAX_RETRY_COUNT = 3;

interface UserProfile {
  id: number;
  displayName: string;
  isActive: boolean;
}

enum HttpStatus {
  Ok = 200,
  NotFound = 404,
  ServerError = 500,
}

function calculateDiscount(price: number, rate: number): number {
  return price * rate;
}

// Bad example
const maxRetryCount = 3;          // constants use UPPER_SNAKE
interface IUserProfile { ... }    // no I prefix (C# convention, not TS)
enum HTTP_STATUS { ... }          // UPPER_SNAKE X → PascalCase
function CalculateDiscount() {}   // PascalCase X → camelCase
```

---

## 2. Indentation & Whitespace

### Indentation
- **2 spaces** (frontend standard)
- No tabs

```typescript
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
```typescript
// Type annotation — space after the colon
const name: string = "Alice";
function greet(name: string): void { ... }

// Arrow — spaces on both sides
const add = (a: number, b: number) => a + b;

// Type operators — spaces on both sides
type StringOrNumber = string | number;
type UserWithPosts = User & { posts: Post[] };

// Generics — no spaces
Array<string>
Map<string, number>
Promise<User>
```

---

## 3. Brace Rules

### K&R Style
```typescript
// Opening brace on the same line
function processUser(user: User) {
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
  constructor(private readonly repo: UserRepository) {}

  getUser(id: number): User | null {
    ...
  }
}
```

### Single-Statement Handling
```typescript
// Arrow functions — omit braces for single-line expressions
const double = (n: number) => n * 2;
const isActive = (u: User) => u.isActive;

// Braces required when multi-line
const process = (user: User) => {
  validate(user);
  return transform(user);
};

// if — always braces (ESLint curly rule)
if (isValid) {
  return result;
}
```

---

## 4. Comments & TSDoc

### TSDoc (library/shared code)
```typescript
/**
 * Filters the user list by role.
 *
 * @param users - the full array of users
 * @param role - the role to filter by
 * @returns the filtered array of users (ascending by name)
 *
 * @example
 * ```ts
 * const admins = filterByRole(users, UserRole.Admin);
 * ```
 *
 * @throws {ValidationError} when role is invalid
 */
function filterByRole(users: User[], role: UserRole): User[] {
  return users
    .filter((u) => u.role === role)
    .sort((a, b) => a.name.localeCompare(b.name));
}

/**
 * A client that handles HTTP requests.
 *
 * @typeParam T - the response data type
 */
class ApiClient<T> {
  ...
}
```

### Inline Comments
```typescript
// Business rule: VIP customers get a 2x discount rate
const discountRate = isVip ? baseRate * 2 : baseRate;

// TODO(develojt): cache strategy needs improvement
// FIXME: 1-hour offset occurs during timezone conversion
// HACK: compatibility with the legacy API's date format
```

---

## 5. Functions & Parameters

### Function Declarations
```typescript
// Regular function (can be hoisted)
function calculateTotal(items: CartItem[]): number {
  return items.reduce((sum, item) => sum + item.price * item.quantity, 0);
}

// Arrow function (callbacks, short functions)
const formatPrice = (amount: number): string =>
  new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "KRW",
  }).format(amount);

// More than 5 parameters → group into an object
interface FetchUsersOptions {
  role?: UserRole;
  isActive?: boolean;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

async function fetchUsers(options: FetchUsersOptions = {}): Promise<User[]> {
  const { role, isActive = true, page = 1, pageSize = 20 } = options;
  ...
}
```

### Overloads
```typescript
// Function overloads (type-safe polymorphism)
function parse(input: string): string[];
function parse(input: string, limit: number): string[];
function parse(input: string, limit?: number): string[] {
  return limit ? input.split(",", limit) : input.split(",");
}
```

### Return Types
```typescript
// Explicit return types recommended (public functions)
function getUser(id: number): User | null { ... }
async function fetchData(): Promise<ApiResponse<User[]>> { ... }

// inference allowed for simple internal functions
const double = (n: number) => n * 2;
```

---

## 6. Type System

### interface vs type
```typescript
// interface: object shape, extensible (recommended)
interface User {
  id: number;
  name: string;
  email: string;
}

interface AdminUser extends User {
  permissions: Permission[];
}

// type: unions, intersections, utilities, primitive aliases
type UserId = number;
type UserRole = "admin" | "editor" | "viewer";
type Nullable<T> = T | null;
type UserWithPosts = User & { posts: Post[] };
```

### Using Utility Types
```typescript
// Partial — all properties optional
type UpdateUser = Partial<User>;

// Required — all properties required
type CompleteUser = Required<User>;

// Pick / Omit — select/exclude properties
type UserSummary = Pick<User, "id" | "name">;
type UserWithoutEmail = Omit<User, "email">;

// Record — key-value mapping
type RolePermissions = Record<UserRole, Permission[]>;

// ReturnType — extract a function's return type
type FetchResult = ReturnType<typeof fetchUsers>;

// Readonly — immutable object
type ReadonlyUser = Readonly<User>;
```

### Type Guards
```typescript
// is keyword (user-defined type guard)
function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    "name" in value
  );
}

// in operator
function processResponse(res: SuccessResponse | ErrorResponse) {
  if ("data" in res) {
    // SuccessResponse
    handleData(res.data);
  } else {
    // ErrorResponse
    handleError(res.error);
  }
}

// discriminated union
type Result<T> =
  | { success: true; data: T }
  | { success: false; error: string };

function handleResult(result: Result<User>) {
  if (result.success) {
    console.log(result.data);  // narrowed to User
  } else {
    console.error(result.error);  // narrowed to string
  }
}
```

### any/unknown
```typescript
// any forbidden (eslint: @typescript-eslint/no-explicit-any)
// use unknown, then narrow with a type guard
function parseJson(text: string): unknown {
  return JSON.parse(text);
}

const data = parseJson(rawText);
if (isUser(data)) {
  // safely use as User
  console.log(data.name);
}
```

---

## 7. Error Handling

```typescript
// Custom error class
class AppError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500,
  ) {
    super(message);
    this.name = "AppError";
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string | number) {
    super(`${resource} not found: ${id}`, "NOT_FOUND", 404);
    this.name = "NotFoundError";
  }
}

class ValidationError extends AppError {
  constructor(
    message: string,
    public readonly fields: Record<string, string>,
  ) {
    super(message, "VALIDATION_ERROR", 400);
    this.name = "ValidationError";
  }
}

// Handle the unknown type in try-catch
try {
  await fetchUser(id);
} catch (err: unknown) {
  if (err instanceof NotFoundError) {
    // handle 404
  } else if (err instanceof Error) {
    logger.error("Unexpected error", err.message);
  } else {
    logger.error("Unknown error", String(err));
  }
}

// Result pattern (alternative to exceptions)
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}
```

---

## 8. Async Patterns

```typescript
// Prefer async/await (instead of Promise chaining)
async function fetchUserData(userId: number): Promise<UserData> {
  const user = await userApi.getById(userId);
  const posts = await postApi.getByUserId(userId);
  return { ...user, posts };
}

// Parallel execution
async function fetchDashboard(): Promise<Dashboard> {
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
    logger.warn("Failed:", result.reason);
  }
}

// AbortController (cancelable request)
async function fetchWithTimeout(
  url: string,
  timeoutMs: number = 5000,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, { signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
}
```

---

## 9. Module & Export

```typescript
// Prefer named exports (tree-shaking optimization)
export function formatDate(date: Date): string { ... }
export function formatCurrency(amount: number): string { ... }
export type { User, UserRole };

// Default export — only for components and classes
export default class UserService { ... }

// Re-export (barrel pattern)
// types/index.ts
export type { User, UserRole } from "./user";
export type { ApiResponse } from "./api";
export type { Post, Comment } from "./post";

// Avoid circular imports
// X: a.ts imports b.ts, b.ts imports a.ts
// O: split shared types into shared.ts
```

### Import Style
```typescript
// type-only import (build optimization)
import type { User, UserRole } from "@/types";

// separate when mixing values and types
import { UserService } from "@/services";
import type { UserServiceConfig } from "@/services";

// or inline type import (TS 4.5+)
import { UserService, type UserServiceConfig } from "@/services";
```

---

## 10. File Rules

### File Rules
- General files: **camelCase.ts** (`userService.ts`, `formatters.ts`)
- Class files: **PascalCase.ts** (`UserService.ts`)
- Directories: **kebab-case** (`user-management/`)
- One file = one class/module (principle)
- Max line length: **100 chars** (Prettier)
- Type-only files: concentrated in the `types/` directory
- Tests: original name + `.test.ts` (`userService.test.ts`)

---

## 11. Configuration & Tooling

### Recommended tsconfig.json Settings
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### ESLint Rules (core)
```json
{
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/prefer-nullish-coalescing": "warn",
    "@typescript-eslint/prefer-optional-chain": "warn",
    "@typescript-eslint/consistent-type-imports": "error",
    "@typescript-eslint/no-floating-promises": "error",
    "curly": ["error", "all"],
    "eqeqeq": ["error", "always"],
    "no-console": "warn"
  }
}
```

### Prettier
```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100
}
```
