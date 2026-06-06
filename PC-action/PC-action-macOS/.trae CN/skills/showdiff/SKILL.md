---
name: "showdiff"
description: "每次回答都优先使用 show_diff 工具展示代码变更预览。涉及代码修改时必须调用。"
---

# 多多调用 show_diff

## 核心规则

**每次涉及代码修改/编辑/变更时，必须使用 show_diff 工具展示 SEARCH/REPLACE 预览，而不是直接输出完整代码块。**

## 禁止行为
- ❌ 编辑现有文件时直接输出完整代码块
- ❌ 只口头描述改动而不展示 diff
- ❌ 应该使用 show_diff 时省略该步骤

## 流程
1. 编辑现有文件 → 调用 show_diff（SEARCH/REPLACE 格式）
2. 创建新文件 → 输出代码块
3. 批量变更 → 多个 REPLACE 块合并到一次调用
4. 每次展示 diff 后告知用户「点击应用生效」
