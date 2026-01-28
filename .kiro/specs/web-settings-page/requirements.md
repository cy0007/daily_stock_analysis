# 需求文档

## 简介

为 A股自选股智能分析系统添加 WebUI 配置页面功能，将原本需要手动编辑 .env 文件的配置项迁移到网页界面，降低用户配置门槛。配置数据持久化存储到 SQLite 数据库，程序启动时优先读取数据库配置，.env 文件作为备选。

## 术语表

- **Settings_Page**: WebUI 设置页面，用于管理系统配置
- **Config_Store**: 配置存储服务，负责配置的持久化读写
- **Config_Manager**: 配置管理器，负责配置的加载优先级控制
- **API_Key**: 第三方服务的访问密钥（如 Gemini、Tavily、SerpAPI、Tushare）
- **Stock_List**: 自选股列表，用户关注的股票代码集合
- **Email_Config**: 邮件推送配置，包含发件人、密码、收件人
- **Schedule_Config**: 定时任务配置，包含启用状态和执行时间

## 需求

### 需求 1：配置存储服务

**用户故事：** 作为系统管理员，我希望配置能够持久化存储到数据库，以便在系统重启后保留用户设置。

#### 验收标准

1. THE Config_Store SHALL 在 SQLite 数据库中创建 `system_settings` 表存储配置项
2. THE Config_Store SHALL 支持以键值对形式存储配置（key-value 结构）
3. WHEN 保存配置时，THE Config_Store SHALL 对敏感字段（API Keys、密码）进行加密存储
4. WHEN 读取配置时，THE Config_Store SHALL 自动解密敏感字段
5. THE Config_Store SHALL 提供批量读写配置的接口

### 需求 2：配置加载优先级

**用户故事：** 作为开发者，我希望系统优先使用数据库配置，.env 作为备选，以便灵活管理配置来源。

#### 验收标准

1. WHEN 系统启动时，THE Config_Manager SHALL 优先从数据库读取配置
2. IF 数据库中不存在某配置项，THEN THE Config_Manager SHALL 从 .env 文件读取该配置
3. IF 数据库和 .env 都不存在某配置项，THEN THE Config_Manager SHALL 使用代码中的默认值
4. THE Config_Manager SHALL 提供刷新配置的方法，支持运行时重新加载

### 需求 3：设置页面 - API Keys 配置

**用户故事：** 作为用户，我希望在网页上配置各种 API Keys，以便无需编辑 .env 文件。

#### 验收标准

1. THE Settings_Page SHALL 提供表单输入以下 API Keys：
   - Gemini API Key
   - Tavily API Keys（支持多个，逗号分隔）
   - SerpAPI Keys（支持多个，逗号分隔）
   - Tushare Token
2. WHEN 显示已保存的 API Key 时，THE Settings_Page SHALL 仅显示部分字符（如 `sk-****xxxx`）以保护隐私
3. WHEN 用户提交表单时，THE Settings_Page SHALL 验证输入格式并保存到数据库
4. IF 用户清空某个 API Key 输入框并提交，THEN THE Config_Store SHALL 删除该配置项

### 需求 4：设置页面 - 自选股配置

**用户故事：** 作为用户，我希望在网页上管理自选股列表，以便快速添加或删除关注的股票。

#### 验收标准

1. THE Settings_Page SHALL 提供文本区域输入自选股代码（支持逗号或换行分隔）
2. WHEN 用户提交自选股列表时，THE Settings_Page SHALL 验证股票代码格式（6位数字）
3. WHEN 保存自选股列表时，THE Config_Store SHALL 同时更新数据库和 .env 文件（保持向后兼容）

### 需求 5：设置页面 - 邮件推送配置

**用户故事：** 作为用户，我希望在网页上配置邮件推送，以便接收股票分析报告。

#### 验收标准

1. THE Settings_Page SHALL 提供表单输入以下邮件配置：
   - 发件人邮箱
   - 邮箱密码/授权码
   - 收件人邮箱（支持多个，逗号分隔）
2. WHEN 显示已保存的邮箱密码时，THE Settings_Page SHALL 显示为掩码（如 `********`）
3. THE Settings_Page SHALL 提供"测试发送"按钮，验证邮件配置是否正确

### 需求 6：设置页面 - 定时任务配置

**用户故事：** 作为用户，我希望在网页上配置定时任务，以便自动执行股票分析。

#### 验收标准

1. THE Settings_Page SHALL 提供以下定时任务配置：
   - 启用/禁用开关
   - 执行时间（支持多个时间点，如 `09:30,15:30,18:00`）
   - 大盘复盘启用开关
2. WHEN 用户修改定时任务配置时，THE Config_Manager SHALL 通知调度器重新加载配置
3. THE Settings_Page SHALL 显示下次执行时间预览

### 需求 7：设置页面路由与导航

**用户故事：** 作为用户，我希望能够方便地访问设置页面，以便管理系统配置。

#### 验收标准

1. THE Settings_Page SHALL 通过 `/settings` 路径访问
2. THE Settings_Page SHALL 在现有首页添加"设置"导航链接
3. WHEN 配置保存成功时，THE Settings_Page SHALL 显示成功提示消息
4. IF 配置保存失败，THEN THE Settings_Page SHALL 显示错误信息并保留用户输入
