# -*- coding: utf-8 -*-
"""
PC-Action Cython 核心模块编译脚本（源码保护·方案2）

作用：把列出的 .py 编译成原生机器码 .pyd，再打进 PyInstaller 包，
     编译后这些模块无法还原成 Python 源码，显著提高反逆向门槛。

前置：
  1) 安装 VS 2022 Build Tools（勾选“使用 C++ 的桌面开发”）
  2) .venv\\Scripts\\pip.exe install cython
用法：
  .venv\\Scripts\\python.exe build_cython.py

重要：不要全量编译。PyQt5 界面层（含 @pyqtSlot / lambda / 动态导入）编译后
容易运行时报错。只编译“纯业务逻辑”模块最稳。
"""
import os
import sys

# ============ 只编译这些关键逻辑模块（可按需增删） ============
# 原则：含 PyQt 信号槽/动态 __import__/lambda/字符串形式引用类名的，别加进来。
CORE_MODULES = [
    "supabase_db.py",      # 云端数据库封装（含账号/授权逻辑）
    "hybrid_db.py",        # 数据库混合层
    "login_manager.py",    # 注册/登录/验证码逻辑
    "entitlement.py",      # 会员/功能解锁判定（若存在）
    "database_helper.py",  # 数据库助手
]

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "cython_build")   # .pyd 输出目录


def main():
    from Cython.Build import cythonize

    os.makedirs(OUT_DIR, exist_ok=True)
    targets = []
    for m in CORE_MODULES:
        p = os.path.join(ROOT, m)
        if os.path.exists(p):
            targets.append(p)
        else:
            print(f"跳过（文件不存在）: {m}")

    if not targets:
        print("没有可编译的目标文件，请检查 CORE_MODULES 里的文件名。")
        return 1

    print("开始编译：", targets)
    cythonize(
        targets,
        output_dir=OUT_DIR,
        language_level=3,
        build_dir=os.path.join(OUT_DIR, "build"),
        compiler_directives={
            "language_level": 3,
            "boundscheck": False,   # 关掉边界检查，性能更好（发布用）
            "wraparound": False,
        },
    )
    print("-" * 50)
    print(f"编译完成！.pyd 已输出到: {OUT_DIR}")
    print("后续：把这些 .pyd 复制回项目根目录（替换同名 .py），再跑 "
          "installer\\build_installer.cmd 重新打包即可。")
    return 0


if __name__ == "__main__":
    sys.exit(main())