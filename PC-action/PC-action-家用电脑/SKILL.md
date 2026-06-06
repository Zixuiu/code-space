# SKILLS

## 技能列表

### codemap

#### 基本信息
```yaml
name: codemap
description: 分析PC-action项目的代码结构、模块依赖和变更。当询问项目结构、代码位置、文件关联、变更内容时使用，或在开始编码任务前使用，提供项目架构上下文。
```

#### 指令
```
Codemap为您提供PC-action项目的即时架构上下文。在探索或修改代码之前主动使用它。
```

#### 命令
```
codemap [options]
  --path <directory>  指定要分析的代码目录（默认: ./resent）
  --depth <number>    设置分析深度（默认: 3）
  --format <format>   输出格式 (tree, graph, json)
  --filter <pattern>  过滤文件和目录（常用: py, ui, db, manager, login, build）
```

#### 使用场景
1. **项目结构探索**：了解PC-action的模块划分、核心文件位置
2. **用户管理代码查找**：找到用户登录、注册、管理相关的代码
3. **数据库操作分析**：查看Supabase和本地数据库的交互逻辑
4. **UI组件定位**：查找特定UI组件的实现代码
5. **打包流程了解**：查看EXE打包相关的脚本和配置

#### 输出解释
- **树状结构**：以层级树形式展示PC-action项目的目录和文件结构
- **依赖图**：可视化展示模块间的依赖关系
- **文件关系**：显示文件之间的导入、调用关系
- **变更摘要**：展示最近的代码变更内容和作者

#### 示例
```
# 示例1：获取主应用目录结构
codemap --path ./resent --depth 2

# 示例2：查找用户管理相关文件
codemap --path ./resent --filter "manager"

# 示例3：查看数据库相关代码
codemap --path ./resent --filter "db"

# 示例4：查看UI相关代码
codemap --path ./resent --filter "ui"
```

#### 输出示例
```
项目结构 (深度: 2):
├── PC-action/
│   ├── resent/           # 主应用目录
│   │   ├── app.py        # 主入口文件
│   │   ├── hybrid_db.py  # 混合数据库管理
│   │   ├── supabase_db.py # Supabase操作
│   │   ├── admin_manager.py # 管理员功能
│   │   ├── login_manager.py # 登录认证
│   │   ├── login_ui.py   # 登录界面
│   │   ├── build_exe_improved.py # 打包脚本
│   │   └── users.json    # 本地用户数据
│   ├── user_data/        # 用户数据目录
│   └── SKILL.md          # 技能定义文件

依赖关系:
app.py → hybrid_db.py, login_manager.py
admin_manager.py → hybrid_db.py, login_manager.py
login_manager.py → hybrid_db.py
build_exe_improved.py → 无内部依赖
```

### pyqt5_ui

#### 基本信息
```yaml
name: pyqt5_ui
description: 分析和修改PC-action项目的PyQt5界面组件。当需要调整UI布局、添加新组件或修改交互逻辑时使用。
```

#### 指令
```
PyQt5 UI技能为您提供PC-action项目的界面组件分析和修改能力。在调整UI布局、添加新组件或修改交互逻辑时使用。
```

#### 命令
```
pyqt5_ui [options]
  --file <path>       指定要分析的UI文件或Python文件
  --action <action>   执行的操作 (analyze, modify, add)
  --component <name>  组件名称
  --property <prop>   组件属性 (如: text, geometry, enabled)
  --value <value>     属性值
```

#### 使用场景
1. **UI组件分析**：了解特定UI组件的结构和属性
2. **布局调整**：修改界面布局、组件大小和位置
3. **交互逻辑修改**：调整按钮点击事件、输入验证等
4. **新组件添加**：向界面添加新的按钮、输入框等组件

#### 示例
```
# 示例1：分析登录界面
pyqt5_ui --file ./resent/login_ui.py --action analyze

# 示例2：修改登录按钮文本
pyqt5_ui --file ./resent/login_ui.py --action modify --component login_button --property text --value "登录系统"

# 示例3：添加新的按钮组件
pyqt5_ui --file ./resent/admin_manager.py --action add --component new_user_button --property text --value "创建新用户"
```

### supabase_operations

#### 基本信息
```yaml
name: supabase_operations
description: 执行PC-action项目的Supabase数据库操作。当需要查询、修改、添加或删除Supabase数据时使用。
```

#### 指令
```
Supabase Operations技能为您提供PC-action项目的数据库操作能力。在查询、修改、添加或删除Supabase数据时使用。
```

#### 命令
```
supabase_operations [options]
  --operation <op>    操作类型 (select, insert, update, delete)
  --table <name>      表名
  --columns <cols>    列名列表 (如: id, username, email)
  --filter <cond>     过滤条件 (如: id=1, username='admin')
  --data <json>       数据JSON (用于insert和update操作)
```

#### 使用场景
1. **用户数据查询**：查询Supabase中的用户信息
2. **用户数据修改**：更新用户的状态、权限等
3. **新用户添加**：向Supabase添加新用户
4. **用户数据删除**：从Supabase删除用户

#### 示例
```
# 示例1：查询所有用户
supabase_operations --operation select --table users --columns id,username,email

# 示例2：添加新用户
supabase_operations --operation insert --table users --data '{"username":"testuser","email":"test@example.com","password_hash":"hashed_password"}'

# 示例3：更新用户状态
supabase_operations --operation update --table users --filter "id=1" --data '{"is_active":true}'

# 示例4：删除用户
supabase_operations --operation delete --table users --filter "id=1"
```
