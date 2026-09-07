# -*- coding: utf-8 -*-
"""
PC-action 账户与激活对话框（方案 6 · 嵌套面板）
- 展示当前权益：VIP 到期日 / 试用剩余天数 / 已过期
- 购买引导（pricing.json 的 channel_url；PayPro 部署后回填生效）
- 已取消激活码卡密模式：VIP 统一改为“付款自动开通到登录邮箱”方式
"""
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QUrl, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QDesktopServices
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QGraphicsDropShadowEffect, QApplication, QFrame,
)

from beautiful_dialog import load_svg_icon, ICON_SCALE
from entitlement import (get_pricing, get_entitlement,
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
                        "channel": pricing.get('channel_name', '官方渠道'),
                        "stage": 2})
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

        # 嵌套灰面板：账户 / 状态
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
        cl.addWidget(panel)

        # 付款开通引导（激活码已取消：VIP 付款后自动开通到登录邮箱）
        hint = QLabel("开通 / 续费 VIP 请点击下方购买入口。\n付款成功后 VIP 将自动开通到您的登录邮箱")
        hint.setWordWrap(True)
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet(
            f"font-size:13px;color:{self.st['muted']};background:transparent;")
        cl.addWidget(hint)

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
            _apply({"ent": ent, "url": None, "price_txt": "", "channel": "", "stage": 1})
            # 阶段2：价格 + 渠道地址（冷缓存时逐个探测候选域名，每个 3s 超时）
            data = {"ent": None, "url": "", "price_txt": "", "channel": "官方渠道", "stage": 2}
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
        """把后台取到的数据刷到 UI（仅主线程调用）。
        修复：阶段1(page=1)才刷新状态卡；阶段2只是价格/地址刷新，ent=None，
        绝不能覆盖掉已正确展示的会员状态（曾导致"会员状态获取失败"误报）。"""
        # 价格/购买链接（阶段1空串不刷，阶段2填入）
        if data.get('price_txt'):
            price_txt = data.get('price_txt', '')
            channel = data.get('channel', '官方渠道')
            url = data.get('url', '')
            if url and not url.startswith('TODO_'):
                link = self.st['link']
                self.buy_label.setText(
                    f'<a href="{url}" style="color:{link};text-decoration:none;">'
                    f'前往 {channel} 开通 / 续费 VIP（{price_txt}）→</a>')
            else:
                self.buy_label.setText(f"购买渠道即将开放（{price_txt}），可先联系客服开通 VIP")

        # 只有阶段1才刷新会员状态；阶段2不带权益，直接返回
        if data.get('stage', 1) != 1:
            return

        ent = data.get('ent')
        if not self.username:
            self.status_card.setText("未登录，请先登录后再开通 / 续费 VIP")
            return
        if ent is None:
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
            self.status_card.setText("试用已过期 · 点击下方入口付款开通 VIP 即可恢复全功能")
            self._set_status_style("rgba(255,59,48,0.10)", "#D70015")

    # ---------------- 购买跳转 ----------------
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
