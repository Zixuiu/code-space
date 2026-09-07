# PC-Action 打包与源码保护指南

目标有两件事：
1. **做成安装包**，安装时让用户选择装到 C 盘或 D 盘。
2. **隐藏源码**，防止源代码被反编译取出、防止被破解/作弊。

本目录已提供可直接使用的产物：

| 文件 | 作用 |
|---|---|
| `setup.iss` | Inno Setup 安装包脚本（含“选择安装到 C/D 盘”向导、快捷方式、卸载） |
| `build_installer.cmd` | 一键脚本：先 PyInstaller 打包 exe，再用 Inno Setup 打成安装包 |
| 本文档 | 操作步骤 + 源码保护方案 |

---

## 第一部分：做成安装包（选 C 盘或 D 盘）

### 需要先安装的工具
1. **Inno Setup 6**（免费）：https://jrsoftware.org/isinfo.php
   - 安装时把 “Create a desktop icon” 勾上即可，会用到一个 `ISCC.exe` 编译器。
2. Python 侧用你现有的 `.venv`（已确认 Python 3.13 可用），里面装好 `pyinstaller`：
   ```cmd
   .venv\Scripts\pip.exe install pyinstaller
   ```

### 构建
- 方式 A（推荐）：在 `installer` 目录双击 `build_installer.cmd`。
- 方式 B：手动两步
  1. `python -m PyInstaller --clean -y ..\PC-Action.spec`（在项目根目录）
  2. `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss`（在 installer 目录）

产物：`installer\output\PC-Action-Setup.exe`

### 安装向导会做到
- 第一步即“选择安装位置”，默认 `D:\PC-Action`（脚本里留的默认是系统盘，你可把 `DefaultDirName` 改成 `D:\PC-Action` 或保持 C 盘）。
- 自定义安装目录：默认即可选任意盘/任意路径（`DisableDirPage=no`）。
- 开始菜单快捷方式 + 桌面快捷方式 + 卸载入口。
- 可勾选“开机自启”（会写注册表 `Run`）。

> 小提示：你现在是**单文件版**（整个 exe 自带图标/定价配置）。安装器只需把这一个 exe 装进选定目录，非常轻。想进一步压缩体积可以用 UPX，但会降低一点兼容性，一般不建议。

---

## 第二部分：隐藏源码 / 防破解防作弊

先说清一个事实原则：**本地代码只能“加大反向难度”，无法绝对防住**。真正能防破解/防作弊的根基是**把授权判断放服务端**。按性价比给你三级方案，建议从下往上做。

### 方案 1（基础，必须做）：关键逻辑放服务端 + 代码签名
- **服务端授权**是防作弊核心：VIP 是否有效、是否允许加载等，都由 Supabase/后端判定，本地只做“拿到结果才允许”的动作（你现在 VIP 已走 Supabase，继续保持并把“功能开关、版本强校验”也挪上去）。这样即使 exe 被改，没有服务端授权也白搭。
- **代码签名**：给 exe 买一个代码签名证书并签名。好处：
  - 防被杀毒误报；
  - 任何人对 exe 动手脚后签名失效，别人想“代打包传播”会被 SmartScreen 警告。
- PyInstaller 本身已把源码编成字节码（非明文），属于这档的默认行为。

### 方案 2（进阶，推荐，免费）：用 Cython 把核心模块编译成机器码
把 `entitlement.py`、`supabase_db.py`、`login_manager.py` 等**核心业务模块**用 Cython 编译成 `.pyd`（原生机器码），再打进包。编译后**无法还原成 Python 源码**，只能逆向机器码，难度提升一个数量级。

步骤（需要 **Visual Studio Build Tools（MSVC，免费）** + `Cython`）：
1. 安装 Visual Studio 2022 Build Tools（勾选 “使用 C++ 的桌面开发”）。
2. `pip install cython`。
3. 写一个 `build_cython.py`，对你选定的核心模块调用
   ```python
   from Cython.Build import cythonize
   # cythonize(['entitlement.py', 'supabase_db.py', ...], output_dir='cython_build')
   ```
4. 把生成的 `.pyd` 放进项目，再跑 `build_installer.cmd`。

⚠ 注意 / 坑：
- **不要**全部无脑编译：PyQt5 界面文件（含 `@pyqtSlot`、lambda、动态 `__import__`）编译后容易在运行时报“找不到符号/导入失败”。建议**只编译纯逻辑模块，界面层保留 .py**。
- 编译越多的模块，出现“这只是把源码藏起来但工程麻烦增大”的可维护性成本越高。如果目的主要是防“普通用户看源码/抄作业”，**方案 1 + 只编译 2~3 个最关键模块**是最划算的。

### 方案 3（商业，最强）：PyArmor
- 付费（约几百元/年起），提供**运行时混淆 + 反调试 + 反虚拟机 + 绑定机器码**，专治逆向/破解/作弊。
- 适合你要做商业化收费且对盗版零容忍时再上。
- 可以只对核心模块执行 `pyarmor gen`，再把加密产物打进 PyInstaller。

---

## 推荐执行顺序
1. **本目录的安装包脚本**现在就能用（装好 Inno Setup → 跑 `build_installer.cmd`）。
2. 先做 **方案 1**：把越权/功能校验尽量挪到 Supabase 服务端，并给 exe 签名。
3. 若担心源码泄露，再加 **方案 2**，先只编译 `entitlement` + `supabase_db` 两个模块看效果。
4. 商业化跑量后再评估是否上 **方案 3（PyArmor）**。