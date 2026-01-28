# 实现计划: WebUI 配置页面

## 概述

将 .env 文件配置迁移到 WebUI 页面，实现配置的可视化管理。采用增量实现方式，每个任务构建在前一个任务基础上。

## 任务

- [-] 1. 创建配置存储层
  - [x] 1.1 在 `src/storage.py` 中添加 `SystemSetting` ORM 模型
    - 定义 system_settings 表结构（id, key, value, is_encrypted, category, description, created_at, updated_at）
    - 添加 key 字段的唯一索引
    - _Requirements: 1.1, 1.2_

  - [x] 1.2 创建 `src/config_store.py` 配置存储服务
    - 实现 `ConfigStore` 类，包含 get/set/delete/get_all/set_batch 方法
    - 实现 Fernet 加密/解密逻辑（_encrypt/_decrypt 方法）
    - 定义 SENSITIVE_KEYS 敏感字段列表
    - _Requirements: 1.3, 1.4, 1.5_

  - [ ] 1.3 编写 ConfigStore 属性测试
    - **Property 1: 敏感配置加密 Round-Trip**
    - **Validates: Requirements 1.3, 1.4**

- [-] 2. 修改配置管理器
  - [x] 2.1 修改 `src/config.py` 实现配置加载优先级
    - 修改 `_load_from_env` 方法，优先从 ConfigStore 读取
    - 添加 `reload` 方法支持运行时刷新
    - 保持与现有代码的向后兼容
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ] 2.2 编写配置优先级属性测试
    - **Property 2: 配置加载优先级**
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [ ] 3. Checkpoint - 确保存储层测试通过
  - 运行所有测试，确保配置存储和加载逻辑正确
  - 如有问题请询问用户

- [-] 4. 创建设置页面服务层
  - [x] 4.1 创建 `web/settings_service.py` 设置业务服务
    - 实现 `SettingsService` 类
    - 实现 `get_all_settings` 获取所有设置
    - 实现 `save_api_keys`、`save_stock_list`、`save_email_config`、`save_schedule_config` 方法
    - 实现 `mask_sensitive_value` 敏感值掩码方法
    - 实现 `test_email_send` 测试邮件发送方法
    - _Requirements: 3.2, 3.3, 4.2, 4.3, 5.2, 5.3_

  - [ ] 4.2 编写敏感值掩码属性测试
    - **Property 3: 敏感值掩码格式**
    - **Validates: Requirements 3.2, 5.2**

  - [ ] 4.3 编写股票代码验证属性测试
    - **Property 6: 股票代码格式验证**
    - **Validates: Requirements 4.2**

- [-] 5. 创建设置页面处理器
  - [x] 5.1 创建 `web/settings_handler.py` 设置页面处理器
    - 实现 `SettingsHandler` 类
    - 实现 `handle_settings_page` 渲染设置页面
    - 实现 `handle_save_api_keys`、`handle_save_stocks`、`handle_save_email`、`handle_save_schedule` 方法
    - 实现 `handle_test_email` 测试邮件发送
    - _Requirements: 3.1, 3.3, 3.4, 4.1, 5.1, 6.1, 7.3, 7.4_

  - [ ] 5.2 编写配置保存与删除属性测试
    - **Property 4: 配置保存与删除**
    - **Validates: Requirements 3.3, 3.4**

- [x] 6. 创建设置页面模板
  - [x] 6.1 在 `web/templates.py` 中添加设置页面模板
    - 实现 `render_settings_page` 函数
    - 创建 API Keys 配置表单（Gemini、Tavily、SerpAPI、Tushare）
    - 创建自选股配置表单
    - 创建邮件配置表单（发件人、密码、收件人、测试按钮）
    - 创建定时任务配置表单（启用开关、执行时间、大盘复盘开关）
    - 显示下次执行时间预览
    - _Requirements: 3.1, 4.1, 5.1, 5.3, 6.1, 6.3_

- [x] 7. 注册路由和导航
  - [x] 7.1 在 `web/router.py` 中注册设置页面路由
    - 注册 GET /settings 路由
    - 注册 POST /settings/api-keys、/settings/stocks、/settings/email、/settings/schedule 路由
    - 注册 POST /settings/test-email 路由
    - _Requirements: 7.1_

  - [x] 7.2 修改 `web/templates.py` 首页添加设置导航链接
    - 在 `render_config_page` 中添加"⚙️ 设置"链接
    - _Requirements: 7.2_

- [ ] 8. Checkpoint - 确保页面功能正常
  - 运行所有测试，确保设置页面可正常访问和操作
  - 如有问题请询问用户

- [ ] 9. 集成调度器配置刷新
  - [ ] 9.1 修改调度器支持配置热更新
    - 在 `src/scheduler.py` 中添加配置变更监听
    - 实现定时任务配置变更后重新加载
    - _Requirements: 6.2_

  - [ ] 9.2 编写自选股双写属性测试
    - **Property 5: 自选股双写一致性**
    - **Validates: Requirements 4.3**

- [ ] 10. 最终检查点 - 确保所有测试通过
  - 运行完整测试套件
  - 验证所有功能正常工作
  - 如有问题请询问用户

## 备注

- 每个任务引用具体需求以保证可追溯性
- 检查点确保增量验证
- 属性测试验证通用正确性属性
