"""
文件: combo_skill_edit_dialog.py
用途: 组合技编辑对话框 - 完整的流程编辑、条件设置、图片选择等功能
"""

import os
import copy
from PyQt5.QtCore import Qt, QEvent, QTimer, QSize, QPoint, QByteArray
from PyQt5.QtGui import QColor, QPixmap, QImage, QIcon, QPainter, QPolygon
try:
    from PyQt5.QtSvg import QSvgRenderer
    _SVG_OK = True
except Exception:
    _SVG_OK = False
from PyQt5.QtWidgets import (QFrame, QListWidget,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QWidget, QComboBox,
    QDoubleSpinBox, QSpinBox, QTextEdit, QStackedWidget, QFrame,
    QFileDialog, QMessageBox, QApplication, QCheckBox, QStylePainter,
    QStyleOptionComboBox, QStyle, QScrollBar
)


# 图标统一放大系数（用户反馈图标偏小）——改这一个值即可全局调整所有图标大小
ICON_SCALE = 1.8

def load_svg_icon(name, size=18, color=None):
    """按脚本绝对路径定位 icons/，渲染 SVG → QIcon；异常兜底返回空 QIcon。
    color 为 None 时保留 SVG 原有语义配色；传 color 则统一为指定色。"""
    import re
    size = int(round(size * ICON_SCALE))
    _p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", f"{name}.svg")
    if not _SVG_OK or not os.path.exists(_p):
        return QIcon()
    _pm = QPixmap(QSize(size, size))
    _pm.fill(Qt.transparent)
    if color is None:
        _r = QSvgRenderer(_p)
    else:
        with open(_p, "r", encoding="utf-8") as f:
            svg = f.read()
        _preserve = {"#ECEFF4", "#C5CEDB", "none", "transparent"}
        def _repl_attr(m):
            attr, val = m.group(1), m.group(2)
            if val.lower() in ("none", "transparent") or val.upper() in _preserve:
                return m.group(0)
            return f'{attr}="{color}"'
        svg = re.sub(r'\b(fill|stroke)="([^"]+)"', _repl_attr, svg)
        def _repl_style(m):
            attr, val = m.group(1), m.group(2)
            if val.lower() in ("none", "transparent") or val.upper() in _preserve:
                return m.group(0)
            return f'{attr}:{color}'
        svg = re.sub(r'\b(fill|stroke):([^;\s]+)', _repl_style, svg)
        _r = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    _painter = QPainter(_pm)
    _painter.setRenderHint(QPainter.Antialiasing)
    _r.render(_painter)
    _painter.end()
    return QIcon(_pm)
T = {
    'primary': '#5A6069', 'primary_hover': '#474C54',
    'bg_main': '#FFFFFF', 'bg_card': '#FAFAFA', 'bg_input': '#FFFFFF',
    'text_primary': '#000000', 'text_secondary': '#888888',
    'border': '#E0E0E0', 'success': '#34C759', 'danger': '#FF3B30',
    'accent': '#00000010', 'header_bg': '#FAFAFA', 'tree_alt': '#F0F0F0',
}
IS_DARK = False
from design_system import ColorPalette, BorderRadiusSystem, TypographySystem
from utils import get_recordings_path, get_screen_size
from beautiful_dialog import StyledMessageDialog
from styles import apply_dialog_style


class CapsuleBorderBox(QWidget):
    """胶囊描边容器：用 cosmetic pen 自绘 1px 物理像素边框。

    为什么不用 QSS border：QSS 的 1px 圆角边框在非整数 DPI 缩放
    （1.25/1.5 等）下会被摊到两个物理像素行，每行只剩一半不透明度，
    视觉上边框"淡出/消失"（底边尤甚，用户截图实锤）。cosmetic pen
    永远按设备像素对齐、宽度不参与缩放，任何 DPI 下都是实心线。

    用法：把输入控件 setFixedHeight/Width 后 addWidget 进本容器，
    胶囊描边画在 owner 控件的 geometry 上（owner 本体 QSS 置
    透明背景 + 无边框）。owner 需 installEventFilter(self) 以联动聚焦态。
    """
    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self._owner = owner
        owner.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is not self._owner:
            return False
        t = ev.type()
        if t in (QEvent.FocusIn, QEvent.FocusOut):
            # 聚焦切换时重画描边（灰→主题色）
            self.update()
        elif t == QEvent.Resize:
            # ★ 行编辑框默认被右侧按钮区砍掉 14px（8+14+8 后只剩 40/70 宽），
            #   文字在这 40px 里居中永远到不了胶囊真中心（偏左 ~7px）。
            #   摊满整个胶囊宽：文字真正居中；透明按钮浮在 le 上层，
            #   右侧点击仍是步进（子控件命中优先），滚轮/输入不受影响。
            # singleShot(0) 延后：eventFilter 先于 owner 的 resizeEvent 执行，
            # 直接设会被基样式随后的布局覆盖。
            ow = self._owner
            def _spread():
                le = ow.lineEdit()
                # qproperty-alignment 在子控件上会静默失效（Qt QSS 已知限制），
                # 只能代码设置
                le.setAlignment(Qt.AlignCenter)
                # ★ 垂直居中不托付给 QLineEdit 内部排版（其行为受全局字体/样式
                #   级联影响，用户实机上文字沉底压边框）：把输入框高度压到文字
                #   实高、垂直钉在胶囊正中——内部无论怎么排都偏无可偏。
                fm = le.fontMetrics()
                th = max(1, fm.height())
                h = ow.height()
                le.setGeometry(0, max(0, (h - th) // 2), ow.width(), min(th, h))
            QTimer.singleShot(0, _spread)
        return False

    def paintEvent(self, ev):
        # ★ 边框必须画在 owner（输入框）在 self 坐标系里的真实位置，而不是 (0,0)：
        # owner 经布局被放在单元格内（带边距、可能被垂直居中/顶部对齐），若死画
        # (0,0) 则可见胶囊与真实输入框错开 → 数字看上去"偏在胶囊下半部"。
        r = self._owner.geometry()
        w, h = r.width(), r.height()
        if w <= 0 or h <= 0:
            return
        from PyQt5.QtGui import QPainterPath, QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        path = QPainterPath()
        # 0.5 内缩：DPR=1 时落在像素中心，线宽恰好 1px 不被削
        path.addRoundedRect(r.x() + 0.5, r.y() + 0.5, w - 1.0, h - 1.0, h / 2.0, h / 2.0)
        border = QColor(T['primary']) if self._owner.hasFocus() else QColor(T['border'])
        # QPen 默认 cosmetic=True：宽度按设备像素计，不随 DPI 缩放摊薄
        p.setPen(QPen(border, 1, Qt.SolidLine))
        # 白底也在这里画：Qt 父控件先画、子控件后画，若白底留在子控件 QSS
        # 里会把父容器刚画好的描边内侧盖掉半根线
        p.setBrush(QColor(T['bg_input']))
        p.drawPath(path)
        p.end()


class _CapsuleSpinBoxBase:
    """胶囊输入框基类：把内部 QLineEdit 在每次尺寸变化时**同步**钉死在正中。

    为什么必须覆盖 resizeEvent 而不是用 QTimer.singleShot(0)：
    QAbstractSpinBox 内部会在 resizeEvent 里重新摆放 lineEdit（给右侧上下按钮
    预留 14px、按样式算内容边距）。singleShot(0) 是延迟异步的，在高频 resize
    （树异步构建、对话框最终布局、item 增删）下会被基类的后续摆放覆盖，导致
    lineEdit 回到"偏左/压底"状态。覆盖 resizeEvent、在 super() 之后立刻重设
    lineEdit 几何，是最后一次、不可被覆盖的操作，任何 DPI/样式下都稳。
    """
    def _pin_lineedit(self):
        le = self.lineEdit()
        if le is None:
            return
        le.setContentsMargins(0, 0, 0, 0)
        le.setTextMargins(0, 0, 0, 0)
        le.setAlignment(Qt.AlignCenter)
        fm = le.fontMetrics()
        th = max(1, fm.height())
        h = self.height()
        w = self.width()
        # 铺满整宽（透明按钮浮在上层，右侧步进点击不受影响），高度=文字实高、
        # 垂直钉在胶囊正中——内部无论怎么排都偏无可偏。
        le.setGeometry(0, max(0, (h - th) // 2), w, min(th, h))

    def resizeEvent(self, ev):
        # CapsuleSpinBox 采用多重继承，MRO 使 super().resizeEvent() 落到 object，
        # 父类并无该方法，直接调用会抛 AttributeError 刷屏并拖慢主线程事件循环。
        try:
            super().resizeEvent(ev)
        except AttributeError:
            pass
        self._pin_lineedit()

    def showEvent(self, ev):
        try:
            super().showEvent(ev)
        except AttributeError:
            pass
        self._pin_lineedit()


class CapsuleSpinBox(QSpinBox, _CapsuleSpinBoxBase):
    pass


class CapsuleDoubleSpinBox(QDoubleSpinBox, _CapsuleSpinBoxBase):
    pass


class StyledCombo(QComboBox):
    """用自绘无边框弹窗替换 QComboBox 原生下拉。

    原生 QComboBox 的下拉列表在 Windows 上会带一圈去不掉的边框/阴影
    （QFrame 面板、系统窗口边框、DWM 投影逐层都难去掉，且 Qt API 够不到 DWM 阴影；
    之前用 FramelessWindowHint/DWM API 硬去仍残留灰线，还把内容搞歪）。
    这里直接不用原生下拉，改成自己画的 Frameless + NoDropShadow 弹窗，
    边框/阴影/错位全部可控。QComboBox 的模型与常用 API（addItem/addItems/
    setCurrentIndex/currentText/currentData/currentIndexChanged 等）照常可用。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup = None
        self._list = None

    def paintEvent(self, event):
        """自定义绘制：隐藏默认矩形箭头，改成实心朝下三角，并补上当前文字。"""
        painter = QStylePainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        # 去掉 Qt 默认的下拉矩形箭头绘制
        opt.subControls = opt.subControls & ~QStyle.SC_ComboBoxArrow
        painter.drawComplexControl(QStyle.CC_ComboBox, opt)

        # 绘制当前选中的文字（QStyle 默认有时会把文字带箭头一起画，这里显式补上）
        text = self.currentText()
        if text:
            edit_rect = self.style().subControlRect(
                QStyle.CC_ComboBox, opt, QStyle.SC_ComboBoxEditField, self
            )
            # 留一点左侧内边距，避免贴边
            edit_rect.adjust(6, 0, -6, 0)
            painter.setPen(QColor(T.get('text_primary', '#333333')))
            painter.drawText(edit_rect, Qt.AlignVCenter | Qt.AlignLeft, text)

        # 在右侧自绘一个尖朝下的实心三角
        arrow_color = QColor(T.get('text_secondary', '#888888'))
        rect = self.rect()
        arrow_w, arrow_h = 10, 6
        right_margin = 8
        x = rect.right() - right_margin - arrow_w
        y = rect.center().y() - arrow_h // 2
        poly = QPolygon([
            QPoint(x, y),
            QPoint(x + arrow_w, y),
            QPoint(x + arrow_w // 2, y + arrow_h)
        ])
        painter.setPen(Qt.NoPen)
        painter.setBrush(arrow_color)
        painter.drawPolygon(poly)

    # 不调用 super().showPopup()，改用自绘弹窗
    def showPopup(self):
        self._open_popup()

    def hidePopup(self):
        self._close_popup()

    def _open_popup(self):
        if self._popup is not None:
            self._close_popup()
        popup = QWidget(None, Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        # ★ 严禁设 WA_DeleteOnClose！
        # 弹窗里的列表项点击 → C++ 发射 lst.itemClicked → 回调 _pick() → _close_popup()
        # 会 close() 这个 popup。若带 WA_DeleteOnClose，close() 会立刻 delete C++ 对象，
        # 连带子控件 lst（也就是那个信号的发送者）一起被销毁；
        # 而此时我们仍在 lst.itemClicked 的 C++ 信号发射栈中，setCurrentIndex 之后
        # 信号返回 C++ 时就会访问已销毁的 sender → 进程级 access violation（try/except 拦不住）。
        # 改为：不自动删除，由 Python 侧持有引用，_close_popup 里显式 deleteLater()
        # 延迟到事件循环安全点再销毁。
        popup.setStyleSheet("QWidget { background: #FFFFFF; border: none; }")

        lst = QListWidget(popup)
        lst.setFrameShape(QFrame.NoFrame)
        lst.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lst.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        lst.setStyleSheet(
            "QListWidget { background: #FFFFFF; border: none; outline: none; padding: 4px; }"
            "QListWidget::item { padding: 7px 12px; border-radius: 6px; "
            "color: #1A1A1A; font-size: 13px; }"
            "QListWidget::item:hover { background: #F2F2F7; }"
            "QListWidget::item:selected { background: #ECEDEF; color: #5A6069; }"
        )
        for i in range(self.count()):
            lst.addItem(self.itemText(i))
        lst.setCurrentRow(self.currentIndex())

        # 计算尺寸（取 combo 宽与内容宽较大者，封顶 360，避免过宽）
        fm = lst.fontMetrics()
        max_w = self.width()
        for i in range(self.count()):
            tw = fm.horizontalAdvance(self.itemText(i)) + 44
            if tw > max_w:
                max_w = tw
        max_w = min(max_w, 360)
        row_h = 34
        h = min(self.count(), 12) * row_h + 8
        popup.resize(max_w, h)
        lst.setGeometry(0, 0, max_w, h)

        # 位置：combo 左下角下方；若超出屏幕底部则翻到上方
        pos = self.mapToGlobal(self.rect().bottomLeft())
        screen_bottom = QApplication.primaryScreen().geometry().bottom()
        if pos.y() + h > screen_bottom:
            pos = self.mapToGlobal(self.rect().topLeft())
            pos.setY(pos.y() - h)
        popup.move(pos)

        lst.itemClicked.connect(lambda it: self._pick(lst.row(it)))
        popup.installEventFilter(self)
        lst.installEventFilter(self)
        self._popup = popup
        self._list = lst
        popup.show()
        lst.setFocus()

    def _pick(self, idx):
        # 先关弹窗：_close_popup 走 deleteLater 延迟销毁，不会在信号栈里同步 delete
        self._close_popup()
        if 0 <= idx < self.count() and idx != self.currentIndex():
            # ★ 关键：把真正的选中动作推到信号发射栈之外执行。
            # _pick 是在 lst.itemClicked 的 C++ 信号发射栈中被调用的；若在栈内直接
            # setCurrentIndex，会同步触发 currentIndexChanged -> 业务槽函数
            # （on_action_detail_changed / on_action_type_changed 等），这些槽函数
            # 可能改动甚至重建流程界面；一旦期间 sender(lst) 被销毁，信号返回 C++
            # 就是 access violation（进程级崩溃，Python try/except 拦不住）。
            # singleShot(0) 让选中动作等回到事件循环后再执行，彻底规避该风险。
            QTimer.singleShot(0, lambda i=idx: self._apply_pick(i))

    def _apply_pick(self, idx):
        """在事件循环空闲时真正应用选中（此时已脱离 sender 的信号发射栈）。"""
        try:
            if 0 <= idx < self.count() and idx != self.currentIndex():
                self.setCurrentIndex(idx)  # 触发 currentIndexChanged
        except RuntimeError:
            # combo 可能已在期间被销毁（例如所属对话框关闭 / 流程树重建）
            pass

    def _close_popup(self):
        popup, lst = self._popup, self._list
        # 先摘掉 Python 侧引用，避免后续再访问到待销毁/已销毁的 C++ 对象
        self._popup = None
        self._list = None
        if popup is None:
            return
        # 移除事件过滤器（此刻对象仍存活，安全）
        for w in (lst, popup):
            if w is None:
                continue
            try:
                w.removeEventFilter(self)
            except Exception:
                pass
        try:
            popup.close()
        except Exception:
            pass
        try:
            # 延迟销毁：真正的 delete 发生在控制返回事件循环之后。
            # 绝不能在此刻直接销毁 —— _pick() 是在 lst.itemClicked 的
            # 信号发射栈中被调用的，同步销毁 sender 会导致进程级 access violation。
            popup.deleteLater()
        except Exception:
            pass

    def eventFilter(self, obj, event):
        # 用局部快照：_close_popup() 会把 self._popup/self._list 置 None，
        # 直接反复读 self._xxx 可能在判断与取值之间变成 None
        popup, lst = self._popup, self._list
        if obj in (popup, lst):
            et = event.type()
            if et in (QEvent.Close, QEvent.DeferredDelete):
                self._popup = None
                self._list = None
            elif et == QEvent.KeyPress:
                key = event.key()
                if key == Qt.Key_Escape:
                    self._close_popup()
                    return True
                if key in (Qt.Key_Return, Qt.Key_Enter) and lst is not None:
                    self._pick(lst.currentRow())
                    return True
                # 上下键交给 QListWidget 自身的导航即可，不拦截
        return super().eventFilter(obj, event)

    def hideEvent(self, event):
        # combo 被隐藏（含所属对话框关闭）时清理自绘弹窗。
        # popup 是无父对象的顶层窗口，不主动 close 会残留成游离窗口。
        self._close_popup()
        super().hideEvent(event)


class InvisibleScrollBar(QScrollBar):
    """滚动条「隐身但可用」。

    需求：不要那个上下拖动的灰块(handle)，但滚轮滚动 / setValue 必须照常工作。

    为什么不用 QSS：
      QSS 里 `QScrollBar:vertical { width: 0px }` **对 QScrollBar 无效** —— Qt 把
      0 值当「未设置」忽略，宽度仍由 QStyle 的 PM_ScrollBarExtent 决定（实测仍 14px）。
      （顺带一提：`width: 6px` 这类非零值是生效的，但做不到归零。）
      QSS 的 `background: transparent` 也挡不住 QStyle 自绘的 handle。

    所以走子类：
      - paintEvent 置空   -> 一个像素都不画，视觉上彻底消失
      - sizeHint/minimumSizeHint 返回 0 + setFixedWidth(0) -> 连 14px 占位也释放给内容区
      - 父类 QScrollBar 的值/信号/range 完全不受影响 -> 滚动能力 100% 保留
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFixedWidth(0)

    def sizeHint(self):
        return QSize(0, 0)

    def minimumSizeHint(self):
        return QSize(0, 0)

    def paintEvent(self, event):
        # 什么都不画：滚动条彻底不可见，但 value/range/wheelEvent 全部照常
        pass


class ComboSkillEditDialog(QDialog):
    """组合技编辑对话框 - 表格对齐版，支持执行操作"""

    def __init__(self, parent=None, skill_data=None):
        super().__init__(parent)
        self.parent = parent
        # 必须深拷贝！否则编辑对话框打开时原地修改flows会污染combo_manager原始数据
        if skill_data:
            self.skill_data = copy.deepcopy(skill_data)
        else:
            self.skill_data = {}
        self.flows = self.skill_data.get('flows', [])
        if len(self.flows) == 0:
            self.flows.append({
                'condition': 'image_found',
                'condition_image': '',
                'action': '',
                'else_branch': None
            })
        for flow in self.flows:
            if 'else_branch' not in flow:
                flow['else_branch'] = None
        self._execute_options_cache = None
        self._async_build_batch_size = 20
        self._async_build_index = 0
        self._loading_overlay = None
        self._pending_image_loads = []
        # Python 侧强引用：image_preview 被 monkey-patch 了 mousePressEvent，
        # 若 Python wrapper 被 GC 而 Qt 端 QLabel 还挂在树上，用户一点击就会
        # 回调到已回收的 lambda → access violation 崩溃。这里永久持有引用。
        self._preview_widgets = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle("编辑组合技" if self.skill_data else "新建组合技")
        # ★ 拉宽 dialog：原 900 不够装下 4 列，水平滚动条才会出现。现在 1180 让所有列塞得下，
        # 同时高度从 600 提到 680，给顶部 header + 底部按钮行 + 控件边距留充足空间。
        self.setFixedSize(1180, 680)

        # 应用全局对话框样式
        self.setStyleSheet('QDialog{background:transparent; border:none;}')

        from PyQt5.QtCore import Qt
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        _, sh = get_screen_size()
        self._sh = sh
        self._drag_pos = None
        btn_r = int(sh * 0.006)
        inp_r = int(sh * 0.006)

        _outer = QVBoxLayout(self)
        _outer.setContentsMargins(0, 0, 0, 0)
        _outer.setSpacing(0)
        _card = QFrame(self)
        _card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 18px;
                border: 1px solid #D1D1D6;
            }
        """)
        _cl = QVBoxLayout(_card)
        _cl.setSpacing(10)
        _cl.setContentsMargins(15, 12, 15, 15)
        _outer.addWidget(_card)
        layout = _cl

        # macOS close dot (右上角)
        _dot_lo = QHBoxLayout()
        _dot_lo.setContentsMargins(0, 0, 0, 0)
        _dot_lo.addStretch()
        _close = QLabel("✕")
        _close.setFixedSize(22, 22)
        _close.setAlignment(Qt.AlignCenter)
        _close.setStyleSheet("QLabel{color:#7A8190; font-size:13px; background:transparent; border:none; border-radius:6px;}QLabel:hover{background:#FF5F57; color:white;}")
        _close.setCursor(Qt.PointingHandCursor)
        def _close_click(ev):
            if ev.button() == Qt.LeftButton:
                self.close()
        _close.mousePressEvent = _close_click
        # 保持 Python 侧引用：monkey-patch 的 mousePressEvent 存在 Python wrapper 上，
        # wrapper 被 GC 后补丁会失效（与 image_preview 同一类问题）
        self._close_dot = _close
        _dot_lo.addWidget(_close)
        layout.addLayout(_dot_lo)


        # ── 顶部栏：标题 + 名称 + 循环次数 + 备注 ──
        top_layout = QHBoxLayout()
        title = QLabel("组合技")
        # 显式压掉 _card 的 QFrame 选择器泄漏：QLabel 继承 QFrame，会把卡片
        # 的白底+18px 圆角边框继承过来，在标题外画出一个"圈"。
        title.setStyleSheet("font-size: 16px; font-weight: bold; background:transparent; border:none;")
        top_layout.addWidget(title)

        self.name_input = QLineEdit(self.skill_data.get('name', ''))
        self.name_input.setPlaceholderText("请输入组合技名称")
        self.name_input.setStyleSheet("background:transparent; border:none; padding:4px 8px;")
        top_layout.addWidget(self.name_input, 1)

        loop_label = QLabel("循环:")
        # ★ 统一字号：不设 font-size 会继承全局 17pt 大字，与步间/图等/点后(12px)不齐，
        #   大字旁边的小胶囊视觉上像沉下去。四个标签必须同一字号同一颜色。
        loop_label.setStyleSheet("background:transparent; border:none; font-size:12px; color:#555;")
        loop_label.setFixedHeight(28)  # 与胶囊同高，中心线严格对齐
        loop_label.setAlignment(Qt.AlignVCenter)
        top_layout.addWidget(loop_label)

        self.loop_count_spin = CapsuleSpinBox()
        self.loop_count_spin.setRange(1, 9999)
        self.loop_count_spin.setValue(self.skill_data.get('loop_count', 1))
        self.loop_count_spin.setFixedHeight(28)  # 胶囊形：高 28 + 圆角 14
        self.loop_count_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: #FFFFFF;
                color: {T['text_primary']};
                border: 1px solid {T['border']};
                border-radius: 14px;
                padding: 0px 10px;
                min-height: 0px;
                font-size: 12px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: transparent;
                border: none;
                width: 14px;
            }}
            QSpinBox QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 0px;
                min-height: 0px;
                font-size: 12px;
                color: {T['text_primary']};
            }}
        """)
        top_layout.addWidget(self.loop_count_spin)

        self.skip_on_fail_check = QCheckBox("跳过失败")
        self.skip_on_fail_check.setChecked(self.skill_data.get('skip_on_fail', False))
        self.skip_on_fail_check.setToolTip("开启后，图片匹配失败时跳过该步骤继续执行；关闭后，匹配失败立即停止运行")
        self.skip_on_fail_check.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                padding: 4px 8px;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1.5px solid #C7C7CC;
                border-radius: 4px;
                background: #FFFFFF;
            }
            QCheckBox::indicator:hover {
                border-color: #8E8E93;
            }
            QCheckBox::indicator:checked {
                background: #5A6069;
                border-color: #5A6069;
            }
        """)
        top_layout.addWidget(self.skip_on_fail_check)

        # ── 统一步骤间隔设置（录制流程内的每步操作之间等待时间）──
        self._step_interval_default = True  # 是否使用默认值
        step_interval_label = QLabel("步间:")
        step_interval_label.setStyleSheet("background:transparent; border:none; font-size:12px; color:#555;")
        step_interval_label.setFixedHeight(28)  # 与胶囊同高，中心线严格对齐
        step_interval_label.setAlignment(Qt.AlignVCenter)
        top_layout.addWidget(step_interval_label)

        raw_interval = self.skill_data.get('step_interval', '__default__')
        if raw_interval == '__default__' or raw_interval is None:
            self._step_interval_default = True
            raw_value = 0.1
        else:
            self._step_interval_default = False
            try:
                raw_value = float(raw_interval)
            except (TypeError, ValueError):
                self._step_interval_default = True
                raw_value = 0.1

        self.step_interval_spin = CapsuleDoubleSpinBox()
        self.step_interval_spin.setRange(0, 999.9)
        self.step_interval_spin.setDecimals(2)
        self.step_interval_spin.setSingleStep(0.1)
        self.step_interval_spin.setSuffix(" 秒")
        self.step_interval_spin.setValue(raw_value)
        self.step_interval_spin.setFixedWidth(100)
        self.step_interval_spin.setFixedHeight(28)  # 胶囊形：高 28 + 圆角 14
        self.step_interval_spin.setEnabled(not self._step_interval_default)
        self.step_interval_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: #FFFFFF;
                color: {T['text_primary']};
                border: 1px solid {T['border']};
                border-radius: 14px;
                padding: 0px 10px;
                min-height: 0px;
                font-size: 12px;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: transparent;
                border: none;
                width: 14px;
            }}
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: transparent;
            }}
            QDoubleSpinBox QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 0px;
                min-height: 0px;
                font-size: 12px;
                color: {T['text_primary']};
            }}
            QDoubleSpinBox:focus {{
                border-color: {T['primary']};
            }}
            QDoubleSpinBox:disabled {{
                background-color: #FFFFFF;
                color: {T['text_secondary']};
                border: 1px solid {T['border']};
            }}
            QDoubleSpinBox:disabled QLineEdit {{
                background-color: transparent;
                color: {T['text_secondary']};
            }}
        """)
        top_layout.addWidget(self.step_interval_spin)

        self.step_interval_default_cb = QCheckBox("默认")
        self.step_interval_default_cb.setChecked(self._step_interval_default)
        self.step_interval_default_cb.setToolTip("勾选后使用系统默认值(0.1秒)")
        self.step_interval_default_cb.setStyleSheet("""
            QCheckBox { font-size: 11px; color: #888; background-color: transparent; }
            QCheckBox::indicator { width: 14px; height: 14px; }
        """)
        self.step_interval_default_cb.stateChanged.connect(
            lambda st: self.step_interval_spin.setEnabled(not st))
        top_layout.addWidget(self.step_interval_default_cb)

        # ── 图片出现等待窗口（turbo 极速模式下，图片未出现时最多等这么久再判失败）──
        img_wait_label = QLabel("图等:")
        img_wait_label.setStyleSheet("background:transparent; border:none; font-size:12px; color:#555;")
        img_wait_label.setToolTip("图片出现等待窗口(秒)\n极速模式下点击后界面过渡动画期间，图片未出现会等这么久，期间图片出现立即点击；超时才跳过/失败。默认0.5s")
        img_wait_label.setFixedHeight(28)  # 与胶囊同高，中心线严格对齐
        img_wait_label.setAlignment(Qt.AlignVCenter)
        top_layout.addWidget(img_wait_label)

        self.turbo_grace_spin = CapsuleDoubleSpinBox()
        self.turbo_grace_spin.setRange(0, 10.0)
        self.turbo_grace_spin.setDecimals(1)
        self.turbo_grace_spin.setSingleStep(0.1)
        _tg_val = self.skill_data.get('turbo_grace', 0.5)
        self.turbo_grace_spin.setValue(float(_tg_val) if _tg_val is not None else 0.5)
        self.turbo_grace_spin.setSuffix(" 秒")
        self.turbo_grace_spin.setFixedWidth(70)
        self.turbo_grace_spin.setFixedHeight(28)  # 胶囊形：高 28 + 圆角 14
        self.turbo_grace_spin.setToolTip("图片出现等待窗口(秒)\n极速模式下点击后界面过渡动画期间，图片未出现会等这么久，期间图片出现立即点击；超时才跳过/失败。默认0.5s")
        self.turbo_grace_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: #FFFFFF;
                color: {T['text_primary']};
                border: 1px solid {T['border']};
                border-radius: 14px;
                padding: 0px 10px;
                min-height: 0px;
                font-size: 12px;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                background-color: transparent;
                border: none;
                width: 14px;
            }}
            QDoubleSpinBox QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 0px;
                min-height: 0px;
                font-size: 12px;
                color: {T['text_primary']};
            }}
            QDoubleSpinBox:focus {{
                border-color: {T['primary']};
            }}
        """)
        top_layout.addWidget(self.turbo_grace_spin)

        # ── turbo 点击后 UI 稳定等待（毫秒）：防止点击后立即匹配到旧画面 ──
        settle_label = QLabel("点后:")
        settle_label.setStyleSheet("background:transparent; border:none; font-size:12px; color:#555;")
        settle_label.setToolTip("点击后UI稳定等待(毫秒)\n极速模式下点击后等一小段，让目标应用处理点击/重绘，避免下一步匹配到点击前的旧画面。默认80ms")
        settle_label.setFixedHeight(28)  # 与胶囊同高，中心线严格对齐
        settle_label.setAlignment(Qt.AlignVCenter)
        top_layout.addWidget(settle_label)

        self.turbo_settle_spin = CapsuleSpinBox()
        self.turbo_settle_spin.setRange(0, 1000)
        self.turbo_settle_spin.setSingleStep(10)
        _ts_val = self.skill_data.get('turbo_settle', 0.08)
        self.turbo_settle_spin.setValue(int(float(_ts_val) * 1000) if _ts_val is not None else 80)
        self.turbo_settle_spin.setSuffix(" ms")
        self.turbo_settle_spin.setFixedWidth(70)
        self.turbo_settle_spin.setFixedHeight(28)  # 胶囊形：高 28 + 圆角 14
        self.turbo_settle_spin.setToolTip("点击后UI稳定等待(毫秒)\n极速模式下点击后等一小段，让目标应用处理点击/重绘，避免下一步匹配到点击前的旧画面。默认80ms")
        self.turbo_settle_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: #FFFFFF;
                color: {T['text_primary']};
                border: 1px solid {T['border']};
                border-radius: 14px;
                padding: 0px 10px;
                min-height: 0px;
                font-size: 12px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: transparent;
                border: none;
                width: 14px;
            }}
            QSpinBox QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 0px;
                min-height: 0px;
                font-size: 12px;
                color: {T['text_primary']};
            }}
            QSpinBox:focus {{
                border-color: {T['primary']};
            }}
        """)
        top_layout.addWidget(self.turbo_settle_spin)

        note_btn = QPushButton("备注")
        note_btn.setStyleSheet(self._bar_btn_style())
        note_btn.clicked.connect(self.show_note_page)
        top_layout.addWidget(note_btn)

        layout.addLayout(top_layout)

        # ★ 顶部四个胶囊（循环/步间/图等/点后）数字居中：复用 CapsuleBorderBox 的
        #   事件钩子（不进布局、不参与绘制——这些胶囊仍走 QSS 描边），只在 spin
        #   尺寸变化时把 lineEdit 铺满整胶囊 + AlignCenter。引用必须挂 self，
        #   否则钩子对象被 GC 时过滤器随之摘除。
        self._capsule_hooks = [
            CapsuleBorderBox(self.loop_count_spin),
            CapsuleBorderBox(self.step_interval_spin),
            CapsuleBorderBox(self.turbo_grace_spin),
            CapsuleBorderBox(self.turbo_settle_spin),
        ]

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet('background:transparent; border:none;')

        # ========== 页面1: 流程编辑页面 ==========
        self.flow_page = QWidget()
        self.flow_page.setStyleSheet('background:transparent; border:none;')
        flow_layout = QVBoxLayout(self.flow_page)
        flow_layout.setContentsMargins(0, 0, 0, 0)
        flow_layout.setSpacing(10)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["执行条件", "条件图片", "执行操作", "等待(s)"])
        self.tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent; border: none; outline: 0;
            }}
            QTreeWidget:focus {{ outline: 0; border: none; }}
            QTreeWidget::viewport {{
                /* 上下/左右边框全去掉；保留上下滚动时仍可拖到底 */
                background: transparent; border: none; outline: 0;
            }}
            QTreeWidget::item {{
                padding: 8px; border-bottom: none; min-height: 45px; outline: none; border: none;
                background: transparent;
            }}
            /* 选中/hover 一律不上色：行内全是可点控件，行高亮只会从透明控件底下
               透出 Windows 原生灰绿条，看起来像整行被切割（T['primary']15 这种
               8位hex写法 QSS 不认，回退成原生高亮） */
            QHeaderView::section {{
                /* 显式白底：transparent 在 Windows 下会让 QHeaderView 回落成原生灰色表头 */
                background-color: #FFFFFF;
                color: #666;
                padding: 10px;
                font-weight: 600;
                border: none;
                border-bottom: 1px solid #E5E5EA;
                font-size: 12px;
            }}
            /* ★ 滚动条「隐身但可用」：handle / 轨道 / 上下箭头全部透明且 0 尺寸，
               滚轮滚动、键盘、程序 setValue 全部照常工作，只是看不见那个灰块 */
            QScrollBar:vertical {{
                background: transparent; border: none;
                width: 0px; margin: 0px; padding: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: transparent; border: none;
                min-height: 0px; width: 0px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: transparent; border: none; height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: transparent; border: none;
            }}
            QScrollBar:horizontal {{
                background: transparent; border: none;
                height: 0px; margin: 0px; padding: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: transparent; border: none;
                min-width: 0px; height: 0px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                background: transparent; border: none; width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: transparent; border: none;
            }}
        """)
        # Windows 上 NoFrame 默认还会留下焦点边框色（橄榄绿），强制清掉
        self.tree_widget.setAttribute(Qt.WA_NoSystemBackground, True)
        self.tree_widget.viewport().setAttribute(Qt.WA_NoSystemBackground, True)
        self.tree_widget.setFocusPolicy(Qt.NoFocus)
        # ★ 关键：列宽 300+230+520(自适应)+90 ≈ 1140，加上 header padding / 列边距也不到 1180，
        # 不再触发水平滚动条。同时把水平滚动条强制关闭，垂直滚动条始终允许。
        self.tree_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.tree_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # ★ 用「隐身」滚动条替换默认垂直滚动条：paintEvent 置空 + sizeHint/width=0，
        # 那个上下拖动的灰块(handle)彻底消失；但 QScrollBar 的值/范围/滚轮事件照常，
        # 用户仍可滚轮上下滑动查看被遮住的内容。
        self.tree_widget.setVerticalScrollBar(InvisibleScrollBar(self.tree_widget))
        self.tree_widget.setRootIsDecorated(False)   # 不画展开箭头（本就是 top-level）
        self.tree_widget.setIndentation(0)           # 去掉默认 16px 缩进，吃掉的列宽释放出来
        # ★ 表头默认 stretchLastSection=True 会把最后一列「等待(s)」拉伸填满剩余宽度
        #   （1180 - 300 - 130 - 440 ≈ 300px），看起来"等待"巨宽。关掉它，
        #   改由「执行操作」列在 show 后按剩余宽度自适应（见 _fit_action_col_widths）。
        self.tree_widget.header().setStretchLastSection(False)
        self.tree_widget.setColumnWidth(0, 300)      # 执行条件
        self.tree_widget.setColumnWidth(1, 230)      # 条件图片（原 130，放不下预览+浏览按钮）
        self.tree_widget.setColumnWidth(2, 520)      # 执行操作（初始值，show 后自适应剩余宽度）
        self.tree_widget.setColumnWidth(3, 90)       # 等待(s)：固定窄列，不再被拉伸

        self.tree_widget.setFrameShape(QFrame.NoFrame)
        self.tree_widget.setLineWidth(0)
        self.tree_widget.setSelectionMode(QTreeWidget.SingleSelection)
        self.dragged_item = None
        self.dragged_index = None
        self.tree_widget.viewport().installEventFilter(self)
        self.tree_widget.setMinimumHeight(380)
        self.flow_widgets = []

        self._build_loading_overlay(flow_layout)
        QTimer.singleShot(50, self._start_async_build)

        flow_layout.addWidget(self.tree_widget, 1)

        # ── 操作按钮行 ──
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("+ 添加")
        add_btn.setStyleSheet(self._bar_btn_style(bg=T['primary'], fg='white', hover_bg=T['primary_hover']))
        add_btn.clicked.connect(self.add_flow)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("- 删除")
        del_btn.setStyleSheet(self._bar_btn_style(bg=T['danger'], fg='white', hover_bg='#FF3B30DD'))
        del_btn.clicked.connect(self.delete_flow)
        btn_layout.addWidget(del_btn)

        btn_layout.addStretch()

        up_btn = QPushButton("上移")
        up_btn.setIcon(load_svg_icon("arrow_up", 16))
        up_btn.setIconSize(QSize(24, 24))
        up_btn.setStyleSheet(self._bar_btn_style())
        up_btn.clicked.connect(self.move_flow_up)
        btn_layout.addWidget(up_btn)

        down_btn = QPushButton("下移")
        down_btn.setIcon(load_svg_icon("arrow_down", 16))
        down_btn.setIconSize(QSize(24, 24))
        down_btn.setStyleSheet(self._bar_btn_style())
        down_btn.clicked.connect(self.move_flow_down)
        btn_layout.addWidget(down_btn)

        flow_layout.addLayout(btn_layout)
        self.stacked_widget.addWidget(self.flow_page)

        # ========== 页面2: 备注编辑页面 ==========
        self.note_page = QWidget()
        note_layout = QVBoxLayout(self.note_page)
        note_layout.setContentsMargins(10, 10, 10, 10)
        note_layout.setSpacing(15)

        note_title_layout = QHBoxLayout()
        note_title = QLabel("组合技备注")
        note_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        note_title_layout.addWidget(note_title)
        note_title_layout.addStretch()

        back_btn = QPushButton("返回")
        back_btn.setIcon(load_svg_icon("arrow_left", 16))
        back_btn.setIconSize(QSize(24, 24))
        back_btn.setStyleSheet(self._bar_btn_style(bg=T['primary'], fg='white', hover_bg=T['primary_hover']))
        back_btn.clicked.connect(self.show_flow_page)
        note_title_layout.addWidget(back_btn)
        note_layout.addLayout(note_title_layout)

        self.note_text = QTextEdit()
        self.note_text.setPlaceholderText("请输入组合技的备注说明...")
        self.note_text.setPlainText(self.skill_data.get('note', ''))
        note_layout.addWidget(self.note_text)

        self.stacked_widget.addWidget(self.note_page)

        layout.addWidget(self.stacked_widget, 1)
        layout.addStretch()

        # ── 底部保存/取消 ──
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #1C1C1E;
                border: none;
                border-radius: {8}px;
                font-size: {13}px;
                font-weight: {600};
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 12px;
                min-height: 34px;
            }}
            QPushButton:hover {{
                background-color: #E5E5EA;
                color: #000000;
            }}
            QPushButton:pressed {{
                background-color: #D1D1D6;
                padding-top: 2px;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setIcon(load_svg_icon("check", 16))
        save_btn.setIconSize(QSize(24, 24))
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {T['primary']};
                color: white;
                border: none;
                border-radius: {8}px;
                font-size: {13}px;
                font-weight: {600};
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 12px;
                min-height: 34px;
            }}
            QPushButton:hover {{
                background-color: {T['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {T['primary']};
                padding-top: 2px;
            }}
        """)
        save_btn.clicked.connect(self.accept)
        bottom_layout.addWidget(save_btn)

        layout.addLayout(bottom_layout)

    def mousePressEvent(self, e):
        from PyQt5.QtCore import Qt
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        from PyQt5.QtCore import Qt
        if self._drag_pos and e.buttons() == Qt.LeftButton:
            self.move(e.globalPos() - self._drag_pos)
        super().mouseMoveEvent(e)

    def show_note_page(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_flow_page(self):
        self.stacked_widget.setCurrentIndex(0)

    def build_flow_tree(self):
        """【性能优化】手动全量重建 (打开时走异步加载 _start_async_build)"""
        try:
            if self._loading_overlay is not None:
                self._loading_overlay.setParent(None)
                self._loading_overlay.deleteLater()
                self._loading_overlay = None
        except Exception:
            pass
        # ── 性能优化关键：冻结更新 + 清空旧widget引用 ──
        self.tree_widget.setUpdatesEnabled(False)     # ① 暂不重绘
        self.tree_widget.blockSignals(True)            # ② 暂停信号（插入行不触发任何回调）
        try:
            self.tree_widget.clear()                   # 旧 widget 在这里被销毁（正常）
            self.flow_widgets = []
            # 旧行已随 clear() 销毁，必须同步释放 preview 的 Python 引用，
            # 否则 _preview_widgets 会残留指向已销毁 C++ 对象的悬空 wrapper
            self._preview_widgets = []

            total_flows = len(self.flows)
            for i in range(total_flows):
                flow_data = self.flows[i]

                main_item = QTreeWidgetItem(self.tree_widget)
                main_item.setText(0, "")
                main_item.setText(1, "")
                main_item.setText(2, "")
                main_item.setData(0, Qt.UserRole, {'index': i, 'is_else': False})

                self.create_flow_item_widgets(main_item, i, flow_data, is_else=False)

                if flow_data.get('else_branch'):
                    else_data = flow_data['else_branch']
                    else_item = QTreeWidgetItem(main_item)
                    else_item.setText(0, "")
                    else_item.setText(1, "")
                    else_item.setText(2, "")
                    else_item.setBackground(0, QColor("#F5F5F7"))
                    else_item.setBackground(1, QColor("#F5F5F7"))
                    else_item.setBackground(2, QColor("#F5F5F7"))
                    else_item.setData(0, Qt.UserRole, {'index': i, 'is_else': True})
                    self.create_flow_item_widgets(else_item, i, else_data, is_else=True)
                    main_item.setExpanded(True)
        finally:
            # 批量构建完成后才恢复绘制（性能提升 5~10 倍）
            self.tree_widget.blockSignals(False)
            self.tree_widget.setUpdatesEnabled(True)


    def _build_loading_overlay(self, parent_layout):
        overlay_wrap = QWidget()
        overlay_wrap.setStyleSheet("background: transparent; border: none;")
        overlay_lo = QVBoxLayout(overlay_wrap)
        overlay_lo.setContentsMargins(0, 0, 0, 0)
        overlay_lo.setSpacing(0)
        spacer_top = QLabel(" ")
        spacer_top.setFixedHeight(350)
        overlay_lo.addWidget(spacer_top)
        overlay_lo.addStretch()
        center = QHBoxLayout()
        center.addStretch()
        box = QVBoxLayout()
        box.setSpacing(10)
        self._loading_spinner = QLabel("Loading...")
        self._loading_spinner.setAlignment(Qt.AlignCenter)
        self._loading_spinner.setStyleSheet("font-size: 18px; color: %s; background: transparent; font-weight: bold;" % T["primary"])
        box.addWidget(self._loading_spinner)
        self._loading_text = QLabel("正在加载流程... 0 / %d" % len(self.flows))
        self._loading_text.setAlignment(Qt.AlignCenter)
        self._loading_text.setStyleSheet("font-size: 13px; color: %s; background: transparent;" % T["text_secondary"])
        box.addWidget(self._loading_text)
        self._loading_progress_bar = QLabel("")
        self._loading_progress_bar.setFixedHeight(4)
        self._loading_progress_bar.setFixedWidth(240)
        self._loading_progress_bar.setStyleSheet("background: #E5E5EA; border-radius: 2px;")
        box.addWidget(self._loading_progress_bar, 0, Qt.AlignCenter)
        center.addLayout(box)
        center.addStretch()
        overlay_lo.addLayout(center)
        overlay_lo.addStretch()
        self._loading_overlay = overlay_wrap
        parent_layout.addWidget(self._loading_overlay)

    def _fit_action_col_widths(self):
        """show 后把「执行操作」列设为剩余宽度，避免关掉 stretchLastSection 后右侧留白。
        对话框 setFixedSize(1180,680)，算一次即可。"""
        try:
            vp = self.tree_widget.viewport().width()
            if vp <= 0:
                return
            others = self.tree_widget.columnWidth(0) + self.tree_widget.columnWidth(1) + self.tree_widget.columnWidth(3)
            self.tree_widget.setColumnWidth(2, max(300, vp - others))
        except Exception:
            pass

    def _start_async_build(self):
        # 对话框已 show（singleShot 在事件循环启动后才触发），此时 viewport 宽度真实可用
        self._fit_action_col_widths()
        self.tree_widget.setUpdatesEnabled(False)
        self.tree_widget.blockSignals(True)
        try:
            self.tree_widget.clear()
            self.flow_widgets = []
            # 旧行已被清空，同步释放 preview 的 Python 引用（避免泄漏 / 悬空 wrapper）
            self._preview_widgets = []
        finally:
            self.tree_widget.blockSignals(False)
            self.tree_widget.setUpdatesEnabled(True)
        self._async_build_index = 0
        total = len(self.flows)
        if total <= self._async_build_batch_size:
            self._async_build_batch_size = max(1, total)
        self._update_loading_progress(0)
        QTimer.singleShot(20, self._load_next_batch)

    def _load_next_batch(self):
        if self._async_build_index >= len(self.flows):
            self._finish_async_build()
            return
        end = min(self._async_build_index + self._async_build_batch_size, len(self.flows))
        self.tree_widget.setUpdatesEnabled(False)
        self.tree_widget.blockSignals(True)
        try:
            for i in range(self._async_build_index, end):
                flow_data = self.flows[i]
                try:
                    main_item = QTreeWidgetItem(self.tree_widget)
                    main_item.setText(0, "")
                    main_item.setText(1, "")
                    main_item.setText(2, "")
                    main_item.setData(0, Qt.UserRole, {"index": i, "is_else": False})
                    self.create_flow_item_widgets(main_item, i, flow_data, is_else=False)
                    if flow_data.get("else_branch"):
                        else_data = flow_data["else_branch"]
                        else_item = QTreeWidgetItem(main_item)
                        else_item.setText(0, "")
                        else_item.setText(1, "")
                        else_item.setText(2, "")
                        else_item.setBackground(0, QColor("#F5F5F7"))
                        else_item.setBackground(1, QColor("#F5F5F7"))
                        else_item.setBackground(2, QColor("#F5F5F7"))
                        else_item.setData(0, Qt.UserRole, {"index": i, "is_else": True})
                        self.create_flow_item_widgets(else_item, i, else_data, is_else=True)
                        main_item.setExpanded(True)
                except Exception:
                    # ★ 单行构建失败不允许断掉 QTimer 构建链，否则 Loading 遮罩永远不消失
                    import traceback as _tb
                    print(f"[COMBO_EDIT] flow #{i} 构建失败:\n{_tb.format_exc()}")
        finally:
            self.tree_widget.blockSignals(False)
            self.tree_widget.setUpdatesEnabled(True)
        self._async_build_index = end
        self._update_loading_progress(end)
        QTimer.singleShot(1, self._load_next_batch)

    def _update_loading_progress(self, loaded):
        total = len(self.flows)
        try:
            if self._loading_text:
                pct = int(loaded * 100 / max(1, total))
                self._loading_text.setText("正在加载流程... %d / %d  (%d%%)" % (loaded, total, pct))
            if self._loading_progress_bar and total > 0:
                w = 240
                fill = int(w * loaded / total)
                ratio = fill / w if w > 0 else 0
                self._loading_progress_bar.setStyleSheet(
                    "background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
                    "stop:0 %(p)s stop:%(r)f %(p)s stop:%(r)f #E5E5EA);"
                    "border-radius: 2px;" % {"p": T["primary"], "r": ratio}
                )
        except Exception:
            pass

    def _resolve_condition_image_path(self, image_path):
        """条件图片路径统一解析：相对路径按 recordings 目录补全，再 normpath。
        与 view_condition_image_path 的解析规则保持一致，避免
        "列表判不存在卡加载中、点开却能拼出真实路径" 的分裂判定。"""
        if not image_path:
            return ''
        if not os.path.isabs(image_path):
            image_path = os.path.join(get_recordings_path(), image_path)
        return os.path.normpath(image_path)

    def _mark_preview_missing(self, preview):
        """文件不存在时把占位从"加载中…"改成"未找到"，并保留点击查看路径的能力"""
        try:
            preview.setStyleSheet(
                "color: #C7C7CC; font-size: 11px; "
                "background-color: #F5F5F7; border: 1px dashed #E5E5EA; border-radius: 6px;"
            )
            preview.setText("未找到")
        except Exception:
            pass

    def _finish_async_build(self):
        # 【性能优化】构建完成后，加载所有延迟的图片缩略图
        if self._pending_image_loads:
            for preview in self._pending_image_loads:
                path = getattr(preview, 'image_path', '')
                if not path:
                    continue
                # 相对路径先按 recordings 目录解析，与点击查看时的判定一致
                resolved = self._resolve_condition_image_path(path)
                if os.path.exists(resolved):
                    self.load_image_to_preview(preview, resolved)
                else:
                    # 文件真不存在：明确显示"未找到"，不再卡"加载中…"
                    self._mark_preview_missing(preview)
            self._pending_image_loads = []
        try:
            if self._loading_overlay is not None:
                self._loading_overlay.setParent(None)
                self._loading_overlay.deleteLater()
                self._loading_overlay = None
        except Exception:
            pass



    def _combo_style(self, width=120):
        """统一的 combo box 样式"""
        return f"""
            QComboBox {{
                background-color: {T['bg_card']}; color: {T['text_primary']};
                border: none; border-radius: 8px;
                padding: 6px 12px; font-size: 12px; font-weight: 500;
            }}
            QComboBox:focus {{ outline: none; border: none; }}
            QComboBox:hover {{ border-color: {T['primary']}; }}
            QComboBox::drop-down {{
                background: transparent; border: none; width: 18px;
                subcontrol-position: center right; subcontrol-origin: padding;
            }}
            QComboBox::down-arrow {{
                image: none; border: none; width: 0; height: 0; background: transparent;
            }}
            QComboBox QAbstractItemView {{
                background-color: {T['bg_card']}; color: {T['text_primary']};
                border: none; border-radius: 8px; padding: 4px; outline: none;
            }}
            QComboBox QListView {{
                background-color: {T['bg_card']}; color: {T['text_primary']};
                border: none; border-radius: 8px; outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px; border-radius: 6px; min-height: 22px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {T['primary']}; color: white;
            }}
        """

    def _btn_style(self, bg=T['primary'], fg='white', font_size=12, padding='3px 10px', radius=6):
        """统一的小按钮样式（扁平：低内边距 + 小圆角）。font_size=12：10px 在高分屏上几乎看不清"""
        return f"background: {bg}; color: {fg}; padding: {padding}; font-size: {font_size}px; border: none; border-radius: {radius}px;"

    def _bar_btn_style(self, bg='transparent', fg='#1C1C1E', hover_bg='#E5E5EA'):
        """底部操作栏按钮样式（扁平滑）"""
        radius = 6
        return f"""
            QPushButton {{
                background-color: {bg}; color: {fg}; border: none;
                border-radius: 6px; font-weight: 500;
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 12px; min-height: 30px;
            }}
            QPushButton:hover {{ background-color: {hover_bg}; color: #000000; }}
            QPushButton:pressed {{ background-color: #D1D1D6; padding-top: 1px; }}
        """

    def create_flow_item_widgets(self, tree_item, index, flow_data, is_else=False):
        condition = flow_data.get('condition', 'always')

        # ── 第0列：流程编号 + 执行条件 ──
        condition_widget = QWidget()
        condition_widget.setStyleSheet("background: transparent; border: none;")
        condition_layout = QHBoxLayout(condition_widget)
        condition_layout.setContentsMargins(5, 2, 5, 2)
        condition_layout.setSpacing(5)

        if not is_else:
            flow_number_label = QLabel(f"{index + 1}")
            flow_number_label.setStyleSheet(f"""
                QLabel {{
                    background: {T['primary']};
                    color: white;
                    border-radius: 10px;
                    padding: 2px 6px;
                    font-size: 11px;
                    font-weight: bold;
                    min-width: 20px;
                    max-width: 20px;
                }}
            """)
            flow_number_label.setAlignment(Qt.AlignCenter)
            condition_layout.addWidget(flow_number_label)
        else:
            else_indent = QLabel("ELSE")
            else_indent.setStyleSheet(f"color: {T['text_secondary']}; font-size: 12px; font-weight: 600; background: transparent; padding: 0 4px;")
            condition_layout.addWidget(else_indent)

        condition_combo = StyledCombo()
        condition_combo.blockSignals(True)
        condition_combo.addItems(["总是执行", "找到图片", "找不到图片", "等待图片"])
        condition_combo.setCurrentIndex({"always": 0, "image_found": 1, "image_not_found": 2, "wait_for_image": 3}.get(condition, 0))
        condition_combo.setStyleSheet(self._combo_style(120))
        condition_combo.setFixedWidth(120)
        if is_else:
            condition_combo.currentIndexChanged.connect(lambda idx, i=index: self.on_else_condition_changed(i, idx))
        else:
            condition_combo.currentIndexChanged.connect(lambda idx, i=index: self.on_condition_changed(i, idx))
        condition_combo.blockSignals(False)
        condition_layout.addWidget(condition_combo)

        if not is_else:
            else_btn = QPushButton("+else")
            else_btn.setStyleSheet(self._btn_style())
            else_btn.setFixedWidth(60)
            else_btn.clicked.connect(lambda checked, i=index: self.add_else_branch(i))
            if flow_data.get('else_branch'):
                else_btn.setEnabled(False)
                else_btn.setText("有else")
            else_btn.setVisible(condition != "always")
            condition_layout.addWidget(else_btn)

        if is_else:
            del_else_btn = QPushButton()
            del_else_btn.setIcon(load_svg_icon("cross", 16))
            del_else_btn.setIconSize(QSize(29, 29))
            del_else_btn.setStyleSheet("""
                QPushButton { background: transparent; border: none; padding: 2px; }
                QPushButton:hover { background-color: rgba(0,0,0,0.06); border-radius:9999px; }
                QPushButton:pressed { background-color: rgba(0,0,0,0.10); border-radius:9999px; }
            """)
            del_else_btn.setFixedWidth(28)
            del_else_btn.setToolTip("删除else分支")
            del_else_btn.clicked.connect(lambda checked, i=index: self.delete_else_branch(i))
            condition_layout.addWidget(del_else_btn)

        wait_time_spin = QSpinBox()
        wait_time_spin.blockSignals(True)
        wait_time_spin.setRange(1, 999999)
        wait_time_spin.setValue(flow_data.get('wait_timeout', 30))
        wait_time_spin.setFixedWidth(50)
        wait_time_spin.setVisible(condition == "wait_for_image")
        wait_time_spin.valueChanged.connect(lambda val, i=index, ie=is_else: self.on_wait_time_changed(i, val, ie))
        wait_time_spin.blockSignals(False)
        condition_layout.addWidget(wait_time_spin)

        # 图片出现等待窗口(秒)：image_found 条件显示（主/else 分支均生效，执行器会判断 else 条件）
        grace_spin = QDoubleSpinBox()
        grace_spin.blockSignals(True)
        grace_spin.setRange(0.1, 10.0)
        grace_spin.setSingleStep(0.1)
        grace_spin.setDecimals(1)
        _wg = flow_data.get('wait_grace', 0.5)
        grace_spin.setValue(float(_wg) if _wg is not None else 0.5)
        grace_spin.setFixedWidth(55)
        grace_spin.setToolTip("图片出现等待窗口(秒)\n未检测到条件图片时先等这么久，期间图片出现立即继续；超时才走else分支")
        grace_spin.setVisible(condition == "image_found")
        grace_spin.valueChanged.connect(lambda val, i=index, ie=is_else: self.on_grace_changed(i, val, ie))
        grace_spin.blockSignals(False)
        condition_layout.addWidget(grace_spin)

        condition_layout.addStretch()
        self.tree_widget.setItemWidget(tree_item, 0, condition_widget)

        # ── 第1列：条件图片 ──
        image_widget = QWidget()
        image_widget.setStyleSheet("background: transparent; border: none; outline: none;")
        image_layout = QHBoxLayout(image_widget)
        image_layout.setContentsMargins(4, 2, 4, 2)
        image_layout.setSpacing(6)

        image_preview = QLabel()
        image_preview.setFixedSize(70, 46)
        # 容器有边框+圆角，无图/失败/永远不显图也都有干净占位，不再"漂着"
        image_preview.setAlignment(Qt.AlignCenter)
        image_preview.setFrameShape(QFrame.NoFrame)
        # ★ image_path 必须在占位渲染之前赋值（曾因先用后赋导致 UnboundLocalError，
        #   异步构建链断裂 → Loading 遮罩永远卡在 0/N）
        image_path = flow_data.get('condition_image', '')
        if condition == 'always':
            # 无条件：直接显示 "—" 占位，不参与后续图片加载
            image_preview.setText("—")
            image_preview.setStyleSheet(
                "color: #C7C7CC; font-size: 16px; font-weight: 500; "
                "background-color: #F5F5F7; border: 1px dashed #E5E5EA; border-radius: 6px;"
            )
        else:
            image_preview.setStyleSheet(
                "color: #8E8E93; font-size: 11px; "
                "background-color: #F5F5F7; border: 1px dashed #D1D1D6; border-radius: 6px;"
            )
            if image_path:
                # 有路径但还没加载：占位文字"加载中"
                image_preview.setText("加载中…")
            else:
                image_preview.setText("无图片")
        image_preview.setCursor(Qt.PointingHandCursor if condition != 'always' else Qt.ArrowCursor)
        # 「总是执行」不需要图片：预览框整个隐藏，不留空占位
        image_preview.setVisible(condition != 'always')

        image_preview.image_path = image_path
        if image_path:
            self._pending_image_loads.append(image_preview)
        image_preview.mousePressEvent = lambda event, path=image_path: self.view_condition_image_path(path) if path else None
        # 保持 Python 引用，避免 wrapper 被 GC 后 Qt 回调崩溃（见 __init__ 说明）
        self._preview_widgets.append(image_preview)
        image_layout.addWidget(image_preview)

        img_btn = QPushButton("浏览")
        img_btn.setStyleSheet(self._btn_style(padding='4px 10px'))
        img_btn.clicked.connect(lambda checked, i=index, ie=is_else: self.browse_image(i, ie))
        img_btn.setVisible(condition != "always")
        image_layout.addWidget(img_btn)

        image_layout.addStretch()
        self.tree_widget.setItemWidget(tree_item, 1, image_widget)

        # ── 第2列：执行操作 ──
        action_widget = QWidget()
        action_widget.setStyleSheet("background: transparent; border: none;")
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(5, 2, 5, 2)
        action_layout.setSpacing(5)

        action_type_combo = StyledCombo()
        action_type_combo.blockSignals(True)
        action_type_combo.setStyleSheet(self._combo_style(120))
        action_type_combo.setFixedWidth(120)
        action_type_combo.setIconSize(QSize(29, 29))
        action_type_combo.addItem(load_svg_icon("stop", 16), "结束组合技", "end")
        action_type_combo.addItem(load_svg_icon("loop", 16), "跳转流程", "goto")
        action_type_combo.addItem(load_svg_icon("play", 16), "执行流程", "execute")
        action_layout.addWidget(action_type_combo)

        action_detail_combo = StyledCombo()
        action_detail_combo.blockSignals(True)
        action_detail_combo.setStyleSheet(self._combo_style(150))
        action_detail_combo.setFixedWidth(150)
        action_layout.addWidget(action_detail_combo)

        current_action = flow_data.get('action', '')
        self.setup_action_combos(action_type_combo, action_detail_combo, current_action, index)

        # 先解阻塞，再连接信号。这样初始化时 setCurrentIndex 的变化不会触发信号，
        # 只有用户实际交互才会触发，避免初始化时意外覆盖 flow 的 action 值
        action_type_combo.blockSignals(False)
        action_detail_combo.blockSignals(False)

        action_type_combo.currentIndexChanged.connect(
            lambda idx, i=index, atc=action_type_combo, adc=action_detail_combo, ie=is_else: self.on_action_type_changed(i, atc, adc, ie)
        )
        action_detail_combo.currentIndexChanged.connect(
            lambda idx, i=index, atc=action_type_combo, adc=action_detail_combo, ie=is_else: self.on_action_detail_changed(i, atc, adc, ie)
        )

        action_layout.addStretch()
        self.tree_widget.setItemWidget(tree_item, 2, action_widget)

        # ── 第3列：执行后等待时间 ──
        # 胶囊描边由 CapsuleBorderBox 自绘（cosmetic pen，任何 DPI 都是实心 1px）。
        # QSS 边框在 1.25/1.5 缩放下会半透明摊薄 → 底边"消失"（用户截图实锤）。
        delay_spin = CapsuleDoubleSpinBox()
        delay_spin.blockSignals(True)
        delay_spin.setRange(0, 999.9)
        delay_spin.setValue(flow_data.get('delay_after', 0))
        delay_spin.setDecimals(1)
        delay_spin.setSingleStep(0.5)
        delay_spin.setFixedWidth(70)
        delay_spin.setFixedHeight(28)
        delay_widget = CapsuleBorderBox(delay_spin)
        delay_widget.setStyleSheet("background: transparent; border: none;")
        delay_layout = QHBoxLayout(delay_widget)
        # 边距 0：让 spinbox（owner）贴在容器左上角 (0,0)，CapsuleBorderBox
        # 的 paintEvent 据此把胶囊画在输入框真实位置，二者严格对齐。
        # （注：树的 item padding 8px 已把 90px 列砍成 74px 可用区，spinbox 70
        #  + 右侧 stretch，所以右侧留 4px，不会影响边框连续性）
        delay_layout.setContentsMargins(0, 0, 0, 0)
        delay_layout.setSpacing(3)
        # 胶囊形：高 28，描边由外层 CapsuleBorderBox 自绘（见其类注释：
        # QSS 1px 圆角边框在高 DPI 下会摊薄淡出，底边直接看不见）。
        # 本体只负责文字；上下按钮透明 + 箭头隐藏（此前白按钮盖掉右线、
        # 基样式退化箭头画成 1px 细碎线贴在边框上，都是踩过的坑）。
        delay_spin.setFixedHeight(28)
        delay_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                background-color: transparent;
                color: {T['text_primary']};
                border: none;
                border-radius: 14px;
                padding: 0px 10px;
                min-height: 0px;
                font-size: 12px;
            }}
            QDoubleSpinBox::up-button {{
                subcontrol-origin: padding; subcontrol-position: top right;
                background-color: transparent; border: none; width: 14px;
            }}
            QDoubleSpinBox::down-button {{
                subcontrol-origin: padding; subcontrol-position: bottom right;
                background-color: transparent; border: none; width: 14px;
            }}
            /* ★ 箭头显式隐藏：不写箭头规则时基样式退化，把箭头画成 1px 细碎线
               贴在右/下边框上，看起来像"边框断线缺一块"；写三角规则又会把整个
               控件打回方形回退渲染。width/height=0 是唯一干净解（按钮仍可点）。 */
            QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow {{
                width: 0px; height: 0px; border: none; background: transparent;
            }}
            QDoubleSpinBox QLineEdit {{
                background-color: transparent;
                border: none;
                padding: 0px;
                min-height: 0px;
                font-size: 12px;
                color: {T['text_primary']};
            }}
        """)
        delay_spin.valueChanged.connect(lambda val, i=index, ie=is_else: self.on_delay_changed(i, val, ie))
        delay_spin.blockSignals(False)
        delay_layout.addWidget(delay_spin)

        delay_layout.addStretch()
        self.tree_widget.setItemWidget(tree_item, 3, delay_widget)

        widget_data = {
            'tree_item': tree_item,
            'flow_index': index,
            'condition_widget': condition_widget,    # 【性能优化】增量刷新序号时做身份匹配
            'image_widget': image_widget,
            'action_widget': action_widget,
            'condition_combo': condition_combo,
            'image_preview': image_preview,
            'img_btn': img_btn,
            'wait_time_spin': wait_time_spin,
            'grace_spin': grace_spin,
            'action_type_combo': action_type_combo,
            'action_detail_combo': action_detail_combo,
            'delay_spin': delay_spin,
            'is_else_branch': is_else
        }
        if not is_else:
            widget_data['else_btn'] = else_btn
        else:
            widget_data['del_else_btn'] = del_else_btn

        self.flow_widgets.append(widget_data)

    def add_else_branch(self, index):
        self.flows[index]['else_branch'] = {
            'condition': 'always',
            'condition_image': '',
            'action': '',
            'delay_after': 0.0
        }
        # 【性能优化】直接在 Tree 第 index 行下面追加 else_child，不再 build_flow_tree() 全量重建
        self.tree_widget.setUpdatesEnabled(False)
        self.tree_widget.blockSignals(True)
        try:
            main_item = self.tree_widget.topLevelItem(index)
            else_data = self.flows[index]['else_branch']
            else_item = QTreeWidgetItem(main_item)
            else_item.setText(0, "")
            else_item.setText(1, "")
            else_item.setText(2, "")
            bg = QColor("#F5F5F7")
            else_item.setBackground(0, bg)
            else_item.setBackground(1, bg)
            else_item.setBackground(2, bg)
            else_item.setData(0, Qt.UserRole, {'index': index, 'is_else': True})
            self.create_flow_item_widgets(else_item, index, else_data, is_else=True)
            main_item.setExpanded(True)
            # 把 +else 按钮禁用掉（避免再加）
            for wd in self.flow_widgets:
                if not wd.get('is_else_branch') and wd.get('flow_index') == index:
                    if 'else_btn' in wd and wd['else_btn'] is not None:
                        wd['else_btn'].setEnabled(False)
                        wd['else_btn'].setText("有else")
                    break
        finally:
            self.tree_widget.blockSignals(False)
            self.tree_widget.setUpdatesEnabled(True)

    def delete_else_branch(self, index):
        self.flows[index]['else_branch'] = None
        # 【性能优化】直接移除第 index 行下面所有子 item，不再全量重建
        self.tree_widget.setUpdatesEnabled(False)
        self.tree_widget.blockSignals(True)
        try:
            main_item = self.tree_widget.topLevelItem(index)
            # 先收集 flow_widgets 中属于 index 的 else 分支
            remove_wds = []
            for cr in range(main_item.childCount()):
                child = main_item.child(cr)
                cond_w = self.tree_widget.itemWidget(child, 0)
                for wd in self.flow_widgets:
                    if wd.get('is_else_branch') and wd.get('condition_widget') is cond_w:
                        remove_wds.append(wd)
                        break
            for wd in remove_wds:
                try:
                    self.flow_widgets.remove(wd)
                except Exception:
                    pass
            # 然后一次性拿掉所有子节点
            while main_item.childCount() > 0:
                main_item.takeChild(0)
            # 再把 +else 按钮恢复可用
            for wd in self.flow_widgets:
                if not wd.get('is_else_branch') and wd.get('flow_index') == index:
                    if 'else_btn' in wd and wd['else_btn'] is not None:
                        wd['else_btn'].setEnabled(True)
                        wd['else_btn'].setText("+else")
                    break
        finally:
            self.tree_widget.blockSignals(False)
            self.tree_widget.setUpdatesEnabled(True)

    def on_condition_changed(self, index, condition_idx):
        condition_map = {0: "always", 1: "image_found", 2: "image_not_found", 3: "wait_for_image"}
        condition = condition_map.get(condition_idx, "always")
        self.flows[index]['condition'] = condition

        # 切换到需要图片的条件时，如果还没有wait_timeout则设置默认值
        if condition == "wait_for_image" and 'wait_timeout' not in self.flows[index]:
            self.flows[index]['wait_timeout'] = 30

        for widget_data in self.flow_widgets:
            if widget_data.get('flow_index') == index and not widget_data.get('is_else_branch'):
                need_image = condition != "always"
                widget_data['image_preview'].setVisible(need_image)
                widget_data['img_btn'].setVisible(need_image)
                is_wait_for_image = (condition == "wait_for_image")
                widget_data['wait_time_spin'].setVisible(is_wait_for_image)
                # wait_time_spin 同步当前值
                if is_wait_for_image and 'wait_time_spin' in widget_data:
                    widget_data['wait_time_spin'].setValue(self.flows[index].get('wait_timeout', 30))
                # grace_spin 仅 image_found 显示，同步当前值
                is_grace_visible = (condition == "image_found")
                widget_data['grace_spin'].setVisible(is_grace_visible)
                if is_grace_visible and 'grace_spin' in widget_data:
                    _cg = self.flows[index].get('wait_grace', 0.5)
                    widget_data['grace_spin'].setValue(float(_cg) if _cg is not None else 0.5)
                if 'else_btn' in widget_data:
                    widget_data['else_btn'].setVisible(need_image)
                break

    def get_flow_index_from_item(self, item):
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            if root.child(i) == item:
                return i
        return None

    def eventFilter(self, obj, event):
        if obj == self.tree_widget.viewport():
            if event.type() == QEvent.MouseButtonPress:
                item = self.tree_widget.itemAt(event.pos())
                if item:
                    flow_index = self.get_flow_index_from_item(item)
                    if flow_index is not None:
                        self.dragged_item = item
                        self.dragged_index = flow_index
                    else:
                        self.dragged_item = None
                        self.dragged_index = None
                        return True
            elif event.type() == QEvent.MouseMove:
                if self.dragged_item and event.buttons() == Qt.LeftButton:
                    self.tree_widget.setCursor(Qt.ClosedHandCursor)
                    return True
            elif event.type() == QEvent.MouseButtonRelease:
                if self.dragged_item:
                    self.tree_widget.setCursor(Qt.ArrowCursor)
                    target_item = self.tree_widget.itemAt(event.pos())
                    if target_item and target_item != self.dragged_item:
                        target_index = self.get_flow_index_from_item(target_item)
                        if target_index is not None and target_index != self.dragged_index:
                            self.swap_flows(self.dragged_index, target_index)
                    self.dragged_item = None
                    self.dragged_index = None
                    return True
        return super().eventFilter(obj, event)

    def swap_flows(self, from_index, to_index):
        if from_index == to_index:
            return
        # 记录交换前的流程对象引用，用于跟踪跳转目标
        flows_before = list(self.flows)
        # 建立旧位置->新位置的映射
        pos_map = {from_index: to_index, to_index: from_index}
        for i in range(len(self.flows)):
            if i not in pos_map:
                pos_map[i] = i
        # 交换流程
        self.flows[from_index], self.flows[to_index] = self.flows[to_index], self.flows[from_index]
        # 重新映射所有跳转目标：跳转目标跟着流程对象走
        def remap_action(action):
            if not isinstance(action, str) or not action.startswith('跳转_'):
                return action
            try:
                old_target = int(action.split('_')[1])
            except (IndexError, ValueError):
                return action
            # 找到 old_target 位置上的流程对象，现在在新位置 pos_map[old_target]
            new_target = pos_map.get(old_target, old_target)
            return f'跳转_{new_target}'
        for flow in self.flows:
            flow['action'] = remap_action(flow.get('action', ''))
            else_branch = flow.get('else_branch') or {}
            if else_branch:
                else_branch['action'] = remap_action(else_branch.get('action', ''))

        # 【性能优化】不再 build_flow_tree()，而是直接交换 Tree 中的两个 TopLevelItem
        self.tree_widget.setUpdatesEnabled(False)
        self.tree_widget.blockSignals(True)
        try:
            # takeTopLevelItem 会把它从 Tree 中取出来（带着所有子 item + widget），我们换个顺序再塞回去
            a = min(from_index, to_index)
            b = max(from_index, to_index)
            item_b = self.tree_widget.takeTopLevelItem(b)
            item_a = self.tree_widget.takeTopLevelItem(a)
            # 然后倒序塞回去（先放原来的 b 到 a 位置，再放原来的 a 到 b 位置）
            if from_index < to_index:
                self.tree_widget.insertTopLevelItem(a, item_b)
                self.tree_widget.insertTopLevelItem(b, item_a)
            else:
                self.tree_widget.insertTopLevelItem(a, item_a)
                self.tree_widget.insertTopLevelItem(b, item_b)
        finally:
            self.tree_widget.blockSignals(False)
            self.tree_widget.setUpdatesEnabled(True)

        # 刷新序号 + 重新绑定回调（因为 index 变了，combo 的回调参数要跟着改）
        self._mark_flow_widgets_before_mutate()
        new_sel_index = to_index  # swap_flows 被 move_up/down 调用后外面还会再 setCurrentIndex，这里不设也行
        self._refresh_flow_numbers_after_change(preserve_index=new_sel_index)

    def on_else_condition_changed(self, index, condition_idx):
        condition_map = {0: "always", 1: "image_found", 2: "image_not_found", 3: "wait_for_image"}
        condition = condition_map.get(condition_idx, "always")
        if self.flows[index].get('else_branch'):
            self.flows[index]['else_branch']['condition'] = condition
            # 切换到wait_for_image时设置默认timeout
            if condition == "wait_for_image" and 'wait_timeout' not in self.flows[index]['else_branch']:
                self.flows[index]['else_branch']['wait_timeout'] = 30
            for widget_data in self.flow_widgets:
                if widget_data.get('flow_index') == index and widget_data.get('is_else_branch'):
                    need_image = condition != "always"
                    widget_data['image_preview'].setVisible(need_image)
                    widget_data['img_btn'].setVisible(need_image)
                    is_wait_for_image = (condition == "wait_for_image")
                    widget_data['wait_time_spin'].setVisible(is_wait_for_image)
                    # wait_time_spin 同步当前值
                    if is_wait_for_image and 'wait_time_spin' in widget_data:
                        widget_data['wait_time_spin'].setValue(self.flows[index]['else_branch'].get('wait_timeout', 30))
                    # grace_spin 仅 image_found 显示，同步当前值
                    is_grace_visible = (condition == "image_found")
                    widget_data['grace_spin'].setVisible(is_grace_visible)
                    if is_grace_visible and 'grace_spin' in widget_data:
                        _eg = self.flows[index]['else_branch'].get('wait_grace', 0.5)
                        widget_data['grace_spin'].setValue(float(_eg) if _eg is not None else 0.5)
                    break

    def on_wait_time_changed(self, index, value, is_else=False):
        if is_else:
            if self.flows[index].get('else_branch'):
                self.flows[index]['else_branch']['wait_timeout'] = value
        else:
            self.flows[index]['wait_timeout'] = value

    def on_grace_changed(self, index, value, is_else=False):
        if is_else:
            if self.flows[index].get('else_branch'):
                self.flows[index]['else_branch']['wait_grace'] = value
        else:
            self.flows[index]['wait_grace'] = value

    def on_delay_changed(self, index, value, is_else=False):
        if is_else:
            if self.flows[index].get('else_branch'):
                self.flows[index]['else_branch']['delay_after'] = value
        else:
            self.flows[index]['delay_after'] = value

    def _get_effective_step_interval(self):
        """
        获取最终生效的步骤间隔值（秒）。
        返回 None 表示使用系统默认（0.1秒）。
        """
        if hasattr(self, 'step_interval_default_cb') and self.step_interval_default_cb.isChecked():
            return None  # 默认
        if hasattr(self, 'step_interval_spin'):
            try:
                return float(self.step_interval_spin.value())
            except (TypeError, ValueError):
                return None
        return None

    def load_flows_to_action_combo(self, combo, selected_action, current_flow_index=0):
        recordings_dir = get_recordings_path()
        combo.clear()
        combo.setIconSize(QSize(29, 29))
        combo.addItem(load_svg_icon("stop", 16), "结束组合技", "end")
        if len(self.flows) > 0:
            combo.insertSeparator(combo.count())
            for i in range(len(self.flows)):
                if i != current_flow_index:
                    flow_action = self.flows[i].get('action', '')
                    if flow_action and not flow_action.startswith('跳转_') and flow_action != 'end':
                        display_name = flow_action
                    else:
                        display_name = f"流程{i+1}"
                    combo.addItem(load_svg_icon("loop", 16), f"跳转到{display_name}", f"跳转_{i}")
        combo.insertSeparator(combo.count())
        try:
            if os.path.exists(recordings_dir):
                folders = [d for d in os.listdir(recordings_dir)
                          if os.path.isdir(os.path.join(recordings_dir, d)) and d != 'trash']
                if folders:
                    for folder in folders:
                        combo.addItem(load_svg_icon("folder", 16), folder, folder)
        except Exception as e:
            pass
        if selected_action:
            for i in range(combo.count()):
                if combo.itemData(i) == selected_action:
                    combo.setCurrentIndex(i)
                    break

    def setup_action_combos(self, type_combo, detail_combo, current_action, index):
        if not current_action:
            # action 为空时，自动加载执行选项并选中第一项，让用户能看到可用流程
            type_combo.setCurrentIndex(2)
            detail_combo.setEnabled(True)
            detail_combo.setVisible(True)
            # 【性能优化】缓存已存在时，直接从缓存加载全部流程选项，避免重复扫描磁盘
            # ★修复：之前只取第一项，导致"执行操作"下拉框只能看到一个流程，改为遍历加载全部
            if self._execute_options_cache is not None:
                for folder in self._execute_options_cache:
                    detail_combo.addItem(f"执行: {folder}", folder)
                if detail_combo.count() > 0:
                    self.flows[index]['action'] = detail_combo.itemData(0)
            else:
                self.load_execute_options(detail_combo)
                if detail_combo.count() > 0:
                    self.flows[index]['action'] = detail_combo.itemData(0)
        elif current_action == 'end':
            type_combo.setCurrentIndex(0)
            detail_combo.clear()
            detail_combo.setEnabled(False)
            detail_combo.setVisible(False)  # 结束组合技无目标可选，隐藏空下拉
        elif current_action.startswith('跳转_'):
            type_combo.setCurrentIndex(1)
            detail_combo.setVisible(True)
            self.load_goto_options(detail_combo, index)
            found_match = False
            for i in range(detail_combo.count()):
                if detail_combo.itemData(i) == current_action:
                    detail_combo.setCurrentIndex(i)
                    found_match = True
                    break
            if not found_match:
                detail_combo.addItem(load_svg_icon("warning", 16), current_action, current_action)
                detail_combo.setCurrentIndex(detail_combo.count() - 1)
        else:
            type_combo.setCurrentIndex(2)
            detail_combo.setVisible(True)
            # 【性能优化】缓存已存在时，直接从缓存查找，避免循环 addItem
            if self._execute_options_cache is not None:
                if current_action in self._execute_options_cache:
                    detail_combo.addItem(f"执行: {current_action}", current_action)
                else:
                    detail_combo.addItem(load_svg_icon("warning", 16), current_action, current_action)
            else:
                self.load_execute_options(detail_combo)
                found_match = False
                for i in range(detail_combo.count()):
                    if detail_combo.itemData(i) == current_action:
                        detail_combo.setCurrentIndex(i)
                        found_match = True
                        break
                if not found_match:
                    detail_combo.addItem(load_svg_icon("warning", 16), current_action, current_action)
                    detail_combo.setCurrentIndex(detail_combo.count() - 1)

    def on_action_type_changed(self, index, type_combo, detail_combo, is_else):
        # 填充详情下拉期间必须屏蔽它自身的信号：clear()/addItem() 会连带触发
        # detail_combo 的 currentIndexChanged，而此刻我们正处在 type_combo 的
        # 信号发射栈中，嵌套回调会同步跑业务槽函数（on_action_detail_changed），
        # 一旦期间有控件被销毁/重建，信号返回 C++ 就是 access violation。
        # 屏蔽后由本函数统一显式写入 flows，最终行为与原来完全一致。
        detail_combo.blockSignals(True)
        try:
            action_type = type_combo.currentData()
            if action_type == 'end':
                detail_combo.clear()
                detail_combo.setEnabled(False)
                detail_combo.setVisible(False)  # 结束组合技：无目标，隐藏下拉
                if is_else:
                    if self.flows[index].get('else_branch'):
                        self.flows[index]['else_branch']['action'] = 'end'
                else:
                    self.flows[index]['action'] = 'end'
            elif action_type == 'goto':
                detail_combo.setEnabled(True)
                detail_combo.setVisible(True)
                self.load_goto_options(detail_combo, index)
                if detail_combo.count() > 0:
                    first_val = detail_combo.itemData(0)
                    if is_else:
                        if self.flows[index].get('else_branch'):
                            self.flows[index]['else_branch']['action'] = first_val
                    else:
                        self.flows[index]['action'] = first_val
            elif action_type == 'execute':
                detail_combo.setEnabled(True)
                detail_combo.setVisible(True)
                self.load_execute_options(detail_combo)
                if detail_combo.count() > 0:
                    first_val = detail_combo.itemData(0)
                    if is_else:
                        if self.flows[index].get('else_branch'):
                            self.flows[index]['else_branch']['action'] = first_val
                    else:
                        self.flows[index]['action'] = first_val
        except RuntimeError:
            # combo 可能已被销毁（流程树重建 / 对话框已关闭），忽略即可
            pass
        finally:
            try:
                detail_combo.blockSignals(False)
            except RuntimeError:
                pass

    def on_action_detail_changed(self, index, is_else_or_typecombo, detailcombo_or_iselse, maybe_typecombo=None):
        """兼容两种回调形式：
        ① 原始：(index, type_combo, detail_combo, is_else)
        ② 增量刷新重绑：(index, is_else, detail_combo, type_combo)
        """
        if hasattr(maybe_typecombo, 'currentData'):
            # 形式 ②
            is_else = is_else_or_typecombo
            detail_combo = detailcombo_or_iselse
            type_combo = maybe_typecombo
        else:
            # 形式 ①
            type_combo = is_else_or_typecombo
            detail_combo = detailcombo_or_iselse
            # ★修复：形式①第4个参数是 is_else 布尔值！之前写死False导致else分支永远存不到else_branch
            if isinstance(maybe_typecombo, bool):
                is_else = maybe_typecombo
            elif not isinstance(type_combo, QComboBox):
                is_else = is_else_or_typecombo
                detail_combo = type_combo
                type_combo = detailcombo_or_iselse
            else:
                is_else = False

        try:
            action_type = type_combo.currentData() if hasattr(type_combo, 'currentData') else None
            selected_value = detail_combo.currentData()
        except RuntimeError:
            # combo 的 C++ 对象已被销毁（流程树重建 / 对话框已关闭），忽略即可
            return
        try:
            if selected_value:
                if is_else:
                    if self.flows[index].get('else_branch'):
                        self.flows[index]['else_branch']['action'] = selected_value
                else:
                    self.flows[index]['action'] = selected_value
        except (RuntimeError, IndexError):
            pass

    def load_goto_options(self, combo, current_index, select_action=None):
        combo.clear()
        for i in range(len(self.flows)):
            if i != current_index:
                flow_action = self.flows[i].get('action', '')
                if flow_action and not flow_action.startswith('跳转_') and flow_action != 'end':
                    display_name = f"流程{i+1} ({flow_action})"
                else:
                    display_name = f"流程{i+1}"
                combo.addItem(f"跳转到{display_name}", f"跳转_{i}")
        # 尝试恢复用户之前选中的 action
        if isinstance(select_action, str) and select_action.startswith('跳转_'):
            for ci in range(combo.count()):
                if combo.itemData(ci) == select_action:
                    combo.setCurrentIndex(ci)
                    break

    def load_execute_options(self, combo):
        combo.clear()
        if self._execute_options_cache is None:
            recordings_dir = get_recordings_path()
            cache = []
            try:
                if os.path.exists(recordings_dir):
                    folders = [d for d in os.listdir(recordings_dir)
                              if os.path.isdir(os.path.join(recordings_dir, d)) and d != 'trash']
                    cache = folders
            except Exception:
                pass
            self._execute_options_cache = cache
        for folder in self._execute_options_cache:
            combo.addItem(f"执行: {folder}", folder)

    def browse_image(self, index, is_else=False):
        recordings_path = get_recordings_path()
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"选择流程 {index + 1} 的条件图片", recordings_path,
            "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            for widget_data in self.flow_widgets:
                if widget_data.get('flow_index') == index and widget_data.get('is_else_branch') == is_else and 'image_preview' in widget_data:
                    image_preview = widget_data['image_preview']
                    self.load_image_to_preview(image_preview, file_path)
                    image_preview.image_path = file_path
                    image_preview.mousePressEvent = lambda event, path=file_path: self.view_condition_image_path(path) if path else None
                    if is_else:
                        self.flows[index]['else_branch']['condition_image'] = file_path
                    else:
                        self.flows[index]['condition_image'] = file_path
                    break

    def view_condition_image(self, image_edit):
        image_path = image_edit.text()
        if not image_path:
            StyledMessageDialog(self, title="提示", text="没有设置条件图片", msg_type="information", buttons="ok").exec_()
            return
        if not os.path.isabs(image_path):
            recordings_path = get_recordings_path()
            image_path = os.path.join(recordings_path, image_path)
        image_path = os.path.normpath(image_path)
        if not os.path.exists(image_path):
            StyledMessageDialog(self, title="警告", text=f"图片文件不存在:\n{image_path}", msg_type="warning", buttons="ok").exec_()
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("查看条件图片")
        dialog.setMinimumSize(300, 200)
        # 「删除确认」同款卡片骨架（左竖条+图标+标题）
        from beautiful_dialog import build_styled_card
        layout = build_styled_card(dialog, "查看条件图片", "camera")
        path_label = QLabel(f"路径: {image_path}")
        path_label.setStyleSheet(f"color: {T['text_secondary']}; font-size: 11px; padding: 5px;")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            StyledMessageDialog(self, title="警告", text="无法加载图片", msg_type="warning", buttons="ok").exec_()
            return
        screen = QApplication.primaryScreen().geometry()
        max_display_width = min(800, screen.width() - 100)
        max_display_height = min(600, screen.height() - 200)
        img_width = pixmap.width()
        img_height = pixmap.height()
        if img_width > max_display_width or img_height > max_display_height:
            scaled_pixmap = pixmap.scaled(max_display_width, max_display_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            display_width = scaled_pixmap.width()
            display_height = scaled_pixmap.height()
        else:
            scaled_pixmap = pixmap
            display_width = img_width
            display_height = img_height
        dialog.resize(display_width + 40, display_height + 100)
        image_label = QLabel()
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        dialog.exec_()

    def load_image_to_preview(self, image_preview, image_path):
        """【性能优化】异步 + 全局缓存加载图片缩略图，避免同步IO卡顿"""
        from PyQt5.QtCore import QThread, pyqtSignal

        if not image_path:
            image_preview.clear()
            return
        if not os.path.exists(image_path):
            # 路径给了但文件不在（含被移动/删除）：明确"未找到"，不静默清空
            self._mark_preview_missing(image_preview)
            return

        # 命中缩略图缓存 → 直接用（CPU 0开销）
        cache_key = (image_path, os.path.getmtime(image_path) if os.path.exists(image_path) else 0)
        if hasattr(ComboSkillEditDialog, '_thumb_cache') and cache_key in ComboSkillEditDialog._thumb_cache:
            image_preview.setPixmap(ComboSkillEditDialog._thumb_cache[cache_key])
            return

        # 还没缓存就先给一个占位（UI立刻可用，不阻塞打开）
        image_preview.setText("")
        image_preview.setStyleSheet("border: none; background: transparent; color: #8E8E93;")

        # 懒初始化全局缓存（类级别，多个对话框间也能共享）
        if not hasattr(ComboSkillEditDialog, '_thumb_cache'):
            ComboSkillEditDialog._thumb_cache = {}
        if not hasattr(ComboSkillEditDialog, '_thumb_workers'):
            ComboSkillEditDialog._thumb_workers = {}

        # 已经在加载了 → 把新的 image_preview 追加到等待队列，加载完统一更新
        if cache_key in ComboSkillEditDialog._thumb_workers:
            ComboSkillEditDialog._thumb_workers[cache_key]['previews'].append(image_preview)
            return

        # 子线程加载（IO + 解码 + 缩放都在后台做，不卡UI）
        class _ThumbLoader(QThread):
            done = pyqtSignal(object, object)  # cache_key, QImage(或None)

            def run(self2):
                # ★ 严禁在此处创建 QPixmap！
                #   QPixmap 是 GUI 资源（背后绑定 QPlatformPixmap/原生位图句柄），Qt 明确规定
                #   只能在 GUI 线程创建与使用。在非 GUI 线程里 QPixmap(image_path) 属未定义行为：
                #   Windows 上与主线程的位图缓存锁发生竞争，典型症状就是界面冻结/未响应
                #   （进程还活着、日志照常，但窗口画不出来），也可能直接访问冲突崩溃。
                #   正解：子线程用 QImage（线程安全的隐式共享值类型）解码并缩放，
                #        回到主线程后再 QPixmap.fromImage() 转成 GUI 资源。
                try:
                    img = QImage(image_path)
                    if not img.isNull():
                        img = img.scaled(60, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    else:
                        img = None
                except Exception:
                    img = None
                self2.done.emit(cache_key, img)

        worker = _ThumbLoader()
        ComboSkillEditDialog._thumb_workers[cache_key] = {
            'worker': worker,
            'previews': [image_preview]
        }

        def _on_done(cache_key2, loaded_image):
            # ★ 本回调经信号队列回到 GUI 线程执行（ worker.done 在主线程 connect ，
            #   PyQt 把跨线程连接自动降级为 QueuedConnection ），因此这里是唯一
            #   允许把 QImage 转成 QPixmap 的位置。
            info = ComboSkillEditDialog._thumb_workers.pop(cache_key2, None)
            if not info:
                return
            scaled_pixmap = None
            if loaded_image is not None and not loaded_image.isNull():
                try:
                    scaled_pixmap = QPixmap.fromImage(loaded_image)
                except Exception:
                    scaled_pixmap = None
            if scaled_pixmap is not None:
                ComboSkillEditDialog._thumb_cache[cache_key2] = scaled_pixmap
                for pv in info['previews']:
                    try:
                        pv.setStyleSheet("background: #FFFFFF; border: 1px solid #E5E5EA; border-radius: 6px;")
                        pv.setText("")
                        pv.setPixmap(scaled_pixmap)
                    except Exception:
                        pass
            else:
                # 加载失败：干净占位（不漂小 error 图标在 70x46 容器里像被切）
                for pv in info['previews']:
                    try:
                        pv.setStyleSheet(
                            "color: #8E8E93; font-size: 11px; "
                            "background-color: #F5F5F7; border: 1px dashed #D1D1D6; border-radius: 6px;"
                        )
                        pv.setText("加载失败")
                    except Exception:
                        pass

        worker.done.connect(_on_done)
        worker.start()

    def view_condition_image_path(self, image_path):
        if not image_path:
            StyledMessageDialog(self, title="提示", text="没有设置条件图片", msg_type="information", buttons="ok").exec_()
            return
        if not os.path.isabs(image_path):
            recordings_path = get_recordings_path()
            image_path = os.path.join(recordings_path, image_path)
        image_path = os.path.normpath(image_path)
        if not os.path.exists(image_path):
            StyledMessageDialog(self, title="警告", text=f"图片文件不存在:\n{image_path}", msg_type="warning", buttons="ok").exec_()
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("查看条件图片")
        dialog.setMinimumSize(300, 200)
        # 「删除确认」同款卡片骨架（左竖条+图标+标题）
        from beautiful_dialog import build_styled_card
        layout = build_styled_card(dialog, "查看条件图片", "camera")
        path_label = QLabel(f"路径: {image_path}")
        path_label.setStyleSheet(f"color: {T['text_secondary']}; font-size: 11px; padding: 5px;")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            StyledMessageDialog(self, title="警告", text="无法加载图片", msg_type="warning", buttons="ok").exec_()
            return
        screen = QApplication.primaryScreen().geometry()
        max_display_width = min(800, screen.width() - 100)
        max_display_height = min(600, screen.height() - 200)
        img_width = pixmap.width()
        img_height = pixmap.height()
        if img_width > max_display_width or img_height > max_display_height:
            scaled_pixmap = pixmap.scaled(max_display_width, max_display_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            display_width = scaled_pixmap.width()
            display_height = scaled_pixmap.height()
        else:
            scaled_pixmap = pixmap
            display_width = img_width
            display_height = img_height
        dialog.resize(display_width + 40, display_height + 100)
        image_label = QLabel()
        image_label.setPixmap(scaled_pixmap)
        image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(image_label)
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        dialog.exec_()

    def add_flow(self):
        """【性能优化】增量追加最后一行，不再全量重建"""
        new_index = len(self.flows)
        self.flows.append({
            'condition': 'always',
            'condition_image': '',
            'action': '',
            'else_branch': None,
            '_visible': True
        })

        # 冻结 + 批处理，避免闪烁
        self.tree_widget.setUpdatesEnabled(False)
        self.tree_widget.blockSignals(True)
        try:
            flow_data = self.flows[new_index]
            main_item = QTreeWidgetItem(self.tree_widget)
            main_item.setText(0, "")
            main_item.setText(1, "")
            main_item.setText(2, "")
            main_item.setData(0, Qt.UserRole, {'index': new_index, 'is_else': False})
            self.create_flow_item_widgets(main_item, new_index, flow_data, is_else=False)
        finally:
            self.tree_widget.blockSignals(False)
            self.tree_widget.setUpdatesEnabled(True)

        # 滚动到最后一行并选中
        if self.tree_widget.topLevelItemCount() > 0:
            last_item = self.tree_widget.topLevelItem(self.tree_widget.topLevelItemCount() - 1)
            self.tree_widget.setCurrentItem(last_item)
            self.tree_widget.scrollToItem(last_item)

    def _refresh_flow_numbers_after_change(self, preserve_index=None):
        """【性能优化】删除/交换流程后，只刷新序号、重新绑定回调、修正 UserRole；不再 build_flow_tree() 全量重建"""
        self.tree_widget.setUpdatesEnabled(False)
        self.tree_widget.blockSignals(True)
        try:
            # 1. 重排 flow_widgets 的 flow_index 绑定（原 build 时存的 index 已过期）
            for wd in self.flow_widgets:
                wd['flow_index'] = None  # 先清空，等下重新匹配
            # 2. 遍历 Tree 中的每一个顶行，重设 UserRole 和编号标签
            for row in range(self.tree_widget.topLevelItemCount()):
                main_item = self.tree_widget.topLevelItem(row)
                # --- 重新设置主步骤的 UserRole（flow_index 可能已经变了）---
                main_item.setData(0, Qt.UserRole, {'index': row, 'is_else': False})
                # 找第 0 列 condition_widget 里的编号标签，改成新序号 row+1
                cond_widget = self.tree_widget.itemWidget(main_item, 0)
                if cond_widget is not None:
                    # 找第一个 label：要么是数字（主步骤）要么是 └（else分支）
                    for child_idx in range(cond_widget.layout().count()):
                        w = cond_widget.layout().itemAt(child_idx).widget()
                        if isinstance(w, QLabel) and w.text().strip().isdigit():
                            w.setText(f"{row + 1}")
                            break
                # 重新把 flow_widgets 里对应旧 index 的绑定改成新 index
                # flow_widgets 里每个都存了 condition_combo 等引用，我们找主步骤编号匹配的
                # 这里用一个简单办法：遍历 flow_widgets 找 'is_else_branch'=False 且 序号未分配 的，
                # 按 Tree 顺序重新分配 index
                for wd in self.flow_widgets:
                    if wd.get('is_else_branch') is False and wd.get('flow_index') is None:
                        if wd.get('__row') == row:
                            continue
                        # 用 layout 第 0 列 widget 身份匹配（同一个 cond_widget 就是它）
                        wd_cond_widget = wd.get('condition_widget')
                        if wd_cond_widget is cond_widget:
                            wd['flow_index'] = row
                            # 3. 重新绑定当前 onChange 回调，让 index 参数是新序号（关键！）
                            c_combo = wd.get('condition_combo')
                            a_type = wd.get('action_type_combo')
                            a_detail = wd.get('action_detail_combo')
                            w_spin = wd.get('wait_time_spin')
                            else_btn = wd.get('else_btn')
                            img_btn = wd.get('img_btn')
                            img_pv = wd.get('image_preview')
                            if c_combo is not None:
                                try:
                                    c_combo.currentIndexChanged.disconnect()
                                except Exception:
                                    pass
                                c_combo.currentIndexChanged.connect(lambda idx, i=row: self.on_condition_changed(i, idx))
                            if w_spin is not None:
                                try:
                                    w_spin.valueChanged.disconnect()
                                except Exception:
                                    pass
                                w_spin.valueChanged.connect(lambda val, i=row, ie=False: self.on_wait_time_changed(i, val, ie))
                            if a_type is not None and a_detail is not None:
                                try:
                                    a_type.currentIndexChanged.disconnect()
                                except Exception:
                                    pass
                                a_type.currentIndexChanged.connect(
                                    lambda idx, i=row, t=a_type, d=a_detail, ie=False:
                                        self.on_action_type_changed(i, t, d, ie)
                                )
                            if else_btn is not None:
                                try:
                                    else_btn.clicked.disconnect()
                                except Exception:
                                    pass
                                else_btn.clicked.connect(lambda checked, i=row: self.add_else_branch(i))
                            if img_btn is not None:
                                try:
                                    img_btn.clicked.disconnect()
                                except Exception:
                                    pass
                                img_btn.clicked.connect(lambda checked, i=row, ie=False: self.browse_image(i, ie))
                            if img_pv is not None:
                                try:
                                    img_pv.mousePressEvent = (
                                        lambda event, path=img_pv.property('image_path'):
                                            self.view_condition_image_path(path) if path else None
                                    )
                                except Exception:
                                    pass
                            # 详情 combo 重新绑定
                            if a_detail is not None:
                                try:
                                    a_detail.currentIndexChanged.disconnect()
                                except Exception:
                                    pass
                                a_detail.currentIndexChanged.connect(
                                    lambda idx, i=row, ie=False, dc=a_detail, tc=a_type:
                                        self.on_action_detail_changed(i, ie, dc, tc)
                                )
                            break

                # --- else 分支的 UserRole 也顺带刷新 ---
                for child_row in range(main_item.childCount()):
                    child_item = main_item.child(child_row)
                    child_item.setData(0, Qt.UserRole, {'index': row, 'is_else': True})
                    # 给 else 分支的 widget 也重绑回调
                    child_cond_widget = self.tree_widget.itemWidget(child_item, 0)
                    for wd in self.flow_widgets:
                        if wd.get('is_else_branch') is True and wd.get('flow_index') is None:
                            if wd.get('condition_widget') is child_cond_widget:
                                wd['flow_index'] = row
                                ec_combo = wd.get('condition_combo')
                                ew_spin = wd.get('wait_time_spin')
                                ea_type = wd.get('action_type_combo')
                                ea_detail = wd.get('action_detail_combo')
                                edel_btn = wd.get('del_else_btn')
                                eimg_btn = wd.get('img_btn')
                                if ec_combo is not None:
                                    try:
                                        ec_combo.currentIndexChanged.disconnect()
                                    except Exception:
                                        pass
                                    ec_combo.currentIndexChanged.connect(lambda idx, i=row: self.on_else_condition_changed(i, idx))
                                if ew_spin is not None:
                                    try:
                                        ew_spin.valueChanged.disconnect()
                                    except Exception:
                                        pass
                                    ew_spin.valueChanged.connect(lambda val, i=row, ie=True: self.on_wait_time_changed(i, val, ie))
                                if ea_type is not None and ea_detail is not None:
                                    try:
                                        ea_type.currentIndexChanged.disconnect()
                                    except Exception:
                                        pass
                                    ea_type.currentIndexChanged.connect(
                                        lambda idx, i=row, t=ea_type, d=ea_detail, ie=True:
                                            self.on_action_type_changed(i, t, d, ie)
                                    )
                                if edel_btn is not None:
                                    try:
                                        edel_btn.clicked.disconnect()
                                    except Exception:
                                        pass
                                    edel_btn.clicked.connect(lambda checked, i=row: self.delete_else_branch(i))
                                if eimg_btn is not None:
                                    try:
                                        eimg_btn.clicked.disconnect()
                                    except Exception:
                                        pass
                                    eimg_btn.clicked.connect(lambda checked, i=row, ie=True: self.browse_image(i, ie))
                                if ea_detail is not None:
                                    try:
                                        ea_detail.currentIndexChanged.disconnect()
                                    except Exception:
                                        pass
                                    ea_detail.currentIndexChanged.connect(
                                        lambda idx, i=row, ie=True, dc=ea_detail, tc=ea_type:
                                            self.on_action_detail_changed(i, ie, dc, tc)
                                    )
                                break

            # 刷新 action_detail_combo 里"跳转_N"的选项（因为序号变了）
            for wd in self.flow_widgets:
                at = wd.get('action_type_combo')
                ad = wd.get('action_detail_combo')
                if at is not None and ad is not None and at.currentData() == 'goto':
                    cur_idx = wd.get('flow_index')
                    if cur_idx is not None:
                        saved_action = None
                        if wd.get('is_else_branch'):
                            if self.flows[cur_idx].get('else_branch'):
                                saved_action = self.flows[cur_idx]['else_branch'].get('action', '')
                        else:
                            saved_action = self.flows[cur_idx].get('action', '')
                        self.load_goto_options(ad, cur_idx, select_action=saved_action)

            # 如果传了要保留选中的 index，这里重新选中
            if preserve_index is not None and 0 <= preserve_index < self.tree_widget.topLevelItemCount():
                self.tree_widget.setCurrentItem(self.tree_widget.topLevelItem(preserve_index))

        finally:
            self.tree_widget.blockSignals(False)
            self.tree_widget.setUpdatesEnabled(True)

    def _mark_flow_widgets_before_mutate(self):
        """【性能优化】在删除/交换之前，给 flow_widgets 打一个临时标记（__row=当前在Tree中的行号），
        方便 mutation 之后按新顺序重新匹配 flow_index，不用 build_flow_tree()"""
        for row in range(self.tree_widget.topLevelItemCount()):
            main_item = self.tree_widget.topLevelItem(row)
            cond = self.tree_widget.itemWidget(main_item, 0)
            for wd in self.flow_widgets:
                if not wd.get('is_else_branch') and wd.get('condition_widget') is cond:
                    wd['__row'] = row
                    break
            for cr in range(main_item.childCount()):
                child = main_item.child(cr)
                cw = self.tree_widget.itemWidget(child, 0)
                for wd in self.flow_widgets:
                    if wd.get('is_else_branch') and wd.get('condition_widget') is cw:
                        wd['__row_child'] = (row, cr)
                        break

    def delete_flow(self):
        """【性能优化】增量删除：只拿走 Tree 里对应行，再刷新序号；不再全部重建"""
        if len(self.flows) <= 1:
            StyledMessageDialog(self, title="提示", text="至少保留一个流程", msg_type="information", buttons="ok").exec_()
            return
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            StyledMessageDialog(self, title="提示", text="请先选择要删除的流程", msg_type="warning", buttons="ok").exec_()
            return
        flow_index = self.get_flow_index_from_item(current_item)
        if flow_index is None:
            StyledMessageDialog(self, title="提示", text="请选择主流程进行删除（不能删除Else分支）", msg_type="warning", buttons="ok").exec_()
            return

        # 1) 删 flow_data
        del self.flows[flow_index]

        # 2) 删除 Tree 中这一整行（含 else child）
        self.tree_widget.setUpdatesEnabled(False)
        self.tree_widget.blockSignals(True)
        try:
            # 把 flow_widgets 中属于这行的也移除
            remove_set = []
            for wd in self.flow_widgets:
                cond_w = wd.get('condition_widget')
                match_row = False
                # 扫描 Tree，看这个 widget 是否在 flow_index 那一行（或其子行 else）
                item_to_remove = self.tree_widget.topLevelItem(flow_index)
                main_cond = self.tree_widget.itemWidget(item_to_remove, 0)
                if wd.get('condition_widget') is main_cond:
                    match_row = True
                else:
                    for cr in range(item_to_remove.childCount()):
                        c_item = item_to_remove.child(cr)
                        if wd.get('condition_widget') is self.tree_widget.itemWidget(c_item, 0):
                            match_row = True
                            break
                if match_row:
                    remove_set.append(wd)
            for wd in remove_set:
                # 手动释放 widget 引用（clear会做），防止 flow_widgets 残留
                self.flow_widgets.remove(wd)

            self.tree_widget.takeTopLevelItem(flow_index)  # 只删掉这一行
        finally:
            self.tree_widget.blockSignals(False)
            self.tree_widget.setUpdatesEnabled(True)

        # 3) 只刷新剩下行的序号 + 回调绑定（性能 10x，无需全量重建 widget）
        self._mark_flow_widgets_before_mutate()
        target_sel = max(0, flow_index - 1)
        self._refresh_flow_numbers_after_change(preserve_index=target_sel)

    def move_flow_up(self):
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return
        flow_index = self.get_flow_index_from_item(current_item)
        if flow_index is None or flow_index <= 0:
            return
        self.swap_flows(flow_index - 1, flow_index)
        # 选中用户刚上移的那个流程（它现在在 flow_index-1 位置）
        self.tree_widget.setCurrentIndex(self.tree_widget.model().index(flow_index - 1, 0))

    def move_flow_down(self):
        current_item = self.tree_widget.currentItem()
        if current_item is None:
            return
        flow_index = self.get_flow_index_from_item(current_item)
        if flow_index is None or flow_index >= len(self.flows) - 1:
            return
        self.swap_flows(flow_index, flow_index + 1)
        # 选中用户刚下移的那个流程（它现在在 flow_index+1 位置）
        self.tree_widget.setCurrentIndex(self.tree_widget.model().index(flow_index + 1, 0))

    def refresh_flow_widgets(self):
        self.build_flow_tree()

    def get_skill_data(self):
        name = self.name_input.text().strip()
        if not name:
            StyledMessageDialog(self, title="提示", text="请输入组合技名称", msg_type="warning", buttons="ok").exec_()
            return None

        all_flows = []
        for flow in self.flows:
            flow_copy = flow.copy()
            flow_copy.pop('_visible', None)
            if flow.get('else_branch'):
                flow_copy['else_branch'] = flow['else_branch'].copy()
            else:
                flow_copy.pop('else_branch', None)
            all_flows.append(flow_copy)

        if not all_flows:
            StyledMessageDialog(self, title="提示", text="请至少配置一个流程", msg_type="warning", buttons="ok").exec_()
            return None

        stop_shortcut = self.skill_data.get('stop_shortcut', '')
        note = self.note_text.toPlainText().strip() if hasattr(self, 'note_text') else self.skill_data.get('note', '')
        loop_count = self.loop_count_spin.value() if hasattr(self, 'loop_count_spin') else self.skill_data.get('loop_count', 1)
        skip_on_fail = self.skip_on_fail_check.isChecked() if hasattr(self, 'skip_on_fail_check') else self.skill_data.get('skip_on_fail', False)
        # step_interval: 录制流程内每个操作步骤之间的统一间隔（秒），None表示用系统默认(0.1秒)
        step_interval = self._get_effective_step_interval() if hasattr(self, 'step_interval_default_cb') \
            else self.skill_data.get('step_interval', None)
        # turbo_grace: 极速模式下图片出现等待窗口（秒），默认0.5
        turbo_grace = self.turbo_grace_spin.value() if hasattr(self, 'turbo_grace_spin') \
            else self.skill_data.get('turbo_grace', 0.5)
        # turbo_settle: 极速模式下点击后UI稳定等待（秒），默认0.08
        turbo_settle = self.turbo_settle_spin.value() / 1000.0 if hasattr(self, 'turbo_settle_spin') \
            else self.skill_data.get('turbo_settle', 0.08)

        result = {
            "name": name,
            "loop_type": "times",
            "loop_count": loop_count,
            "until_image": "",
            "flows": all_flows,
            "stop_shortcut": stop_shortcut,
            "note": note,
            "skip_on_fail": skip_on_fail,
            "turbo_grace": turbo_grace,
            "turbo_settle": turbo_settle,
        }
        # step_interval: None 表示默认，不存（省空间）；具体数值才保存
        if step_interval is not None:
            result["step_interval"] = step_interval
        return result