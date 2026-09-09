# Action（原 PC-Action）安装包构建说明（NSIS 版）

目标：把项目打成一个**标准 Windows 安装包**，安装时用户自己选择装到 C 盘、D 盘或任意位置。

相比早期的 Inno Setup 方案（`../PC-Action.iss`），本方案**不需要在本机安装任何打包工具**：
NSIS 便携版已随项目放在 `installer\tools\nsis\`（缺失时构建脚本会自动下载）。

> 注意：应用已在一次提交中从 `PC-Action` 改名为 `Action`。
> 包名、`dist\Action\Action.exe`、卸载注册表项全部用 `Action`，请以此为准。

## 目录内容

| 文件 | 作用 |
|---|---|
| `setup.nsi` | NSIS 安装脚本（中文向导、选择安装位置、快捷方式、卸载） |
| `build_installer.cmd` | 一键构建：图标 → PyInstaller → NSIS 安装包 |
| `make_icon.py` | 生成 `app.ico`（安装包/快捷方式图标） |
| `make_license.py` | 由 `docs/EULA与隐私政策.md` 生成 `license.txt` |
| `license.txt` | 安装向导第 2 页显示的许可协议 |
| `app.ico` | 安装包图标（已存在时不重新生成） |
| `tools/nsis/nsis-3.10/` | NSIS 3.10 便携版编译器（勿删） |
| `output/` | 最终产物：`Action-<版本>-Setup.exe` |
| `../PC-Action-install.spec` | PyInstaller 打包配置（onedir 模式，专供安装包使用） |

## 首次在本机准备环境（换电脑 / 删过 .venv 必做）

`.venv` **不进 git**，clone 下来一定是空的；脚本第一步就会以此为错误退出。先建一次：

```cmd
cd 01-space\PC-action\PC-action-macOS
python -m venv .venv
.venv\Scripts\python.exe -m pip install -U pip wheel
```

> **别直接 `pip install -r requirements.txt`**。实测一次性全装会让 resolver 在
> `supabase` 的深层传递依赖上反复回溯，实测跑到 17 分钟仍一个包都没装上。
> 按下面的顺序分批装，总共约 7 分钟（ `-i` 是国内镜像源，可选但快很多）：

```cmd
set PIP=-i https://pypi.tuna.tsinghua.edu.cn/simple --prefer-binary

.venv\Scripts\python.exe -m pip install %PIP% "PyQt5>=5.15.11" "PyQt5-sip>=12.15" numpy
.venv\Scripts\python.exe -m pip install %PIP% opencv-python Pillow mss
.venv\Scripts\python.exe -m pip install %PIP% pyautogui keyboard pynput pygetwindow pyperclip requests python-dotenv
.venv\Scripts\python.exe -m pip install %PIP% supabase pyinstaller
```

> **Python 版本**：本机为 3.13，已验证可用（PyQt5 5.15.11 提供 cp313 wheel、
> PyQt5-sip 12.19、numpy 2.5.3、opencv-python 5.0.0）。
> 但注意 opencv 升到 5.x 后打包体积与旧文档记录的 278MB 略有出入，属正常。

确认依赖全部就位（应打印 `OK`）：

```cmd
.venv\Scripts\python.exe -c "import PyQt5, cv2, numpy, pyautogui, keyboard, pynput, mss, requests, supabase; print('OK')"
```

## 一键构建

在 `installer` 目录双击 `build_installer.cmd`，或命令行执行：

```cmd
build_installer.cmd          :: 版本默认 1.0.0
build_installer.cmd 1.0.1    :: 指定版本号
```

分三步，全程约 5–10 分钟：

1. 生成 `app.ico`（已存在则跳过）
2. PyInstaller → `dist\Action\Action.exe`（onedir，约 2–5 分钟）
3. NSIS → `installer\output\Action-1.0.0-Setup.exe`（LZMA 固实压缩）

## 手动分步执行（想看清每一步 / 脚本报错时用它定位）

在**项目根目录**（`PC-action-macOS`）执行：

```cmd
REM 1) 图标（通常已存在，可跳过）
.venv\Scripts\python.exe installer\make_icon.py

REM 2) PyInstaller 打包成 dist\Action\
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm PC-Action-install.spec

REM 3) NSIS 编译（注意：output 目录必须存在，makensis 不会自己建）
cd installer
if not exist output mkdir output
tools\nsis\nsis-3.10\makensis.exe /V2 /DAPP_VERSION=1.0.0 /DREQUIRED_MB=900 setup.nsi
```

只想重打第 3 步（比如只改了文案/注册表逻辑，不想重跑 PyInstaller）时，用上面第 3 步即可，
前提是 `dist\Action\Action.exe` 还在。

## 安装向导做什么

1. **欢迎页** —— 自动结束正在运行的 Action（避免文件占用）
2. **许可协议** —— 内容来自 `license.txt`
3. **选择安装位置** —— 默认 `D:\Action`（无 D 盘时为 `C:\Program Files\Action`），
   可“浏览”改到任意盘任意目录；离开本页会校验目标磁盘剩余空间；
   已安装过则自动沿用上次的目录（覆盖升级）
4. **附加选项** —— 桌面快捷方式、开机自启（均可不勾）
5. **安装** —— 释放文件、写“添加/删除程序”信息、创建开始菜单快捷方式
6. **完成** —— 可勾选“立即运行 Action”

卸载：开始菜单 → `卸载 Action`，或控制面板卸载。卸载时先结束进程，
并询问**是否保留用户数据**（`user_data` / `recordings`，即录制的流程与登录信息）。

## 排错

| 现象 | 原因与处理 |
|---|---|
| `[错误] 未找到虚拟环境` | `.venv` 不存在，按上文“首次准备环境”重建 |
| `Can't open output file`<br>（且退出码非 0，无产物） | NSIS **不会自动创建** `OutFile` 的目录。先 `mkdir output` 再编译 |
| NSIS 报 `!insertmacro: macro ... not found` | 便携版缺 `Include`，重新下载 nsis-3.10 完整解压 |
| 安装后启动缺图标/资源 | `PC-Action-install.spec` 的 `datas` 要带上 `icons`、`data`、`pricing.json` |
| 装完却在设置/64 位工具里找不到卸载项 | 注册表落到了 WOW6432Node，见“64 位注册表视图”一节 |
| `pip install -r requirements.txt` 十几分钟不动 | resolver 在 supabase 依赖链上回溯，改成分批安装（见上文） |
| 安装包体积异常小（几十 KB） | `dist\Action` 是空的或不存在，`File /r` 没抓到文件，重跑第 2 步 |
| 运行报缺 `cv2` / `pynput` 后端 | 补到 spec 的 `hiddenimports` 里再重打包 |

## 64 位注册表视图（重要，已修）

`makensis` 默认产出 **32 位**安装程序。不显式切换时，注册表会被系统重定向到
`HKLM\SOFTWARE\WOW6432Node\...`，卸载项因此**只在 32 位视图可见**，
控制面板虽然仍显示，但 64 位工具（PowerShell `Get-Package`、winget、批量卸载脚本）会读不到。

`setup.nsi` 已在 `.onInit` / `un.onInit` 加了 `SetRegView 64`，卸载段额外用
`SetRegView 32` 回扫一次，负责清掉历史上装在 WOW6432Node 的旧键；
`.onInit` 读取 `InstallLocation` 时也会回退读 32 位视图一次，保证覆盖升级仍装到原目录。

**改动这段时务必两个 Bit 都自测**：装完检查两处注册表键的位置。

## 常见调整

- **改默认安装盘**：编辑 `setup.nsi` 的 `.onInit`，改
  `System::Call 'kernel32::GetDriveType(t "D:\\") i .r2'` 那段即可
  （别用 `IfFileExists "D:\"`，它对驱动器根目录判定不可靠）。
- **改所需空间提示**：构建脚本按打包体积自动算；手动编译加 `/DREQUIRED_MB=400`。
- **改版本号**：`build_installer.cmd 1.0.1`，或 `makensis /DAPP_VERSION=1.0.1 setup.nsi`。
  版本号同时影响安装目录名、卸载项显示、exe 属性里的产品版本。
- **改包名/厂商/官网**：改 `setup.nsi` 顶部的 `APP_NAME`、`APP_PUBLISHER`、`APP_URL`，
  同时同步 spec 里 `EXE` 和 `COLLECT` 的 `name`。

## 体积说明

实测（2026-09-09，Python 3.13 + opencv 5.0）：`dist\Action` **274MB / 272 个文件**，
LZMA 固实压缩后安装包 **77MB**（比早期 90–120MB 更小，opencv 版本升级所致）；
NSIS 压缩这一步约需 4 分钟。
如需瘦身，可在 `PC-Action-install.spec` 的 `excludes` 里加不需要的模块，
或删掉 `dist\Action\_internal` 中确认用不到的组件
（如 `PyQt5/Qt5/bin/opengl32sw.dll` 20MB、`cv2/opencv_videoio_ffmpeg500_64.dll` 29MB）。

## 关于源码保护

安装包只解决“安装”问题。如需防反编译/破解，路线是
**服务端授权 → Cython 编核心模块 → PyArmor**，核心原则：**授权判断放服务端**，本地只做执行。
