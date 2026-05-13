# 接单人与被接单人标签及消息通知修复

## 需求概述
修复"我来帮"应用中接单人和被接单人标签显示错误、消息通知逻辑缺失、Store 调用绕过等问题

## 📋 Checklist

### P0 - 必须修复（严重 Bug）

#### 第一轮：标签和按钮显示问题
- [x] 修复 chat.vue 中 roleLabel 标签显示反了的问题
- [x] 修复 need-detail.vue 中 goToChat 方法使用错误字段的问题
- [x] 确保聊天跳转时使用正确的 helper.id 和 helper.nickname
- [x] 修复 need-detail.vue 缺少 Helper 的"申请完成"按钮
- [x] 修复 accept-order.vue handleAccept 没有调用 needStore 的问题
- [x] 修复 order.js applyComplete 权限校验逻辑错误
- [x] 修复 order.js cancelOrder 缺少权限校验

#### 第二轮：按钮显示和逻辑问题
- [x] 修复 need-detail.vue 两个按钮只显示一个的问题（v-else-if 改为 v-if）
- [x] 修复 order-detail.vue 帮手"确认完成"按钮逻辑错误
- [x] 修复 order-detail.vue contactUser 添加更明确错误提示

#### 第三轮：Store 调用绕过问题
- [x] 修复 order-detail.vue completeOrder 方法正确调用 store 并处理返回值
- [x] 修复 order-detail.vue applyComplete 方法调用 orderStore.applyComplete()
- [x] 修复 order-detail.vue confirmComplete 方法调用 needStore.confirmComplete()
- [x] 修复 order-detail.vue cancelOrder 方法调用 orderStore.cancelOrder()
- [x] 修复 orders.vue cancelOrder 方法调用 needStore/orderStore
- [x] 修复 orders.vue sendCancelNotification 添加 TabBar Badge 更新

### P1 - 重要功能（通知逻辑）
- [x] 修复 sendNotification 方法，确保通知能正确保存到本地并更新 TabBar Badge
- [x] 修复 need-detail.vue 中 sendCancelNotification 添加 TabBar Badge 更新
- [x] 修复 order-detail.vue 中 confirmComplete 添加更清晰的通知消息
- [x] 修复 accept-order.vue 中 sendNotification 添加 TabBar Badge 更新
- [x] 修复 need.js sendCompleteNotification 添加 TabBar Badge 更新
- [x] 新增 order-detail.vue sendCancelNotification 单独方法

### P2 - 优化项（数据一致性）
- [x] 统一聊天消息 key 的生成方式，创建 utils/chat.js 工具模块
- [x] 统一 chat.vue 和 need.js 中的 getChatKey 函数

---

## ✅ 验收标准

### 成功场景
1. 用户A发布需求，用户B接单 → 用户A聊天时显示"接单人"标签，用户B显示"发单人"标签 ✅
2. 发布者点击"立即沟通" → 正确跳转到与帮手的聊天页面 ✅
3. 帮手标记完成 → 发布者收到"帮手已申请完成"的通知 ✅
4. 发布者确认完成 → 帮手收到"发布者已确认"的通知 ✅
5. 发布者取消订单 → 帮手收到"订单已取消"的通知 ✅
6. Helper 在 accepted 状态时 → 同时看到"申请完成"和"联系发布者"两个按钮 ✅
7. 所有订单操作（取消、申请完成、确认完成）都经过 Store 权限校验 ✅

### 失败场景
1. 通知发送失败 → 本地记录并提示用户
2. 聊天跳转时无 helper 信息 → 提示用户"暂无可沟通的对方"
3. 权限校验失败 → 显示 Store 返回的错误消息

---

## 修复内容汇总

### 第三轮修复 - Store 调用绕过问题

#### 1. order-detail.vue completeOrder
- **文件**: pages/order-detail/order-detail.vue
- **修改**: 调用 `orderStore.completeOrder()` 并正确处理返回值，添加失败提示

#### 2. order-detail.vue applyComplete
- **文件**: pages/order-detail/order-detail.vue
- **修改**: 调用 `orderStore.applyComplete()` 代替直接修改数据
- **权限校验**: 只能 helper 调用

#### 3. order-detail.vue confirmComplete
- **文件**: pages/order-detail/order-detail.vue
- **修改**: 调用 `needStore.confirmComplete()` 代替直接修改数据
- **功能**: 自动判断订单是否真正完成（双方都确认）

#### 4. order-detail.vue cancelOrder
- **文件**: pages/order-detail/order-detail.vue
- **修改**: 调用 `orderStore.cancelOrder()` 代替直接修改数据
- **新增**: sendCancelNotification() 方法，用于发送取消通知并更新 Badge

#### 5. orders.vue cancelOrder
- **文件**: pages/orders/orders.vue
- **修改**: 调用 `needStore.cancelNeed()` 或 `orderStore.cancelOrder()` 代替直接修改数据

#### 6. orders.vue sendCancelNotification
- **文件**: pages/orders/orders.vue
- **修改**: 添加 TabBar Badge 更新逻辑

---

## 累计修复汇总

| 轮次 | 修复数量 | 主要问题 |
|------|----------|----------|
| 第一轮 | 7项 | 标签显示、按钮缺失、权限校验 |
| 第二轮 | 3项 | 按钮显示逻辑、错误提示 |
| 第三轮 | 6项 | Store 调用绕过、Badge 更新 |

**总计修复**: 16 项问题

---

## 执行记录

| 日期 | 完成项 | 状态 |
|------|--------|------|
| 2026-05-04 | P0 第一轮修复 (7项) | ✅ 已完成 |
| 2026-05-04 | P1 通知逻辑 (6项) | ✅ 已完成 |
| 2026-05-04 | P2 数据一致性 (2项) | ✅ 已完成 |
| 2026-05-04 | P0 第二轮修复 (3项) | ✅ 已完成 |
| 2026-05-04 | P0 第三轮修复 (6项) | ✅ 已完成 |
