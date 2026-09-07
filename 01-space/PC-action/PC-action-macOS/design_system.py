"""macOS Design System - Based on Apple Human Interface Guidelines"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPainter
from PyQt5.QtWidgets import QStyle, QStyledItemDelegate

class TypographySystem:
    """macOS 瀛椾綋绯荤粺"""
    FONT_FAMILY = '"Microsoft YaHei", "Microsoft YaHei", "Segoe UI Emoji", sans-serif' if sys.platform=="win32" else '-apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", "Apple Color Emoji", "Helvetica Neue", sans-serif'
    FONT_FAMILY_MONO = '"SF Mono", Menlo, Monaco, Consolas, monospace'
    WEIGHT_REGULAR=400;WEIGHT_MEDIUM=500;WEIGHT_SEMIBOLD=600;WEIGHT_BOLD=700
    BASE_SIZE=13;SIZE_XS=11;SIZE_SM=12;SIZE_BASE=13;SIZE_MD=14;SIZE_LG=16;SIZE_XL=20;SIZE_2XL=24;SIZE_3XL=28
    LINE_HEIGHT_TIGHT=1.2;LINE_HEIGHT_BASE=1.47059;LINE_HEIGHT_LOOSE=1.6

class SpacingSystem:
    UNIT=4;XS=4;SM=8;MD=12;LG=16;XL=20;XXL=24;XXXL=32

class BorderRadiusSystem:
    NONE=0;XS=6;SM=8;MD=10;LG=12;XL=16;XXL=20;FULL=999

class ButtonSize:
    HEIGHT_SMALL=26;HEIGHT_MEDIUM=30;HEIGHT_REGULAR=34;HEIGHT_LARGE=40;HEIGHT_XL=48
    MIN_WIDTH_SMALL=56;MIN_WIDTH_MEDIUM=68;MIN_WIDTH_REGULAR=80;MIN_WIDTH_LARGE=100;MIN_WIDTH_XL=130
    PADDING_H_SMALL=10;PADDING_H_REGULAR=12;PADDING_H_LARGE=20

class ColorPalette:
    PRIMARY="#5A6069";PRIMARY_HOVER="#474C54";PRIMARY_ACTIVE="#474C54";PRIMARY_BG="#EDEEF0"
    SUCCESS="#34C759";SUCCESS_BG="#E8F9ED";WARNING="#FF9500";WARNING_BG="#FFF4E5"
    ERROR="#FF3B30";ERROR_BG="#FFE5E5";INFO="#5AC8FA";INFO_BG="#E8F7FC"
    GRAY_50="#FBFBFD";GRAY_100="#F5F5F7";GRAY_200="#E8E8ED";GRAY_300="#D1D1D6";GRAY_400="#AEAEB2"
    GRAY_500="#86868B";GRAY_600="#6E6E73";GRAY_700="#48484A";GRAY_800="#3A3A3C";GRAY_900="#1D1D1F"
    BG_MAIN="#F5F5F7";BG_CARD="#FFFFFF";BG_SIDEBAR="#F5F5F7";BG_TOOLBAR="#FFFFFF";BG_HOVER="#F0F0F2"
    TEXT_PRIMARY="#1D1D1F";TEXT_SECONDARY="#86868B";TEXT_MUTED="#AEAEB2";TEXT_DISABLED="#D1D1D6"
    BORDER_LIGHT="#E8E8ED";BORDER_DEFAULT="#D1D1D6";BORDER_STRONG="#AEAEB2";SEPARATOR="#E8E8ED"
    SYSTEM_RED="#FF3B30";SYSTEM_ORANGE="#FF9500";SYSTEM_YELLOW="#FFCC00";SYSTEM_GREEN="#34C759"
    SYSTEM_MINT="#00C7BE";SYSTEM_TEAL="#5AC8FA";SYSTEM_BLUE="#5A6069";SYSTEM_INDIGO="#5856D6"
    SYSTEM_PURPLE="#AF52DE";SYSTEM_PINK="#FF2D55";SYSTEM_BROWN="#A2845E"

class ShadowSystem:
    SHADOW_SM="0 1px 3px rgba(0,0,0,0.08)";SHADOW_MD="0 4px 12px rgba(0,0,0,0.1)";SHADOW_LG="0 8px 24px rgba(0,0,0,0.12)"
    SHADOW_PRIMARY="0 2px 8px rgba(90,96,105,0.2)"

class AnimationTokens:
    DURATION_FAST=100;DURATION_NORMAL=200;DURATION_SLOW=300
    EASING_STANDARD="cubic-bezier(0.4,0,0.2,1)";EASING_OUT="cubic-bezier(0,0,0.2,1)"

THEME_PRIMARY=ColorPalette.PRIMARY;THEME_SECONDARY=ColorPalette.INFO;THEME_ACCENT=ColorPalette.PRIMARY
THEME_BG=ColorPalette.BG_MAIN;THEME_CARD=ColorPalette.BG_CARD;THEME_TEXT=ColorPalette.TEXT_PRIMARY
THEME_MUTED=ColorPalette.TEXT_SECONDARY;THEME_BORDER=ColorPalette.BORDER_DEFAULT
MACOS_FONT_STACK=TypographySystem.FONT_FAMILY
TYPOGRAPHY=TypographySystem();SPACING=SpacingSystem();BORDER_RADIUS=BorderRadiusSystem()
COLORS=ColorPalette()

def get_table_stylesheet(bg_color=ColorPalette.BG_CARD,header_bg=ColorPalette.BG_CARD,header_color=ColorPalette.TEXT_SECONDARY,text_color=ColorPalette.TEXT_PRIMARY,border_color=ColorPalette.SEPARATOR,hover_color=ColorPalette.BG_HOVER,selected_color="#E8F0FE",alternate_color="#F5F5F5",border_radius=12,header_font_size=12,cell_font_size=14,cell_padding_v=12,cell_padding_h=16,row_height=48):
    return f"""
        QTableWidget {{
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
            background: {bg_color};
            outline: none;
            gridline-color: transparent;
            font-size: {cell_font_size}px;
            font-family: "Microsoft YaHei", "Segoe UI Emoji", sans-serif;
        }}
        QTableWidget::item {{
            font-weight: 500;
            padding: {cell_padding_v}px {cell_padding_h}px;
            border-bottom: 1px solid rgba(0,0,0,0.05);
            color: {text_color};
            min-height: {row_height-cell_padding_v*2}px;
        }}
        QTableWidget::item:hover {{ background: {hover_color} }}
        QTableWidget::item:selected {{ background: {selected_color}; color: {text_color}; }}
        QTableWidget::item:alternate {{ background: {alternate_color}; }}
        QTableWidget:focus {{ border: 1px solid {border_color}; outline: none; }}
        QHeaderView::section {{
            background: {header_bg};
            color: {header_color};
            padding: {max(cell_padding_v-2,8)}px {cell_padding_h}px;
            border: none;
            border-right: 1px solid {border_color};
            border-bottom: 1px solid {border_color};
            font-weight: 700;
            font-size: {header_font_size}px;
            font-family: "Microsoft YaHei", "Segoe UI Emoji", sans-serif;
        }}
        QHeaderView::section:first {{ border-top-left-radius: {border_radius}px; }}
        QHeaderView::section:last {{
            border-right: none;
            border-top-right-radius: {border_radius}px;
        }}
        QScrollBar:vertical {{ width: 8px; background: transparent; border-radius: 4px; }}
        QScrollBar::handle:vertical {{ background: {ColorPalette.GRAY_300}; border-radius: 4px; min-height: 20px; }}
        QScrollBar::handle:vertical:hover {{ background: {ColorPalette.GRAY_400}; }}
        QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}
        QScrollBar:horizontal {{ height: 8px; background: transparent; border-radius: 4px; }}
        QScrollBar::handle:horizontal {{ background: {ColorPalette.GRAY_300}; border-radius: 4px; min-width: 20px; }}
        QScrollBar::handle:horizontal:hover {{ background: {ColorPalette.GRAY_400}; }}
        QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal {{ width: 0px; background: transparent; }}
    """

def configure_table(table,style=None):
    from PyQt5.QtWidgets import QAbstractItemView,QHeaderView
    if style is None: style=get_table_stylesheet()
    table.setStyleSheet(style)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    # 选中行时表头不再自动变粗（Qt 默认会加粗高亮被选中列的表头）
    table.horizontalHeader().setHighlightSections(False)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)


def flat_button_style(variant="neutral", radius=6, font_size=13, padding="6px 14px"):
    """统一扁平按钮样式：无边框、无阴影、统一圆角/内边距、语义化配色。

    variant:
      'primary' 主操作（强调色填充，白字）
      'neutral' 次要操作（浅灰底，深字）
      'danger'  危险操作（红底，白字）
    用法：btn.setStyleSheet(flat_button_style('primary'))
    """
    conf = {
        # bg, fg, hover, pressed
        "primary": ("#5A6069", "#FFFFFF", "#474C54", "#3F434A"),
        "neutral": ("#F2F3F5", "#1D1D1F", "#E8EAED", "#DEE0E4"),
        "danger":  ("#FF3B30", "#FFFFFF", "#E0352B", "#C92E25"),
    }
    bg, fg, hover, pressed = conf.get(variant, conf["neutral"])
    font = TypographySystem.FONT_FAMILY
    return f"""
        QPushButton {{
            background-color: {bg};
            color: {fg};
            border: none;
            border-radius: {radius}px;
            padding: {padding};
            font-size: {font_size}px;
            font-weight: 600;
            font-family: {font};
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:pressed {{ background-color: {pressed}; padding-top: 1px; }}
        QPushButton:disabled {{ background-color: {ColorPalette.GRAY_200}; color: {ColorPalette.TEXT_MUTED}; }}
    """

SHADOWS=ShadowSystem()
ANIMATIONS=AnimationTokens()


# ==================== Soft UI 大圆角卡片表格（风格10） ====================

class SoftCardDelegate(QStyledItemDelegate):
    """软 UI 风格委托：把每个单元格画成浅灰底上的白色圆角卡片。

    行与行之间通过上下留缝露出灰底，形成"每行一张小卡片"的观感；
    悬浮淡蓝、选中浅蓝；文本颜色/对齐/字体仍尊重 item 的 ForegroundRole /
    TextAlignmentRole / FontRole，功能行为（点击、右键）不受影响。
    """

    BASE_COLOR = "#F5F7FB"      # 表格灰底
    CARD_COLOR = "#FFFFFF"      # 卡片白
    HOVER_COLOR = "#F8FAFF"     # 悬浮
    SELECTED_COLOR = "#E8F0FE"  # 选中
    TEXT_FALLBACK = "#4A5568"

    def __init__(self, radius=10, h_margin=6, v_margin=3, parent=None):
        super().__init__(parent)
        self._radius = radius
        self._hm = h_margin
        self._vm = v_margin

    def paint(self, painter, option, index):
        from PyQt5.QtCore import Qt as _Qt
        from PyQt5.QtGui import QBrush

        # 1) 画卡片底：整格内缩，行间露出灰底缝隙
        #    注意：这里不能用 QPainterPath + drawPath（在离屏/光栅渲染下会直接崩溃），
        #    drawRoundedRect 效果等价且稳定。
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        rect = option.rect.adjusted(self._hm, self._vm, -self._hm, -self._vm)
        card = QColor(self.CARD_COLOR)
        if option.state & QStyle.State_Selected:
            card = QColor(self.SELECTED_COLOR)
        elif option.state & QStyle.State_MouseOver:
            card = QColor(self.HOVER_COLOR)
        painter.setPen(_Qt.NoPen)
        painter.setBrush(card)
        painter.drawRoundedRect(rect, self._radius, self._radius)
        painter.restore()

        # 2) 画文本（手动，避免默认绘制把 QSS 底色/选中色盖回卡片上）
        text = index.data(_Qt.DisplayRole)
        if text:
            painter.save()
            fg = index.data(_Qt.ForegroundRole)
            if isinstance(fg, QBrush):
                color = fg.color()
            elif isinstance(fg, QColor):
                color = fg
            else:
                color = QColor(self.TEXT_FALLBACK)
            painter.setPen(color)
            font = index.data(_Qt.FontRole)
            painter.setFont(font if font else option.font)
            align = index.data(_Qt.TextAlignmentRole)
            if not align:
                align = _Qt.AlignLeft | _Qt.AlignVCenter
            text_rect = rect.adjusted(8, 0, -8, 0)
            painter.drawText(text_rect, int(align), str(text))
            painter.restore()


def get_soft_table_stylesheet(header_font_size=12):
    """风格10：灰底容器 + 白色圆角行 + 彩色按键徽章观感（Soft UI）"""
    return f"""
        QTableWidget {{
            background: {SoftCardDelegate.BASE_COLOR};
            border: none;
            border-radius: 14px;
            outline: none;
            gridline-color: transparent;
            font-size: 14px;
            font-family: "Microsoft YaHei", "Segoe UI Emoji", sans-serif;
        }}
        QTableWidget::item {{ border: none; }}
        QHeaderView::section {{
            background: #EEF1F8;
            color: #7A8399;
            padding: 12px 14px;
            border: none;
            font-weight: 600;
            font-size: {header_font_size}px;
            font-family: "Microsoft YaHei", "Segoe UI Emoji", sans-serif;
        }}
        QHeaderView::section:first {{ border-top-left-radius: 14px; }}
        QHeaderView::section:last {{ border-top-right-radius: 14px; }}
        QScrollBar:vertical {{ width: 8px; background: transparent; border-radius: 4px; }}
        QScrollBar::handle:vertical {{ background: {ColorPalette.GRAY_300}; border-radius: 4px; min-height: 20px; }}
        QScrollBar::handle:vertical:hover {{ background: {ColorPalette.GRAY_400}; }}
        QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}
        QScrollBar:horizontal {{ height: 8px; background: transparent; border-radius: 4px; }}
        QScrollBar::handle:horizontal {{ background: {ColorPalette.GRAY_300}; border-radius: 4px; min-width: 20px; }}
        QScrollBar::handle:horizontal:hover {{ background: {ColorPalette.GRAY_400}; }}
        QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal {{ width: 0px; background: transparent; }}
    """


def configure_soft_card_table(table, row_height=48):
    """把一张 QTableWidget 配置成软 UI 卡片风格（含委托/行高/悬浮/选择行为）"""
    from PyQt5.QtWidgets import QAbstractItemView
    table.setStyleSheet(get_soft_table_stylesheet())
    table.setItemDelegate(SoftCardDelegate())
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setMouseTracking(True)   # 让委托能收到 State_MouseOver 实现悬浮变色
    table.setShowGrid(False)
    table.setAlternatingRowColors(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.horizontalHeader().setHighlightSections(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(row_height)

# ==================== 行卡片式表格（风格8，纯 QSS） ====================

def get_row_card_table_stylesheet(header_font_size=12, cell_font_size=14):
    """风格8：灰底容器 + 白色行卡片（行间透缝）+ 悬浮/选中高亮。
    纯 QSS 实现，无需自定义委托，稳定且行为与默认表格完全一致。"""
    return f"""
        QTableWidget {{
            background: #EEF1F7;
            border: none;
            border-radius: 12px;
            outline: none;
            gridline-color: transparent;
            font-size: {cell_font_size}px;
            font-family: "Microsoft YaHei", "Segoe UI Emoji", sans-serif;
            color: #333333;
        }}
        QTableWidget::item {{
            background: #FFFFFF;
            border-bottom: 6px solid #EEF1F7;
            color: #333333;
            padding: 10px 14px;
        }}
        QTableWidget::item:hover {{ background: #FAFBFF; }}
        QTableWidget::item:selected {{ background: #E8F0FE; color: #333333; }}
        QHeaderView::section {{
            background: #E3E7F0;
            color: #7A8399;
            padding: 11px 14px;
            border: none;
            font-weight: 600;
            font-size: {header_font_size}px;
            font-family: "Microsoft YaHei", "Segoe UI Emoji", sans-serif;
        }}
        QHeaderView::section:first {{ border-top-left-radius: 12px; }}
        QHeaderView::section:last {{ border-top-right-radius: 12px; }}
        QScrollBar:vertical {{ width: 8px; background: transparent; border-radius: 4px; }}
        QScrollBar::handle:vertical {{ background: {ColorPalette.GRAY_300}; border-radius: 4px; min-height: 20px; }}
        QScrollBar::handle:vertical:hover {{ background: {ColorPalette.GRAY_400}; }}
        QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height: 0px; background: transparent; }}
        QScrollBar:horizontal {{ height: 8px; background: transparent; border-radius: 4px; }}
        QScrollBar::handle:horizontal {{ background: {ColorPalette.GRAY_300}; border-radius: 4px; min-width: 20px; }}
        QScrollBar::handle:horizontal:hover {{ background: {ColorPalette.GRAY_400}; }}
        QScrollBar::add-line:horizontal,QScrollBar::sub-line:horizontal {{ width: 0px; background: transparent; }}
    """


def configure_row_card_table(table, row_height=52):
    """把一张 QTableWidget 配置成行卡片风格（纯 QSS，无自定义委托）"""
    from PyQt5.QtWidgets import QAbstractItemView
    table.setStyleSheet(get_row_card_table_stylesheet())
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setMouseTracking(True)
    table.setShowGrid(False)
    table.setAlternatingRowColors(False)
    table.horizontalHeader().setHighlightSections(False)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(row_height)
