# 注册功能重构进度说明 (Registration Process)

本篇文档记录了“极简注册 (Email Only) + 自动登录”功能的开发进度与实施步骤。

## 1. 总体目标
- [x] **后端**: 支持纯邮箱+验证码注册，自动生成用户名和头像，注册即返回 Token。
- [x] **前端**: 实现验证码发送、注册提交、自动保存登录态并跳转。

---

## 2. 后端进度 (Completed ✅)

### 2.1 数据模型与逻辑
- [x] **Schema 重构**: 取消 `UserBase` 继承，显式定义 `UserCreate` 和 `UserResponse`。
- [x] **自动生成用户名**: 实现 `_generate_unique_username`，基于邮箱前缀+随机 4 位字符，确保数据库唯一。
- [x] **自动生成头像**: 集成 **DiceBear API**，根据用户名种子生成 `adventurer` 风格卡通头像 URL。
- [x] **安全性增强**: 实现 Redis 验证码校验 `verify_code` 逻辑，验证即销毁。

### 2.2 接口规格 (API Specs)
- [x] `POST /auth/send-code`: 发送 6 位数字验证码到邮箱（当前模拟打印控制台）。
- [x] `POST /auth/register`: 接收 `{email, password, verification_code}`，返回 `UserAuthResponse`（含 Token）。
- [x] `POST /auth/login`: 适配 `UserAuthResponse` 结构，返回 Token 和完整用户信息。

---

## 3. 前端实施计划 (Completed ✅)

### 第一阶段：API 基础设施升级 (Infrastructure)
- [x] **`api` 目录重构**: 
    - 建立 `src/api/index.ts` (Axios 基础实例，含拦截器和环境变量配置)。
    - 建立 `src/api/auth.api.ts` (业务接口)。
    - 完整定义 `User`, `AuthResponse` 等 TypeScript 接口，与后端 Schema 对齐。

### 第二阶段：状态管理适配 (Store)
- [x] **`auth.store.ts` 升级**:
    - 更新 `login` action，直接存储后端返回的 `user` 对象。
    - 新增 `register` action，实现“注册即登录”逻辑 (复用 setToken)。

### 第三阶段：界面逻辑实装 (UI/UX)
- [x] **`RegisterView.vue` 对接**:
    - 实装 `sendCodeApi`，配合倒计时逻辑。
    - 实装 `authStore.register`，成功后自动跳转首页。
    - 完善错误处理（如邮箱占用提示）。

---

## 4. 下一步计划 (Next Steps 🚀)

**当前状态**：用户已成功注册并登录，拥有自动生成的 Username 和 Avatar。

### 优先任务：用户个人中心 (User Profile)
- [ ] **后端**: 
    - 确认 `PATCH /users/me` 接口逻辑，确保允许修改 `nickname`, `bio` 等字段。
    - (可选) 确认头像上传或修改机制。
- [ ] **前端**:
    - 创建/完善 `UserProfileView.vue` (个人资料页)。
    - 对接修改资料 API。
    - 展示用户的卡通头像和基本信息。

### 后续任务
- [ ] 文章发布功能 (Post CRUD)。
- [ ] 单元测试补充 (Vitest)。
