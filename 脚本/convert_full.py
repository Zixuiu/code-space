import tkinter as tk
from tkinter import ttk

class ModernSalesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("智能销售系统 Pro")
        self.root.geometry("1100x700")
        self.root.configure(bg="#F0F2F5")
        
        # 取消窗口默认边框，自己做标题栏（更现代）
        self.root.overrideredirect(False) 
        
        # 配色方案 (暗黑科技风)
        self.bg_dark = "#1E1E2E"
        self.bg_medium = "#2D2D44"
        self.accent_color = "#7C3AED" # 紫色强调色
        self.text_light = "#E0E0E0"
        self.text_dark = "#333333"
        self.bg_light = "#F8F9FA"
        
        self.current_btn = None

        self.setup_ui()

    def setup_ui(self):
        # --- 左侧导航栏 ---
        self.sidebar = tk.Frame(self.root, bg=self.bg_dark, width=240)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Logo 区域
        tk.Label(self.sidebar, text="🚀 智能销售", font=("微软雅黑", 18, "bold"), 
                 bg=self.bg_dark, fg="white").pack(pady=(40, 5), anchor="w", padx=20)
        tk.Label(self.sidebar, text="Smart Sales System", font=("Arial", 10), 
                 bg=self.bg_dark, fg="#888888").pack(pady=(0, 40), anchor="w", padx=20)

        # 菜单按钮
        menus = [
            ("📊  销售流程", self.show_pipeline),
            ("🤖  AI 客户分析", self.show_ai),
            ("🎭  销售场景", self.show_scenarios),
            ("📚  知识库", self.show_knowledge)
        ]

        for text, cmd in menus:
            btn = tk.Label(self.sidebar, text=text, font=("微软雅黑", 12), 
                           bg=self.bg_dark, fg=self.text_light, anchor="w", padx=20, pady=12,
                           cursor="hand2")
            btn.pack(fill=tk.X, pady=2)
            # 绑定鼠标事件实现悬停和点击效果
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.bg_medium) if b != self.current_btn else None)
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.bg_dark) if b != self.current_btn else None)
            btn.bind("<Button-1>", lambda e, b=btn, c=cmd: self.select_menu(b, c))

        # --- 右侧主内容区 ---
        self.main_area = tk.Frame(self.root, bg=self.bg_light)
        self.main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 顶部标题栏
        self.header = tk.Frame(self.main_area, bg="white", height=60)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)
        self.header_title = tk.Label(self.header, text="仪表盘", font=("微软雅黑", 14, "bold"), bg="white", fg=self.text_dark)
        self.header_title.pack(side=tk.LEFT, padx=30)
        
        # 内容容器
        self.content = tk.Frame(self.main_area, bg=self.bg_light)
        self.content.pack(fill=tk.BOTH, expand=True, padx=25, pady=20)

        # 默认选中第一个
        self.select_menu(self.sidebar.winfo_children()[2], self.show_pipeline)

    def select_menu(self, btn_widget, cmd):
        # 重置所有按钮状态
        for widget in self.sidebar.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=self.bg_dark, fg=self.text_light)
        
        # 高亮当前按钮
        btn_widget.config(bg=self.bg_medium, fg="white")
        self.current_btn = btn_widget
        
        # 更新标题并执行命令
        self.header_title.config(text=btn_widget.cget("text").strip())
        cmd()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def create_card(self, parent, title, content_text, color="#7C3AED"):
        card = tk.Frame(parent, bg="white", highlightbackground="#E0E0E0", highlightthickness=1)
        card.pack(fill=tk.X, pady=8, padx=5)
        
        # 左侧彩色指示条
        tk.Frame(card, bg=color, width=4).pack(side=tk.LEFT, fill=tk.Y)
        
        text_frame = tk.Frame(card, bg="white")
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=12)
        
        tk.Label(text_frame, text=title, font=("微软雅黑", 11, "bold"), bg="white", fg=self.text_dark).pack(anchor="w")
        tk.Label(text_frame, text=content_text, font=("微软雅黑", 9), bg="white", fg="#666666", justify=tk.LEFT).pack(anchor="w", pady=(4,0))

    # ---------------- 以下是各个页面内容 ----------------

    def show_pipeline(self):
        self.clear_content()
        
        # 数据卡片行
        stats_frame = tk.Frame(self.content, bg=self.bg_light)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        stats = [("💰 总金额池", "¥ 450,000", "#7C3AED"), ("📈 本月新增", "23 个线索", "#10<codegeex-cursor></codegeex-cursor>
