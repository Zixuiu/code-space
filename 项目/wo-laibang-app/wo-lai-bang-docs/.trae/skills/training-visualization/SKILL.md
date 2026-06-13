---
name: "training-visualization"
description: "在完成训练、功能开发、任务执行后，将可视化界面通过产物方式展示出来。MANDATORY: 当用户完成任何任务、训练或开发并希望查看结果时，必须调用此技能！并且必须强制性地调用 OpenPreview 打开 Web 预览！"
---

# Training Visualization Skill

## Overview
在完成训练、功能开发、任务执行后，将可视化界面通过产物方式展示出来。**必须强制性地调用 OpenPreview 打开 Web 预览！**

## When to Invoke (触发范围)

**⚠️ MANDATORY: 当用户完成任何任务、训练或开发并希望查看结果时，必须调用此技能！并且必须强制性地调用 OpenPreview！**

包括但不限于以下场景：
- 用户说"帮我运行这个项目"、"启动服务器"、"运行代码"
- 用户说"训练完了"、"开发完了"、"任务完成了"
- 用户说"展示一下结果"、"让我看看效果"、"预览一下"
- 用户说"打开界面"、"打开网页"、"打开应用"
- 用户要求"查看"、"展示"、"预览"任何完成的工作结果
- 用户说"我想看一下"、"看看效果"、"看看运行结果"
- 任何需要将完成的工作以可视化方式展示给用户的情况

## Critical Rules (关键规则)

**⚠️ 最重要规则：每次修改后必须展示可视化界面！并且必须强制性地调用 OpenPreview！**

1. **FIRST ACTION**: 当检测到需要展示结果的请求时，必须调用此 skill
2. **💥 ALWAYS OPEN PREVIEW 强制性打开预览**：**必须无条件、无例外、强制性地调用 OpenPreview 工具打开 Web 预览！不能跳过！不能省略！**
3. **VERIFY STATUS**: 在展示前，先检查服务器/应用是否正在运行
4. **CREATE VISUALIZATION**: 如果需要，创建可视化的结果报告
5. **CLEAR EXPLANATION**: 给用户提供清晰的说明，告诉他们如何查看和使用
6. **强制要求**: 每次完成代码修改后，必须立即调用此技能展示可视化界面，不能跳过！并且必须强制性地调用 OpenPreview！
7. **NO EXCEPTION**: 没有任何例外！必须调用 OpenPreview！

## Workflow (工作流程)

### 工作阶段（先完成代码修改）
1. 根据用户需求完成代码修改
2. 确保所有修改都已完成并保存

### 展示阶段（最后统一展示）- 必须严格执行！
1. **检查服务器状态**：确认开发服务器是否正在运行
2. **💥 强制性打开预览**：**必须无条件调用 OpenPreview 工具打开 Web 预览！这一步不能省略！不能跳过！**
3. **创建报告**（可选）：创建可视化结果报告
4. **给用户说明**：告诉用户预览已经打开，说明如何使用

**⚠️ 重要：不要在工作进行中反复检查状态和打开预览，只在最后统一展示一次！但最后必须展示！必须调用 OpenPreview！**

## Code Patterns (代码模式)

### 💥 0. 标准完整流程（必须严格执行）
```javascript
// 第一步：检查服务器状态
RunCommand({
  command: "ps aux | grep vite",
  blocking: true,
  requires_approval: false,
  target_terminal: "new"
})

// 第二步：如果服务器没运行，启动服务器
RunCommand({
  command: "npm run dev:h5",
  blocking: false,
  requires_approval: false,
  target_terminal: "new",
  command_type: "web_server",
  wait_ms_before_async: 5000
})

// 第三步：💥 强制性打开预览！必须调用！不能跳过！
OpenPreview({
  command_id: "job-123",
  preview_url: "http://localhost:5173"
})
```

### 1. 检查服务器状态
```javascript
RunCommand({
  command: "ps aux | grep vite",
  blocking: true,
  requires_approval: false,
  target_terminal: "new"
})
```

### 2. 💥 打开预览（必须调用！强制性！）
```javascript
OpenPreview({
  command_id: "dev-server",
  preview_url: "http://localhost:5173"
})
```

### 3. 启动开发服务器（如果需要）
```javascript
RunCommand({
  command: "npm run dev:h5",
  blocking: false,
  requires_approval: false,
  target_terminal: "new",
  command_type: "web_server",
  wait_ms_before_async: 5000
})
```

### 4. 创建可视化结果报告
```javascript
Write({
  file_path: "/workspace/docs/visualization-report.md",
  content: `# 可视化结果报告

## 完成的工作
- ✅ 任务1: ...
- ✅ 任务2: ...

## 主要功能
- 功能1: ...
- 功能2: ...

## 使用指南
1. 打开浏览器访问 http://localhost:5173
2. ...

## 预览截图
（在此处插入截图描述）
`
})
```

## Example (完整示例)

### 用户请求
"帮我运行这个项目，然后让我看看效果"

### 执行步骤（必须严格执行！）
1. 检查服务器是否正在运行
2. 如果没有，启动 `npm run dev:h5`
3. 等待服务器启动
4. **💥 强制性调用 OpenPreview 打开预览！不能跳过！**
5. 给用户说明如何查看

### 响应
"✅ 项目已经成功运行！
- 🚀 开发服务器已启动
- 🌐 预览地址: http://localhost:5173
- 📱 请在浏览器中打开查看

**使用说明**:
1. 在浏览器中访问 http://localhost:5173
2. 你会看到应用的主界面
3. 可以进行各种操作测试功能"

## Common Preview URLs (常用预览地址)
- Vite/UniApp: `http://localhost:5173`
- Webpack: `http://localhost:8080`
- React: `http://localhost:3000`
- Vue: `http://localhost:8080`

## Important Notes (注意事项)

1. **💥 强制性要求**：**必须无条件调用 OpenPreview！不能跳过！不能省略！**
2. **始终确保服务正在运行**: 在打开预览前，必须确认服务已启动
3. **提供清晰说明**: 告诉用户如何查看和使用
4. **保持简洁**: 不要给用户过多不必要的信息
5. **确保 URL 正确**: 检查预览地址是否正确
6. **NO EXCEPTION**: 没有任何例外！必须调用 OpenPreview！
