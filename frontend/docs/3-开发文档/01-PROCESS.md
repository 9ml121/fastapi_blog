| 顺序  | 任务                                  | 依赖     |
| --- | ----------------------------------- | ------ |
| 1   | 后端：新增 `PasswordResetRequest` Schema | 无      |
| 2   | 后端：实现 `POST /auth/forgot-password`  | Schema |
| 3   | 后端：实现 `POST /auth/reset-password`   | Schema |
| 4   | 后端：测试 API（Swagger UI）               | API 完成 |
| 5   | 前端：创建 `ForgotPasswordView.vue`      | API 完成 |
| 6   | 前端：添加路由                             | 页面完成   |
| 7   | 测试完整流程                              | 全部完成   |
