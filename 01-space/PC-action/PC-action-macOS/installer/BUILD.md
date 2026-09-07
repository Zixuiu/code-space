# PC-Action 安装包构建说明（NSIS 版）

目标：把项目打成一个**标准 Windows 安装包**，安装时用户自己选择装到 C 盘、D 盘或任意位置。

相比之前的 Inno Setup 方案，本方案**不需要在本机安装任何打包工具**：
NSIS 便携版已随项目放在 `installer\tools\nsis\`（缺失时构建脚本会自动下载）。

## 目录内容

| 文件 | 作用 |
|---|---|
| `setup.nsi` | NSIS 安装脚本（中文向导、选择安装位置、快捷方式、卸载） |
| `build_installer.cmd` | 一键构建：图标 → PyInstaller → NSIS 安装包 |
| `make_icon.py` | 用 `icons/play.svg` 生成 `app.ico`（安装包/快捷方式图标） |
| `license.txt` | 由 `docs/EULA与隐私政策.md` 生成的许可协议（安装向导第 2 页显示） |
| `app.ico` | 安装包图标（首次构建时自动生成） |
| `tools/nsis/` | NSIS 3.10 便携版编译器（约 20MB，勿删） |
| `output/` | 最终产物：`PC-Action-<版本>-Setup.exe` |
| `../PC-Action-install.spec` | PyInstaller 打包配置（onedir 模式，供安装包使用） |

## 一键构建

在 `installer` 目录双击 `build_installer.cmd`（或命令行执行）：

```cmd
build_installer.cmd          :: 版本默认 1.0.0
build_installer.cmd 1.0.1    :: 指定版本号
```

前置条件（只需一次）：

```cmd
.venv\Scripts\python.exe -m pip install pyinstaller
```

构建分三步：
1. 生成 `app.ico`（已存在则跳过）
2. PyInstaller → `dist\PC-Action\PC-Action.exe`（onedir，约 2-5 分钟）
3. NSIS → `installer\output\PC-Action-1.0.0-Setup.exe`（LZMA 固实压缩）

## 安装向导做什么

1. **欢迎页** —— 自动结束正在运行的 PC-Action（避免文件占用）
2. **许可协议** —— 内容来自 `license.txt`
3. **选择安装位置** —— 默认 `D:\PC-Action`（无 D 盘时为 `C:\Program Files\PC-Action`），
   有“浏览”按钮可改到任意盘任意目录；离开本页会校验目标磁盘剩余空间；
   已安装过则自动沿用上次的目录（覆盖升级）
4. **附加选项** —— 桌面快捷方式、开机自启（均可不勾）
5. **安装** —— 释放文件、写“添加/删除程序”信息、创建开始菜单快捷方式
6. **完成** —— 可勾选“立即运行 PC-Action”

卸载：开始菜单 → `卸载 PC-Action`，或控制面板卸载。卸载时会先结束进程，
并询问**是否保留用户数据**（`user_data` / `recordings`，即录制的流程与登录信息）。

## 常见调整

- **改默认安装盘**：编辑 `setup.nsi` 的 `.onInit`，把
  `IfFileExists "D:\" 0 +2` / `StrCpy $INSTDIR "D:\${APP_NAME}"` 改成你想要的默认路径。
- **改所需空间提示**：构建脚本会自动按打包体积计算；手动编译用
  `makensis /DREQUIRED_MB=400 setup.nsi`。
- **改版本号**：`build_installer.cmd 1.0.1`，或 `makensis /DAPP_VERSION=1.0.1 setup.nsi`。
- **版本号同时影响**安装目录名、卸载项显示、exe 属性里的产品版本。

## 体积说明

当前打包约 278MB（opencv + PyQt5 + numpy），安装包压缩后约 90-120MB。
如需瘦身，可在 `PC-Action-install.spec` 的 `excludes` 里加不需要的模块，
或删除 `dist\PC-Action\_internal` 中确认用不到的组件（如
`PyQt5/Qt5/bin/opengl32sw.dll` 20MB、`cv2/opencv_videoio_ffmpeg500_64.dll` 29MB）。

## 关于源码保护

安装包只解决“安装”问题。如果需要防止源码被反编译/破解，参见本文档旧版的
“方案 1（服务端授权 + 代码签名）→ 方案 2（Cython 编核心模块）→ 方案 3（PyArmor）”，
核心原则是：**授权判断放服务端**，本地只做执行。
