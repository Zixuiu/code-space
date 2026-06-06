import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from word_processor import process_word_document

# 字体大小设置
FIRST_LINE_FONT_SIZE = 13.5
BOLD_FONT_SIZE = 12  # 小四对应12磅


class WordProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Word文档处理工具")
        self.root.geometry("600x450")
        
        # 设置变量
        self.input_file = tk.StringVar()
        self.output_file = tk.StringVar()
        self.input_folder = tk.StringVar()
        self.clear_borders = tk.BooleanVar(value=True)
        self.set_font = tk.BooleanVar(value=True)
        self.clean_content = tk.BooleanVar(value=True)
        
        # 创建界面
        self.create_widgets()
    
    def create_widgets(self):
        # 创建样式
        style = ttk.Style()
        style.configure("Bold.TLabelframe.Label", font=("微软雅黑", BOLD_FONT_SIZE, "bold"))
        style.configure("Bold.TLabel", font=("微软雅黑", BOLD_FONT_SIZE, "bold"))
        style.configure("FirstLine.TLabel", font=("微软雅黑", FIRST_LINE_FONT_SIZE))
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(self.root, text="文件选择", padding=10, style="Bold.TLabelframe")
        file_frame.pack(fill="x", padx=10, pady=5)
        
        # 输入文件
        ttk.Label(file_frame, text="输入文件:", style="FirstLine.TLabel").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(file_frame, textvariable=self.input_file, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="浏览", command=self.browse_input_file).grid(row=0, column=2, pady=5)
        
        # 输出文件
        ttk.Label(file_frame, text="输出文件:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(file_frame, textvariable=self.output_file, width=50).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="浏览", command=self.browse_output_file).grid(row=1, column=2, pady=5)
        
        # 文件夹处理区域
        folder_frame = ttk.LabelFrame(self.root, text="文件夹批量处理", padding=10, style="Bold.TLabelframe")
        folder_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(folder_frame, text="选择文件夹:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(folder_frame, textvariable=self.input_folder, width=50).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(folder_frame, text="浏览文件夹", command=self.browse_input_folder).grid(row=0, column=2, pady=5)
        
        ttk.Label(folder_frame, text="警告: 处理后将直接替换原文件，请确保已备份重要文件！", foreground="#ff0000").grid(row=1, column=0, columnspan=3, sticky="w", pady=2)
        
        # 处理选项区域
        options_frame = ttk.LabelFrame(self.root, text="处理选项", padding=10, style="Bold.TLabelframe")
        options_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Checkbutton(options_frame, text="清除表格边框", variable=self.clear_borders).pack(anchor="w", pady=2)
        ttk.Checkbutton(options_frame, text="设置字体为微软雅黑", variable=self.set_font).pack(anchor="w", pady=2)
        ttk.Checkbutton(options_frame, text="清理文档内容(删除多余空格、空行、空段落)", variable=self.clean_content).pack(anchor="w", pady=2)
        
        # 处理按钮
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="处理单个文档", command=self.process_document).pack(side="left", padx=5)
        ttk.Button(button_frame, text="批量处理文件夹", command=self.process_folder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit).pack(side="right", padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def browse_input_file(self):
        file_path = filedialog.askopenfilename(
            title="选择Word文档",
            filetypes=[("Word文档", "*.docx"), ("所有文件", "*.*")]
        )
        if file_path:
            self.input_file.set(file_path)
            # 如果输出文件为空，自动设置输出文件名
            if not self.output_file.get():
                base_name = os.path.splitext(file_path)[0]
                self.output_file.set(f"{base_name}_processed.docx")
    
    def browse_output_file(self):
        file_path = filedialog.asksaveasfilename(
            title="保存处理后的文档",
            defaultextension=".docx",
            filetypes=[("Word文档", "*.docx"), ("所有文件", "*.*")]
        )
        if file_path:
            self.output_file.set(file_path)
    
    def process_document(self):
        input_path = self.input_file.get()
        output_path = self.output_file.get()
        
        if not input_path:
            messagebox.showerror("错误", "请选择输入文件")
            return
        
        if not output_path:
            messagebox.showerror("错误", "请指定输出文件")
            return
        
        if not os.path.exists(input_path):
            messagebox.showerror("错误", f"输入文件不存在: {input_path}")
            return
        
        # 禁用按钮，防止重复点击
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            # 处理文档
            result = process_word_document(
                input_path,
                output_path,
                self.clear_borders.get(),
                self.set_font.get(),
                self.clean_content.get()
            )
            
            if result:
                messagebox.showinfo("成功", f"文档处理完成！\n已保存到: {result}")
                self.status_var.set(f"处理完成: {os.path.basename(result)}")
            else:
                messagebox.showerror("错误", "文档处理失败")
                self.status_var.set("处理失败")
        except Exception as e:
            messagebox.showerror("错误", f"处理文档时出错: {str(e)}")
            self.status_var.set(f"处理出错: {str(e)}")
        finally:
            # 恢复鼠标指针
            self.root.config(cursor="")
    
    def process_folder(self):
        """批量处理文件夹中的所有Word文档并直接替换原文件"""
        input_folder = self.input_folder.get()
        
        if not input_folder:
            messagebox.showerror("错误", "请选择要处理的文件夹")
            return
        
        if not os.path.exists(input_folder):
            messagebox.showerror("错误", f"文件夹不存在: {input_folder}")
            return
        
        # 显示确认对话框，提醒用户会直接替换原文件
        confirm = messagebox.askyesno("确认操作", "处理后将直接替换原文件，建议先备份重要文件！\n\n确定要继续吗？")
        if not confirm:
            return
        
        # 收集所有.docx文件
        docx_files = [f for f in os.listdir(input_folder) 
                     if f.lower().endswith('.docx') and os.path.isfile(os.path.join(input_folder, f))]
        
        if not docx_files:
            messagebox.showinfo("提示", "所选文件夹中没有找到Word文档(.docx)")
            return
        
        # 禁用按钮，防止重复点击
        self.root.config(cursor="watch")
        self.root.update()
        
        success_count = 0
        fail_count = 0
        fail_files = []
        
        try:
            # 显示进度条对话框
            progress_window = tk.Toplevel(self.root)
            progress_window.title("处理进度")
            progress_window.geometry("400x120")
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            ttk.Label(progress_window, text="正在批量处理文档...").pack(pady=10)
            
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100)
            progress_bar.pack(fill="x", padx=20, pady=10)
            
            status_label = ttk.Label(progress_window, text="准备开始处理...")
            status_label.pack(pady=5)
            
            # 处理每个文件
            for i, filename in enumerate(docx_files):
                # 更新进度
                progress = (i + 1) / len(docx_files) * 100
                progress_var.set(progress)
                status_label.config(text=f"正在处理: {filename}")
                progress_window.update()
                
                # 设置文件路径（输入和输出路径相同，直接替换原文件）
                file_path = os.path.join(input_folder, filename)
                
                # 处理文档
                try:
                    result = process_word_document(
                        file_path,
                        file_path,  # 输出路径与输入路径相同，直接替换
                        self.clear_borders.get(),
                        self.set_font.get(),
                        self.clean_content.get()
                    )
                    
                    if result:
                        success_count += 1
                    else:
                        fail_count += 1
                        fail_files.append(filename)
                except Exception as e:
                    fail_count += 1
                    fail_files.append(f"{filename} - 错误: {str(e)}")
            
            # 关闭进度窗口
            progress_window.destroy()
            
            # 显示处理结果
            result_msg = f"批量处理完成！\n" \
                       f"成功: {success_count} 个文件\n" \
                       f"失败: {fail_count} 个文件\n" \
                       f"文件已直接替换原文件"
            
            if fail_files:
                result_msg += "\n\n失败的文件:"
                for fail_file in fail_files[:5]:  # 只显示前5个失败的文件
                    result_msg += f"\n- {fail_file}"
                if len(fail_files) > 5:
                    result_msg += f"\n... 还有 {len(fail_files) - 5} 个失败文件"
            
            messagebox.showinfo("批量处理结果", result_msg)
            self.status_var.set(f"批量处理完成: 成功{success_count}个，失败{fail_count}个")
            
        except Exception as e:
            messagebox.showerror("错误", f"批量处理时出错: {str(e)}")
            self.status_var.set(f"批量处理出错: {str(e)}")
        finally:
            # 恢复鼠标指针
            self.root.config(cursor="")
    
    def browse_input_folder(self):
        """选择输入文件夹"""
        folder_path = filedialog.askdirectory(title="选择要处理的文件夹")
        if folder_path:
            self.input_folder.set(folder_path)


if __name__ == "__main__":
    root = tk.Tk()
    app = WordProcessorGUI(root)
    root.mainloop()