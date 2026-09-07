# -*- coding: utf-8 -*-
"""
PC-action 账户与激活对话框（方案 6 · 嵌套面板）
- 展示当前权益：VIP 到期日 / 试用剩余天数 / 已过期
- 输入激活码一键开通（entitlement.activate_code，卡密模式）
- 购买引导（pricing.json 的 channel_url；PayPro 部署后回填生效）
"""
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QUrl, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QDesktopServices
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QGraphicsDropShadowEffect, QApplication, QFrame,
)

from beautiful_dialog import load_svg_icon, ICON_SCALE
from entitlement import (get_pricing, get_entitlement, activate_code,
                         resolve_channel_url, warmup_channel_url)
from activation_styles import get_style

THEME_PRIMARY = "#5A6069"
GREEN = "#34C759"
RED = "#FF3B30"
ORANGE = "#FF9500"


class ActivationDialog(QDialog):
    """账户与激活：嵌套灰面板 + 激活码输入 + 购买引导"""

    # 后台线程 → 主线程的结果投递（QTimer.singleShot 在无事件循环的工作线程里不会触发，
    # 曾导致"加载中"永远不更新；信号跨线程走队列投递才是对的）
    _status_ready = pyqtSignal(object)

    def __init__(self, parent=None, username=None, style=None):
        super().__init__(parent)
        self.username = username or ""
        self.st = get_style(style)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 注意：不能在弹窗上 setStyleSheet —— 上级样式表一旦存在，QFrame#C 的圆角渲染会被破坏
        # （全局主题 QDialog{background:#FFF} 的白底改由 showEvent 里清 WA_StyledBackground 压制）
        self.setModal(True)
        self.setFixedWidth(460)
        self._status_ready.connect(self._apply_status)
        self._build()
        self._add_shadow()
        QTimer.singleShot(0, self._center)
        QTimer.singleShot(50, self._fade_in)
        # 状态加载全部异步化：get_pricing/resolve_channel_url/get_entitlement 都是网络请求，
        # 同步跑会卡住弹窗打开（曾实测"等老半天"）。先显示加载态，后台取完再刷 UI。
        self.status_card.setText("正在获取会员状态…")
        self._refresh_status()
        # 后台预热/校验充值地址（cpolar 域名漂移自愈），完成后刷新购买链接
        self._warm_channel()

    def _warm_channel(self):
        try:
            import threading

            def _work():
                try:
                    resolve_channel_url(deep=True)
                except Exception:
                    pass
                # 预热完成后补一次购买行刷新（用信号投递，勿用 QTimer.singleShot——
                # 工作线程无事件循环，定时器永远不会触发）
                try:
                    pricing = get_pricing()
                    self._status_ready.emit({
                        "ent": None, "url": pricing.get('channel_url', ''),
                        "price_txt": f"¥{pricing.get('plan_1', {}).get('price', 99):.0f}/"
                                     f"{pricing.get('plan_1', {}).get('months', 1) * 30}天",
                        "channel": pricing.get('channel_name', '官方渠道')})
                except Exception:
                    pass
            threading.Thread(target=_work, daemon=True).start()
        except Exception:
            pass

    # ---------------- UI 构建 ----------------
    def _build(self):
        """方案 6 · 嵌套面板：标题行(图标徽章+红点) + 灰面板(账户/状态/输入/提示) + 墨色按钮"""
        # 双层同格布局：影子宿主(仅出阴影) + 圆角容器。
        # 阴影效果绝不能挂在容器上——样式化 QLineEdit 会破坏效果离屏渲染里的圆角
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        host = QFrame()
        host.setObjectName("ShadowHost")
        host.setAttribute(Qt.WA_StyledBackground, True)
        host.setStyleSheet(
            "QFrame#ShadowHost{background:#000000;border:none;"
            "border-radius:18px;margin:16px;margin-bottom:24px;}")

        # QFrame 才支持 QSS border/border-radius（普通 QWidget 只画背景 → 四角永远直角）
        container = QFrame()
        container.setObjectName("C")
        container.setAttribute(Qt.WA_StyledBackground, True)
        container.setStyleSheet(self.st["container"])

        layout.addWidget(host, 0, 0)
        layout.addWidget(container, 0, 0)

        # 子控件直接挂在样式化 QFrame 上（不夹普通 QWidget 层，避免方形底盖掉圆角）
        cl = QVBoxLayout(container)
        cl.setContentsMargins(22, 20, 22, 22)
        cl.setSpacing(12)

        # 标题行：图标徽章 + 标题 + 红点关闭
        hr = QHBoxLayout()
        icon = QLabel()
        icon.setPixmap(load_svg_icon("member", 18).pixmap(
            int(round(18 * ICON_SCALE)), int(round(18 * ICON_SCALE))))
        icon.setStyleSheet(
            f"background:{self.st.get('chip', '#F5F5F7')};border:none;border-radius:9px;")
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignCenter)
        hr.addWidget(icon)
        hr.addSpacing(10)
        tl = QLabel("账户与激活")
        tl.setStyleSheet(self.st["title"])
        hr.addWidget(tl, 1)
        close_btn = QPushButton("")
        close_btn.setFixedSize(16, 16)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setStyleSheet(self.st["close"])
        close_btn.clicked.connect(self.close)
        hr.addWidget(close_btn)
        cl.addLayout(hr)

        # 嵌套灰面板：账户 / 状态 / 激活码输入 / 提示
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setAttribute(Qt.WA_StyledBackground, True)
        panel.setStyleSheet(self.st.get(
            "panel", "QFrame#Panel{background:#F5F5F7;border:none;border-radius:14px;}"))
        pv = QVBoxLayout(panel)
        pv.setContentsMargins(14, 14, 14, 14)
        pv.setSpacing(10)

        self.user_label = QLabel(f"当前账户：{self.username or '（未登录）'}")
        self.user_label.setStyleSheet(
            f"font-size:13px;color:{self.st['muted']};background:transparent;")
        pv.addWidget(self.user_label)

        self.status_card = QLabel()
        self.status_card.setAlignment(Qt.AlignCenter)
        self.status_card.setWordWrap(True)
        self._set_status_style("#FFFFFF", "#1C1C1E")
        pv.addWidget(self.status_card)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("请输入激活码，如 A1B2C3D4E5F6")
        self.code_input.setFixedHeight(42)
        self.code_input.setStyleSheet(self.st["input"].format())
        self.code_input.returnPressed.connect(self._on_activate)
        pv.addWidget(self.code_input)

        tip = QLabel("输入激活码开通 / 续费 VIP 会员（每码 1 个月起）")
        tip.setStyleSheet(f"font-size:13px;color:{self.st['muted']};background:transparent;")
        pv.addWidget(tip)
        cl.addWidget(panel)

        # 激活按钮（墨色 · 胶囊形）：居中不再通栏，42 高配 21 圆角
        btn_row = QHBoxLayout()
        self.activate_btn = QPushButton("立即激活")
        self.activate_btn.setFixedSize(220, 42)
        self.activate_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.activate_btn.setStyleSheet(self.st["button"].format())
        self.activate_btn.clicked.connect(self._on_activate)
        btn_row.addStretch()
        btn_row.addWidget(self.activate_btn)
        btn_row.addStretch()
        cl.addLayout(btn_row)

        # 结果消息
        self.msg_label = QLabel("")
        self.msg_label.setWordWrap(True)
        self.msg_label.setStyleSheet(
            f"font-size:13px;color:{self.st['muted']};background:transparent;")
        cl.addWidget(self.msg_label)

        # 购买引导
        buy_row = QHBoxLayout()
        self.buy_label = QLabel()
        self.buy_label.setCursor(QCursor(Qt.PointingHandCursor))
        self.buy_label.setStyleSheet(
            f"font-size:14px;color:{self.st['link']};background:transparent;")
        self.buy_label.linkActivated.connect(self._open_buy)
        buy_row.addWidget(self.buy_label)
        buy_row.addStretch()
        cl.addLayout(buy_row)

        layout.addWidget(container)

    # ---------------- 状态刷新 ----------------
    def _set_status_style(self, bg, fg):
        """状态卡配色随权益状态变化，形状跟随当前风格预设"""
        self.status_card.setStyleSheet(self.st["status"].format(bg=bg, fg=fg))

    def _refresh_status(self):
        """异步加载权益/价格/渠道（网络请求全在后台线程，UI 只做最终赋值）。
        分两阶段：先取权益（快，~1s）刷状态卡；再解析购买链接（可能多次 URL 探测）补购买行。"""
        import threading
        username = self.username

        def _apply(data):
            self._status_ready.emit(data)

        def _work():
            # 阶段1：权益状态（Supabase 查询，通常 <1s）
            ent = None
            if username:
                try:
                    ent = get_entitlement(username)
                except Exception:
                    ent = None
            _apply({"ent": ent, "url": None, "price_txt": "", "channel": ""})
            # 阶段2：价格 + 渠道地址（冷缓存时逐个探测候选域名，每个 3s 超时）
            data = {"ent": None, "url": "", "price_txt": "", "channel": "官方渠道"}
            try:
                pricing = get_pricing()
                plan = pricing.get('plan_1', {})
                data['price_txt'] = f"¥{plan.get('price', 99):.0f}/{plan.get('months', 1) * 30}天"
                data['channel'] = pricing.get('channel_name', '官方渠道')
                url = pricing.get('channel_url', '')
                try:
                    data['url'] = resolve_channel_url(url) or url
                except Exception:
                    data['url'] = url
            except Exception:
                pass
            _apply(data)

        threading.Thread(target=_work, daemon=True).start()

    def _apply_status(self, data):
        """把后台取到的数据刷到 UI（仅主线程调用）。url=None 表示本次只刷权益不刷购买行"""
        if data.get('price_txt'):
            price_txt = data.get('price_txt', '')
            channel = data.get('channel', '官方渠道')
            url = data.get('url', '')
            if url and not url.startswith('TODO_'):
                link = self.st['link']
                self.buy_label.setText(
                    f'<a href="{url}" style="color:{link};text-decoration:none;">'
                    f'没有激活码？去 {channel} 购买（{price_txt}）→</a>')
            else:
                self.buy_label.setText(f"购买渠道即将开放（{price_txt}），可先联系客服获取激活码")

        ent = data.get('ent')
        if ent is None:
            if not self.username:
                self.status_card.setText("未登录，请先登录后再激活")
            else:
                self.status_card.setText("会员状态获取失败（网络异常），可稍后重试")
            return
        if ent.get('is_vip') and ent.get('vip_end'):
            self.status_card.setText(f"👑 VIP 会员 · 有效期至 {ent['vip_end']}")
            self._set_status_style("rgba(52,199,89,0.12)", "#248A3D")
        elif ent.get('trial_valid'):
            self.status_card.setText(f"试用中 · 剩余 {ent['trial_end']} 到期")
            self._set_status_style("rgba(255,149,0,0.12)", "#C93400")
        elif ent.get('has_access'):
            self.status_card.setText("当前为全功能访问（离线模式）")
        else:
            self.status_card.setText("试用已过期 · 输入激活码即可恢复全功能")
            self._set_status_style("rgba(255,59,48,0.10)", "#D70015")

    # ---------------- 激活动作 ----------------
    def _on_activate(self):
        code = self.code_input.text().strip()
        if not code:
            self._show_msg("请输入激活码", RED)
            return
        if not self.username:
            self._show_msg("请先登录后再激活", RED)
            return
        self.activate_btn.setEnabled(False)
        self.activate_btn.setText("正在激活…")
        self.msg_label.setStyleSheet(
            f"font-size:12px;color:{self.st['muted']};background:transparent;")
        self.msg_label.setText("")

        # 网络请求放后台一拍，避免 UI 冻结
        def _do():
            ok, msg = activate_code(code, self.username)
            QTimer.singleShot(0, lambda: self._on_activate_done(ok, msg))
        QTimer.singleShot(10, _do)

    def _on_activate_done(self, ok, msg):
        self.activate_btn.setEnabled(True)
        self.activate_btn.setText("立即激活")
        if ok:
            self._show_msg(f"✅ {msg}", GREEN)
            self.code_input.clear()
            self._refresh_status()
        else:
            self._show_msg(f"❌ {msg}", RED)

    def _show_msg(self, text, color):
        self.msg_label.setText(text)
        self.msg_label.setStyleSheet(
            f"font-size:12px;font-weight:600;color:{color};background:transparent;")

    def _open_buy(self, url):
        if url and not url.startswith('TODO_'):
            QDesktopServices.openUrl(QUrl(url))

    # ---------------- 窗口效果 ----------------
    def _add_shadow(self):
        """阴影挂在影子宿主上（容器不能挂效果，否则样式化输入框破坏圆角）"""
        host = self.findChild(QFrame, "ShadowHost")
        if host:
            blur, color = self.st["shadow"]
            s = QGraphicsDropShadowEffect()
            s.setBlurRadius(blur)
            s.setColor(QColor(*color))
            s.setOffset(0, 8)
            host.setGraphicsEffect(s)

    def _center(self):
        p = self.parent()
        if p:
            r = p.geometry()
            self.move(r.center().x() - self.width() // 2,
                      r.center().y() - self.height() // 2)
        else:
            s = QApplication.primaryScreen().geometry()
            self.move(s.center().x() - self.width() // 2,
                      s.center().y() - self.height() // 2)

    def _fade_in(self):
        self.a = QPropertyAnimation(self, b"windowOpacity")
        self.a.setDuration(180)
        self.a.setStartValue(0.0)
        self.a.setEndValue(1.0)
        self.a.setEasingCurve(QEasingCurve.OutCubic)
        self.a.start()

    def showEvent(self, event):
        # polish 阶段全局主题会给 QDialog 打上 WA_StyledBackground 并刷白底（方角），
        # 在 showEvent（polish 之后）清掉，让弹窗本体保持透明，只露出圆角容器
        self.setAttribute(Qt.WA_StyledBackground, False)
        super().showEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)
