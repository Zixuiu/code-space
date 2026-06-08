"""
文件: combo_skill_edit_dialog.py
用途: 组合技编辑对话框 - 完整的流程编辑、条件设置、图片选择等功能
"""

import os
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (QFrame,
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QWidget, QComboBox,
    QDoubleSpinBox, QSpinBox, QTextEdit, QStackedWidget, QFrame,
    QFileDialog, QMessageBox, QApplication
)
T = {
    'primary': '#000000', 'primary_hover': '#333333',
    'bg_main': '#FFFFFF', 'bg_card': '#FAFAFA', 'bg_input': '#FFFFFF',
    'text_primary': '#000000', 'text_secondary': '#888888',
    'border': '#E0E0E0', 'success': '#000000', 'danger': '#000000',
    'accent': '#00000010', 'header_bg': '#FAFAFA', 'tree_alt': '#F0F0F0',
}
IS_DARK = False
from design_system import ColorPalette, BorderRadiusSystem, TypographySystem
from utils import get_recordings_path, get_screen_size
from beautiful_dialog import StyledMessageDialog
from styles import apply_dialog_style


class ComboSkillEditDialog(QDialog):
    """组合技编辑对话框 - 表格对齐版，支持执行操作"""

    def __init__(self, parent=None, skill_data=None):
        super().__init__(parent)
        self.parent = parent
        self.skill_data = skill_data or {}
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
        self.initUI()

    def initUI(self):
        self.setWindowTitle("编辑组合技" if self.skill_data else "新建组合技")
        self.setFixedSize(900, 600)

        # 应用全局对话框样式
        self.setStyleSheet(f'background: {T["bg_main"]}; border-radius: 16px;')

        from PyQt5.QtCore import Qt
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        _, sh = get_screen_size()
        self._sh = sh
        self._drag_pos = None
        btn_r = int(sh * 0.006)
        inp_r = int(sh * 0.006)

        _outer = QVBoxLayout(self)
        _outer.setContentsMargins(0,0,0,0)
        _card = QFrame(self)
        _card.setStyleSheet('QFrame{background-color:#FFFFFF;border-radius:12px;}')
        _cl = QVBoxLayout(_card)
        _cl.setSpacing(10)
        _cl.setContentsMargins(15, 40, 15, 15)
        _outer.addWidget(_card)
        layout = _cl

        # macOS close dot
        _close = QFrame(_card)
        _close.setFixedSize(14,14)
        _close.setStyleSheet('QFrame{background-color:#FF5F57;border:none;border-radius:7px;}QFrame:hover{background-color:#FF3B30;}')
        _close.setCursor(Qt.PointingHandCursor)
        _close.move(self.width()-32, 12)
        def _close_click(ev):
            from PyQt5.QtCore import Qt as _QQt
            if ev.button() == _QQt.LeftButton:
                self.close()
        _close.mousePressEvent = _close_click


        # ── 顶部栏：标题 + 名称 + 循环次数 + 备注 ──
        top_layout = QHBoxLayout()
        title = QLabel("🎯 组合技")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_layout.addWidget(title)

        self.name_input = QLineEdit(self.skill_data.get('name', ''))
        self.name_input.setPlaceholderText("请输入组合技名称")
        top_layout.addWidget(self.name_input, 1)

        loop_label = QLabel("循环:")
        top_layout.addWidget(loop_label)

        self.loop_count_spin = QSpinBox()
        self.loop_count_spin.setRange(1, 9999)
        self.loop_count_spin.setValue(self.skill_data.get('loop_count', 1))
        top_layout.addWidget(self.loop_count_spin)

        note_btn = QPushButton("📝 备注")
        note_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: #8E8E93;
                border: 1px solid #D1D1D6;
                border-radius: {8}px;
                font-size: {13}px;
                font-weight: {600};
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 18px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #F0F0F2;
                color: #6E6E73;
                border: 1px solid #D1D1D6;
            }}
            QPushButton:pressed {{
                background-color: #E8E8ED;
                padding-top: 2px;
            }}
        """)
        note_btn.clicked.connect(self.show_note_page)
        top_layout.addWidget(note_btn)

        layout.addLayout(top_layout)

        self.stacked_widget = QStackedWidget()

        # ========== 页面1: 流程编辑页面 ==========
        self.flow_page = QWidget()
        flow_layout = QVBoxLayout(self.flow_page)
        flow_layout.setContentsMargins(0, 0, 0, 0)
        flow_layout.setSpacing(10)

        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["执行条件", "条件图片", "执行操作", "等待时间(s)"])
        self.tree_widget.setStyleSheet(f"""
            QTreeWidget {{
                background: {T['bg_card']};
                border-radius: 6px;
                border: 1px solid {T['border']};
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {T['border']}55;
                min-height: 45px;
                outline: none;
                border: none;
            }}
            QTreeWidget::item:selected {{
                background: {T['primary']}15;
                border: none;
                outline: none;
            }}
            QHeaderView::section {{
                background: #F5F5F5;
                color: #333333;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #E0E0E0;
                font-size: 13px;
            }}
        """)
        self.tree_widget.setColumnWidth(0, 250)
        self.tree_widget.setColumnWidth(1, 180)
        self.tree_widget.setColumnWidth(2, 280)
        self.tree_widget.setColumnWidth(3, 90)

        self.tree_widget.setSelectionMode(QTreeWidget.SingleSelection)
        self.dragged_item = None
        self.dragged_index = None
        self.tree_widget.viewport().installEventFilter(self)
        self.tree_widget.setMinimumHeight(350)
        self.flow_widgets = []

        self.build_flow_tree()

        flow_layout.addWidget(self.tree_widget, 1)

        # ── 操作按钮行 ──
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("+ 添加")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {T['primary']};
                color: white;
                border: none;
                border-radius: {8}px;
                font-size: {13}px;
                font-weight: {700};
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 18px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: {T['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {T['primary']};
                padding-top: 2px;
            }}
        """)
        add_btn.clicked.connect(self.add_flow)
        btn_layout.addWidget(add_btn)

        del_btn = QPushButton("- 删除")
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {T['danger']};
                color: white;
                border: none;
                border-radius: {8}px;
                font-size: {13}px;
                font-weight: {700};
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 18px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #FF3B30DD;
            }}
            QPushButton:pressed {{
                background-color: #FF3B30BB;
                padding-top: 2px;
            }}
        """)
        del_btn.clicked.connect(self.delete_flow)
        btn_layout.addWidget(del_btn)

        btn_layout.addStretch()

        up_btn = QPushButton("↑ 上移")
        up_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: #8E8E93;
                border: 1px solid #D1D1D6;
                border-radius: {8}px;
                font-size: {13}px;
                font-weight: {600};
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 18px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #F0F0F2;
                color: #6E6E73;
            }}
            QPushButton:pressed {{
                background-color: #E8E8ED;
                padding-top: 2px;
            }}
        """)
        up_btn.clicked.connect(self.move_flow_up)
        btn_layout.addWidget(up_btn)

        down_btn = QPushButton("↓ 下移")
        down_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #FFFFFF;
                color: #8E8E93;
                border: 1px solid #D1D1D6;
                border-radius: {8}px;
                font-size: {13}px;
                font-weight: {600};
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 18px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #F0F0F2;
                color: #6E6E73;
            }}
            QPushButton:pressed {{
                background-color: #E8E8ED;
                padding-top: 2px;
            }}
        """)
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
        note_title = QLabel("📝 组合技备注")
        note_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        note_title_layout.addWidget(note_title)
        note_title_layout.addStretch()

        back_btn = QPushButton("← 返回")
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {T['primary']};
                color: white;
                border: none;
                border-radius: {8}px;
                font-size: {13}px;
                font-weight: {700};
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 18px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: {T['primary_hover']};
            }}
            QPushButton:pressed {{
                background-color: {T['primary']};
                padding-top: 2px;
            }}
        """)
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
                background-color: #FFFFFF;
                color: #8E8E93;
                border: 1px solid #D1D1D6;
                border-radius: {8}px;
                font-size: {13}px;
                font-weight: {600};
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 18px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: #F0F0F2;
                color: #6E6E73;
            }}
            QPushButton:pressed {{
                background-color: #E8E8ED;
                padding-top: 2px;
            }}
        """)
        cancel_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(cancel_btn)

        save_btn = QPushButton("✓ 保存")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {T['primary']};
                color: white;
                border: none;
                border-radius: {8}px;
                font-size: {13}px;
                font-weight: {700};
                font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
                padding: 0 24px;
                min-height: 36px;
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
        self.tree_widget.clear()
        self.flow_widgets = []

        for i in range(len(self.flows)):
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
                else_item.setBackground(0, QColor("#fff2f0"))
                else_item.setBackground(1, QColor("#fff2f0"))
                else_item.setBackground(2, QColor("#fff2f0"))
                else_item.setData(0, Qt.UserRole, {'index': i, 'is_else': True})
                self.create_flow_item_widgets(else_item, i, else_data, is_else=True)
                main_item.setExpanded(True)

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
            else_indent = QLabel("  └")
            else_indent.setStyleSheet(f"color: {T['text_secondary']}; font-size: 11px;")
            condition_layout.addWidget(else_indent)

        condition_combo = QComboBox()
        condition_combo.addItems(["总是执行", "找到图片", "找不到图片", "等待图片"])
        condition_combo.setCurrentIndex({"always": 0, "image_found": 1, "image_not_found": 2, "wait_for_image": 3}.get(condition, 0))
        condition_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {T['bg_card']};
                color: {T['text_primary']};
                border: 1.5px solid {T['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QComboBox:hover {{
                border-color: {T['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                subcontrol-position: center right;
                subcontrol-origin: padding;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {T['text_secondary']};
                width: 0;
                height: 0;
            }}
            QComboBox QAbstractItemView {{
                background-color: {T['bg_card']};
                color: {T['text_primary']};
                border: 1px solid {T['border']};
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                border-radius: 6px;
                min-height: 22px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {T['primary']};
                color: white;
            }}
        """)
        condition_combo.setFixedWidth(120)
        if is_else:
            condition_combo.currentIndexChanged.connect(lambda idx, i=index: self.on_else_condition_changed(i, idx))
        else:
            condition_combo.currentIndexChanged.connect(lambda idx, i=index: self.on_condition_changed(i, idx))
        condition_layout.addWidget(condition_combo)

        if not is_else:
            else_btn = QPushButton("+else")
            else_btn.setStyleSheet(f"background: {T['primary']}; color: white; padding: 4px 8px; font-size: 10px; border: none; border-radius: {8}px;")
            else_btn.setFixedWidth(50)
            else_btn.clicked.connect(lambda checked, i=index: self.add_else_branch(i))
            if flow_data.get('else_branch'):
                else_btn.setEnabled(False)
                else_btn.setText("有else")
            else_btn.setVisible(condition != "always")
            condition_layout.addWidget(else_btn)

        if is_else:
            del_else_btn = QPushButton("✕")
            del_else_btn.setStyleSheet(f"background: {T['danger']}; color: white; padding: 2px 6px; font-size: 10px; border: none; border-radius: 3px;")
            del_else_btn.setFixedWidth(25)
            del_else_btn.setToolTip("删除else分支")
            del_else_btn.clicked.connect(lambda checked, i=index: self.delete_else_branch(i))
            condition_layout.addWidget(del_else_btn)

        wait_time_spin = QSpinBox()
        wait_time_spin.setRange(1, 999999)
        wait_time_spin.setValue(flow_data.get('wait_timeout', 30))
        wait_time_spin.setFixedWidth(50)
        wait_time_spin.setVisible(condition == "wait_for_image")
        wait_time_spin.valueChanged.connect(lambda val, i=index, ie=is_else: self.on_wait_time_changed(i, val, ie))
        condition_layout.addWidget(wait_time_spin)

        condition_layout.addStretch()
        self.tree_widget.setItemWidget(tree_item, 0, condition_widget)

        # ── 第1列：条件图片 ──
        image_widget = QWidget()
        image_widget.setStyleSheet("background: transparent; border: none; outline: none;")
        image_layout = QHBoxLayout(image_widget)
        image_layout.setContentsMargins(5, 2, 5, 2)
        image_layout.setSpacing(5)

        image_preview = QLabel()
        image_preview.setFixedSize(60, 40)
        image_preview.setStyleSheet("border: none; background: transparent; outline: none;")
        image_preview.setFrameStyle(QFrame.NoFrame)
        image_preview.setLineWidth(0)
        image_preview.setMidLineWidth(0)
        image_preview.setAlignment(Qt.AlignCenter)
        image_preview.setCursor(Qt.PointingHandCursor)
        image_preview.setVisible(condition != "always")

        image_path = flow_data.get('condition_image', '')
        if image_path and os.path.exists(image_path):
            self.load_image_to_preview(image_preview, image_path)
        image_preview.image_path = image_path
        image_preview.mousePressEvent = lambda event, path=image_path: self.view_condition_image_path(path) if path else None
        image_layout.addWidget(image_preview)

        img_btn = QPushButton("浏览")
        img_btn.setStyleSheet(f"background: {T['primary']}; color: white; padding: 4px 10px; font-size: 10px; border: none; border-radius: {8}px;")
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

        action_type_combo = QComboBox()
        action_type_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {T['bg_card']};
                color: {T['text_primary']};
                border: 1.5px solid {T['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QComboBox:hover {{
                border-color: {T['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                subcontrol-position: center right;
                subcontrol-origin: padding;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {T['text_secondary']};
                width: 0;
                height: 0;
            }}
            QComboBox QAbstractItemView {{
                background-color: {T['bg_card']};
                color: {T['text_primary']};
                border: 1px solid {T['border']};
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                border-radius: 6px;
                min-height: 22px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {T['primary']};
                color: white;
            }}
        """)
        action_type_combo.setFixedWidth(120)
        action_type_combo.addItem("⏹ 结束组合技", "end")
        action_type_combo.addItem("↻ 跳转流程", "goto")
        action_type_combo.addItem("▶ 执行流程", "execute")
        action_layout.addWidget(action_type_combo)

        action_detail_combo = QComboBox()
        action_detail_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {T['bg_card']};
                color: {T['text_primary']};
                border: 1.5px solid {T['border']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QComboBox:hover {{
                border-color: {T['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                subcontrol-position: center right;
                subcontrol-origin: padding;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {T['text_secondary']};
                width: 0;
                height: 0;
            }}
            QComboBox QAbstractItemView {{
                background-color: {T['bg_card']};
                color: {T['text_primary']};
                border: 1px solid {T['border']};
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                border-radius: 6px;
                min-height: 22px;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {T['primary']};
                color: white;
            }}
        """)
        action_detail_combo.setFixedWidth(150)
        action_layout.addWidget(action_detail_combo)

        current_action = flow_data.get('action', '')
        self.setup_action_combos(action_type_combo, action_detail_combo, current_action, index)

        action_type_combo.currentIndexChanged.connect(
            lambda idx, i=index, atc=action_type_combo, adc=action_detail_combo, ie=is_else: self.on_action_type_changed(i, atc, adc, ie)
        )
        action_detail_combo.currentIndexChanged.connect(
            lambda idx, i=index, atc=action_type_combo, adc=action_detail_combo, ie=is_else: self.on_action_detail_changed(i, atc, adc, ie)
        )

        action_layout.addStretch()
        self.tree_widget.setItemWidget(tree_item, 2, action_widget)

        # ── 第3列：执行后等待时间 ──
        delay_widget = QWidget()
        delay_widget.setStyleSheet("background: transparent; border: none;")
        delay_layout = QHBoxLayout(delay_widget)
        delay_layout.setContentsMargins(5, 2, 5, 2)
        delay_layout.setSpacing(3)

        delay_spin = QDoubleSpinBox()
        delay_spin.setRange(0, 999.9)
        delay_spin.setValue(flow_data.get('delay_after', 0))
        delay_spin.setDecimals(1)
        delay_spin.setSingleStep(0.5)
        delay_spin.setFixedWidth(70)
        delay_spin.valueChanged.connect(lambda val, i=index, ie=is_else: self.on_delay_changed(i, val, ie))
        delay_layout.addWidget(delay_spin)

        delay_layout.addStretch()
        self.tree_widget.setItemWidget(tree_item, 3, delay_widget)

        widget_data = {
            'tree_item': tree_item,
            'flow_index': index,
            'condition_combo': condition_combo,
            'image_preview': image_preview,
            'img_btn': img_btn,
            'wait_time_spin': wait_time_spin,
            'action_type_combo': action_type_combo,
            'action_detail_combo': action_detail_combo,
            'delay_spin': delay_spin,
            'is_else_branch': is_else
        }
        if not is_else:
            widget_data['else_btn'] = else_btn

        self.flow_widgets.append(widget_data)

    def add_else_branch(self, index):
        self.flows[index]['else_branch'] = {
            'condition': 'always',
            'condition_image': '',
            'action': ''
        }
        self.build_flow_tree()

    def delete_else_branch(self, index):
        self.flows[index]['else_branch'] = None
        self.build_flow_tree()

    def on_condition_changed(self, index, condition_idx):
        condition_map = {0: "always", 1: "image_found", 2: "image_not_found", 3: "wait_for_image"}
        condition = condition_map.get(condition_idx, "always")
        self.flows[index]['condition'] = condition

        for widget_data in self.flow_widgets:
            if widget_data.get('flow_index') == index and not widget_data.get('is_else_branch'):
                need_image = condition != "always"
                widget_data['image_preview'].setVisible(need_image)
                widget_data['img_btn'].setVisible(need_image)
                is_wait_for_image = (condition == "wait_for_image")
                widget_data['wait_time_spin'].setVisible(is_wait_for_image)
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
        old_from, old_to = from_index, to_index
        new_from, new_to = to_index, from_index
        self.flows[from_index], self.flows[to_index] = self.flows[to_index], self.flows[from_index]
        for i, flow in enumerate(self.flows):
            action = flow.get('action', '')
            if action.startswith('跳转_'):
                target = int(action.split('_')[1])
                if target == old_from:
                    flow['action'] = f'跳转_{new_from}'
                elif target == old_to:
                    flow['action'] = f'跳转_{new_to}'
            else_branch = flow.get('else_branch') or {}
            else_action = else_branch.get('action', '')
            if else_action.startswith('跳转_'):
                target = int(else_action.split('_')[1])
                if target == old_from:
                    else_branch['action'] = f'跳转_{new_from}'
                elif target == old_to:
                    else_branch['action'] = f'跳转_{new_to}'
        self.build_flow_tree()

    def on_else_condition_changed(self, index, condition_idx):
        condition_map = {0: "always", 1: "image_found", 2: "image_not_found", 3: "wait_for_image"}
        condition = condition_map.get(condition_idx, "always")
        if self.flows[index].get('else_branch'):
            self.flows[index]['else_branch']['condition'] = condition
            for widget_data in self.flow_widgets:
                if widget_data.get('flow_index') == index and widget_data.get('is_else_branch'):
                    need_image = condition != "always"
                    widget_data['image_preview'].setVisible(need_image)
                    widget_data['img_btn'].setVisible(need_image)
                    is_wait_for_image = (condition == "wait_for_image")
                    widget_data['wait_time_spin'].setVisible(is_wait_for_image)
                    break

    def on_wait_time_changed(self, index, value, is_else=False):
        if is_else:
            if self.flows[index].get('else_branch'):
                self.flows[index]['else_branch']['wait_timeout'] = value
        else:
            self.flows[index]['wait_timeout'] = value

    def on_delay_changed(self, index, value, is_else=False):
        if is_else:
            if self.flows[index].get('else_branch'):
                self.flows[index]['else_branch']['delay_after'] = value
        else:
            self.flows[index]['delay_after'] = value

    def load_flows_to_action_combo(self, combo, selected_action, current_flow_index=0):
        recordings_dir = get_recordings_path()
        combo.clear()
        combo.addItem("⏹ 结束组合技", "end")
        if len(self.flows) > 0:
            combo.insertSeparator(combo.count())
            for i in range(len(self.flows)):
                if i != current_flow_index:
                    flow_action = self.flows[i].get('action', '')
                    if flow_action and not flow_action.startswith('跳转_') and flow_action != 'end':
                        display_name = flow_action
                    else:
                        display_name = f"流程{i+1}"
                    combo.addItem(f"↻ 跳转到{display_name}", f"跳转_{i}")
        combo.insertSeparator(combo.count())
        try:
            if os.path.exists(recordings_dir):
                folders = [d for d in os.listdir(recordings_dir)
                          if os.path.isdir(os.path.join(recordings_dir, d)) and d != 'trash']
                if folders:
                    for folder in folders:
                        combo.addItem(f"▶ {folder}", folder)
        except Exception as e:
            pass
        if selected_action:
            for i in range(combo.count()):
                if combo.itemData(i) == selected_action:
                    combo.setCurrentIndex(i)
                    break

    def setup_action_combos(self, type_combo, detail_combo, current_action, index):
        if not current_action:
            type_combo.setCurrentIndex(2)
            self.load_execute_options(detail_combo)
            if detail_combo.count() > 0:
                detail_combo.setCurrentIndex(0)
                self.flows[index]['action'] = detail_combo.itemData(0)
        elif current_action == 'end':
            type_combo.setCurrentIndex(0)
            detail_combo.clear()
            detail_combo.setEnabled(False)
        elif current_action.startswith('跳转_'):
            type_combo.setCurrentIndex(1)
            self.load_goto_options(detail_combo, index)
            for i in range(detail_combo.count()):
                if detail_combo.itemData(i) == current_action:
                    detail_combo.setCurrentIndex(i)
                    break
        else:
            type_combo.setCurrentIndex(2)
            self.load_execute_options(detail_combo)
            for i in range(detail_combo.count()):
                if detail_combo.itemData(i) == current_action:
                    detail_combo.setCurrentIndex(i)
                    break

    def on_action_type_changed(self, index, type_combo, detail_combo, is_else):
        action_type = type_combo.currentData()
        if action_type == 'end':
            detail_combo.clear()
            detail_combo.setEnabled(False)
            if is_else:
                if self.flows[index].get('else_branch'):
                    self.flows[index]['else_branch']['action'] = 'end'
            else:
                self.flows[index]['action'] = 'end'
        elif action_type == 'goto':
            detail_combo.setEnabled(True)
            self.load_goto_options(detail_combo, index)
        elif action_type == 'execute':
            detail_combo.setEnabled(True)
            self.load_execute_options(detail_combo)

    def on_action_detail_changed(self, index, type_combo, detail_combo, is_else):
        action_type = type_combo.currentData()
        selected_value = detail_combo.currentData()
        if selected_value:
            if is_else:
                if self.flows[index].get('else_branch'):
                    self.flows[index]['else_branch']['action'] = selected_value
            else:
                self.flows[index]['action'] = selected_value

    def load_goto_options(self, combo, current_index):
        combo.clear()
        for i in range(len(self.flows)):
            if i != current_index:
                flow_action = self.flows[i].get('action', '')
                if flow_action and not flow_action.startswith('跳转_') and flow_action != 'end':
                    display_name = f"流程{i+1} ({flow_action})"
                else:
                    display_name = f"流程{i+1}"
                combo.addItem(f"跳转到{display_name}", f"跳转_{i}")

    def load_execute_options(self, combo):
        recordings_dir = get_recordings_path()
        combo.clear()
        try:
            if os.path.exists(recordings_dir):
                folders = [d for d in os.listdir(recordings_dir)
                          if os.path.isdir(os.path.join(recordings_dir, d)) and d != 'trash']
                for folder in folders:
                    combo.addItem(f"执行: {folder}", folder)
        except Exception as e:
            pass

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
        apply_dialog_style(dialog)
        layout = QVBoxLayout(dialog)
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
        if not image_path or not os.path.exists(image_path):
            image_preview.clear()
            return
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            image_preview.clear()
            return
        fixed_width = 60
        fixed_height = 40
        scaled_pixmap = pixmap.scaled(fixed_width, fixed_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        image_preview.setPixmap(scaled_pixmap)

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
        apply_dialog_style(dialog)
        layout = QVBoxLayout(dialog)
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
        self.flows.append({
            'condition': 'always',
            'condition_image': '',
            'action': '',
            'else_branch': None,
            '_visible': True
        })
        self.build_flow_tree()

    def delete_flow(self):
        if len(self.flows) <= 1:
            StyledMessageDialog(self, title="提示", text="至少保留一个流程", msg_type="information", buttons="ok").exec_()
            return
        self.flows.pop()
        self.build_flow_tree()

    def move_flow_up(self):
        current_index = self.tree_widget.currentIndex()
        if not current_index.isValid():
            return
        row = current_index.row()
        if row <= 0 or row >= len(self.flows):
            return
        self.swap_flows(row - 1, row)
        self.tree_widget.setCurrentIndex(self.tree_widget.model().index(row - 1, 0))

    def move_flow_down(self):
        current_index = self.tree_widget.currentIndex()
        if not current_index.isValid():
            return
        row = current_index.row()
        if row < 0 or row >= len(self.flows) - 1:
            return
        self.swap_flows(row, row + 1)
        self.tree_widget.setCurrentIndex(self.tree_widget.model().index(row + 1, 0))

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

        return {
            "name": name,
            "loop_type": "times",
            "loop_count": loop_count,
            "until_image": "",
            "flows": all_flows,
            "stop_shortcut": stop_shortcut,
            "note": note
        }