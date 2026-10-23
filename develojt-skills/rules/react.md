---
paths:
  - "**/*.tsx"
  - "**/*.jsx"
---

# React Coding Rules (TypeScript + Function Components)

## Table of Contents
1. [Naming Rules](#1-naming-rules)
2. [Indentation & Whitespace](#2-indentation--whitespace)
3. [Braces & JSX Rules](#3-braces--jsx-rules)
4. [Comments](#4-comments)
5. [Components & Props](#5-components--props)
6. [Import Rules](#6-import-rules)
7. [Hooks Rules](#7-hooks-rules)
8. [State Management](#8-state-management)
9. [Type Definitions](#9-type-definitions)
10. [File Rules](#10-file-rules)

---

## 1. Naming Rules

| Target | Style | Example |
|------|--------|------|
| Component | PascalCase | `UserProfile`, `DataTable` |
| Component file | PascalCase.tsx | `UserProfile.tsx`, `DataTable.tsx` |
| Hook | use + camelCase | `useAuth`, `useLocalStorage` |
| Hook file | use + camelCase.ts | `useAuth.ts` |
| Regular function | camelCase | `formatDate()`, `calculateTotal()` |
| Variable | camelCase | `userName`, `isLoading` |
| Constant | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `API_BASE_URL` |
| Type/interface | PascalCase | `UserDto`, `ApiResponse` |
| Props type | Component name + Props | `UserProfileProps`, `DataTableProps` |
| Enum | PascalCase | `UserRole.Admin` |
| Event handler | handle + event | `handleClick`, `handleSubmit` |
| Event props | on + event | `onClick`, `onSubmit`, `onUserCreate` |
| Boolean | is/has/can/should | `isLoading`, `hasError`, `canEdit` |
| Utility file | camelCase.ts | `formatters.ts`, `validators.ts` |
| CSS Module | PascalCase.module.css | `UserProfile.module.css` |
| Test | OriginalName.test.tsx | `UserProfile.test.tsx` |

```tsx
// Good example
const UserProfile: React.FC<UserProfileProps> = ({ userId, onEdit }) => {
  const [isLoading, setIsLoading] = useState(false);
  const { user, error } = useUser(userId);

  const handleEditClick = () => {
    onEdit(userId);
  };

  return <div>...</div>;
};

// Bad example
const user_profile = ({ user_id, editCallback }) => {  // snake_case X
  const [Loading, SetLoading] = useState(false);        // PascalCase X
  
  const edit_click = () => { ... };  // snake_case X, no handle prefix
  
  return <div>...</div>;
};
```

---

## 2. Indentation & Whitespace

### Indentation
- **2 spaces** (React/frontend standard)

```tsx
// JSX indentation
return (
  <div className="container">
    <header>
      <h1>{title}</h1>
    </header>
    <main>
      {items.map((item) => (
        <ItemCard key={item.id} item={item} />
      ))}
    </main>
  </div>
);

// Long props — one per line
<UserCard
  userId={user.id}
  name={user.name}
  role={user.role}
  isActive={user.isActive}
  onEdit={handleEdit}
  onDelete={handleDelete}
/>

// Short props — single line
<Button size="sm" onClick={handleClick}>Save</Button>
```

### Whitespace Rules
```tsx
// No spaces inside JSX braces
<div className={styles.container}>     {/* O */}
<div className={ styles.container }>   {/* X */}

// Space before JSX self-closing
<UserAvatar />    {/* O */}
<UserAvatar/>     {/* X */}

// Spaces around the arrow in arrow functions
const add = (a: number, b: number) => a + b;

// Spaces inside object braces
const user = { name: "Alice", age: 30 };
```

---

## 3. Braces & JSX Rules

### JSX Return
```tsx
// Single element — parentheses optional
return <div>{message}</div>;

// Multiple lines — wrap in parentheses
return (
  <div>
    <h1>{title}</h1>
    <p>{description}</p>
  </div>
);

// Use Fragment (no unnecessary divs)
return (
  <>
    <Header />
    <Main />
    <Footer />
  </>
);
```

### Conditional Rendering
```tsx
// && operator (simple conditions)
{isLoading && <Spinner />}

// Ternary operator (if-else)
{isError ? <ErrorMessage /> : <Content />}

// Complex conditions — early return or extract to a variable
const renderContent = () => {
  if (isLoading) return <Spinner />;
  if (isError) return <ErrorMessage error={error} />;
  if (!data) return <EmptyState />;
  return <DataTable data={data} />;
};

return <div>{renderContent()}</div>;

// Caution with 0: the number 0 renders when using &&
{items.length > 0 && <ItemList items={items} />}  // O
{items.length && <ItemList items={items} />}       // X - 0 renders
```

### List Rendering
```tsx
// key must always be a stable, unique ID
{users.map((user) => (
  <UserCard key={user.id} user={user} />
))}

// Do not use index as key (bugs when order changes)
{users.map((user, index) => (
  <UserCard key={index} user={user} />  // X
))}
```

---

## 4. Comments

```tsx
// Inline comment (above the code)
// Restore the post-login redirect URL from the session
const redirectUrl = sessionStorage.getItem("redirectUrl");

// JSX comment
return (
  <div>
    {/* User profile header */}
    <Header user={user} />
    
    {/* TODO: need to add pagination */}
    <ItemList items={items} />
  </div>
);

// TSDoc (library/shared components)
/**
 * A component that displays user information as a card.
 *
 * @param props - the component props
 * @param props.user - the user object to display
 * @param props.onEdit - the edit-button click handler
 *
 * @example
 * ```tsx
 * <UserCard user={currentUser} onEdit={handleEdit} />
 * ```
 */
```

---

## 5. Components & Props

### Component Definition
```tsx
// Define the Props interface (right above the component)
interface UserProfileProps {
  userId: number;
  showAvatar?: boolean;
  onEdit: (userId: number) => void;
  children?: React.ReactNode;
}

// Function declaration (hoistable, recommended)
export default function UserProfile({
  userId,
  showAvatar = true,
  onEdit,
  children,
}: UserProfileProps) {
  // hooks
  const { user, isLoading } = useUser(userId);
  const [isEditing, setIsEditing] = useState(false);

  // event handlers
  const handleEditClick = useCallback(() => {
    setIsEditing(true);
    onEdit(userId);
  }, [userId, onEdit]);

  // early return
  if (isLoading) return <Spinner />;
  if (!user) return <NotFound />;

  // rendering
  return (
    <div className="user-profile">
      {showAvatar && <Avatar src={user.avatarUrl} />}
      <h2>{user.name}</h2>
      <button onClick={handleEditClick}>Edit</button>
      {children}
    </div>
  );
}

// Arrow function (small components, inner components)
const Badge: React.FC<{ label: string }> = ({ label }) => (
  <span className="badge">{label}</span>
);
```

### Component Internal Order
1. Props destructuring
2. Hooks (useState, useEffect, custom hooks)
3. Derived state / computed values
4. Event handlers
5. Early returns (loading, error)
6. JSX return

---

## 6. Import Rules

### Order
```tsx
// 1. React-related
import React, { useState, useEffect, useCallback } from "react";

// 2. Third-party libraries
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "react-hot-toast";
import clsx from "clsx";

// 3. Internal components
import { Button } from "@/components/ui/Button";
import { UserCard } from "@/components/UserCard";

// 4. Hooks
import { useAuth } from "@/hooks/useAuth";
import { useUser } from "@/hooks/useUser";

// 5. Utilities / constants
import { formatDate, formatCurrency } from "@/utils/formatters";
import { API_ENDPOINTS } from "@/constants";

// 6. Types (type-only import)
import type { User, UserRole } from "@/types";

// 7. Styles
import styles from "./UserProfile.module.css";
```

### Rules
- **One blank line** between each group
- Use `import type` for `type` imports (build optimization)
- Use barrel exports (index.ts) appropriately
- Avoid circular imports

---

## 7. Hooks Rules

### Basic Principles
- Call Hooks only at the **top level of the component**
- Do not call Hooks inside conditionals/loops
- Custom Hooks must use the `use` prefix

```tsx
// Custom Hook pattern
function useUser(userId: number) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;

    const fetchUser = async () => {
      try {
        setIsLoading(true);
        const data = await api.getUser(userId);
        if (!cancelled) {
          setUser(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err as Error);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchUser();
    return () => { cancelled = true; };
  }, [userId]);

  return { user, isLoading, error };
}

// useCallback — functions passed to children
const handleSubmit = useCallback(
  (values: FormValues) => {
    mutation.mutate(values);
  },
  [mutation]
);

// useMemo — expensive computations
const sortedItems = useMemo(
  () => items.sort((a, b) => a.name.localeCompare(b.name)),
  [items]
);
```

---

## 8. State Management

```tsx
// Simple state: useState
const [count, setCount] = useState(0);

// Complex state: useReducer
interface State {
  users: User[];
  isLoading: boolean;
  error: string | null;
  page: number;
}

type Action =
  | { type: "FETCH_START" }
  | { type: "FETCH_SUCCESS"; payload: User[] }
  | { type: "FETCH_ERROR"; payload: string }
  | { type: "SET_PAGE"; payload: number };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "FETCH_START":
      return { ...state, isLoading: true, error: null };
    case "FETCH_SUCCESS":
      return { ...state, isLoading: false, users: action.payload };
    case "FETCH_ERROR":
      return { ...state, isLoading: false, error: action.payload };
    case "SET_PAGE":
      return { ...state, page: action.payload };
  }
}

// Server state: React Query
const { data, isLoading, error } = useQuery({
  queryKey: ["users", filters],
  queryFn: () => api.getUsers(filters),
  staleTime: 5 * 60 * 1000,
});
```

---

## 9. Type Definitions

```tsx
// interface (extendable, recommended for object shapes)
interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  isActive: boolean;
  createdAt: string;
}

// type (unions, intersections, utilities)
type UserRole = "admin" | "editor" | "viewer";
type UserWithPosts = User & { posts: Post[] };
type PartialUser = Partial<User>;

// Props with children
interface LayoutProps {
  title: string;
  sidebar?: React.ReactNode;
  children: React.ReactNode;
}

// Event types
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  setValue(e.target.value);
};

const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
};

// Generic component
interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  onRowClick?: (row: T) => void;
}

function Table<T extends { id: number }>({
  data,
  columns,
  onRowClick,
}: TableProps<T>) {
  ...
}

// API response type
interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  pagination?: {
    page: number;
    totalPages: number;
    totalItems: number;
  };
}
```

---

## 10. File Rules

### File Rules
- One file = one component (export default)
- Max line length: **80 chars** (Prettier default) or **100 chars**
- Semicolons: **yes** (Prettier default)
- Quotes: **double quotes** (JSX standard)
- Trailing commas: **always** (trailing comma)

### Prettier + ESLint Configuration
```json
// .prettierrc
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 80,
  "jsxSingleQuote": false,
  "bracketSpacing": true
}
```
