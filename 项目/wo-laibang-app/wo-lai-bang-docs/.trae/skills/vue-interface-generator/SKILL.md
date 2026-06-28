---
name: "vue-interface-generator"
description: "Generates Vue.js UniApp interfaces following wo-laibang-app conventions. MANDATORY: Invoke IMMEDIATELY as FIRST action when user asks to create, generate, build, design, or implement any Vue page, component, UI, screen, or interface. NEVER manually write Vue code without calling this skill first."
---

# Vue Interface Generator

This skill generates Vue.js UniApp interfaces following the established patterns and conventions of the **wo-laibang-app** project.

## Project Context

**Tech Stack:**
- UniApp + Vue.js
- Pinia for state management
- Custom CSS (no Tailwind)
- Custom IconFont component (not emoji icons)

**Theme Colors (必须保持一致，禁止随意更改):**
- Primary: `#10B981` (green)
- Primary Dark: `#059669`
- Background: `#F8FAFC` / `#F9FAFB`
- Text: `#1E293B` / `#111827`
- Text Secondary: `#64748B` / `#6B7280`
- Border: `rgba(16, 185, 129, 0.05)`
- Success: `#10B981`
- Warning: `#F59E0B`
- Error: `#EF4444`
- Info: `#3B82F6`

## When to Use (触发范围)

**⚠️ MANDATORY: 当用户要求创建、生成、设计、构建任何 Vue 页面、组件或 UI 时，必须在 FIRST ACTION 调用此技能！**

**🚫 NEVER: 不要在没有调用此 skill 的情况下手动编写 Vue 代码！**

包括但不限于以下场景：
- "Create a new page" (创建新页面)
- "Generate a Vue interface" (生成 Vue 界面)
- "Add a new screen" (添加新屏幕)
- "Build a form page" (构建表单页面)
- "Design a list page" (设计列表页面)
- "Create a component" (创建组件)
- Any request involving creating Vue UI (任何创建 Vue UI 的请求)
- 用户说"做个页面"、"生成界面"、"写个组件"
- 用户说"新增xxx页面"、"添加xxx组件"
- 用户说"帮我写一个Vue页面"
- 用户描述了一个页面需求并要求实现

## Critical Rules (关键规则)

1. **FIRST ACTION**: 当检测到任何 Vue/页面/组件创建请求时，必须 FIRST 调用此 skill
2. **NO MANUAL VUE**: 绝对不要在没有调用此 skill 的情况下手动编写 Vue 代码
3. **COLOR CONSISTENCY**: 必须严格使用项目原有颜色，禁止引入新的配色方案
4. **STYLE DIVERSITY**: 禁止所有页面使用相同的样式模板，每个页面必须有独特的布局和样式设计
5. **CHECK EXISTING**: 在生成新页面之前，先查看该页面的现有代码，了解当前样式

## Style Diversity Requirements (样式多样性要求)

**⚠️ 重要：每个页面必须有独特的样式设计，禁止千篇一律！**

### 禁止出现的模板化设计：
- 禁止所有页面都使用相同的头部样式
- 禁止所有卡片都使用相同的圆角（24px）、间距、内边距
- 禁止所有列表项使用相同的布局结构
- 禁止滥用相同的渐变背景

### 允许的样式变化：
- **圆角**: 16px / 20px / 24px / 32px / 40px 可以混合使用
- **间距**: 根据内容密度调整padding和margin
- **卡片**: 可以有不同大小、不同背景色、不同边框样式
- **布局**: 可以用flex、grid、瀑布流等不同布局方式
- **头部**: 可以有不同高度、不同背景色、不同元素排列

### 颜色使用场景：
| 场景 | 颜色 |
|------|------|
| 主要按钮、强调 | `#10B981` |
| 成功状态 | `#10B981` |
| 警告状态 | `#F59E0B` |
| 错误状态 | `#EF4444` |
| 信息提示 | `#3B82F6` |
| 主要背景 | `#F8FAFC` |
| 卡片背景 | `#FFFFFF` |
| 主要文字 | `#1E293B` |
| 次要文字 | `#64748B` |

## Generated Code Structure

### 1. Page Template Structure

根据页面内容和功能选择合适的布局结构：

```vue
<template>
	<view class="container">
		<!-- Header (for non-tab pages) -->
		<view class="header">
			<view class="back-btn" @click="goBack">
				<IconFont name="chevron-left" :size="24" />
			</view>
			<text class="header-title">Page Title</text>
		</view>

		<!-- Content Area -->
		<scroll-view class="content-scroll" scroll-y>
			<!-- Page Content Here -->

			<!-- Empty State (when needed) -->
			<view v-if="list.length === 0" class="empty-state">
				<view class="empty-icon-wrapper">
					<IconFont name="bell" :size="40" color="#10B981" />
				</view>
				<text class="empty-title">暂无数据</text>
				<text class="empty-subtitle">快去做一些事情吧~</text>
			</view>

			<!-- Bottom Safe Area -->
			<view class="bottom-space"></view>
		</scroll-view>
	</view>
</template>
```

### 2. Script Structure

```vue
<script>
import { useUserStore } from '@/stores/user'
import { useNeedStore } from '@/stores/need'
import { useOrderStore } from '@/stores/order'
import IconFont from '@/components/icon-font/icon-font.vue'

export default {
	components: {
		IconFont
	},
	setup() {
		const userStore = useUserStore()
		const needStore = useNeedStore()
		const orderStore = useOrderStore()
		return { userStore, needStore, orderStore }
	},
	data() {
		return {
			// Local reactive state
		}
	},
	computed: {
		// Derived state from stores
	},
	onShow() {
		uni.hideTabBar() // For non-tab pages
		// Load data
	},
	onLoad(options) {
		// Receive navigation params
	},
	methods: {
		// Event handlers and actions

		// Navigation helpers
		goBack() {
			uni.navigateBack()
		},
		navigateTo(url) {
			uni.navigateTo({ url })
		},
		switchTab(url) {
			uni.switchTab({ url })
		},

		// Toast notifications
		showToast(title, icon = 'none') {
			uni.showToast({ title, icon })
		},

		// Modal confirmations
		showConfirm(title, content, confirmColor = '#10B981') {
			return new Promise((resolve) => {
				uni.showModal({
					title,
					content,
					confirmColor,
					success: (res) => resolve(res.confirm)
				})
			})
		}
	}
}
</script>
```

### 3. Style Conventions (样式规范)

```vue
<style scoped>
.container {
	min-height: 100vh;
	background: #F8FAFC;
}

/* Header Styles - 可以根据页面功能调整高度和背景 */
.header {
	padding: 64rpx 24rpx 16rpx;
	background: #FFFFFF;
	display: flex;
	align-items: center;
	gap: 16rpx;
	border-bottom: 1rpx solid #F1F5F9;
}

.back-btn {
	width: 40px;
	height: 40px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.header-title {
	flex: 1;
	font-size: 18px;
	font-weight: 700;
	color: #1E293B;
	text-align: center;
}

/* Content Scroll */
.content-scroll {
	height: calc(100vh - 89px);
}

/* Card Styles - 圆角和间距可以根据内容调整 */
.card {
	background: #FFFFFF;
	border-radius: 24rpx;
	padding: 20rpx;
	margin: 16rpx 20rpx;
	box-shadow: 0 4rpx 12rpx rgba(16, 185, 129, 0.05);
}

/* Input Styles */
.input-group {
	margin-bottom: 16rpx;
}

.input-label {
	font-size: 12px;
	color: #64748B;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	margin-bottom: 8rpx;
	display: block;
}

.input-wrapper {
	background: #F8FAFC;
	border-radius: 14rpx;
	padding: 14rpx 16rpx;
	display: flex;
	align-items: center;
	gap: 12rpx;
}

.input-wrapper:focus-within {
	background: #FFFFFF;
	border-color: #10B981;
	box-shadow: 0 6rpx 16rpx rgba(16, 185, 129, 0.08);
}

.input-field {
	flex: 1;
	font-size: 15px;
	font-weight: 600;
	color: #1E293B;
	border: none;
	outline: none;
	background: transparent;
}

/* Button Styles */
.btn-primary {
	width: 100%;
	height: 52px;
	background: linear-gradient(135deg, #10B981, #059669);
	color: #FFFFFF;
	border-radius: 26px;
	font-weight: 800;
	font-size: 16px;
	border: none;
	box-shadow: 0 8rpx 24rpx rgba(16, 185, 129, 0.35);
	display: flex;
	align-items: center;
	justify-content: center;
}

.btn-primary:active:not(:disabled) {
	transform: translateY(-2px);
}

.btn-primary:disabled {
	opacity: 0.6;
}

/* Empty State */
.empty-state {
	padding-top: 100px;
	display: flex;
	flex-direction: column;
	align-items: center;
}

.empty-icon-wrapper {
	width: 80px;
	height: 80px;
	background: #ECFDF5;
	border-radius: 30px;
	display: flex;
	align-items: center;
	justify-content: center;
	margin-bottom: 20px;
}

.empty-title {
	font-size: 16px;
	font-weight: 700;
	color: #374151;
	margin-bottom: 8px;
}

.empty-subtitle {
	font-size: 14px;
	color: #9CA3AF;
}

/* List Item Styles */
.list-item {
	background: #FFFFFF;
	border-radius: 24rpx;
	padding: 20rpx;
	margin-bottom: 15rpx;
	display: flex;
	gap: 15rpx;
}

.item-icon {
	width: 52px;
	height: 52px;
	background: #ECFDF5;
	border-radius: 18px;
	display: flex;
	align-items: center;
	justify-content: center;
}

.item-content {
	flex: 1;
}

.item-title {
	font-size: 16px;
	font-weight: 700;
	color: #111827;
	margin-bottom: 4px;
}

.item-desc {
	font-size: 13px;
	color: #6B7280;
}

/* Bottom Space */
.bottom-space {
	height: 100px;
}

/* Status Badge */
.status-badge {
	background: #ECFDF5;
	color: #10B981;
	font-size: 12px;
	font-weight: 700;
	padding: 4px 12px;
	border-radius: 100px;
}

/* Tab Styles */
.tabs {
	display: flex;
	justify-content: space-around;
	padding: 20rpx 40rpx 32rpx;
	background: #FFFFFF;
}

.tab {
	position: relative;
	padding: 16rpx 20rpx 12rpx;
}

.tab-text {
	font-size: 30rpx;
	font-weight: 600;
	color: #6B7280;
}

.tab.active .tab-text {
	color: #10B981;
}

.tab.active::after {
	content: '';
	position: absolute;
	bottom: 0;
	left: 50%;
	transform: translateX(-50%);
	width: 40rpx;
	height: 6rpx;
	background: #10B981;
	border-radius: 3rpx;
}
</style>
```

## Common Patterns

### 1. Form Page Pattern
```vue
<template>
	<view class="container">
		<view class="header">
			<view class="back-btn" @click="goBack">
				<IconFont name="chevron-left" :size="24" />
			</view>
			<text class="header-title">表单标题</text>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="form-card">
				<view class="input-group">
					<label class="input-label">字段标签</label>
					<view class="input-wrapper">
						<input
							class="input-field"
							v-model="form.field"
							placeholder="请输入..."
						/>
					</view>
				</view>

				<button class="btn-primary" @click="handleSubmit">
					提交
				</button>
			</view>
		</scroll-view>
	</view>
</template>
```

### 2. List Page Pattern
```vue
<template>
	<view class="container">
		<view class="header">
			<text class="header-title">列表标题</text>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view v-if="list.length === 0" class="empty-state">
				<!-- Empty state content -->
			</view>

			<view v-else class="list">
				<view
					v-for="item in list"
					:key="item.id"
					class="list-item"
					@click="onItemClick(item)"
				>
					<!-- Item content -->
				</view>
			</view>
		</scroll-view>

		<bottom-nav :current="tabIndex"></bottom-nav>
	</view>
</template>
```

### 3. Detail Page Pattern
```vue
<template>
	<view class="container">
		<view class="header">
			<view class="back-btn" @click="goBack">
				<IconFont name="chevron-left" :size="24" />
			</view>
			<text class="header-title">详情</text>
		</view>

		<scroll-view class="content-scroll" scroll-y>
			<view class="detail-content">
				<!-- Detail content -->
			</view>

			<view class="bottom-actions">
				<button class="btn-primary" @click="handleAction">
					主要操作
				</button>
			</view>
		</scroll-view>
	</view>
</template>
```

### 4. Modal/Action Sheet Pattern
```vue
// Show action sheet
uni.showActionSheet({
	itemList: ['选项1', '选项2', '选项3'],
	success: (res) => {
		switch (res.tapIndex) {
			case 0: this.handleOption1(); break;
			case 1: this.handleOption2(); break;
		}
	}
})

// Show modal
uni.showModal({
	title: '确认操作',
	content: '确定要执行此操作吗？',
	confirmColor: '#10B981',
	success: (res) => {
		if (res.confirm) {
			this.confirmAction()
		}
	}
})
```

### 5. Loading State Pattern
```vue
data() {
	return {
		isLoading: false
	}
}

methods: {
	async handleSubmit() {
		if (this.isLoading) return

		this.isLoading = true
		try {
			// Async operation
			await this.submitData()
			this.showToast('提交成功', 'success')
		} catch (error) {
			this.showToast('提交失败', 'none')
		} finally {
			this.isLoading = false
		}
	}
}
```

## Validation Patterns

```vue
methods: {
	validateForm() {
		if (!this.form.field1?.trim()) {
			this.showToast('请填写字段1', 'none')
			return false
		}
		if (!/^1[3-9]\d{9}$/.test(this.form.phone)) {
			this.showToast('请输入正确的手机号', 'none')
			return false
		}
		return true
	},

	handleSubmit() {
		if (!this.validateForm()) return
		// Submit logic
	}
}
```

## Navigation Patterns

| Navigation Type | Code |
|-----------------|------|
| Go to tab page | `uni.switchTab({ url: '/pages/xxx/xxx' })` |
| Go to sub page | `uni.navigateTo({ url: '/pages/xxx/xxx' })` |
| Go back | `uni.navigateBack()` |
| ReLaunch app | `uni.reLaunch({ url: '/pages/login/login' })` |
| With params | `uni.navigateTo({ url: `/pages/detail/detail?id=${id}` })` |

## File Naming Convention

- Pages: `pages/{page-name}/{page-name}.vue`
- Components: `components/{component-name}/{component-name}.vue`
- Stores: `stores/{store-name}.js`

## Icon Strategy

使用 IconFont 组件：
```vue
<IconFont name="icon-name" :size="40" />
```

常用图标名称：
- home: 首页
- user: 用户
- users: 多人
- search: 搜索
- bell: 通知
- settings: 设置
- check: 成功
- x: 关闭
- plus: 添加
- star: 收藏/评分
- heart: 喜欢
- lock: 锁
- wallet: 钱包
- coin: 金钱
- message: 消息
- tag: 标签
- shield: 安全
- help: 帮助
- user-x: 黑名单
- life-buoy: 救生圈/客服支持

## Responsive Units

- Use `rpx` for padding, margin, width, height (automatic scaling)
- Use `px` only for very small values (1-3px borders)
- Font sizes: 11-16px typically

## Important Notes

1. Always use `uni.` prefix for UniApp APIs (not `wx.`)
2. Use `scroll-view` with `scroll-y` for scrollable content
3. Add `bottom-space` of 100rpx at bottom for tab pages
4. Call `uni.hideTabBar()` in `onShow()` for non-tab pages
5. Use Chinese text for all UI labels and messages
6. Follow the exact class naming patterns shown above
7. Use Pinia stores for global state, local `data()` for page state
8. Always handle empty states with friendly messages
9. **禁止随意更改主题颜色**，所有颜色必须使用本文件规定的颜色值
10. **禁止使用模板化设计**，每个页面必须有独特的样式