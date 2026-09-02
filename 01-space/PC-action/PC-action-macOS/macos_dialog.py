"""macOS 风格对话框：圆角白底 + 边框 + 右上角黄绿红三点点（自绘圆点）。

三个圆点的排布严格对齐主窗口 MacOSToolbar（app_macos.py:895-906）：
顺序 黄(最小化) → 绿(最大化) → 红(关闭)，16×16、间距 6、距右 18、距顶 16，
色值与 hover 色均取自 MacOSColors（#FFD60A/#34C759/#FF3B30）。

## 设计背景
旧 styles.apply_dialog_style 在 Windows 上不能正常工作：
- WA_TranslucentBackground + QSS background-color 是 Qt 著名坑：layered window
  下 QSS 不会自动渲染，主窗口内容会透到对话框里。
- 三个圆点用绝对定位 + eventFilter（QFrame 方案）→ Python GC 回收 eventFilter，
  圆点彻底失效，用户关不掉窗口（之前修过）。
- 改用 QPushButton 子控件 + border-radius 后，Windows 默认主题下 QPushButton
  的 border-radius 渲染异常，圆点变椭圆/胶囊。

## 本类做法
- 用 QSS 圆角白底 + 1px 边框（系统正常绘制，非 layered window）
- 三个圆点用 paintEvent + QPainter.drawEllipse 自绘（完全可控的圆形）
- mousePressEvent 用坐标命中测试判断点中了哪个圆点 → 触发关闭/最小化/最大化
- mouseMoveEvent 支持无边框窗口拖拽 + hover 高亮（setMouseTracking）
- 子控件（QLabel/QDoubleSpinBox/QPushButton 确定取消等）由 super().paintEvent
  照常绘制，不影响

用法：
    from macos_dialog import MacOSDialog
    dialog = MacOSDialog(self)
    dialog.setWindowTitle("...")
    layout = QVBoxLayout()
    ...
    dialog.setLayout(layout)        # 自动套用内容 margin（顶部留 38px 给圆点）
    dialog.adjustSize()
    dialog.exec_()

不要 setWindowFlags、不要调 apply_dialog_style —— MacOSDialog 内部已配好。
"""
from PyQt5.QtCore import Qt, QPoint, QRect, QRectF
from PyQt5.QtGui import QPainter, QColor, QPainterPath
from PyQt5.QtWidgets import QDialog, QLayout


# 三个圆点的颜色定义
# 与主窗口 MacOSToolbar（app_macos.py:895-906）保持完全一致：
# 顺序从左到右是 黄(最小化) → 绿(最大化) → 红(关闭)，色值取 MacOSColors 常量。
_DOT_COLORS = [
    # (常态色, hover色, 动作名)
    ("#FFD60A", "#FFBD3A", "minimize"),   # 黄 - 最小化
    ("#34C759", "#28C840", "maximize"),   # 绿 - 最大化
    ("#FF3B30", "#FF6B5E", "close"),      # 红 - 关闭
]


class MacOSDialog(QDialog):
    """macOS 风格对话框：QSS 圆角白底 + 边框 + 左上角自绘红黄绿三点点。"""

    # 内容区 margin（left, top, right, bottom）
    # 圆点在右上角 → 左侧不再需要让位，left 收回与 right 对称
    # top=38 给圆点让位（16 距顶 + 16 直径 + 6 余量）
    CONTENT_MARGIN = (22, 38, 22, 22)
    CONTENT_SPACING = 14

    # 圆点几何参数 —— 对齐主窗口 MacOSToolbar（16×16 / spacing 6 / margin 18）
    DOT_DIAMETER = 16                # 直径（主窗口 setFixedSize(16,16)）
    DOT_RIGHT_PADDING = 18           # 距右（主窗口 layout margin 18）
    DOT_TOP_PADDING = 16             # 距顶（主窗口 48 高工具栏里 16 圆点居中 = 16）
    DOT_GAP = 6                      # 圆点间距（主窗口 controls_layout spacing 6）
    DOT_HIT_PADDING = 4              # 命中区域外扩，让点击更宽容

    # 圆角矩形半径
    RADIUS = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        # 窗口标志：无系统标题栏 + 置顶 + Dialog
        self.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        # 用 QSS 圆角 + 边框 + 白底。注意：不要 WA_TranslucentBackground，
        # 否则会变 layered window，QSS 在 Windows 上失效（透出主窗口）。
        self.setObjectName("MacOSDialog")
        self.setStyleSheet(f"""
            QDialog#MacOSDialog {{
                background-color: #FFFFFF;
                border: 1px solid #D0D4DA;
                border-radius: {self.RADIUS}px;
            }}
        """)

        # 拖拽状态
        self._dragging = False
        self._drag_offset = QPoint()

        # hover 状态：当前鼠标悬停在第几个圆点上（-1 = 没有）
        self._hover_dot = -1
        self.setMouseTracking(True)   # 不按下鼠标也要收到 mouseMoveEvent

        # 三个圆点的几何信息（paintEvent 和 鼠标事件都用）
        self._dot_rects = []   # 三个 QRect，从左到右：红、黄、绿
        self._last_dot_width = -1  # 上次算 dot_rects 时的 self.width()
        # 注意：不要在这里调 _refresh_dot_rects —— 此时 self.width() 还是
        # QDialog 默认的 ~640，会算出错的圆点 x。setFixedWidth/setLayout/
        # adjustSize 之后，showEvent 会触发首次重算。

    # ---------------- paintEvent 自绘 ----------------

    def paintEvent(self, event):
        """自绘三个圆点。子控件（QLabel/SpinBox/确定取消按钮等）由
        super().paintEvent 照常绘制。QSS 已画了圆角白底和边框。"""
        # 确保圆点位置用最新 self.width() 算（之前 __init__ 时算的 width 已过期）
        self._refresh_dot_rects()

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        # 三个圆点（右上角，从左到右：黄、绿、红）；hover 时切到高亮色，
        # 与主窗口 QFrame:hover 表现一致。
        for idx, (dot_rect, (normal, hover, _action)) in enumerate(
                zip(self._dot_rects, _DOT_COLORS)):
            p.setBrush(QColor(hover if idx == self._hover_dot else normal))
            p.setPen(Qt.NoPen)
            p.drawEllipse(dot_rect)

        p.end()

        # 子控件自己画（QLabel/SpinBox/确定取消按钮等）
        super().paintEvent(event)

    # ---------------- 三个圆点几何 ----------------

    def _refresh_dot_rects(self):
        """根据当前窗口尺寸计算三个圆点的位置。从左到右：黄、绿、红（同主窗口）。
        仅在 self.width() 变化时重算（性能优化，避免 paintEvent 每次都算）。"""
        if self._last_dot_width == self.width() and self._dot_rects:
            return
        self._last_dot_width = self.width()

        # 三个圆点（右上角，从左到右：黄、绿、红 —— 与主窗口一致）
        # 总宽 = 3*直径 + 2*间距，从右边反推起点 x
        total_width = self.DOT_DIAMETER * 3 + self.DOT_GAP * 2
        start_x = self.width() - self.DOT_RIGHT_PADDING - total_width
        step = self.DOT_DIAMETER + self.DOT_GAP

        self._dot_rects = [
            QRect(start_x + i * step, self.DOT_TOP_PADDING,
                  self.DOT_DIAMETER, self.DOT_DIAMETER)
            for i in range(3)
        ]

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._last_dot_width = -1  # 强制 _refresh_dot_rects 在下次 paint 重算
        self._refresh_dot_rects()

    def showEvent(self, event):
        super().showEvent(event)
        self._last_dot_width = -1  # 首次 show 时 width 才是真实值
        self._refresh_dot_rects()

    # ---------------- 鼠标事件：圆点点击 + 拖拽 ----------------

    def _hit_dot(self, pos):
        """判断鼠标位置点中了哪个圆点，返回动作名或 None。"""
        for idx, dot_rect in enumerate(self._dot_rects):
            hit = dot_rect.adjusted(
                -self.DOT_HIT_PADDING, -self.DOT_HIT_PADDING,
                self.DOT_HIT_PADDING, self.DOT_HIT_PADDING
            )
            if hit.contains(pos):
                return _DOT_COLORS[idx][2]
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            action = self._hit_dot(event.pos())
            if action == "close":
                self.close()
                return
            elif action == "minimize":
                self.showMinimized()
                return
            elif action == "maximize":
                if self.isMaximized():
                    self.showNormal()
                else:
                    self.showMaximized()
                return
            # 没点中圆点 → 进入拖拽模式
            self._dragging = True
            self._drag_offset = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging and (event.buttons() & Qt.LeftButton):
            self.move(event.globalPos() - self._drag_offset)
            event.accept()
            return
        # 非拖拽时追踪 hover，让圆点变色（对齐主窗口 QFrame:hover）
        hovered = -1
        for idx, dot_rect in enumerate(self._dot_rects):
            hit = dot_rect.adjusted(
                -self.DOT_HIT_PADDING, -self.DOT_HIT_PADDING,
                self.DOT_HIT_PADDING, self.DOT_HIT_PADDING
            )
            if hit.contains(event.pos()):
                hovered = idx
                break
        if hovered != self._hover_dot:
            self._hover_dot = hovered
            self.update()   # 触发 paintEvent 重绘
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """鼠标移出对话框 → 清掉 hover 高亮。"""
        if self._hover_dot != -1:
            self._hover_dot = -1
            self.update()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    # ---------------- 接管 setLayout ----------------

    def setLayout(self, layout):
        """统一应用内容 margin（顶部 30 给圆点让位）和 spacing。"""
        if layout is not None and isinstance(layout, QLayout):
            try:
                layout.setContentsMargins(*self.CONTENT_MARGIN)
                layout.setSpacing(self.CONTENT_SPACING)
            except Exception:
                pass
        super().setLayout(layout)