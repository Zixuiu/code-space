import tkinter as tk
from tkinter import ttk

class EnterpriseSalesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SalesForce Pro - 智能销售管理平台")
        
        # 🚀 核心改变1：全屏启动，占据整个显示器
        self.root.state('zoomed') 
        
        # 现代化配色方案
        self.bg_dark = "#0F172A"
        self.bg_sidebar = "#1E293B"
        self.accent_blue = "#3B82F6"
        self.accent_green = "#10B981"
        self.accent_purple = "#8B5CF6"
        self.text_white = "#F8FAFC"
        self.text_gray = "#94A3B8"
        self.bg_main = "#F1F5F9"
        self.bg_card = "#FFFFFF"
        
        self.current_btn = None

        self.setup_layout()
    def show_add_lead_dialog(self):
        # 创建模态弹窗
        dialog = tk.Toplevel(self.root)
        dialog.title("录入新客户")
        dialog.geometry("450x400")
        dialog.configure(bg="white")
        dialog.resizable(False, False)
        # 设置模态
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 450) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 400) // 2
        dialog.geometry(f"+{x}+{y}")

        # 标题
        tk.Label(dialog, text="新增销售线索", font=("微软雅黑", 16, "bold"), bg="white", fg="#0F172A").pack(anchor="w", padx=30, pady=(25, 20))
        
        # 表单字段 (对应销售系统/1.py的数据结构)
        fields = ["客户名称", "预计金额(万)", "当前阶段", "负责人"]
        entries = {}
        
        stages = ["线索", "沟通", "报价", "谈判", "成交"] # 对应销售系统漏斗阶段
        
        for field in fields:
            frame = tk.Frame(dialog, bg="white")
            frame.pack(fill=tk.X, padx=30, pady=8)
            tk.Label(frame, text=field, font=("微软雅黑", 11), bg="white", fg="#64748B").pack(anchor="w")
            
            if field == "当前阶段":
                combo = ttk.Combobox(frame, values=stages, state="readonly", font=("微软雅黑", 11))
                combo.set(stages[0])
                combo.pack(fill=tk.X, pady=(5, 0))
                entries[field] = combo
            else:
                entry = tk.Entry(frame, font=("微软雅黑", 11), bg="#F8FAFC", relief="flat", highlightthickness=1, highlightcolor=self.accent_blue)
                entry.pack(fill=tk.X, pady=(5, 0), ipady=4)
                entries[field] = entry

        # 底部按钮
        btn_frame = tk.Frame(dialog, bg="white")
        btn_frame.pack(fill=tk.X, padx=30, pady=25, side=tk.BOTTOM)
        
        def submit():
            comp = entries["客户名称"].get().strip()
            if not comp:
                tk.messagebox.showwarning("提示", "客户名称不能为空", parent=dialog)
                return
            
            # 获取表格对象并插入数据
            if hasattr(self, 'current_tree') and self.current_tree:
                amt = entries["预计金额(万)"].get() or "0"
                stage = entries["当前阶段"].get()
                user = entries["负责人"].get() or "未分配"
                
                # 阶段映射 emoji
                stage_map = {"线索": "⚪", "沟通": "🟡", "报价": "🔵", "谈判": "🟢", "成交": "🟣"}
                stage_text = f"{stage_map.get(stage, '')} {stage}"
                
                self.current_tree.insert("", tk.END, values=(comp, stage_text, f"¥{amt}万", "待评估", user))
                self.current_tree.update_idletasks()
            
            dialog.destroy()

        tk.Button(btn_frame, text="取消", font=("微软雅黑", 11), bg="#F1F5F9", fg="#64748B", bd=0, padx=20, pady=8, command=dialog.destroy).pack(side=tk.RIGHT, padx=(10, 0))
        tk.Button(btn_frame, text="提交线索", font=("微软雅黑", 11, "bold"), bg=self.accent_blue, fg="white", bd=0, padx=20, pady=8, command=submit).pack(side=tk.RIGHT)

    def setup_layout(self):
        # --- 左侧导航栏 (更宽) ---
        self.sidebar = tk.Frame(self.root, bg=self.bg_sidebar, width=260)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        # Logo 区域
        top_area = tk.Frame(self.sidebar, bg=self.bg_sidebar)
        top_area.pack(fill=tk.X, pady=(40, 50), padx=24)
        tk.Label(top_area, text="Sales", font=("Arial", 26, "bold"), bg=self.bg_sidebar, fg=self.text_white).pack(side=tk.LEFT)
        tk.Label(top_area, text="Pro", font=("Arial", 26, "bold"), bg=self.bg_sidebar, fg=self.accent_blue).pack(side=tk.LEFT)
        tk.Label(self.header, text="👤 管理员", font=("微软雅黑", 12), bg="white", fg="#64748B").pack(side=tk.RIGHT, padx=40)
        
        # 🚀 新增：录入客户按钮
        add_btn = tk.Button(self.header, text="＋ 录入客户", font=("微软雅黑", 11, "bold"), 
                            bg=self.accent_blue, fg="white", bd=0, padx=20, pady=6,
                            cursor="hand2", command=self.show_add_lead_dialog)
        add_btn.pack(side=tk.RIGHT, padx=10)

        # 菜单按钮
        menus = [
            ("📊  工作台", self.show_dashboard),
            ("🤖  AI 客户分析", self.show_ai),
            ("🎭  场景与话术", self.show_scenarios),
            ("📚  知识库", self.show_knowledge)
        ]

        for text, cmd in menus:
            btn = tk.Label(self.sidebar, text=text, font=("微软雅黑", 13), 
                           bg=self.bg_sidebar, fg=self.text_gray, anchor="w", padx=24, pady=14,
                           cursor="hand2")
            btn.pack(fill=tk.X, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#334155", fg=self.text_white) if b != self.current_btn else None)
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.bg_sidebar, fg=self.text_gray) if b != self.current_btn else None)
            btn.bind("<Button-1>", lambda e, b=btn, c=cmd: self.select_menu(b, c))

        # --- 右侧主内容区 ---
        self.main_area = tk.Frame(self.root, bg=self.bg_main)
        self.main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 顶部标题栏 (模拟官方顶栏)
        self.header = tk.Frame(self.main_area, bg="white", height=70)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)
        self.header_title = tk.Label(self.header, text="工作台", font=("微软雅黑", 18, "bold"), bg="white", fg="#0F172A")
        self.header_title.pack(side=tk.LEFT, padx=40)
        
        # 模拟右上角用户头像
        tk.Label(self.header, text="👤 管理员", font=("微软雅黑", 12), bg="white", fg="#64748B").pack(side=tk.RIGHT, padx=40)
        
        # 内容容器 (增加内边距)
        self.content = tk.Frame(self.main_area, bg=self.bg_main)
        self.content.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)

        # 默认选中第一个
        self.select_menu(self.sidebar.winfo_children()[2], self.show_dashboard)

    def select_menu(self, btn_widget, cmd):
        for widget in self.sidebar.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=self.bg_sidebar, fg=self.text_gray)
        
        btn_widget.config(bg="#334155", fg=self.text_white)
        self.current_btn = btn_widget
        
        self.header_title.config(text=btn_widget.cget("text").strip())
        cmd()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def create_stat_card(self, parent, title, value, sub_value, color):
        card = tk.Frame(parent, bg=self.bg_card)
        card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8)
        
        # 顶部彩色线条
        tk.Frame(card, bg=color, height=4).pack(fill=tk.X)
        
        # 🚀 核心改变2：巨大的数据展示，模拟官方大屏数据
        frame = tk.Frame(card, bg=self.bg_card)
        frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)
        
        tk.Label(frame, text=title, font=("微软雅黑", 11), bg=self.bg_card, fg="#64748B").pack(anchor="w")
        tk.Label(frame, text=value, font=("Arial", 32, "bold"), bg=self.bg_card, fg="#0F172A").pack(anchor="w", pady=5)
        tk.Label(frame, text=sub_value, font=("微软雅黑", 10), bg=self.bg_card, fg=color).pack(anchor="w")

    def create_content_card(self, parent, title, height=300):
        card = tk.Frame(parent, bg=self.bg_card)
        card.pack(fill=tk.BOTH, expand=True, pady=(15, 0), padx=8)
        
        header = tk.Frame(card, bg=self.bg_card)
        header.pack(fill=tk.X, padx=24, pady=(20, 10))
        tk.Label(header, text=title, font=("微软雅黑", 14, "bold"), bg=self.bg_card, fg="#0F172A").pack(side=tk.LEFT)
        
        return card

    # ---------------- 以下是各个页面内容 ----------------

    def show_dashboard(self):
        self.clear_content()
        
        # 第一行：核心数据大屏
        stats_frame = tk.Frame(self.content, bg=self.bg_main)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.create_stat_card(stats_frame, "本月销售总额", "¥ 1,258,000", "较上月 +12.5%", self.accent_green)
        self.create_stat_card(stats_frame, "新增线索数", "186", "较上月 +28个", self.accent_blue)
        self.create_stat_card(stats_frame, "平均赢单周期", "32 天", "较上月 -3天", self.accent_purple)
        self.create_stat_card(stats_frame, "本月赢单率", "35.8%", "较上月 +2.1%", self.accent_green)

        # 第二行：销售漏斗表格
        table_card = self.create_content_card(self.content, "销售流程跟进")
        
        style = ttk.Style()
        # 🚀 核心改变3：超大行高，类似Web端表格
        style.configure("Enterprise.Treeview", font=("微软雅黑", 11), rowheight=45, background="white", fieldbackground="white", borderwidth=0)
        style.configure("Enterprise.Treeview.Heading", font=("微软雅黑", 11, "bold"), background="#F8FAFC", foreground="#64748B", borderwidth=0)
        style.map("Enterprise.Treeview", background=[('selected', '#EFF6FF')])

        # 表格区域带内部边距
        tree_frame = tk.Frame(table_card, bg=self.bg_card)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 20))
        
        tree = ttk.Treeview(tree_frame, columns=("名称", "阶段", "金额", "概率", "负责人"), show="headings", style="Enterprise.Treeview")
        tree.heading("名称", text="客户名称")
        tree.heading("阶段", text="当前阶段")
        tree.heading("金额", text="预计金额")
        tree.heading("概率", text="赢单概率")
        tree.heading("负责人", text="负责人")
        
        # 列宽自适应拉伸
        for col in ("名称", "阶段", "金额", "概率", "负责人"):
            tree.column(col, anchor="center", width=100)

        tree.pack(fill=tk.BOTH, expand=True)
        self.current_tree = tree 
        data = [
            ("北京科技A公司", "🟢 谈判", "¥500,000", "80%", "张经理"),
            ("上海制造B集团", "🔵 报价", "¥320,000", "60%", "李主管"),
            ("深圳零售C企业", "🟡 沟通", "¥180,000", "30%", "王销售"),
            ("广州教育D机构", "⚪ 线索", "¥90,000", "10%", "赵新人")
        ]
        for item in data:
            tree.insert("", tk.END, values=item)

    def show_ai(self):
        self.clear_content()
        
        # 顶部统计
        stats_frame = tk.Frame(self.content, bg=self.bg_main)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        self.create_stat_card(stats_frame, "待分析客户总数", "1,245", "AI模型已更新", self.accent_blue)
        self.create_stat_card(stats_frame, "高意向流失预警", "18", "需立即介入", "#EF4444")

        # AI 洞察卡片
        ai_card = self.create_content_card(self.content, "🧠 AI 智能客群聚类与行动建议")
        
        insights = [
            ("🟢 高价值活跃客户", "共 65 人", "该群体购买力强且活跃，建议立即推送年度VIP升级服务，预计转化率可达45%。", self.accent_green),
            ("🟡 高价值沉睡客户", "共 42 人", "该群体有消费能力但近期未互动，建议触发专属挽回优惠券及人工电话回访。", "#F59E0B"),
            ("🔵 低价值活跃客户", "共 93 人", "该群体频次高但客单价低，建议进行组合套餐交叉销售，提升单次购买金额。", self.accent_blue),
            ("🔴 流失预警客户", "共 18 人", "近期投诉率上升或登录骤降，建议安排高级客户经理1对1介入解决痛点。", "#EF4444")
        ]
        
        insight_frame = tk.Frame(ai_card, bg=self.bg_card)
        insight_frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 20))
        
        for title, count, desc, color in insights:
            row = tk.Frame(insight_frame, bg="#F8FAFC")
            row.pack(fill=tk.X, pady=5, padx=5)
            
            tk.Frame(row, bg=color, width=6).pack(side=tk.LEFT, fill=tk.Y, pady=5)
            
            text_frame = tk.Frame(row, bg="#F8FAFC")
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=15, pady=10)
            
            header_row = tk.Frame(text_frame, bg="#F8FAFC")
            header_row.pack(fill=tk.X)
            tk.Label(header_row, text=title, font=("微软雅黑", 12, "bold"), bg="#F8FAFC", fg="#0F172A").pack(side=tk.LEFT)
            tk.Label(header_row, text=count, font=("微软雅黑", 10), bg="#F8FAFC", fg="#64748B").pack(side=tk.LEFT, padx=10)
            
            tk.Label(text_frame, text=desc, font=("微软雅黑", 10), bg="#F8FAFC", fg="#64748B", wraplength=800, justify=tk.LEFT).pack(anchor="w", pady=(2,0))

    def show_scenarios(self):
        self.clear_content()
        
        card = self.create_content_card(self.content, "⚔️ 实战场景与应对策略")
        
        scenarios = [
            ("价格异议", "策略：价值重塑，不比单价比总成本。\n\n话术：王总，单纯看报价我们高一些，但算上节省的20%运维时间，三年总成本其实更低。", self.accent_purple),
            ("竞品比较", "策略：承认竞品，强调差异化与行业经验。\n\n话术：X公司很优秀，但在制造行业我们有50家经验，算法更贴合车间实际，您要不要看看数据对比？", self.accent_blue),
            ("决策拖延", "策略：制造紧迫感，量化拖延成本。\n\n话术：李总，早一天上线每天就能少加2小时班。另外本月底补贴政策就截止了，下月恢复原价差2万块。", "#F59E0B")
        ]
        
        frame = tk.Frame(card, bg=self.bg_card)
        frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 20))
        
        for title, content, color in scenarios:
            row = tk.Frame(frame, bg="white", highlightbackground="#E2E8F0", highlightthickness=1)
            row.pack(fill=tk.X, pady=8)
            
            tk.Frame(row, bg=color, width=6).pack(side=tk.LEFT, fill=tk.Y)
            
            text_frame = tk.Frame(row, bg="white")
            text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=15)
            
            tk.Label(text_frame, text=f"场景：{title}", font=("微软雅黑", 12, "bold"), bg="white", fg="#0F172A").pack(anchor="w")
            tk.Label(text_frame, text=content, font=("微软雅黑", 10), bg="white", fg="#64748B", justify=tk.LEFT).pack(anchor="w", pady=(5,0))

    def show_knowledge(self):
        self.clear_content()
        
        card = self.create_content_card(self.content, "📖 销售知识图谱")
        
        # 使用 Notebook 实现标签页切换 (更符合官方APP交互)
        style = ttk.Style()
        style.configure("TNotebook", background="white", borderwidth=0)
        style.configure("TNotebook.Tab", font=("微软雅黑", 11), padding=[20, 10], background="#F8FAFC")
        style.map("TNotebook.Tab", background=[("selected", "white")], foreground=[("selected", "#3B82F6")])
        
        notebook = ttk.Notebook(card)
        notebook.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 20))
        
        # 标签1：产品知识
        tab1 = tk.Frame(notebook, bg="white")
        notebook.add(tab1, text=" 💻 产品知识 ")
        tk.Label(tab1, text="智能CRM专业版", font=("微软雅黑", 14, "bold"), bg="white", fg="#0F172A").pack(anchor="w", padx=20, pady=20)
        tk.Label(tab1, text="核心卖点：包含AI客户画像、销售预测漏斗、自动化工作流。支持API接入企业微信/钉钉。", font=("微软雅黑", 11), bg="white", fg="#64748B", wraplength=800, justify=tk.LEFT).pack(anchor="w", padx=20)

        # 标签2：话术库
        tab2 = tk.Frame(notebook, bg="white")
        notebook.add(tab2, text=" 🗣️ 话术库 ")
        tk.Label(tab2, text="破冰开场白", font=("微软雅黑", 14, "bold"), bg="white", fg="#0F172A").pack(anchor="w", padx=20, pady=20)
        tk.Label(tab2, text="您好王总，我是[公司]的小张。了解到贵司最近在扩张业务线，想跟您探讨一下如何提升新团队的成单效率，您现在方便接听电话吗？", font=("微软雅黑", 11), bg="white", fg="#64748B", wraplength=800, justify=tk.LEFT).pack(anchor="w", padx=20)

        # 标签3：常见Q&A
        tab3 = tk.Frame(notebook, bg="white")
        notebook.add(tab3, text=" ❓ 常见Q&A ")
        tk.Label(tab3, text="Q: 实施周期多长？", font=("微软雅黑", 12, "bold"), bg="white", fg="#0F172A").pack(anchor="w", padx=20, pady=(20,5))
        tk.Label(tab3, text="A: 标准版1周上线，专业版根据定制需求一般2-4周。", font=("微软雅黑", 11), bg="white", fg="#64748B", wraplength=800, justify=tk.LEFT).pack(anchor="w", padx=20)


if __name__ == "__main__":
    root = tk.Tk()
    app = EnterpriseSalesApp(root)
    root.mainloop()
