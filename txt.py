import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import re
import chardet
import ctypes

class NovelMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("小说整合工具")
        
        # 设置窗口尺寸
        window_width = 1650
        window_height = 800
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")  # 设置窗口居中
        
        # 启用高DPI支持，解决缩放问题
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        self.root.tk.call('tk', 'scaling', 1.5)  # 设置缩放因子为1.5，根据需要调整
        
        # 设置字体为微软雅黑
        font = ('Microsoft YaHei', 12)

        # 初始化变量
        self.loaded_file = None
        self.chapter_list = []
        self.chapter_contents = {}

        # 布局：第一行 - 按钮
        self.button_frame = ttk.Frame(root)
        self.button_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.open_button = ttk.Button(self.button_frame, text="打开文件", command=self.open_file)
        self.open_button.grid(row=0, column=0, padx=5)
        
        self.save_button = ttk.Button(self.button_frame, text="保存", command=self.save_file)
        self.save_button.grid(row=0, column=1, padx=5)
        
        self.exit_button = ttk.Button(self.button_frame, text="退出", command=self.exit_app)
        self.exit_button.grid(row=0, column=2, padx=5)

        # 布局：第二行 - 章节列表和内容显示
        self.chapter_frame = ttk.Frame(root)
        self.chapter_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # 章节列表和滚动条
        self.chapter_listbox = tk.Listbox(self.chapter_frame, height=20, width=40, font=font)
        self.chapter_listbox.grid(row=0, column=0, sticky="nsew")

        self.chapter_scrollbar = ttk.Scrollbar(self.chapter_frame, orient=tk.VERTICAL, command=self.chapter_listbox.yview)
        self.chapter_scrollbar.grid(row=0, column=1, sticky="ns")
        self.chapter_listbox.config(yscrollcommand=self.chapter_scrollbar.set)
        
        self.chapter_listbox.bind("<<ListboxSelect>>", self.show_chapter_content)

        # 章节内容显示和滚动条
        self.content_frame = ttk.Frame(root)
        self.content_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")

        self.content_text = tk.Text(self.content_frame, height=20, width=100, font=font)
        self.content_text.grid(row=0, column=0, sticky="nsew")

        self.content_scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.content_text.yview)
        self.content_scrollbar.grid(row=0, column=1, sticky="ns")
        self.content_text.config(yscrollcommand=self.content_scrollbar.set)

        # 布局：第三行 - 添加和删除章节按钮
        self.add_button = ttk.Button(root, text="添加", command=self.add_chapter)
        self.add_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        self.delete_button = ttk.Button(root, text="删除", command=self.delete_chapter)
        self.delete_button.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        
        # 布局：第四行 - 日志显示区域
        self.log_frame = ttk.Frame(root)
        self.log_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.log_text = tk.Text(self.log_frame, height=5, width=150, font=font, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=self.scrollbar.set)

        # 启用拖放功能
        self.root.drop_target_register(DND_FILES)  # 注册拖放文件目标
        self.root.dnd_bind('<<Drop>>', self.on_file_drop)  # 绑定拖放事件
        
        # 自适应窗口大小
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=2)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                encoding = chardet.detect(raw_data)['encoding']
                content = raw_data.decode(encoding)

                self.chapter_list = []
                self.chapter_contents = {}
                
                # 按章节拆分内容
                chapters = content.split('\n')
                chapter_name = None
                chapter_content = []
                
                for line in chapters:
                    if line.startswith("第") and "章" in line:
                        if chapter_name:
                            self.chapter_contents[chapter_name] = "\n".join(chapter_content)
                        chapter_name = line.strip()
                        chapter_content = []
                    else:
                        chapter_content.append(line.strip())
                
                # 添加最后一章
                if chapter_name:
                    self.chapter_contents[chapter_name] = "\n".join(chapter_content)
                
                # 更新章节列表
                self.chapter_listbox.delete(0, tk.END)
                for chapter in self.chapter_contents.keys():
                    self.chapter_listbox.insert(tk.END, chapter)
                
                self.loaded_file = file_path

                # Log the action
                self.log("文件已打开")

    def show_chapter_content(self, event):
        selection = self.chapter_listbox.curselection()
        if selection:
            chapter_name = self.chapter_listbox.get(selection[0])
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, self.chapter_contents.get(chapter_name, ""))

    def save_file(self):
        if not self.loaded_file:
            self.log("没有加载文件，无法保存!")
            return
        
        with open(self.loaded_file, 'w', encoding='utf-8') as file:
            for chapter in self.chapter_listbox.get(0, tk.END):  # 使用listbox中的章节顺序
                content = self.chapter_contents.get(chapter, "")
                file.write(f"{chapter}\n")
                file.write(f"{content}\n\n")
        
        self.log("文件已保存！")

    def exit_app(self):
        if self.loaded_file:
            self.save_file()
        self.loaded_file = None
        self.chapter_list = []
        self.chapter_contents = {}
        self.chapter_listbox.delete(0, tk.END)
        self.content_text.delete(1.0, tk.END)

        self.log("应用已退出")

    def add_chapter(self):
        if not self.loaded_file:
            self.log("没有加载文件，无法添加章节!")
            return
        
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.add_chapter_from_file(file_path)

    def add_chapter_from_file(self, file_path):
        with open(file_path, 'rb') as new_file:
            raw_data = new_file.read()

            # 使用chardet检测文件编码
            encoding = chardet.detect(raw_data)['encoding']
            
            # 尝试解码，若解码失败则忽略错误
            try:
                new_content = raw_data.decode(encoding, errors='ignore')  # 忽略无法解码的字符
            except UnicodeDecodeError:
                # 如果解码失败，尝试其他常见编码
                self.log(f"无法用 {encoding} 解码，尝试用其他编码...")
                for enc in ['utf-8', 'gbk', 'gb2312', 'big5']:
                    try:
                        new_content = raw_data.decode(enc, errors='ignore')
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    self.log(f"无法解码文件 {file_path}，请检查文件编码！")
                    return  # 如果无法解码，退出

            # 检查并移除以 "第*章" 开头的行
            new_content_lines = new_content.split("\n")
            for i, line in enumerate(new_content_lines):
                if re.match(r"^第\d+章", line.strip()):
                    new_content_lines.pop(i)
                    break
            new_content = "\n".join(new_content_lines)
            
            # 使用文件名创建新的章节名
            new_chapter_name = f"第{len(self.chapter_contents) + 1}章 - {os.path.splitext(os.path.basename(file_path))[0]}"

            # 检查是否已存在相同章节
            for chapter_name, content in self.chapter_contents.items():
                if content == new_content:
                    self.log(f"章节 '{new_chapter_name}' 已存在，跳过导入。")
                    return  # 如果内容相同，则跳过

            # 检查是否需要更新已有章节
            if new_content > self.chapter_contents.get(new_chapter_name, ""):
                self.chapter_contents[new_chapter_name] = new_content
                self.log(f"章节 '{new_chapter_name}' 已更新。")
            else:
                self.chapter_contents[new_chapter_name] = new_content
                self.log(f"章节 '{new_chapter_name}' 已添加。")
            
            # 更新列表框并显示内容
            self.chapter_listbox.insert(tk.END, new_chapter_name)
            self.chapter_listbox.selection_set(tk.END)
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(tk.END, new_content)

    def delete_chapter(self):
        selection = self.chapter_listbox.curselection()
        if selection:
            chapter_name = self.chapter_listbox.get(selection[0])
            del self.chapter_contents[chapter_name]
            self.chapter_listbox.delete(selection[0])
            self.content_text.delete(1.0, tk.END)
            self.log(f"章节 '{chapter_name}' 已删除！")
        else:
            self.log("请选择一个章节进行删除！")

    def on_file_drop(self, event):
        file_path = event.data.strip()  # 去掉路径两端的空白字符
        print(file_path)  # 打印拖拽的文件路径，检查路径是否正确

        # 处理可能包含大括号的网络路径（某些网络路径会被大括号包裹）
        if file_path.startswith('{') and file_path.endswith('}'):  # 检查路径是否被大括号包裹
            file_path = file_path[1:-1]  # 去掉路径两端的花括号

        # 确保路径指向的是一个txt文件
        if file_path.endswith(".txt"):  
            self.add_chapter_from_file(file_path)  # 如果是txt文件，调用方法添加章节
        else:
            self.log("请拖放一个有效的txt文件！")  # 如果不是txt文件，弹出警告

    def log(self, message):
        """ 将日志消息显示到日志框 """
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.yview(tk.END)  # 滚动到最新的日志

if __name__ == "__main__":
    root = TkinterDnD.Tk()  # 使用TkinterDnD.Tk()代替tk.Tk()
    app = NovelMergerApp(root)
    root.mainloop()
