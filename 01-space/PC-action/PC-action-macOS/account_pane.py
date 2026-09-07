# -*- coding: utf-8 -*-
"""
已登录账户页（布局 2 · 账户信息明细表）
=============================================
登录成功后，「账户」页展示本页而非登录表单：
- 白色圆角面板：标题「账户信息」+ key-value 明细行（用户名/会员状态/功能权限/到期时间）
- 底部三等分操作条：开通 VIP / 续费会员 / 退出登录
- 续费 / 购买会员（浏览器打开充值页，域名动态下发）
- 退出登录（发出 logout_requested，由主窗口接管切回登录页）

视觉：iOS 色调（#F2F2F7 底 + 白卡 + #0A84FF 主色 + #FF3B30 红），
尺寸沿用 login_pane.py 的 SCALE，保证 DPI 一致。
"""
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMessageBox,
)

from login_pane import SCALE

# ---- 布局 2 色板（iOS 色调） ----
BG = "#F2F2F7"        # 页面底
CARD = "#FFFFFF"      # 面板
INK = "#1C1C1E"       # 主文字
SUB = "#8E8E93"       # 次要文字（key）
LINE = "#E5E5EA"      # 分隔线
BLUE = "#0A84FF"      # 主操作
RED = "#FF3B30"       # 危险操作 / 异常状态
GOOD = "#34C759"      # 良好状态

FIXED_RECHARGE_AMOUNT = 9.9   # 固定充值单价：扫码即付 9.9 元，无需用户手填

FONT_FAMILY = "Microsoft YaHei"

BLOCK_W = round(240 * SCALE)          # (240) 与登录表单同宽
PANEL_W = BLOCK_W + round(40 * SCALE)   # (280) 紧凑卡片：比旧列窄
HEAD_SIZE = round(13 * SCALE)
KV_SIZE = round(10.5 * SCALE)
KEY_W = round(76 * SCALE)
ROW_PAD = round(8 * SCALE)
BTN_H = round(32 * SCALE)
BTN_SIZE = round(10.5 * SCALE)


def _label(text, size, color, bold=False):
    w = "bold" if bold else "500"
    l = QLabel(text)
    l.setStyleSheet(
        f"color: {color}; font-size: {size}px; font-weight: {w}; font-family: \"{FONT_FAMILY}\"; background: transparent;"
    )
    return l


class _KVRow(QFrame):
    """key-value 明细行：左侧灰色 key + 右侧主色 value，行底 0.5px 分隔线"""
    def __init__(self, key, parent=None):
        super().__init__(parent)
        self.setObjectName("kvRow")
        self.setStyleSheet(
            f"#kvRow {{ background: {CARD}; border-bottom: 1px solid {LINE}; }}"
        )
        h = QHBoxLayout(self)
        h.setContentsMargins(round(16 * SCALE), ROW_PAD, round(16 * SCALE), ROW_PAD)
        h.setSpacing(0)
        self.key_label = _label(key, KV_SIZE, SUB)
        self.key_label.setFixedWidth(KEY_W)
        self.value_label = _label("—", KV_SIZE, INK)
        self.value_label.setWordWrap(True)
        h.addWidget(self.key_label)
        h.addWidget(self.value_label, 1)

    def set_value(self, text, color=INK):
        self.value_label.setText(text)
        self.value_label.setStyleSheet(
            f"color: {color}; font-size: {KV_SIZE}px; font-weight: 500; font-family: \"{FONT_FAMILY}\"; background: transparent;"
        )


class _BarBtn(QPushButton):
    """底部操作条按钮：扁平、透明底、hover 浅灰"""
    def __init__(self, text, color, sep=True, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        border = f"border-right: 1px solid {LINE};" if sep else ""
        self.setFixedHeight(BTN_H)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none; {border}
                color: {color}; font-size: {BTN_SIZE}px; font-weight: 500;
                font-family: "{FONT_FAMILY}";
            }}
            QPushButton:hover {{ background-color: {BG}; }}
        """)


class AccountPane(QWidget):
    logout_requested = pyqtSignal()
    open_activation_requested = pyqtSignal()
    open_recharge_requested = pyqtSignal()
    _ent_ready = pyqtSignal(str, object)   # (username, entitlement dict)，由后台线程发放，主线程刷新 UI

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG};")
        self._username = None

        root = QVBoxLayout(self)
        root.setContentsMargins(round(24 * SCALE), round(20 * SCALE), round(24 * SCALE), round(20 * SCALE))
        root.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # ---- 白色圆角面板 ----
        panel = QFrame()
        panel.setObjectName("acctPanel")
        panel.setFixedWidth(PANEL_W)
        panel.setStyleSheet(
            f"#acctPanel {{ background: {CARD}; border-radius: {round(14 * SCALE)}px; }}"
        )
        root.addWidget(panel, 0, Qt.AlignTop)

        col = QVBoxLayout(panel)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        # 标题
        head_wrap = QWidget()
        head_wrap.setStyleSheet("background: transparent;")
        hv = QVBoxLayout(head_wrap)
        hv.setContentsMargins(round(16 * SCALE), round(12 * SCALE), round(16 * SCALE), round(10 * SCALE))
        hv.addWidget(_label("账户信息", HEAD_SIZE, INK, bold=True))
        col.addWidget(head_wrap)

        # ---- key-value 明细行 ----
        self.row_user = _KVRow("用户名")
        self.row_status = _KVRow("会员状态")
        self.row_access = _KVRow("功能权限")
        self.row_expiry = _KVRow("到期时间")
        for r in (self.row_user, self.row_status, self.row_access, self.row_expiry):
            col.addWidget(r)

        # ---- 充值审核区：状态提示 + 「我已充值完成」提交入口 ----
        recharge_wrap = QWidget()
        recharge_wrap.setStyleSheet("background: transparent;")
        rv = QVBoxLayout(recharge_wrap)
        rv.setContentsMargins(round(16 * SCALE), round(14 * SCALE), round(16 * SCALE), round(4 * SCALE))
        rv.setSpacing(0)

        self.recharge_hint_label = _label(f"每笔充值固定 {FIXED_RECHARGE_AMOUNT} 元 · 扫码支付后点击下方按钮确认", round(9 * SCALE), SUB)
        self.recharge_hint_label.setWordWrap(True)
        self.recharge_hint_label.setAlignment(Qt.AlignCenter)
        rv.addWidget(self.recharge_hint_label)
        rv.addSpacing(round(8 * SCALE))

        self.recharge_status_label = QLabel("")
        self.recharge_status_label.setWordWrap(True)
        self.recharge_status_label.setAlignment(Qt.AlignCenter)
        self.recharge_status_label.hide()
        rv.addWidget(self.recharge_status_label, 0, Qt.AlignHCenter)
        rv.addSpacing(round(8 * SCALE))

        self.btn_recharge_done = QPushButton(f"我已充值完成（{FIXED_RECHARGE_AMOUNT} 元）")
        self.btn_recharge_done.setCursor(Qt.PointingHandCursor)
        self.btn_recharge_done.setFixedHeight(BTN_H)
        self.btn_recharge_done.setStyleSheet(f"""
            QPushButton {{
                background-color: {BLUE}; color: white; border: none;
                border-radius: {round(8 * SCALE)}px; font-size: {BTN_SIZE}px;
                font-weight: 700; font-family: "{FONT_FAMILY}";
            }}
            QPushButton:hover {{ background-color: #2F95F8; }}
            QPushButton:disabled {{ background-color: #C6C6CB; }}
        """)
        self.btn_recharge_done.clicked.connect(self._on_recharge_done)
        rv.addWidget(self.btn_recharge_done)
        col.addWidget(recharge_wrap)

        # ---- 底部三等分操作条 ----
        bar = QFrame()
        bar.setObjectName("btnBar")
        bar.setFixedHeight(BTN_H)
        bar.setStyleSheet(f"#btnBar {{ background: {CARD}; border-top: 1px solid {LINE}; }}")
        bh = QHBoxLayout(bar)
        bh.setContentsMargins(0, 0, 0, 0)
        bh.setSpacing(0)

        self.btn_activation = _BarBtn("开通 VIP", BLUE, sep=True)
        self.btn_activation.clicked.connect(self.open_activation_requested.emit)
        self.btn_recharge = _BarBtn("续费会员", BLUE, sep=True)
        self.btn_recharge.clicked.connect(self.open_recharge_requested.emit)
        self.btn_logout = _BarBtn("退出", RED, sep=False)
        self.btn_logout.clicked.connect(self.logout_requested.emit)
        self._ent_ready.connect(self._on_ent_ready)
        for b in (self.btn_activation, self.btn_recharge, self.btn_logout):
            bh.addWidget(b, 1)
        col.addWidget(bar)

        # 版本号（主窗口可能写入；无内容时不占视觉）
        self.version_label = _label("", round(8 * SCALE), SUB)
        self.version_label.setAlignment(Qt.AlignHCenter)
        vw = QWidget()
        vw.setStyleSheet("background: transparent;")
        vv = QVBoxLayout(vw)
        vv.setContentsMargins(0, round(8 * SCALE), 0, round(10 * SCALE))
        vv.addWidget(self.version_label)
        col.addWidget(vw)

    # ---------------- 数据刷新 ----------------
    def refresh(self, username):
        """按当前登录用户刷新界面。
        用户名立即显示；会员状态/权限等首次查询会走网络（Supabase），
        放到后台线程获取，完成后经 _ent_ready 信号回主线程刷新，避免登录后界面卡死。"""
        self._username = username
        if not username:
            self.row_user.set_value("未登录", INK)
            self.row_status.set_value("—", SUB)
            self.row_access.set_value("—", SUB)
            self.row_expiry.set_value("—", SUB)
            return
        self.row_user.set_value(username, INK)
        # 先用占位，避免空白
        self.row_status.set_value("查询中…", SUB)
        self.row_access.set_value("—", SUB)
        self.row_expiry.set_value("—", SUB)

        try:
            import threading
            threading.Thread(target=self._fetch_ent, args=(username,), daemon=True).start()
        except Exception:
            self.row_status.set_value("未知", SUB)

    def _fetch_ent(self, username):
        try:
            from entitlement import get_entitlement
            ent = get_entitlement(username) or {}
        except Exception:
            ent = {}
        self._ent_ready.emit(username, ent)

    def _on_ent_ready(self, username, ent):
        if username != self._username:
            return
        if not ent or not isinstance(ent, dict):
            self.row_status.set_value("未知", SUB)
            self.row_access.set_value("—", SUB)
            self.row_expiry.set_value("—", SUB)
            return
        if ent.get("is_vip"):
            self.row_status.set_value("VIP 会员", GOOD)
            self.row_expiry.set_value(ent.get("vip_end") or "—", INK)
        elif ent.get("trial_valid"):
            self.row_status.set_value("试用中", BLUE)
            self.row_expiry.set_value(ent.get("trial_end") or "—", INK)
        else:
            self.row_status.set_value("已过期", RED)
            self.row_expiry.set_value("—", SUB)

        if ent.get("has_access"):
            self.row_access.set_value("全功能可用", GOOD)
        else:
            self.row_access.set_value("已锁定", RED)

        # 充值审核状态：持久展示「等待审核通过」
        self._refresh_recharge_status(username)

    def _refresh_recharge_status(self, username):
        """查询最新一条充值申请，更新账户页「待审核」持久状态"""
        self.recharge_status_label.hide()
        self.btn_recharge_done.setEnabled(True)
        self.btn_recharge_done.setText("我已充值完成")
        if not username:
            return
        try:
            from database_helper import DatabaseHelper
            recs = DatabaseHelper.get_recharge_records(username, status=None) or []
        except Exception:
            return
        latest = None
        for r in recs:  # 已按时间倒序
            if r.get('status') in ('pending', 'approved', 'rejected'):
                latest = r
                break
        if not latest:
            return
        st = latest.get('status')
        if st == 'pending':
            self.recharge_status_label.setText("充值待审核 · 请等待审核通过")
            self.recharge_status_label.setStyleSheet(_status_style('pending', SCALE, SUB))
            self.recharge_status_label.show()
            self.btn_recharge_done.setEnabled(False)
            self.btn_recharge_done.setText("待审核中")
        elif st == 'approved':
            self.recharge_status_label.setText("充值已审核通过")
            self.recharge_status_label.setStyleSheet(_status_style('approved', SCALE, SUB))
            self.recharge_status_label.show()
        elif st == 'rejected':
            self.recharge_status_label.setText("充值申请被驳回，请重新提交或联系客服")
            self.recharge_status_label.setStyleSheet(_status_style('rejected', SCALE, SUB))
            self.recharge_status_label.show()
            self.btn_recharge_done.setText("重新提交")

    def _on_recharge_done(self):
        """用户点击「我已充值完成」：写一条待审核充值记录并提醒等待审核通过"""
        username = self._username
        if not username:
            QMessageBox.information(self, "提示", "请先登录后再操作。")
            return
        try:
            from database_helper import DatabaseHelper
            pending = DatabaseHelper.get_recharge_records(username, status='pending') or []
            if pending:
                QMessageBox.information(self, "提示", "您已提交充值申请，正在等待审核通过，请耐心等待。")
                self._refresh_recharge_status(username)
                return
            rec = DatabaseHelper.add_recharge_record(
                username, FIXED_RECHARGE_AMOUNT, 0,
                payment_method=f'固定码扫码 {FIXED_RECHARGE_AMOUNT}元 · 账号 {username}',
                status='pending'
            )
            if rec:
                QMessageBox.information(self, "提交成功", f"充值申请已提交，请等待审核通过。\n金额：{FIXED_RECHARGE_AMOUNT} 元\n账号：{username}（将用于核实）\n审核结果将展示在账户页。")
            else:
                QMessageBox.warning(self, "提交失败", "提交失败，请稍后再试或联系客服。")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"提交失败：{e}")
        self._refresh_recharge_status(username)


def _status_style(kind, scale, sub):
    """充值审核状态提示的整体小卡片样式（pending / approved / rejected）"""
    if kind == 'pending':
        bg, fg = "#FFF3D6", "#B26A00"
    elif kind == 'approved':
        bg, fg = "#E9F9EE", "#1E8E3E"
    else:  # rejected
        bg, fg = "#FDEAEC", "#C5221F"
    return (
        f"background-color: {bg}; color: {fg}; font-size: {round(10.5 * scale)}px; "
        f"font-weight: 700; border-radius: {round(8 * scale)}px; "
        f"padding: {round(8 * scale)}px {round(12 * scale)}px; "
        f"font-family: \"{FONT_FAMILY}\"; text-align: center;"
    )
