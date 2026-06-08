"""macOS Design System - Based on Apple Human Interface Guidelines"""

import sys

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
    HEIGHT_SMALL=28;HEIGHT_MEDIUM=32;HEIGHT_REGULAR=36;HEIGHT_LARGE=44;HEIGHT_XL=52
    MIN_WIDTH_SMALL=60;MIN_WIDTH_MEDIUM=72;MIN_WIDTH_REGULAR=88;MIN_WIDTH_LARGE=110;MIN_WIDTH_XL=140
    PADDING_H_SMALL=12;PADDING_H_REGULAR=18;PADDING_H_LARGE=24

class ColorPalette:
    PRIMARY="#007AFF";PRIMARY_HOVER="#0051D5";PRIMARY_ACTIVE="#004FC4";PRIMARY_BG="#F0F4FF"
    SUCCESS="#34C759";SUCCESS_BG="#E8F9ED";WARNING="#FF9500";WARNING_BG="#FFF4E5"
    ERROR="#FF3B30";ERROR_BG="#FFE5E5";INFO="#5AC8FA";INFO_BG="#E8F7FC"
    GRAY_50="#FBFBFD";GRAY_100="#F5F5F7";GRAY_200="#E8E8ED";GRAY_300="#D1D1D6";GRAY_400="#AEAEB2"
    GRAY_500="#86868B";GRAY_600="#6E6E73";GRAY_700="#48484A";GRAY_800="#3A3A3C";GRAY_900="#1D1D1F"
    BG_MAIN="#F5F5F7";BG_CARD="#FFFFFF";BG_SIDEBAR="#F5F5F7";BG_TOOLBAR="#FFFFFF";BG_HOVER="#F0F0F2"
    TEXT_PRIMARY="#1D1D1F";TEXT_SECONDARY="#86868B";TEXT_MUTED="#AEAEB2";TEXT_DISABLED="#D1D1D6"
    BORDER_LIGHT="#E8E8ED";BORDER_DEFAULT="#D1D1D6";BORDER_STRONG="#AEAEB2";SEPARATOR="#E8E8ED"
    SYSTEM_RED="#FF3B30";SYSTEM_ORANGE="#FF9500";SYSTEM_YELLOW="#FFCC00";SYSTEM_GREEN="#34C759"
    SYSTEM_MINT="#00C7BE";SYSTEM_TEAL="#5AC8FA";SYSTEM_BLUE="#007AFF";SYSTEM_INDIGO="#5856D6"
    SYSTEM_PURPLE="#AF52DE";SYSTEM_PINK="#FF2D55";SYSTEM_BROWN="#A2845E"

class ShadowSystem:
    SHADOW_SM="0 1px 3px rgba(0,0,0,0.08)";SHADOW_MD="0 4px 12px rgba(0,0,0,0.1)";SHADOW_LG="0 8px 24px rgba(0,0,0,0.12)"
    SHADOW_PRIMARY="0 2px 8px rgba(0,122,255,0.2)"

class AnimationTokens:
    DURATION_FAST=100;DURATION_NORMAL=200;DURATION_SLOW=300
    EASING_STANDARD="cubic-bezier(0.4,0,0.2,1)";EASING_OUT="cubic-bezier(0,0,0.2,1)"

THEME_PRIMARY=ColorPalette.PRIMARY;THEME_SECONDARY=ColorPalette.INFO;THEME_ACCENT=ColorPalette.PRIMARY
THEME_BG=ColorPalette.BG_MAIN;THEME_CARD=ColorPalette.BG_CARD;THEME_TEXT=ColorPalette.TEXT_PRIMARY
THEME_MUTED=ColorPalette.TEXT_SECONDARY;THEME_BORDER=ColorPalette.BORDER_DEFAULT
MACOS_FONT_STACK=TypographySystem.FONT_FAMILY
TYPOGRAPHY=TypographySystem();SPACING=SpacingSystem();BORDER_RADIUS=BorderRadiusSystem()
COLORS=ColorPalette()

def get_table_stylesheet(bg_color=ColorPalette.BG_CARD,header_bg=ColorPalette.BG_CARD,header_color=ColorPalette.TEXT_SECONDARY,text_color=ColorPalette.TEXT_PRIMARY,border_color=ColorPalette.SEPARATOR,hover_color=ColorPalette.BG_HOVER,selected_color="#E8F0FE",alternate_color="#FAFAFC",border_radius=12,header_font_size=12,cell_font_size=14,cell_padding_v=12,cell_padding_h=16,row_height=48):
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
            border-bottom: 1px solid {border_color};
            border-top-left-radius: {border_radius}px;
            border-top-right-radius: {border_radius}px;
            font-weight: 600;
            font-size: {header_font_size}px;
            font-family: "Microsoft YaHei", "Segoe UI Emoji", sans-serif;
        }}
        QHeaderView::section:last {{ border-top-right-radius: {border_radius}px; }}
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
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)

SHADOWS=ShadowSystem()
ANIMATIONS=AnimationTokens()


