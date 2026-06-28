---
name: "candy-theme-ui"
description: "Generates PyQt5 desktop app UI with rainbow candy theme (gradient buttons, pill inputs, cards). Invoke when user asks to create a desktop app with candy/cute style or generate UI using this theme."
---

# Candy Theme UI Generator

Generates PyQt5 desktop application interfaces using the Rainbow Candy Theme (Scheme 15) - young, fashionable, gradient color scheme.

## Color Palette

```python
PRIMARY_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF6B6B, stop:1 #4ECDC4)"  # Pink to Mint Green
SECONDARY = "#FFE66D"   # Yellow
ACCENT = "#FF6B6B"      # Pink
BG = "#FFFFFF"          # White background
CARD = "#FFF9F9"        # Light pink card
TEXT = "#2C3E50"        # Dark text
MUTED = "#636E72"       # Gray text
BORDER = "#DFE6E9"      # Light border
```

## Font Settings

- **Title**: 38px, bold, Microsoft YaHei UI
- **Subtitle**: 22px, Microsoft YaHei UI
- **GroupBox Title**: 26px, bold
- **Button Text**: 18px, bold
- **Input Text**: 24px
- **Checkbox/Radio**: 20px
- **Card Title**: 28px, bold
- **Card Description**: 22px
- **Label**: 20px

## Component Styles

### Primary Button (Pink→Mint Gradient)
```python
def get_primary_btn_style(self):
    return f"""
        QPushButton {{
            background: {self.PRIMARY_GRADIENT};
            color: white;
            border: none;
            border-radius: 25px;
            padding: 8px 24px;
            font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            font-size: 18px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFE66D, stop:1 #FF6B6B);
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #e55a5a, stop:1 #FF6B6B);
        }}
    """
```

### Secondary Button (Yellow)
```python
def get_secondary_btn_style(self):
    return f"""
        QPushButton {{
            background-color: {self.SECONDARY};
            color: {self.TEXT};
            border: none;
            border-radius: 25px;
            padding: 8px 24px;
            font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            font-size: 18px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {self.ACCENT};
            color: white;
        }}
    """
```

### Input Field (Pill Shape)
```python
def get_input_style(self):
    return f"""
        QLineEdit {{
            background-color: {self.BG};
            color: {self.TEXT};
            border: 2px solid {self.BORDER};
            border-radius: 999px;
            padding: 14px 20px;
            font-family: 'Microsoft YaHei UI', 'Segoe UI', sans-serif;
            font-size: 24px;
        }}
        QLineEdit:focus {{
            border-color: {self.ACCENT};
        }}
        QLineEdit::placeholder {{
            color: {self.MUTED};
        }}
    """
```

### Checkbox (Circular Indicator)
```python
def get_checkbox_style(self):
    return f"""
        QCheckBox {{
            color: {self.TEXT};
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            font-size: 20px;
        }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border-radius: 9px;
            border: 2px solid {self.BORDER};
            background: {self.BG};
        }}
        QCheckBox::indicator:checked {{
            background: {self.ACCENT};
            border-color: {self.ACCENT};
        }}
    """
```

### Card Frame (Pill Shape)
```python
def get_card_style(self):
    return f"""
        QFrame {{
            background-color: {self.CARD};
            border: 1px solid {self.BORDER};
            border-radius: 999px;
        }}
    """
```

### Tab Widget
```python
def get_tab_style(self):
    return f"""
        QTabWidget::pane {{
            border: 1px solid {self.BORDER};
            background-color: {self.BG};
            border-radius: 999px;
        }}
        QTabBar::tab {{
            background: {self.CARD};
            border: 1px solid {self.BORDER};
            padding: 10px 20px;
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            color: {self.MUTED};
            border-top-left-radius: 20px;
            border-top-right-radius: 20px;
        }}
        QTabBar::tab:selected {{
            background: {self.PRIMARY_GRADIENT};
            color: white;
            border-top-left-radius: 20px;
            border-top-right-radius: 20px;
        }}
        QTabBar::tab:hover:!selected {{
            background: {self.CARD};
            color: {self.ACCENT};
            border-top-left-radius: 20px;
            border-top-right-radius: 20px;
        }}
    """
```

## Layout Structure

### Window Settings
- Minimum size: 900x700
- Content margins: 20px
- Spacing: 15px

### Title Bar (Gradient Background)
```python
title_frame = QFrame()
title_frame.setStyleSheet(f"""
    QFrame {{
        background: {self.PRIMARY_GRADIENT};
        border-radius: 999px;
        padding: 25px;
    }}
""")
```

### Color Bar (Bottom)
- Displays all theme colors as swatches
- Each swatch: 40x25px with 4px border-radius

## Usage

When generating a desktop app with this theme:

1. Inherit colors: `self.PRIMARY_GRADIENT`, `self.SECONDARY`, `self.ACCENT`, `self.BG`, `self.CARD`, `self.TEXT`, `self.MUTED`, `self.BORDER`

2. Apply styles to components:
   - Primary actions → `get_primary_btn_style()`
   - Secondary actions → `get_secondary_btn_style()`
   - Text inputs → `get_input_style()`
   - Options → `get_checkbox_style()`
   - Content containers → `get_card_style()`
   - Navigation → `get_tab_style()`

3. Use pill-shaped borders (border-radius: 999px) for modern candy look

4. Recommended button height: 50px

5. Window minimum size: 900x700

## Example Window Title
```python
self.setWindowTitle("🎨 应用名称")
```

## Dependencies
- PyQt5
