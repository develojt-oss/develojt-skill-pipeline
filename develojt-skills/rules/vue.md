---
paths:
  - "**/*.vue"
---

# Vue.js Coding Rules (Vue 3 Composition API + TypeScript)

## Table of Contents
1. [Naming Rules](#1-naming-rules)
2. [Indentation & Whitespace](#2-indentation--whitespace)
3. [SFC Structure & Templates](#3-sfc-structure--templates)
4. [Comments](#4-comments)
5. [Composition API Patterns](#5-composition-api-patterns)
6. [Props & Emits](#6-props--emits)
7. [Import & Dependencies](#7-import--dependencies)
8. [State Management (Pinia)](#8-state-management-pinia)
9. [Type Definitions](#9-type-definitions)
10. [File Rules](#10-file-rules)

---

## 1. Naming Rules

| Target | Style | Example |
|------|--------|------|
| Component file | PascalCase.vue | `UserProfile.vue`, `DataTable.vue` |
| Component registration | PascalCase | `<UserProfile />` |
| Composable | use + camelCase | `useAuth`, `useUser` |
| Composable file | use + camelCase.ts | `useAuth.ts` |
| Props | camelCase | `userId`, `isActive` |
| Emits | camelCase | `update:modelValue`, `userCreate` |
| Variable/function | camelCase | `userName`, `fetchData()` |
| Constant | UPPER_SNAKE_CASE | `API_BASE_URL`, `MAX_COUNT` |
| Type/interface | PascalCase | `UserDto`, `ApiResponse` |
| Store (Pinia) | use + Store | `useUserStore`, `useAuthStore` |
| Route name | kebab-case | `user-profile`, `order-detail` |
| CSS class | kebab-case (BEM recommended) | `user-card`, `user-card__title` |
| Event handler | handle/on + action | `handleClick`, `onSubmit` |
| Boolean | is/has/can/should | `isLoading`, `hasError` |

```vue
<!-- Good example: PascalCase in templates -->
<template>
  <UserProfile :user-id="currentUserId" @user-edit="handleEdit" />
  <DataTable :items="filteredItems" :is-loading="isLoading" />
</template>
```

```ts
// Good example: camelCase in scripts
const userName = ref("");
const isLoading = ref(false);
const handleSubmit = () => { ... };

// Bad example
const user_name = ref("");         // snake_case X
const UserName = ref("");          // PascalCase X (variable)
const submit_handler = () => {};   // snake_case X
```

---

## 2. Indentation & Whitespace

### Indentation
- **2 spaces** (Vue ecosystem standard)
- 2 spaces inside `<template>`, `<script>`, and `<style>` alike

```vue
<template>
  <div class="user-profile">
    <header class="user-profile__header">
      <h1>{{ user.name }}</h1>
    </header>
    <main>
      <p v-if="user.bio">{{ user.bio }}</p>
      <ul>
        <li v-for="item in items" :key="item.id">
          {{ item.name }}
        </li>
      </ul>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import type { User } from "@/types";

const props = defineProps<{
  userId: number;
}>();

const user = ref<User | null>(null);
const isLoading = ref(true);
</script>
```

### Attribute Alignment
```vue
<!-- 3 attributes or fewer: single line -->
<Button size="sm" variant="primary" @click="handleClick">Save</Button>

<!-- More than 3 attributes: one per line -->
<UserCard
  :user-id="user.id"
  :name="user.name"
  :role="user.role"
  :is-active="user.isActive"
  @edit="handleEdit"
  @delete="handleDelete"
/>
```

### Attribute Order (Vue official recommendation)
1. Definition (`is`, `v-is`)
2. List rendering (`v-for`)
3. Conditionals (`v-if`, `v-else-if`, `v-else`, `v-show`)
4. Render modifiers (`v-once`, `v-pre`)
5. Global (`id`)
6. Unique (`ref`, `key`)
7. Two-way binding (`v-model`)
8. Other attributes (props)
9. Events (`@click`, `@input`)
10. Content (`v-html`, `v-text`)

---

## 3. SFC Structure & Templates

### SFC Order
```vue
<!-- 1. template -->
<template>
  <div>...</div>
</template>

<!-- 2. script setup (recommended) -->
<script setup lang="ts">
...
</script>

<!-- 3. style (scoped required) -->
<style scoped>
...
</style>
```

### Template Rules
```vue
<template>
  <!-- Single root element (Vue 3 allows multiple roots, but single is recommended) -->
  <div class="user-list">
    
    <!-- v-if / v-else at the same level -->
    <LoadingSpinner v-if="isLoading" />
    <ErrorMessage v-else-if="error" :message="error.message" />
    <template v-else>
      <!-- v-for + key required -->
      <UserCard
        v-for="user in sortedUsers"
        :key="user.id"
        :user="user"
        @click="handleUserClick(user)"
      />

      <!-- Empty state -->
      <EmptyState v-if="sortedUsers.length === 0" />
    </template>
  </div>
</template>
```

### Directive Shorthands
```vue
<!-- v-bind shorthand -->
<img :src="imageUrl" :alt="title">

<!-- v-on shorthand -->
<button @click="handleClick">Click</button>

<!-- v-slot shorthand -->
<template #header>
  <h1>Title</h1>
</template>

<!-- v-model (Vue 3) -->
<CustomInput v-model="searchQuery" />
<CustomInput v-model:title="pageTitle" />
```

### Self-closing
```vue
<!-- Component without content: self-closing -->
<UserAvatar />
<LoadingSpinner />

<!-- HTML elements: no self-closing (HTML spec) -->
<div></div>
<span></span>

<!-- void elements may be self-closing -->
<img :src="url" />
<input type="text" />
```

---

## 4. Comments

```vue
<template>
  <!-- User profile area -->
  <section class="profile">
    <!-- TODO: add avatar upload feature -->
    <UserAvatar :src="user.avatar" />
  </section>
</template>

<script setup lang="ts">
// Mark inactive after 30+ days without login (business rule)
const INACTIVE_THRESHOLD_DAYS = 30;

/**
 * Filters and sorts the user list by role.
 *
 * @param users - the full user array
 * @param role - the role to filter by
 * @returns the filtered user array (ascending by name)
 */
function filterUsersByRole(users: User[], role: UserRole): User[] {
  return users
    .filter((u) => u.role === role)
    .sort((a, b) => a.name.localeCompare(b.name));
}
</script>

<style scoped>
/* Mobile-first responsive layout */
.profile {
  padding: 1rem;
}
</style>
```

---

## 5. Composition API Patterns

### `<script setup>` Internal Order
```vue
<script setup lang="ts">
// 1. import
import { ref, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import type { User } from "@/types";

// 2. Props & Emits
const props = defineProps<{
  userId: number;
  showAvatar?: boolean;
}>();

const emit = defineEmits<{
  edit: [userId: number];
  delete: [userId: number];
}>();

// 3. Composables / Store
const router = useRouter();
const userStore = useUserStore();
const { user, isLoading, error } = useUser(props.userId);

// 4. Reactive state
const searchQuery = ref("");
const isEditing = ref(false);

// 5. Computed
const filteredItems = computed(() =>
  items.value.filter((item) =>
    item.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
);

// 6. Watch
watch(
  () => props.userId,
  (newId) => {
    fetchUser(newId);
  }
);

// 7. Functions / event handlers
const handleEdit = () => {
  isEditing.value = true;
  emit("edit", props.userId);
};

const handleDelete = async () => {
  if (!confirm("Are you sure you want to delete?")) return;
  await userStore.deleteUser(props.userId);
  emit("delete", props.userId);
};

// 8. Lifecycle
onMounted(async () => {
  await fetchUser(props.userId);
});

// 9. Expose (when allowing parent access)
defineExpose({ refresh: () => fetchUser(props.userId) });
</script>
```

### Composable Pattern
```ts
// composables/useUser.ts
import { ref, watch, type Ref } from "vue";
import type { User } from "@/types";
import { userApi } from "@/services/userApi";

interface UseUserReturn {
  user: Ref<User | null>;
  isLoading: Ref<boolean>;
  error: Ref<Error | null>;
  refresh: () => Promise<void>;
}

export function useUser(userId: Ref<number> | number): UseUserReturn {
  const user = ref<User | null>(null);
  const isLoading = ref(true);
  const error = ref<Error | null>(null);

  const fetchUser = async (id: number) => {
    try {
      isLoading.value = true;
      error.value = null;
      user.value = await userApi.getById(id);
    } catch (err) {
      error.value = err as Error;
    } finally {
      isLoading.value = false;
    }
  };

  // Watch the reactive userId
  const idRef = isRef(userId) ? userId : ref(userId);
  watch(idRef, (newId) => fetchUser(newId), { immediate: true });

  const refresh = () => fetchUser(idRef.value);

  return { user, isLoading, error, refresh };
}
```

---

## 6. Props & Emits

### TypeScript Props (recommended)
```vue
<script setup lang="ts">
// Type-based (no runtime validation, concise)
const props = defineProps<{
  userId: number;
  name: string;
  role?: UserRole;
  isActive?: boolean;
}>();

// Provide defaults via withDefaults
const props = withDefaults(
  defineProps<{
    userId: number;
    name: string;
    role?: UserRole;
    isActive?: boolean;
    items?: string[];
  }>(),
  {
    role: "viewer",
    isActive: true,
    items: () => [],  // object/array defaults use a factory function
  }
);
</script>
```

### Emits
```vue
<script setup lang="ts">
// Type-based Emits
const emit = defineEmits<{
  // event name: [parameter types]
  submit: [values: FormValues];
  cancel: [];
  "update:modelValue": [value: string];
}>();

// Usage
emit("submit", formValues);
emit("cancel");
emit("update:modelValue", newValue);
</script>
```

### Passing Props (template)
```vue
<!-- camelCase props → kebab-case attributes (both allowed, kebab recommended) -->
<UserCard
  :user-id="user.id"
  :is-active="user.isActive"
  :full-name="user.name"
/>

<!-- Boolean props: usable without a value -->
<Modal visible closable />
<!-- Same meaning: <Modal :visible="true" :closable="true" /> -->
```

---

## 7. Import & Dependencies

### Import Order
```ts
// 1. Vue core
import { ref, computed, watch, onMounted } from "vue";

// 2. Vue ecosystem (Router, Pinia)
import { useRouter, useRoute } from "vue-router";
import { storeToRefs } from "pinia";

// 3. Third-party
import axios from "axios";
import dayjs from "dayjs";

// 4. Internal components
import UserCard from "@/components/UserCard.vue";
import BaseButton from "@/components/ui/BaseButton.vue";

// 5. Composables
import { useAuth } from "@/composables/useAuth";
import { useUser } from "@/composables/useUser";

// 6. Store
import { useUserStore } from "@/stores/user";

// 7. Utils / constants
import { formatDate } from "@/utils/formatters";
import { API_ENDPOINTS } from "@/constants";

// 8. Types
import type { User, UserRole } from "@/types";
```

---

## 8. State Management (Pinia)

```ts
// stores/user.ts
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { User } from "@/types";
import { userApi } from "@/services/userApi";

// Setup Store style (consistent with the Composition API)
export const useUserStore = defineStore("user", () => {
  // state
  const users = ref<User[]>([]);
  const currentUser = ref<User | null>(null);
  const isLoading = ref(false);

  // getters (computed)
  const activeUsers = computed(() =>
    users.value.filter((u) => u.isActive)
  );

  const userCount = computed(() => users.value.length);

  // actions (functions)
  async function fetchUsers() {
    isLoading.value = true;
    try {
      users.value = await userApi.getAll();
    } finally {
      isLoading.value = false;
    }
  }

  async function deleteUser(userId: number) {
    await userApi.delete(userId);
    users.value = users.value.filter((u) => u.id !== userId);
  }

  function reset() {
    users.value = [];
    currentUser.value = null;
  }

  return {
    // state
    users,
    currentUser,
    isLoading,
    // getters
    activeUsers,
    userCount,
    // actions
    fetchUsers,
    deleteUser,
    reset,
  };
});
```

### Using the Store
```vue
<script setup lang="ts">
import { storeToRefs } from "pinia";
import { useUserStore } from "@/stores/user";

const userStore = useUserStore();

// Use storeToRefs to preserve reactivity
const { users, isLoading, activeUsers } = storeToRefs(userStore);

// actions can be destructured directly
const { fetchUsers, deleteUser } = userStore;

onMounted(() => {
  fetchUsers();
});
</script>
```

---

## 9. Type Definitions

```ts
// types/user.ts
export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export type UserRole = "admin" | "editor" | "viewer";

export interface CreateUserPayload {
  name: string;
  email: string;
  role?: UserRole;
}

export interface UpdateUserPayload extends Partial<CreateUserPayload> {
  id: number;
}

// types/api.ts
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    pageSize: number;
    totalPages: number;
    totalItems: number;
  };
}
```

---

## 10. File Rules

### File Rules
- Component: **PascalCase.vue** (single file)
- View (page): **PascalCase + View suffix** (`UserListView.vue`)
- Max line length: **100 chars** (Prettier)
- Semicolons: **yes**
- Quotes: **double quotes** (template consistency)

### Naming Prefix Patterns
- Base components: `Base` prefix (`BaseButton`, `BaseInput`)
- Layout: `App` prefix (`AppHeader`, `AppSidebar`)
- Views: `View` suffix (`UserListView`)
- Store: `use` + `Store` suffix (`useUserStore`)
