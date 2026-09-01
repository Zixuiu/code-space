"""回归测试：组合技编辑器滚动条「隐身但可用」。

验证三件事：
  1. 垂直滚动条不可见（宽度 0），不再有灰色 handle 块
  2. 滚动能力保留 —— setValue 后视口确实移动
  3. 列宽/视口宽度不受滚动条挤占，水平滚动条仍为 0 范围
"""
import os, sys, time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, r"D:\codespace\01-space\PC-action\PC-action-macOS")

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

app = QApplication.instance() or QApplication(sys.argv)
from combo_skill_edit_dialog import ComboSkillEditDialog

# 造 14 条流程，确保必须滚动
flows = []
for i in range(14):
    flows.append({
        "condition": "找到图片",
        "image": "",
        "action_type": "execute",
        "action": f"执行流程 - 第{i+1}步",
        "wait": 0.5,
        "has_else": True,
        "else_branch": {"condition": "找不到图片", "image": "",
                        "action_type": "goto", "action": f"跳转-{i+1}"},
    })

skill = {
    "name": "滚动测试", "flows": flows, "loop_count": 1,
    "step_interval": 0.0, "default_step_interval": False, "skip_on_fail": True,
}

dlg = ComboSkillEditDialog(skill_data=skill)
dlg.show()
app.processEvents()

deadline = time.time() + 5.0
while time.time() < deadline and dlg.tree_widget.topLevelItemCount() < len(flows):
    app.processEvents()
    time.sleep(0.05)
app.processEvents()

tree = dlg.tree_widget
vsb = tree.verticalScrollBar()
hsb = tree.horizontalScrollBar()

print("[dialog size]     ", dlg.size().width(), "x", dlg.size().height())
print("[viewport w/h]    ", tree.viewport().width(), "x", tree.viewport().height())
print("[col widths]      ", [tree.columnWidth(i) for i in range(4)])
print("[col total]       ", sum(tree.columnWidth(i) for i in range(4)))

print("\n--- 水平滚动条 ---")
print("[hscroll range]   ", hsb.maximum(), "(应为 0)")
print("[hscroll visible] ", hsb.isVisible(), "(应为 False)")

print("\n--- 垂直滚动条（隐身但可用）---")
print("[vscroll width]   ", vsb.width(), "(应为 0 => 灰块不可见)")
print("[vscroll range]   ", vsb.maximum(), "(应 > 0 => 可滚动)")
print("[vscroll visible] ", vsb.isVisible())
print("[vscroll value]   ", vsb.value())

# 1) 断言：滚动条宽度为 0（隐身）
assert vsb.width() == 0, f"垂直滚动条宽度应为 0（隐身），实际 {vsb.width()}"
assert hsb.maximum() == 0 and not hsb.isVisible(), "水平滚动条应彻底消失"

# 2) 断言：滚动范围 > 0（可滚动）
assert vsb.maximum() > 0, f"垂直滚动范围应 > 0，实际 {vsb.maximum()}"

# 3) 断言：setValue 真的让视口滚动（滚动能力保留）
vsb.setValue(0)
app.processEvents()
first_item_y_before = tree.visualItemRect(tree.topLevelItem(0)).y()

target = min(vsb.maximum(), 200)
vsb.setValue(target)
app.processEvents()
first_item_y_after = tree.visualItemRect(tree.topLevelItem(0)).y()

print(f"\n[scroll test]     setValue(0) -> 首行y={first_item_y_before}")
print(f"[scroll test]     setValue({target}) -> 首行y={first_item_y_after}")
assert first_item_y_after < first_item_y_before, \
    f"setValue 后首行应上移（{first_item_y_before} -> {first_item_y_after}），滚动能力已失效！"

# 4) 断言：列宽总和 = viewport 宽（滚动条没挤占空间）
cols_total = sum(tree.columnWidth(i) for i in range(4))
assert cols_total <= tree.viewport().width() + 1, \
    f"列总宽 {cols_total} 应 ≤ viewport 宽 {tree.viewport().width()}"

print("\n✅ 垂直滚动条已隐身（width=0，无灰块）")
print("✅ 滚动能力保留（setValue 生效，视口真实位移）")
print("✅ 水平滚动条消失，列宽不再被挤占")
