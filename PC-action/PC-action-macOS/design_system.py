"""
macOS Design System - Based on Apple Human Interface Guidelines
参考: https://developer.apple.com/design/human-interface-guidelines/
"""


class TypographySystem:
    """macOS 字体系统 - 基于 SF Pro 和 PingFang SC"""

    # macOS 标准字体栈 (优先使用系统字体)
    # Windows: Microsoft YaHei, macOS: PingFang SC / SF Pro
    import sys
    if sys.platform == "win32":
        FONT_FAMILY = '"Microsoft YaHei", "SimHei", sans-serif'
    else:
        FONT_FAMILY = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "PingFang SC", "Helvetica Neue", sans-serif'
    FONT_FAMILY_MONO = '"SF Mono", "Menlo", "Monaco", "Consolas", monospace'

    # 字重 (macOS 标准)
    WEIGHT_REGULAR = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700

    # 字号规范 (macOS 桌面应用标准)
    # 基准: 13px (macOS 标准正文字号)
    BASE_SIZE = 13

    SIZE_XS = 11      # 辅助标签、徽章
    SIZE_SM = 12      # 次要信息、说明文字
    SIZE_BASE = 13    # 正文、按钮、输入框
    SIZE_MD = 14      # 小标题、列表项
    SIZE_LG = 16      # 卡片标题
    SIZE_XL = 20      # 页面标题
    SIZE_2XL = 24     # 大标题
    SIZE_3XL = 28     # 特大标题

    # 行高
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_BASE = 1.47059    # macOS 标准行高 (19/13)
    LINE_HEIGHT_LOOSE = 1.6


class SpacingSystem:
    """macOS 间距系统 - 基于 4pt 网格"""

    UNIT = 4

    XS = 4      # 图标与文字间距
    SM = 8      # 相关元素间距
    MD = 12     # 标准内边距
    LG = 16     # 卡片内边距
    XL = 20     # 区块间距
    XXL = 24    # 大间距
    XXXL = 32   # 页面边距


class BorderRadiusSystem:
    """macOS/iOS 圆角系统 - Big Sur/Monterey/Ventura/Sonoma 风格"""

    NONE = 0
    XS = 6      # 极小圆角(徽章)
    SM = 8      # 小按钮、输入框 (iOS 标准)
    MD = 10     # 标准按钮圆角 (macOS 标准按钮)
    LG = 12     # 标准按钮、卡片 (iOS 标准)
    XL = 16     # 大卡片、对话框
    XXL = 20     # 超大容器
    FULL = 999  # 圆形/药丸形


class ButtonSize:
    """macOS 按钮尺寸系统 - 全局统一

    设计原则:
    - SMALL (28px)  - 工具栏图标按钮、列表行内操作
    - MEDIUM (32px) - 表单内次要按钮
    - REGULAR (36px) - 通用按钮(标准)
    - LARGE (44px)  - 主操作按钮 (iOS 触控标准)
    - XL (52px)     - 卡片内强调按钮
    """

    # 高度 (px)
    HEIGHT_SMALL = 28
    HEIGHT_MEDIUM = 32
    HEIGHT_REGULAR = 36
    HEIGHT_LARGE = 44
    HEIGHT_XL = 52

    # 最小宽度 (px)
    MIN_WIDTH_SMALL = 60
    MIN_WIDTH_MEDIUM = 72
    MIN_WIDTH_REGULAR = 88
    MIN_WIDTH_LARGE = 110
    MIN_WIDTH_XL = 140

    # 内边距 (水平)
    PADDING_H_SMALL = 12
    PADDING_H_REGULAR = 18
    PADDING_H_LARGE = 24


class ColorPalette:
    """macOS 颜色系统 - 官方色彩规范"""

    # ============================================
    # Apple 官方主色
    # ============================================
    # macOS Blue (系统强调色)
    PRIMARY = "#007AFF"
    PRIMARY_HOVER = "#0051D5"
    PRIMARY_ACTIVE = "#004FC4"
    PRIMARY_BG = "#F0F4FF"

    # ============================================
    # 功能色 (Apple 官方)
    # ============================================
    SUCCESS = "#34C759"       # Green
    SUCCESS_BG = "#E8F9ED"

    WARNING = "#FF9500"       # Orange
    WARNING_BG = "#FFF4E5"

    ERROR = "#FF3B30"         # Red
    ERROR_BG = "#FFE5E5"

    INFO = "#5AC8FA"          # Teal
    INFO_BG = "#E8F7FC"

    # ============================================
    # macOS 灰色系 (官方规范)
    # ============================================
    GRAY_50 = "#FBFBFD"       # 超浅灰 (窗口背景)
    GRAY_100 = "#F5F5F7"      # 浅灰 (侧边栏)
    GRAY_200 = "#E8E8ED"      # 边框浅
    GRAY_300 = "#D1D1D6"      # 边框标准
    GRAY_400 = "#AEAEB2"      # 禁用状态
    GRAY_500 = "#86868B"      # 次要文字
    GRAY_600 = "#6E6E73"      # 较深灰
    GRAY_700 = "#48484A"      # 深灰
    GRAY_800 = "#3A3A3C"      # 很深灰
    GRAY_900 = "#1D1D1F"      # 主要文字

    # ============================================
    # 语义化映射
    # ============================================
    BG_MAIN = "#F5F5F7"        # 主窗口背景
    BG_CARD = "#FFFFFF"        # 卡片背景
    BG_SIDEBAR = "#F5F5F7"     # 侧边栏背景
    BG_TOOLBAR = "#FFFFFF"     # 工具栏背景
    BG_HOVER = "#F0F0F2"       # 悬停背景

    TEXT_PRIMARY = "#1D1D1F"   # 主要文字
    TEXT_SECONDARY = "#86868B" # 次要文字
    TEXT_MUTED = "#AEAEB2"     # 提示文字
    TEXT_DISABLED = "#D1D1D6"  # 禁用文字

    BORDER_LIGHT = "#E8E8ED"   # 浅色边框
    BORDER_DEFAULT = "#D1D1D6" # 标准边框
    BORDER_STRONG = "#AEAEB2"  # 强调边框

    SEPARATOR = "#E8E8ED"      # 分割线

    # ============================================
    # macOS 系统颜色
    # ============================================
    SYSTEM_RED = "#FF3B30"
    SYSTEM_ORANGE = "#FF9500"
    SYSTEM_YELLOW = "#FFCC00"
    SYSTEM_GREEN = "#34C759"
    SYSTEM_MINT = "#00C7BE"
    SYSTEM_TEAL = "#5AC8FA"
    SYSTEM_BLUE = "#007AFF"
    SYSTEM_INDIGO = "#5856D6"
    SYSTEM_PURPLE = "#AF52DE"
    SYSTEM_PINK = "#FF2D55"
    SYSTEM_BROWN = "#A2845E"


class ShadowSystem:
    """macOS 阴影系统 - 微妙层次感"""

    # macOS 使用非常微妙的阴影
    SHADOW_SM = "0 1px 3px rgba(0, 0, 0, 0.08)"
    SHADOW_MD = "0 4px 12px rgba(0, 0, 0, 0.1)"
    SHADOW_LG = "0 8px 24px rgba(0, 0, 0, 0.12)"

    # 彩色阴影 (用于按钮等交互元素)
    SHADOW_PRIMARY = "0 2px 8px rgba(0, 122, 255, 0.2)"


class AnimationTokens:
    """macOS 动画规范"""

    DURATION_FAST = 100       # 快速反馈
    DURATION_NORMAL = 200     # 标准过渡
    DURATION_SLOW = 300       # 慢速动画

    EASING_STANDARD = "cubic-bezier(0.4, 0, 0.2, 1)"
    EASING_OUT = "cubic-bezier(0, 0, 0.2, 1)"


# ============================================
# 导出兼容常量
# ============================================
THEME_PRIMARY = ColorPalette.PRIMARY
THEME_SECONDARY = ColorPalette.INFO
THEME_ACCENT = ColorPalette.PRIMARY
THEME_BG = ColorPalette.BG_MAIN
THEME_CARD = ColorPalette.BG_CARD
THEME_TEXT = ColorPalette.TEXT_PRIMARY
THEME_MUTED = ColorPalette.TEXT_SECONDARY
THEME_BORDER = ColorPalette.BORDER_DEFAULT

MACOS_FONT_STACK = TypographySystem.FONT_FAMILY

TYPOGRAPHY = TypographySystem()
SPACING = SpacingSystem()
BORDER_RADIUS = BorderRadiusSystem()
COLORS = ColorPalette()


# ============================================
# 统一表格样式系统
# ============================================
def get_table_stylesheet(
    bg_color=ColorPalette.BG_CARD,
    header_bg=ColorPalette.BG_CARD,
    header_color=ColorPalette.TEXT_SECONDARY,
    text_color=ColorPalette.TEXT_PRIMARY,
    border_color=ColorPalette.SEPARATOR,
    hover_color=ColorPalette.BG_HOVER,
    selected_color="#E8F0FE",
    alternate_color="#FAFAFC",
    border_radius=12,
    header_font_size=12,
    cell_font_size=13,
    cell_padding_v=12,
    cell_padding_h=16,
    row_height=48,
):
    """生成 macOS 17 风格统一样式表 - 现代化设计
    
    所有参数都有默认值,不传参数即可获得 iOS/macOS 原生风格。
    """
    return f"""
        QTableWidget {{
            border: 1px solid {border_color};
            border-radius: {border_radius}px;
            background: {bg_color};
            outline: none;
            gridline-color: transparent;
            font-size: {cell_font_size}px;
            font-family: 'PingFang SC', 'Microsoft YaHei UI', sans-serif;
        }}
        QTableWidget::item {{
            padding: {cell_padding_v}px {cell_padding_h}px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.05);
            color: {text_color};
            min-height: {row_height - cell_padding_v * 2}px;
        }}
        QTableWidget::item:hover {{
            background: {hover_color};
        }}
        QTableWidget::item:selected {{
            background: {selected_color};
            color: {text_color};
        }}
        QTableWidget::item:alternate {{
            background: {alternate_color};
        }}
        QTableWidget:focus {{
            border: 1px solid {ColorPalette.PRIMARY};
            outline: none;
        }}
        QTableWidget::item:focus {{
            outline: none;
        }}
        QHeaderView::section {{
            background: {header_bg};
            color: {header_color};
            padding: {max(cell_padding_v - 2, 8)}px {cell_padding_h}px;
            border: none;
            border-bottom: 1px solid {border_color};
            border-top-left-radius: {border_radius}px;
            border-top-right-radius: {border_radius}px;
            font-weight: 600;
            font-size: {header_font_size}px;
            font-family: 'PingFang SC', 'Microsoft YaHei UI', sans-serif;
        }}
        QHeaderView::section:last {{
            border-top-right-radius: {border_radius}px;
        }}
        QScrollBar:vertical {{
            width: 8px;
            background: transparent;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {ColorPalette.GRAY_300};
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {ColorPalette.GRAY_400};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
            background: transparent;
        }}
        QScrollBar:horizontal {{
            height: 8px;
            background: transparent;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: {ColorPalette.GRAY_300};
            border-radius: 4px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {ColorPalette.GRAY_400};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
            background: transparent;
        }}
    """


def configure_table(table, style=None):
    """给 QTableWidget 设置统一 macOS 风格

    Args:
        table: QTableWidget 实例
        style: 可选,用 get_table_stylesheet() 生成的样式,不传则使用默认
    """
    from PyQt5.QtWidgets import QAbstractItemView, QHeaderView

    if style is None:
        style = get_table_stylesheet()
    table.setStyleSheet(style)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)


SHADOWS = ShadowSystem()
ANIMATIONS = AnimationTokens()
