# Vue Router 导航守卫详解

> 本文档详细介绍 Vue Router 4.x 的导航守卫（Navigation Guards）机制，包括类型、用法和常见应用场景。

---

## 一、什么是导航守卫？

**导航守卫**是 Vue Router 提供的一种拦截机制，允许你在路由跳转的不同阶段插入自定义逻辑。

常见用途：
- 🔐 登录权限验证
- 📊 页面访问埋点
- 📝 动态修改页面标题
- 🚫 阻止未保存的表单离开

---

## 二、守卫类型一览

Vue Router 提供了 **3 类守卫**，按作用范围从大到小排列：

| 类型 | 定义位置 | 作用范围 | 适用场景 |
|------|----------|----------|----------|
| **全局守卫** | `router.beforeEach()` | 所有路由 | 登录验证、全局权限 |
| **路由独享守卫** | 路由配置 `beforeEnter` | 单个路由 | 特定页面准入检查 |
| **组件内守卫** | 组件 `onBeforeRouteLeave` 等 | 单个组件 | 离开确认、数据预加载 |

---

## 三、全局守卫（最常用）

### 3.1 三种全局守卫

```typescript
// 1. 全局前置守卫 - 跳转前执行（最常用）
router.beforeEach((to, from) => { ... })

// 2. 全局解析守卫 - 在组件内守卫和异步路由组件解析后调用
router.beforeResolve((to, from) => { ... })

// 3. 全局后置钩子 - 跳转完成后执行（无法阻止跳转）
router.afterEach((to, from) => { ... })
```

### 3.2 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `to` | RouteLocationNormalized | 目标路由对象（即将进入的页面） |
| `from` | RouteLocationNormalized | 来源路由对象（当前所在页面） |

常用属性：

```typescript
router.beforeEach((to, from) => {
  console.log(to.path)       // 路径，如 '/login'
  console.log(to.name)       // 路由名，如 'Login'
  console.log(to.meta)       // 元信息，如 { requiresAuth: true }
  console.log(to.params)     // 动态参数，如 { id: '123' }
  console.log(to.query)      // 查询参数，如 { page: '1' }
})
```

### 3.3 返回值控制跳转

Vue Router 4.x 简化了 API，通过**返回值**控制跳转行为：

| 返回值 | 效果 |
|--------|------|
| 不返回 / `undefined` | 放行，继续跳转 |
| `true` | 放行 |
| `false` | 取消跳转，留在当前页面 |
| `'/path'` | 重定向到指定路径 |
| `{ path: '/path' }` | 重定向（对象形式） |
| `{ name: 'RouteName' }` | 重定向到命名路由 |

示例：

```typescript
router.beforeEach((to, from) => {
  // 需要登录但未登录
  if (to.meta.requiresAuth && !isLoggedIn()) {
    return '/login'  // 重定向到登录页
  }
  // 不返回表示放行
})
```

---

## 四、路由元信息 `meta`

### 4.1 定义 meta

在路由配置中添加自定义字段：

```typescript
const routes = [
  {
    path: '/admin',
    component: AdminView,
    meta: {
      requiresAuth: true,      // 需要登录
      roles: ['admin'],        // 需要 admin 角色
      title: '管理后台'         // 页面标题
    }
  }
]
```

### 4.2 在守卫中读取 meta

```typescript
router.beforeEach((to, from) => {
  if (to.meta.requiresAuth) {
    // 进行登录验证...
  }
})
```

### 4.3 TypeScript 类型扩展

如果使用 TypeScript，需要扩展 `RouteMeta` 类型：

```typescript
// src/router/index.ts 或单独的类型文件
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: string[]
    title?: string
  }
}
```

---

## 五、常见应用场景

### 场景 1：登录验证

```typescript
import { getToken } from '@/modules/auth/token'

router.beforeEach((to, from) => {
  if (to.meta.requiresAuth && !getToken()) {
    return '/login'
  }
})
```

### 场景 2：动态页面标题

```typescript
router.afterEach((to) => {
  const baseTitle = 'InkFlow'
  document.title = to.meta.title 
    ? `${to.meta.title} - ${baseTitle}` 
    : baseTitle
})
```

### 场景 3：路由切换进度条

```typescript
import NProgress from 'nprogress'

router.beforeEach(() => {
  NProgress.start()
})

router.afterEach(() => {
  NProgress.done()
})
```

### 场景 4：页面访问埋点

```typescript
router.afterEach((to, from) => {
  analytics.trackPageView({
    path: to.path,
    referrer: from.path
  })
})
```

### 场景 5：阻止离开未保存的表单

在组件内使用：

```typescript
import { onBeforeRouteLeave } from 'vue-router'

// 在 setup 中
onBeforeRouteLeave((to, from) => {
  if (hasUnsavedChanges.value) {
    const confirmed = window.confirm('有未保存的更改，确定离开吗？')
    if (!confirmed) return false
  }
})
```

---

## 六、执行顺序

完整的导航解析流程：

```
1. 导航被触发
     ↓
2. 失活组件调用 onBeforeRouteLeave
     ↓
3. 调用全局 beforeEach
     ↓
4. 重用组件调用 onBeforeRouteUpdate
     ↓
5. 路由配置中的 beforeEnter
     ↓
6. 解析异步路由组件
     ↓
7. 激活组件调用 onBeforeRouteEnter
     ↓
8. 调用全局 beforeResolve
     ↓
9. 导航确认
     ↓
10. 调用全局 afterEach
     ↓
11. DOM 更新
```

---

## 七、注意事项

### 7.1 避免无限重定向

```typescript
// ❌ 错误：会无限循环！
router.beforeEach((to, from) => {
  if (!isLoggedIn()) {
    return '/login'  // 访问 /login 也会触发，再次重定向...
  }
})

// ✅ 正确：排除登录页
router.beforeEach((to, from) => {
  if (to.meta.requiresAuth && !isLoggedIn()) {
    return '/login'
  }
})
```

### 7.2 异步守卫

守卫可以是 `async` 函数：

```typescript
router.beforeEach(async (to, from) => {
  if (to.meta.requiresAuth) {
    const user = await fetchCurrentUser()
    if (!user) return '/login'
  }
})
```

---

## 八、总结

| 概念 | 说明 |
|------|------|
| `beforeEach` | 全局前置守卫，每次跳转前执行 |
| `afterEach` | 全局后置守卫，跳转完成后执行 |
| `to` / `from` | 目标/来源路由对象 |
| 返回值 | 控制放行、重定向或取消跳转 |
| `meta` | 路由元信息，用于自定义标签 |
| `to.meta.requiresAuth` | 常用的登录验证标记 |

---

## 相关链接

- [Vue Router 官方文档 - 导航守卫](https://router.vuejs.org/zh/guide/advanced/navigation-guards.html)
