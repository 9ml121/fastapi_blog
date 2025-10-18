## phase5.2 待办清单
- [x] Step 1: 创建自定义异常类（app/core/exceptions.py）✅ 首次模式
- [x] Step 2: 配置 CORS 和异常处理器（app/main.py）
- [x] Step 3: 添加环境配置（app/core/config.py） ⏬ ✅ 2025-10-16
- [x] Step 4: 修改 auth 端点使用新异常（app/api/v1/endpoints/auth.py）
- [x] Step 5: 修改 users 端点使用新异常（app/api/v1/endpoints/users.py）
- [x] Step 6: 优化 API 文档元数据（app/main.py 和路由）



## phase5 遗留问题
- [x] user 数据模型中，校验密码的代码逻辑有重复 ✅ 2025-10-12
- [x] user api 的 get_current_user_profile 和 auth 的get_current_user_info 重复 ✅ 2025-10-12
- [ ] 🔼 按照 deps.py 重构 users 的 CRUD代码
	- update_user 方法处理密码更新的逻辑应该删除
	- update_user 也应该检查邮箱冲突
	- 抽取两个 update方法中邮箱更新的方法  - option
- [ ] user 数据库模型增加 bio字段（个人简介/签名），涉及修改模型、schema、迁移 🔼 
- [x] 已定义全局异常处理类，修改 user 和 auth的 api端点异常处理，还有其他 api 和测试用例待修改 🔺 ✅ 2025-10-16
- [ ] OpenAPI的文档markdown说明在 swagger UI 没有渲染出来 🔽 
- [ ] 统一重构配置管理，目前是硬编码 🔽 
- [ ] 很多地方异常没有适配全局异常 ⏫  




 在开始编码前，我有几个设计问题需要与你确认：

  1. 状态流转规则：
    - 已发布的文章能否改回草稿？（当前设计：不能，防止丢失内容）
    - 归档的文章能否恢复为已发布？（当前设计：不能）
  2. 草稿可见性：
    - 管理员是否应该能查看所有用户的草稿？（当前设计：只有作者能看）
  3. 删除逻辑：
    - 删除文章时是否应该只允许删除草稿和归档文章？（当前设计：所有状态可删除）

  请确认这些设计决策是否合理，或者你有其他想法？