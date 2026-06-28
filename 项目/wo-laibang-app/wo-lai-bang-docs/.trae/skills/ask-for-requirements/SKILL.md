# ask-for-requirements

**Description:** 在每次接收到用户问题后，先询问用户具体的需求是什么。MANDATORY: 每次用户提问时，必须首先调用此技能！

## Overview
每次用户提问时，先暂停下来，使用 AskUserQuestion 工具向用户询问具体需求，确保我们完全理解用户想要做什么。

## When to Invoke (触发范围)

**⚠️ MANDATORY: 每次用户提问时，必须首先调用此技能！**

包括但不限于以下场景：
- 用户发送任何问题或请求
- 用户说"帮我..."、"我想..."、"请你..."
- 用户提出功能需求、修改建议或问题报告
- 用户任何需要进一步澄清的请求

## Critical Rules (关键规则)

1. **FIRST ACTION**: 每次接收到用户问题时，必须首先调用此 skill
2. **USE AskUserQuestion**: 必须使用 AskUserQuestion 工具来询问用户
3. **CLEAR QUESTIONS**: 询问的问题要清晰、具体，帮助用户明确表达需求
4. **MULTIPLE QUESTIONS**: 如果需求不明确，可以询问多个问题
5. **WAIT FOR RESPONSE**: 必须等待用户回复后，再开始执行任务

## Workflow (工作流程)

### 询问阶段
1. 接收用户问题
2. 使用 AskUserQuestion 工具向用户询问具体需求
3. 等待用户回复
4. 根据用户的回复，明确任务范围和需求

### 执行阶段
1. 理解用户明确的需求
2. 开始执行相应的任务

## Code Patterns (代码模式)

### 1. 询问用户需求
```javascript
AskUserQuestion({
  questions: [
    {
      question: "请您详细描述一下您想要实现的功能或解决的问题是什么？",
      header: "需求确认",
      options: [],
      multiSelect: false
    },
    {
      question: "这个功能是给谁使用的？有什么特殊的使用场景吗？",
      header: "使用场景",
      options: [],
      multiSelect: false
    },
    {
      question: "您希望这个功能达到什么样的效果或目标？",
      header: "目标效果",
      options: [],
      multiSelect: false
    }
  ]
})
```

### 2. 简单询问
```javascript
AskUserQuestion({
  questions: [
    {
      question: "请您详细说明一下具体的需求是什么？",
      header: "需求确认",
      options: [],
      multiSelect: false
    }
  ]
})
```

## Example (完整示例)

### 用户输入
"帮我修复一下这个问题"

### 执行步骤
1. 使用 AskUserQuestion 向用户询问
2. 用户回复具体需求
3. 根据用户回复开始任务

### 询问示例
"为了更好地帮助您，我需要了解一些信息：
1. 请您详细描述一下遇到的问题是什么？
2. 这个问题在什么情况下会出现？
3. 您期望的正确结果应该是什么？"

## Important Notes (注意事项)

1. **始终先询问**: 在没有明确用户需求前，不要开始执行任何任务
2. **问题要清晰**: 询问的问题要简单明了，避免让用户困惑
3. **灵活调整**: 根据用户初步的回复，可以进一步追问更具体的问题
4. **记录需求**: 确保理解了用户的所有需求后，再开始工作
