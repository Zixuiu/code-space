# 🚀 Code Space 工作区

> **最后更新**: 2026-06-28
>
> **状态**: 🔄 正在整理中...

## 📂 目录结构

```
code-space/
├── 01-开发项目/          # 主要开发项目
│   ├── PC-action/       # ⭐ macOS风格桌面应用 (WiFi手机控制器)
│   ├── ai-news-daily/   # AI新闻每日更新
│   └── map/             # 地图应用
│
├── 02-Web应用/           # Web应用和网页
│   ├── 销售系统/         # 销售管理系统
│   └── 清单/             # 清单管理
│
├── 03-移动应用/          # 移动端应用
│   └── wo-laibang-app/  # UniApp应用
│
├── 04-工具脚本/          # 常用工具
├── 05-文档资源/          # 文档和资源
├── 06-临时文件/          # 待整理文件
│
├── .gitignore            # Git忽略规则
├── README.md             # 本文件
└── 整理方案.md            # 详细整理指南
```

## 🎯 核心项目

### 1. PC-action (主项目) ⭐
**位置**: `01-开发项目/PC-action/PC-action-macOS/`

**功能**:
- ✅ macOS风格桌面应用程序
- ✅ WiFi手机远程控制器
- ✅ 屏幕镜像、触摸操作、文件传输
- ✅ 快捷操作、自定义命令

**主要文件**:
- [wifi_phone_controller.py](01-开发项目/PC-action/PC-action-macOS/wifi_phone_controller.py) - WiFi手机控制器
- [app_macos.py](01-开发项目/PC-action/PC-action-macOS/app_macos.py) - 主应用程序
- [main.py](01-开发项目/PC-action/PC-action-macOS/main.py) - 入口文件

**运行方法**:
```bash
cd 01-开发项目/PC-action/PC-action-macOS/
python main.py
```

### 2. 其他项目

| 项目 | 类型 | 说明 |
|------|------|------|
| ai-news-daily | Python | AI新闻自动更新 |
| map | Python | 地图应用 |
| wo-laibang-app | UniApp | 移动端应用 |
| 销售系统 | HTML | 销售管理系统 |
| 清单 | HTML+JS | 清单管理工具 |

## 🛠️ 开发环境

### 必需
- Python 3.8+
- PyQt5
- Android SDK Platform Tools (ADB)

### 可选
- Node.js (用于wo-laibang-app)
- HBuilderX (用于UniApp开发)

## 📦 安装依赖

```bash
# Python依赖
pip install PyQt5

# ADB (Android Debug Bridge)
# 下载: https://developer.android.com/studio/releases/platform-tools
```

## 🔧 常用命令

### Git操作
```bash
# 查看状态
git status

# 提交更改
git add -A
git commit -m "update: 描述更改内容"

# 推送到远程
python 推送git.py  # 或使用脚本
```

### 项目操作
```bash
# 运行主程序
cd 01-开发项目/PC-action/PC-action-macOS/
python main.py

# 运行WiFi控制器
python wifi_phone_controller.py

# 运行AI新闻
cd 01-开发项目/ai-news-daily/
python main.py
```

## 📋 项目规范

### 目录命名规范
- **编号前缀**: `01-`, `02-` 等，便于排序
- **中文描述**: 使用清晰的中文
- **kebab-case**: 多个单词用连字符连接

### 新增项目流程
1. 确定项目类型（开发/Web/移动）
2. 放入对应目录
3. 更新本README
4. 添加.gitignore规则（如需要）

### Git提交规范
```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 格式调整
refactor: 重构代码
test: 测试相关
chore: 构建/工具
```

## 🗂️ 文件清理建议

### 可以删除的文件
- ❌ `recordings/` 中不常用的录制文件
- ❌ `*.pyc`, `__pycache__/` 缓存文件
- ❌ `*.log` 日志文件
- ❌ 临时测试文件

### 必须保留的文件
- ✅ `.gitignore`
- ✅ `README.md`
- ✅ 核心源代码
- ✅ 配置文件

## 📊 项目统计

- **总项目数**: 6个
- **主要语言**: Python, JavaScript/Vue, HTML/CSS
- **代码行数**: ~15,000+
- **最后整理**: 2026-06-28

## 🎓 学习资源

### WiFi手机控制
- [ADB官方文档](https://developer.android.com/tools/adb)
- [PyQt5教程](https://www.pyqt5.com/)
- [无线调试设置](https://developer.android.com/studio/command-line/adb#Wireless)

### UniApp开发
- [UniApp官网](https://uniapp.dcloud.net.cn/)
- [Vue.js文档](https://vuejs.org/)

## 🤝 贡献指南

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📝 更新日志

### 2026-06-28
- ✨ 添加WiFi手机控制器功能
- 🔧 开始目录结构整理
- 📝 创建完整的README文档
- 🗂️ 制定整理方案

## ⚠️ 注意事项

1. **node_modules已忽略** - wo-laibang-app需要单独执行 `npm install`
2. **录制文件较大** - 定期清理recordings目录
3. **路径引用** - 移动项目后检查配置文件中的路径
4. **备份重要数据** - 整理前务必备份

## 📞 支持

遇到问题？
- 查看[整理方案.md](整理方案.md)获取详细指南
- 检查各项目的README
- 查看代码注释

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

<div align="center">

**⭐ 如果这个工作区对你有帮助，请给一个Star！⭐**

Made with ❤️ by Code Space Team

</div>