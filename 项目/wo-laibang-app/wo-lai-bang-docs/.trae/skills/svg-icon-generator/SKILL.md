---
name: "svg-icon-generator"
description: "Generates modern, beautiful SVG icons with strong semantic meaning. MANDATORY: Invoke IMMEDIATELY as FIRST action for ANY icon-related request including create, generate, make, draw, design, replace, modify, change, update, fix, or improve any icon, logo, graphic, symbol, image for the app. NEVER manually create or edit SVG files without calling this skill first."
---

# SVG Icon Generator

## Overview
Generates high-quality, modern, and beautiful SVG icons for the wo-laibang-app project. Icons must clearly convey their functional meaning through intuitive visual design.

## When to Invoke (触发范围)
**⚠️ MANDATORY: 任何与图标生成、创建、设计、修改相关的请求，都必须在 FIRST ACTION 调用此技能！**

**🚫 NEVER: 不要在没有调用此技能的情况下手动创建或编辑 SVG 文件！**

包括但不限于以下场景：
- 用户说"生成一个图标"、"创建图标"、"画一个图标"
- 用户说"生成SVG"、"创建SVG"、"做SVG"
- 用户说"设计一个图标"、"做个logo"、"设计符号"
- 用户说"换一个图标"、"替换图标"、"改图标"、"修改图标"、"更换图标"
- 用户说"图标不对"、"显示不出来"、"重新生成图标"、"图标报错"
- 用户提到任何图标名称并要求创建（如"生成提现图标"、"做个转账图标"）
- 用户说"美化图标"、"优化图标"、"改进图标"
- 用户描述了一个功能并要求生成对应的视觉元素
- 用户说"做个xxx的图片"、"生成xxx的图形"
- 用户提到"icon"、"图标"、"logo"、"符号"、"图片"、"图形"并要求创建或修改
- 用户要求"把某个图标换成另一个"或"更新某个图标"
- 用户说"增加一个图标"、"添加图标"、"补充图标"
- 用户提到任何视觉元素并要求生成、修改、调整

## Critical Rules (关键规则)
1. **FIRST ACTION**: 当检测到任何图标相关关键词时，必须 FIRST 调用此 skill
2. **NO MANUAL SVG**: 绝对不要手动编写或修改 SVG 文件
3. **NO DIRECT EDIT**: 绝对不要直接编辑 `static/icons/` 目录下的文件
4. **ALWAYS INVOKE**: 即使是简单的图标更换或修复，也必须调用此 skill
5. **CHECK FIRST**: 在开始任何图标相关工作前，先检查是否应该调用此 skill
6. **TRANSPARENT BACKGROUND**: ⚠️ 所有图标必须采用透明背景设计，禁止添加圆形或矩形背景填充！图标应该是独立的图形元素，能够适配任何背景色。

## Core Design Principles

### 1. Semantic Clarity (功能含义明确)
- **图标必须一眼就能看出其功能含义**
- 避免抽象或歧义的图形
- 使用用户熟悉的视觉隐喻：
  - 钱包/金钱 → 钱包形状、硬币、钞票
  - 上传/下载 → 箭头方向明确
  - 转账/交换 → 双向箭头
  - 通知 → 铃铛
  - 设置 → 齿轮
  - 搜索 → 放大镜

### 2. Modern Aesthetic (现代化美感)
- **圆润的几何形状**：使用 rx/ry 圆角
- **层次分明**：使用多层元素叠加（主色+白色半透明点缀）
- **动态感**：通过渐变、弧线、旋转等增加活力
- **简洁但不单调**：2-3个层次元素，避免过于扁平

### 3. Visual Quality (视觉精美度)
- 使用多层渐变或叠加效果
- 添加白色半透明高光（opacity: 0.2-0.5）
- 元素比例协调，视觉重心稳定
- 避免生硬的直角，多用圆角和弧线

### 4. Transparent Background (透明背景) ⚠️重要
- **禁止添加任何背景填充**：不要使用 `<circle>` 或 `<rect>` 作为背景容器
- 图标应该是独立的图形元素，视觉上自包含
- 可以通过组合多个图形元素来创建丰富的视觉效果
- 透明背景让图标能更好地融入各种卡片背景中

## Technical Standards

### Template (透明背景版本)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <defs>
    <linearGradient id="grad{ID}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{COLOR1};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{COLOR2};stop-opacity:1" />
    </linearGradient>
  </defs>
  <!-- 主体图形元素（无背景填充）-->
  {CONTENT}
</svg>
```

### Rules
1. **Dimensions**: Always 48x48, viewBox="0 0 48 48"
2. **Gradient ID**: Use unique grad{ID} (check existing to avoid conflicts, start from grad60 for new icons)
3. **Color Palette**:
   - 💰 金钱/钱包: `#10B981` → `#34D399` 或 `#059669` → `#10B981`
   - 💸 提现/消费: `#F59E0B` → `#FBBF24` 或 `#D97706` → `#F59E0B`
   - 💳 转账/支付: `#3B82F6` → `#60A5FA` 或 `#2563EB` → `#3B82F6`
   - 🔔 通知/消息: `#8B5CF6` → `#A78BFA`
   - ✅ 成功/完成: `#10B981` → `#34D399`
   - 🎨 其他: 根据功能选择合适色调
4. **NO BACKGROUND**: 禁止添加背景圆形或背景矩形！

### Design Patterns (透明背景图标模式)

#### Pattern 1: 主体 + 点缀
```
[主体: 大图形填充渐变色]
  + [点缀: 小图形白色或透明色增加细节]
```

#### Pattern 2: 线条 + 形状混合
```
[形状: 主要视觉元素]
  + [线条: 弧线或路径增加动态感]
  + [圆点: 点缀增加精致感]
```

#### Pattern 3: 组合图形
```
[多个图形元素组合]
  + [各元素使用不同透明度增加层次感]
  + [整体形成完整的视觉含义]
```

## Registration
After creating the SVG file in `static/icons/{name}.svg`, also register it in `components/icon-font/icon-font.vue`:
```javascript
'{name}': '{name}',
```

## Workflow
1. Understand the icon's purpose and functional meaning
2. Choose appropriate colors based on the feature type
3. Design a clear, modern, beautiful icon using the patterns above
4. **IMPORTANT**: Ensure NO background fill (no circle, no rect background)
5. Create SVG file in `static/icons/`
6. Register in icon-font.vue
7. Confirm creation with user

## Examples (全部采用透明背景设计)

### Premium Wallet Icon (透明背景版本)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <defs>
    <linearGradient id="grad17" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#10B981;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#34D399;stop-opacity:1" />
    </linearGradient>
  </defs>
  <!-- 钱包主体 -->
  <rect x="4" y="10" width="40" height="28" rx="4" fill="url(#grad17)"/>
  <!-- 钱包卡槽高光 -->
  <rect x="8" y="14" width="32" height="8" rx="2" fill="white" opacity="0.3"/>
  <!-- 钱包按钮 -->
  <circle cx="34" cy="30" r="4" fill="white"/>
</svg>
```

### Modern Transfer Icon (透明背景版本)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <defs>
    <linearGradient id="grad60" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#3B82F6;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#60A5FA;stop-opacity:1" />
    </linearGradient>
  </defs>
  <!-- 上方右箭头 -->
  <path d="M16 18H32" stroke="url(#grad60)" stroke-width="4" stroke-linecap="round"/>
  <path d="M26 12L32 18L26 24" stroke="url(#grad60)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <!-- 下方左箭头 -->
  <path d="M32 30H16" stroke="url(#grad60)" stroke-width="4" stroke-linecap="round"/>
  <path d="M22 24L16 30L22 36" stroke="url(#grad60)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>
```

### Elegant Withdraw Icon (透明背景版本)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <defs>
    <linearGradient id="grad61" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#F59E0B;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#FBBF24;stop-opacity:1" />
    </linearGradient>
  </defs>
  <!-- 向上箭头主体 -->
  <rect x="21" y="14" width="6" height="22" rx="3" fill="url(#grad61)"/>
  <path d="M14 20L24 10L34 20" stroke="url(#grad61)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <!-- 底部托盘 -->
  <rect x="10" y="34" width="28" height="4" rx="2" fill="url(#grad61)" opacity="0.8"/>
</svg>
```

### Three Dots Icon (透明背景版本)
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48">
  <defs>
    <linearGradient id="grad62" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#8B5CF6;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#A78BFA;stop-opacity:1" />
    </linearGradient>
  </defs>
  <!-- 三个圆点 -->
  <circle cx="14" cy="24" r="6" fill="url(#grad62)"/>
  <circle cx="24" cy="24" r="6" fill="url(#grad62)"/>
  <circle cx="34" cy="24" r="6" fill="url(#grad62)"/>
  <!-- 高光点缀 -->
  <circle cx="12" cy="22" r="2" fill="white" opacity="0.4"/>
  <circle cx="22" cy="22" r="2" fill="white" opacity="0.4"/>
  <circle cx="32" cy="22" r="2" fill="white" opacity="0.4"/>
</svg>
```
