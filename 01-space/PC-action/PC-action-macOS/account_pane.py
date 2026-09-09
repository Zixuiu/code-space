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

# ---- 布局 2 色板（白境画廊 · 与主程序一致的深绿主题） ----
BG = "#FFFFFF"        # 页面底（纯白）
CARD = "#FFFFFF"      # 面板
INK = "#1A1A1A"       # 主文字
SUB = "#9AA0A8"       # 次要文字（key / 提示）
LINE = "#E9EAEE"      # 分隔线
BLUE = "#0D7A4D"      # 主操作 · 深绿（与主程序一致）
GREEN_HOVER = "#0A6B42"  # 深绿悬停
GREEN_BG = "#E6F4EE"  # 浅绿信息块
RED = "#FF3B30"       # 危险操作 / 异常状态
GOOD = "#0D7A4D"      # 良好状态（深绿）

FIXED_RECHARGE_AMOUNT = 9.9   # 固定充值单价：扫码即付 9.9 元，无需用户手填

FONT_FAMILY = "Microsoft YaHei"

BLOCK_W = round(240 * SCALE)          # (240) 与登录表单同宽
PANEL_W = round(420 * SCALE)          # 左右分栏（A11）加宽卡片
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
    """key-value 明细行：左侧灰色 key + 右侧主色 value，行底 0.5px 分隔线
    tag=True 时 value 渲染为圆角色块（pill）。"""
    def __init__(self, key, parent=None, tag=False):
        super().__init__(parent)
        self._tag = tag
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
        if self._tag:
            hh = round(KV_SIZE * 1.6)
            self.value_label.setAttribute(Qt.WA_StyledBackground, True)
            self.value_label.setFixedHeight(hh)
            self.value_label.setAlignment(Qt.AlignCenter)
            self.value_label.setStyleSheet(
                f"background-color: {color}; color: white; "
                f"border-radius: {hh // 2}px; "
                f"padding: 0 {round(8 * SCALE)}px; "
                f"font-size: {KV_SIZE}px; font-weight: 700; font-family: \"{FONT_FAMILY}\";"
            )
        else:
            self.value_label.setFixedHeight(round(KV_SIZE * 1.4))
            self.value_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
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
    _recharge_ready = pyqtSignal(str, object)  # (username, 最新充值记录或 None)，后台查询 → 主线程刷 UI

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {BG};")
        self._username = None

        root = QVBoxLayout(self)
        root.setContentsMargins(round(24 * SCALE), round(20 * SCALE), round(24 * SCALE), round(20 * SCALE))
        root.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        # ---- 白卡（A11 左右分栏 · 比例对齐设计稿）----
        W = PANEL_W
        _hr1 = round(0.025 * W)
        _hr5 = round(0.05 * W)
        self._badge_size = round(44 * SCALE)        # 徽章直径（方案1 · 比例协调）
        _user_font = round(self._badge_size / 2.8)  # 用户名 ≈ 徽章 / 2.8
        _r_avail = (W - 2 * _hr1 - 1) * 9.0 / 20 - _hr1      # 右栏内容可用宽度
        _rb_w = round(_r_avail * 0.88)              # 提示块/按钮 ≈ 右栏内容 88%
        _btn_h = round(0.09 * W)                    # 按钮高 ≈ 9% 卡宽（胶囊）

        panel = QFrame()
        panel.setObjectName("acctPanel")
        panel.setFixedWidth(W)
        panel.setStyleSheet(
            f"#acctPanel {{ background: {CARD}; border-radius: {round(20 * SCALE)}px; }}"
        )
        root.addWidget(panel, 0, Qt.AlignTop)

        side = QHBoxLayout(panel)
        side.setContentsMargins(round(16 * SCALE), round(18 * SCALE), round(16 * SCALE), round(18 * SCALE))
        side.setSpacing(0)

        # ---------- 左栏（60%） ----------
        left = QWidget()
        left.setStyleSheet("background: transparent;")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, round(14 * SCALE), 0)
        lv.setSpacing(round(12 * SCALE))

        badge_row = QHBoxLayout()
        badge_row.setSpacing(round(12 * SCALE))
        self.badge_label = QLabel("✓")
        self.badge_label.setAttribute(Qt.WA_StyledBackground, True)
        self.badge_label.setFixedSize(self._badge_size, self._badge_size)
        self.badge_label.setAlignment(Qt.AlignCenter)
        self.badge_label.setStyleSheet(self._badge_style(BLUE))
        self.user_label = _label("—", _user_font, INK, bold=True)
        badge_row.addWidget(self.badge_label)
        badge_row.addWidget(self.user_label, 1)
        lv.addLayout(badge_row)

        # 明细行（会员状态为绿色胶囊 tag）
        self.row_user = _KVRow("用户名")
        self.row_user.hide()
        self.row_status = _KVRow("会员状态", tag=True)
        self.row_access = _KVRow("功能权限")
        self.row_expiry = _KVRow("到期时间")
        for r in (self.row_status, self.row_access, self.row_expiry):
            lv.addWidget(r)
        side.addWidget(left, 6)

        # ---------- 竖向灰分隔线 ----------
        sep = QFrame()
        sep.setObjectName("vSep")
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"#vSep {{ background: {LINE}; }}")
        side.addWidget(sep, 0, Qt.AlignVCenter)

        # ---------- 右栏（40%） ----------
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        rv = QVBoxLayout(right)
        rv.setContentsMargins(round(14 * SCALE), 0, 0, 0)
        rv.setSpacing(round(14 * SCALE))
        rv.setAlignment(Qt.AlignVCenter)

        # 充值审核状态（仅当有审核结果时显示）
        self.recharge_status_label = QLabel("")
        self.recharge_status_label.setWordWrap(True)
        self.recharge_status_label.setAlignment(Qt.AlignCenter)
        self.recharge_status_label.hide()
        rv.addWidget(self.recharge_status_label, 0, Qt.AlignHCenter)

        def _link_btn(text, color):
            b = QPushButton(text)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton {{ background: transparent; border: none; outline: none; color: {color}; "
                f"font-size: {BTN_SIZE}px; font-weight: 700; font-family: \"{FONT_FAMILY}\"; }}"
            )
            return b
        self.btn_logout = _link_btn("退出", RED)
        self.btn_logout.clicked.connect(self.logout_requested.emit)
        rv.addWidget(self.btn_logout, 0, Qt.AlignHCenter)

        self._ent_ready.connect(self._on_ent_ready)
        self._recharge_ready.connect(self._on_recharge_ready)
        side.addWidget(right, 4)

        # 版本号：置于面板下方整行（非第三列）
        self.version_label = _label("", round(0.015 * W), SUB)
        self.version_label.setAlignment(Qt.AlignHCenter)
        root.addSpacing(round(6 * SCALE))
        root.addWidget(self.version_label, 0, Qt.AlignHCenter)

    def _badge_style(self, color):
        return (
            f"background: {color}; color: white; outline: none; "
            f"border-radius: {self._badge_size // 2}px; "
            f"font-size: {round(self._badge_size * 0.5)}px; font-weight: 700;"
        )

    # ---------------- 数据刷新 ----------------
    def refresh(self, username):
        """按当前登录用户刷新界面。
        用户名立即显示；会员状态/权限等首次查询会走网络（Supabase），
        放到后台线程获取，完成后经 _ent_ready 信号回主线程刷新，避免登录后界面卡死。"""
        self._username = username
        if not username:
            self.user_label.setText("未登录")
            self.badge_label.setStyleSheet(self._badge_style(SUB))
            self.row_user.set_value("未登录", INK)
            self.row_status.set_value("—", SUB)
            self.row_access.set_value("—", SUB)
            self.row_expiry.set_value("—", SUB)
            return
        self.user_label.setText(username)
        self.badge_label.setStyleSheet(self._badge_style(SUB))
        self.row_user.set_value(username, INK)
        # 先用占位，避免空白
        self.row_status.set_value("查询中…", SUB)
        self.row_access.set_value("—", SUB)
        self.row_expiry.set_value("—", SUB)

        # 乐观渲染：本地有签名的权益缓存就先显示（零网络），
        # 避免"查询中…"停留大半天；后台联网取到权威结果后再覆盖。
        # 只影响展示，权限判定仍走后台 get_entitlement 的联网结果。
        try:
            from entitlement import peek_cached_entitlement
            cached = peek_cached_entitlement(username)
            if cached:
                self._apply_ent(cached)
        except Exception:
            pass

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
        else:
            self._apply_ent(ent)
        # 充值审核状态：持久展示「等待审核通过」
        self._refresh_recharge_status(username)

    def _apply_ent(self, ent):
        """把权益字典刷到明细行（纯 UI 赋值，主线程调用；不发网络请求）"""
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

        active = ent.get("is_vip") or ent.get("trial_valid")
        self.badge_label.setStyleSheet(self._badge_style(GOOD if active else RED))

    def _refresh_recharge_status(self, username):
        """查询最新一条充值申请，更新账户页「待审核」持久状态。
        查询走后台线程（Supabase 网络请求原先在主线程同步跑，会把整个界面卡住），
        结果经 _recharge_ready 信号回主线程刷新 UI。"""
        self.recharge_status_label.hide()
        if not username:
            return

        def _work():
            try:
                from database_helper import DatabaseHelper
                recs = DatabaseHelper.get_recharge_records(username, status=None) or []
            except Exception:
                recs = []
            latest = None
            for r in recs:  # 已按时间倒序
                if r.get('status') in ('pending', 'approved', 'rejected'):
                    latest = r
                    break
            self._recharge_ready.emit(username, latest)

        try:
            import threading
            threading.Thread(target=_work, daemon=True).start()
        except Exception:
            pass

    def _on_recharge_ready(self, username, latest):
        """充值审核查询结果回主线程后的 UI 刷新"""
        if username != self._username:
            return
        if not latest:
            return
        st = latest.get('status')
        if st == 'pending':
            self.recharge_status_label.setText("充值待审核 · 请等待审核通过")
            self.recharge_status_label.setStyleSheet(_status_style('pending', SCALE, SUB))
            self.recharge_status_label.show()
        elif st == 'approved':
            self.recharge_status_label.setText("充值已审核通过")
            self.recharge_status_label.setStyleSheet(_status_style('approved', SCALE, SUB))
            self.recharge_status_label.show()
        elif st == 'rejected':
            self.recharge_status_label.setText("充值申请被驳回，请重新提交或联系客服")
            self.recharge_status_label.setStyleSheet(_status_style('rejected', SCALE, SUB))
            self.recharge_status_label.show()


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
