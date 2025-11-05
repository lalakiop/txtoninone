import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import re
import chardet
import ctypes
from datetime import datetime
import configparser
import uuid
import shutil

class NovelMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("小说整合工具")
        
        # 设置窗口尺寸
        window_width = 1850
        window_height = 1050
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = (screen_width - window_width) // 2
        y_position = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
        
        # 启用高DPI支持
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        self.root.tk.call('tk', 'scaling', 1.5)
        
        # 设置字体
        font = ('Microsoft YaHei', 12)

        # 初始化变量
        self.loaded_file = None
        self.project_folder = None  # 项目文件夹路径
        self.chapter_order = []  # 章节顺序列表
        self.chapter_contents = {}  # 章节内容
        self.drag_enabled_var = tk.BooleanVar(value=False)  # 拖动功能开关变量（关键修复）
        self.dragging_index = -1  # 正在拖动的索引
        self.include_filename = tk.BooleanVar(value=False)  # 是否包含文件名前缀的变量

        # 布局：第一行 - 按钮和历史记录
        self.container_frame = ttk.Frame(root)
        self.container_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # 按钮框架
        self.button_frame = ttk.Frame(self.container_frame)
        self.button_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.open_button = ttk.Button(self.button_frame, text="打开文件", command=self.open_file)
        self.open_button.grid(row=0, column=0, padx=5)
        
        self.save_button = ttk.Button(self.button_frame, text="保存", command=self.save_file)
        self.save_button.grid(row=0, column=1, padx=5)
        
        self.exit_button = ttk.Button(self.button_frame, text="退出", command=self.exit_app)
        self.exit_button.grid(row=0, column=2, padx=5)
        
        # 历史记录
        self.history_label = ttk.Label(self.container_frame, text="历史记录:")
        self.history_label.grid(row=0, column=1, padx=5)

        self.history_dropdown = ttk.Combobox(self.container_frame, state="readonly")
        self.history_dropdown.grid(row=0, column=2, padx=5, sticky="ew")
        self.history_dropdown.bind("<<ComboboxSelected>>", self.select_history)
        self.update_history_dropdown()

        # 布局：第二行 - 章节列表和内容显示
        self.chapter_container_frame = ttk.Frame(root)
        self.chapter_container_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # 章节列表区域（包含操作按钮）
        self.chapter_controls_frame = ttk.Frame(self.chapter_container_frame)
        self.chapter_controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # 章节列表和滚动条
        self.chapter_frame = ttk.Frame(self.chapter_controls_frame)
        self.chapter_frame.pack(fill="both", expand=True)

        self.chapter_listbox = tk.Listbox(self.chapter_frame, height=20, width=40, font=font)
        self.chapter_listbox.grid(row=0, column=0, sticky="nsew")

        self.chapter_scrollbar = ttk.Scrollbar(self.chapter_frame, orient=tk.VERTICAL, command=self.chapter_listbox.yview)
        self.chapter_scrollbar.grid(row=0, column=1, sticky="ns")
        self.chapter_listbox.config(yscrollcommand=self.chapter_scrollbar.set)
        
        self.chapter_listbox.bind("<<ListboxSelect>>", self.show_chapter_content)
        self.chapter_listbox.bind("<Delete>", lambda event: self.delete_chapter())
        # 拖动相关绑定
        self.chapter_listbox.bind("<Button-1>", self.start_drag)
        self.chapter_listbox.bind("<B1-Motion>", self.on_drag)
        self.chapter_listbox.bind("<ButtonRelease-1>", self.end_drag)

        # 章节排序按钮
        self.order_buttons_frame = ttk.Frame(self.chapter_controls_frame)
        self.order_buttons_frame.pack(fill="x", pady=5)

        self.up_button = ttk.Button(self.order_buttons_frame, text="上移", command=self.move_up)
        self.up_button.pack(side="left", padx=5, fill="x", expand=True)
        
        self.down_button = ttk.Button(self.order_buttons_frame, text="下移", command=self.move_down)
        self.down_button.pack(side="left", padx=5, fill="x", expand=True)

        # 拖动开关（关键修复：绑定到self.drag_enabled_var）
        self.drag_checkbox = ttk.Checkbutton(
            self.order_buttons_frame, 
            text="允许拖动排序", 
            variable=self.drag_enabled_var,  # 绑定到实例变量
            command=self.toggle_drag
        )
        self.drag_checkbox.pack(side="left", padx=5)

        # 包含文件名前缀的复选框
        self.filename_prefix_checkbox = ttk.Checkbutton(
            self.order_buttons_frame,
            text="包含导入文件的章节名",
            variable=self.include_filename,
            command=lambda: self.log(f"包含文件名前缀: {'启用' if self.include_filename.get() else '禁用'}")
        )
        self.filename_prefix_checkbox.pack(side="left", padx=5)

        # 章节内容显示
        self.content_frame = ttk.Frame(self.chapter_container_frame)
        self.content_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.content_text = tk.Text(self.content_frame, height=20, width=100, font=font)
        self.content_text.grid(row=0, column=0, sticky="nsew")

        self.content_scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.content_text.yview)
        self.content_scrollbar.grid(row=0, column=1, sticky="ns")
        self.content_text.config(yscrollcommand=self.content_scrollbar.set)

        # 布局：第三行 - 添加和删除章节按钮
        self.button_container_frame = ttk.Frame(root)
        self.button_container_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.add_button = ttk.Button(self.button_container_frame, text="添加章节", command=self.add_chapter)
        self.add_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.delete_button = ttk.Button(self.button_container_frame, text="删除章节", command=self.delete_chapter)
        self.delete_button.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        
        # 布局：第四行 - 日志显示区域
        self.log_frame = ttk.Frame(root)
        self.log_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.log_text = tk.Text(self.log_frame, height=5, width=150, font=font, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(self.log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=self.scrollbar.set)

        # 启用拖放功能
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_file_drop)

        # 自适应窗口大小
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)

        self.container_frame.grid_columnconfigure(0, weight=1)
        self.container_frame.grid_columnconfigure(1, weight=1)
        self.container_frame.grid_columnconfigure(2, weight=2)

        self.chapter_container_frame.grid_rowconfigure(0, weight=1)
        self.chapter_container_frame.grid_columnconfigure(0, weight=1)
        self.chapter_container_frame.grid_columnconfigure(1, weight=2)

        self.button_container_frame.grid_columnconfigure(0, weight=1)
        self.button_container_frame.grid_columnconfigure(1, weight=1)

        self.chapter_frame.grid_rowconfigure(0, weight=1)
        self.chapter_frame.grid_columnconfigure(0, weight=1)

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

    # 项目管理核心功能（保持不变）
    def generate_24bit_code(self):
        return uuid.uuid4().hex[:24]

    def read_project_code(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                f.seek(-24, 2)
                code = f.read(24).decode('utf-8')
                if re.match(r'^[0-9a-fA-F]{24}$', code):
                    return code
                return None
        except (OSError, UnicodeDecodeError):
            return None

    def get_project_by_code(self, code):
        config = configparser.ConfigParser()
        if os.path.exists("data.ini"):
            try:
                config.read("data.ini", encoding="utf-8")
            except UnicodeDecodeError:
                config.read("data.ini", encoding="gbk")
        
        for section in config.sections():
            if config.get(section, "code") == code:
                return config.get(section, "path")
        return None

    def save_project_code(self, file_path, code):
        config = configparser.ConfigParser()
        
        if os.path.exists("data.ini"):
            try:
                config.read("data.ini", encoding="utf-8")
            except UnicodeDecodeError:
                config.read("data.ini", encoding="gbk")
        
        for section in config.sections():
            if config.get(section, "path") == file_path:
                del config[section]
        
        section = os.path.basename(file_path)
        config[section] = {
            "path": file_path,
            "code": code,
            "last_modified": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        with open("data.ini", "w", encoding="utf-8") as f:
            config.write(f)

    def create_project_folder(self, file_path):
        """创建项目文件夹，统一放在脚本目录下的"项目文件夹"中"""
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 主项目文件夹（统一存放所有小说项目）
        main_project_dir = os.path.join(script_dir, "项目文件夹")
        # 单个小说项目的文件夹名（基于文件名）
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        # 完整项目路径
        project_folder = os.path.join(main_project_dir, file_name)
        
        # 确保主项目文件夹存在
        if not os.path.exists(main_project_dir):
            os.makedirs(main_project_dir)
            self.log(f"创建主项目文件夹: {main_project_dir}")
        
        # 创建单个项目文件夹
        if not os.path.exists(project_folder):
            os.makedirs(project_folder)
            self.log(f"创建项目文件夹: {project_folder}")
        else:
            self.log(f"项目文件夹已存在: {project_folder}")
            
        return project_folder

    def split_into_chapters(self, content):
        chapters = []
        chapter_name = None
        chapter_content = []
        
        lines = content.split('\n')
        for line in lines:
            stripped_line = line.strip()
            if re.match(r"^第(\d+|[一二三四五六七八九十百千万]+)章.*", stripped_line) or re.match(r"^正文.*$", stripped_line):
                if chapter_name:
                    chapters.append((chapter_name, "\n".join(chapter_content)))
                chapter_name = stripped_line
                chapter_content = []
            else:
                chapter_content.append(line)
        
        if chapter_name:
            chapters.append((chapter_name, "\n".join(chapter_content)))
            
        return chapters

    def clean_chapter_name(self, name):
        cleaned = re.sub(r"^第(\d+|[一二三四五六七八九十百千万]+)章[:：\s]*", "", name)
        cleaned = re.sub(r"^正文[:：\s]*", "", cleaned)
        cleaned = cleaned.strip()
        if not cleaned:
            cleaned = "未知章节"
        return cleaned

    def handle_duplicate_names(self, base_name, existing_names):
        if base_name not in existing_names:
            return base_name
            
        count = 1
        pattern = re.compile(f"^{re.escape(base_name)}-(\\d+)$")
        for name in existing_names:
            match = pattern.match(name)
            if match:
                num = int(match.group(1))
                if num >= count:
                    count = num + 1
                    
        return f"{base_name}-{count}"

    def save_chapter_files(self, chapters):
        chapter_files = []
        cleaned_names = []
        for _, chapter_content in chapters:
            raw_name = chapters[chapters.index((_, chapter_content))][0]
            cleaned_name = self.clean_chapter_name(raw_name)
            cleaned_name = self.handle_duplicate_names(cleaned_name, cleaned_names)
            cleaned_names.append(cleaned_name)
        
        for i, (raw_name, chapter_content) in enumerate(chapters):
            cleaned_name = cleaned_names[i]
            chapter_filename = f"{cleaned_name}.txt"
            chapter_path = os.path.join(self.project_folder, chapter_filename)
            
            with open(chapter_path, 'w', encoding='utf-8') as f:
                f.write(chapter_content)
                
            chapter_files.append((cleaned_name, chapter_path))
            self.log(f"保存章节: {cleaned_name}")
        
        return chapter_files

    def create_config_ini(self, chapter_names):
        config = configparser.ConfigParser()
        config["ChapterOrder"] = {}
        
        for i, name in enumerate(chapter_names):
            config["ChapterOrder"][str(i+1)] = name
            
        config_path = os.path.join(self.project_folder, "config.ini")
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
            
        self.log(f"创建配置文件: {config_path}")
        return config_path

    def load_config_ini(self):
        config_path = os.path.join(self.project_folder, "config.ini")
        if not os.path.exists(config_path):
            return []
            
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        if "ChapterOrder" not in config:
            return []
            
        chapter_order = []
        for key in sorted(config["ChapterOrder"], key=lambda k: int(k)):
            chapter_order.append(config["ChapterOrder"][key])
            
        return chapter_order

    def update_config_ini(self):
        if not self.project_folder or not self.chapter_order:
            return
            
        config_path = os.path.join(self.project_folder, "config.ini")
        config = configparser.ConfigParser()
        config["ChapterOrder"] = {}
        
        for i, name in enumerate(self.chapter_order):
            config["ChapterOrder"][str(i+1)] = name
            
        with open(config_path, 'w', encoding='utf-8') as f:
            config.write(f)
            
        self.log("配置文件已更新")

    def load_chapter_contents(self):
        contents = {}
        for chapter_name in self.chapter_order:
            chapter_path = os.path.join(self.project_folder, f"{chapter_name}.txt")
            if os.path.exists(chapter_path):
                with open(chapter_path, 'r', encoding='utf-8') as f:
                    contents[chapter_name] = f.read()
        return contents

    def refresh_chapter_list(self):
        self.chapter_listbox.delete(0, tk.END)
        for i, chapter_name in enumerate(self.chapter_order):
            self.chapter_listbox.insert(tk.END, f"第{i+1}章：{chapter_name}")

    # 历史记录相关（保持不变）
    def read_history(self):
        if not os.path.exists("data.ini"):
            return {}
        
        config = configparser.ConfigParser()
        config.read("data.ini", encoding="utf-8")
        history = {}
        
        for section in config.sections():
            history[section] = {
                "path": config.get(section, "path"),
                "code": config.get(section, "code")
            }
        
        return history
    
    def save_history(self, file_path, code):
        self.save_project_code(file_path, code)
        self.update_history_dropdown()
    
    def update_history_dropdown(self):
        history = self.read_history()
        history_list = list(history.keys())
        self.history_dropdown["values"] = history_list
        if history_list:
            self.history_dropdown.current(0)
            
    def select_history(self, event):
        selected_file = self.history_dropdown.get()
        if selected_file:
            history = self.read_history()
            file_info = history.get(selected_file)
            if file_info:
                self.open_file2(file_info["path"])

    # 文件操作相关（保持不变）
    def record_file_times(self, file_path):
        try:
            creation_time = os.path.getctime(file_path)
            modification_time = os.path.getmtime(file_path)
            return (
                datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S'),
                datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d %H:%M:%S')
            )
        except Exception as e:
            self.log(f"无法获取文件时间: {e}")
            return None, None

    def restore_file_times(self, file_path, creation_time, modification_time):
        try:
            if creation_time and modification_time:
                creation_timestamp = datetime.strptime(creation_time, '%Y-%m-%d %H:%M:%S').timestamp()
                modification_timestamp = datetime.strptime(modification_time, '%Y-%m-%d %H:%M:%S').timestamp()
                os.utime(file_path, (creation_timestamp, modification_timestamp))
        except Exception as e:
            pass

    def convert_to_utf8(self, file_path):
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']

        if not encoding or encoding.lower() != 'utf-8':
            filecreation_time, filemodification_time = self.record_file_times(file_path)
            encodings = [encoding, 'utf-8', 'gbk', 'gb2312', 'big5']
            text = None

            for enc in encodings:
                try:
                    if enc:
                        with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                            text = f.read()
                        self.log(f"成功使用编码 {enc} 读取文件")
                        break
                except (UnicodeDecodeError, TypeError):
                    self.log(f"使用编码 {enc} 读取文件失败")

            if text is None:
                self.log("所有编码尝试均失败，无法读取文件")
                return False

            temp_file = file_path + ".tmp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            os.remove(file_path)
            shutil.move(temp_file, file_path)
            
            self.restore_file_times(file_path, filecreation_time, filemodification_time)
            return True
        return True

    # 核心功能实现（保持不变）
    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not file_path:
            return
            
        self.loaded_file = file_path
        
        if not self.convert_to_utf8(file_path):
            return
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        code = self.read_project_code(file_path)
        project_path = None
        
        if code:
            project_path = self.get_project_by_code(code)
            self.log(f"检测到项目编码: {code}")
        
        if project_path and os.path.exists(project_path):
            self.project_folder = self.create_project_folder(file_path)
            self.chapter_order = self.load_config_ini()
            self.chapter_contents = self.load_chapter_contents()
            self.refresh_chapter_list()
            self.log(f"加载已有项目: {os.path.basename(file_path)}")
            self.save_history(file_path, code)
            return
        
        self.project_folder = self.create_project_folder(file_path)
        
        if len(content) >= 24 and re.match(r'^[0-9a-fA-F]{24}$', content[-24:]):
            content = content[:-24]
        
        chapters = self.split_into_chapters(content)
        if not chapters:
            self.log("未检测到任何章节，可能格式不符合要求")
            return
            
        chapter_files = self.save_chapter_files(chapters)
        chapter_names = [name for name, _ in chapter_files]
        
        self.create_config_ini(chapter_names)
        
        self.chapter_order = chapter_names
        self.chapter_contents = self.load_chapter_contents()
        
        self.refresh_chapter_list()
        
        new_code = self.generate_24bit_code()
        self.save_project_code(file_path, new_code)
        self.log(f"新项目创建完成，编码: {new_code}")
        
        self.save_history(file_path, new_code)

    def open_file2(self, file_path):
        if not os.path.exists(file_path):
            self.log(f"文件不存在: {file_path}")
            return
            
        self.loaded_file = file_path
        
        code = self.read_project_code(file_path)
        
        self.project_folder = self.create_project_folder(file_path)
        self.chapter_order = self.load_config_ini()
        self.chapter_contents = self.load_chapter_contents()
        self.refresh_chapter_list()
        self.log(f"加载项目: {os.path.basename(file_path)}")

    def show_chapter_content(self, event):
        selection = self.chapter_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.chapter_order):
                chapter_name = self.chapter_order[index]
                self.content_text.delete(1.0, tk.END)
                self.content_text.insert(tk.END, self.chapter_contents.get(chapter_name, ""))

    def save_file(self):
        if not self.loaded_file or not self.project_folder or not self.chapter_order:
            self.log("没有加载文件或项目，无法保存!")
            return
        
        selection = self.chapter_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.chapter_order):
                chapter_name = self.chapter_order[index]
                content = self.content_text.get(1.0, tk.END).rstrip('\n')
                self.chapter_contents[chapter_name] = content
                
                chapter_path = os.path.join(self.project_folder, f"{chapter_name}.txt")
                with open(chapter_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.log(f"已更新章节内容: {chapter_name}")
        
        with open(self.loaded_file, 'w', encoding='utf-8') as f:
            for i, chapter_name in enumerate(self.chapter_order):
                chapter_title = f"第{i+1}章：{chapter_name}"
                f.write(f"{chapter_title}\n")
                f.write(f"{self.chapter_contents.get(chapter_name, '')}\n\n")
            
            code = self.generate_24bit_code()
            f.write(code)
        
        self.save_project_code(self.loaded_file, code)
        self.log(f"文件已保存，新编码: {code}")

    def exit_app(self):
        if self.loaded_file:
            pass
            #self.save_file()
        
        self.loaded_file = None
        self.project_folder = None
        self.chapter_order = []
        self.chapter_contents = {}
        self.chapter_listbox.delete(0, tk.END)
        self.content_text.delete(1.0, tk.END)

        self.log("应用已退出")

    # 章节操作（保持不变）
    def add_chapter(self):
        """添加新章节（支持多选文件，每个文件先拆分再加入）"""
        if not self.loaded_file or not self.project_folder:
            self.log("没有加载文件，无法添加章节!")
            return
        
        # 允许选择多个文件
        file_paths = filedialog.askopenfilenames(filetypes=[("Text Files", "*.txt")])
        if not file_paths:
            return
        
        # 遍历每个选中的文件
        for file_path in file_paths:
            self.process_multiple_chapters(file_path)  # 处理单个文件的章节拆分

    def process_multiple_chapters(self, file_path):
        """处理单个文件：先拆分章节，再逐个添加（包含文件名前缀逻辑）"""
        try:
            # 获取文件名（不含扩展名）作为前缀
            file_prefix = os.path.splitext(os.path.basename(file_path))[0]
            
            # 读取文件内容（自动处理编码）
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
            
            # 尝试解码（兼容多种编码）
            try:
                if encoding:
                    content = raw_data.decode(encoding, errors='ignore')
                else:
                    content = raw_data.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                self.log(f"无法解码文件 {os.path.basename(file_path)}，添加失败")
                return

            # 去除文件末尾可能存在的24位编码
            if len(content) >= 24 and re.match(r'^[0-9a-fA-F]{24}$', content[-24:]):
                content = content[:-24]

            # 使用现有方法拆分章节
            chapters = self.split_into_chapters(content)
            if not chapters:
                self.log(f"文件 {os.path.basename(file_path)} 中未检测到章节")
                return

            self.log(f"文件 {os.path.basename(file_path)} 中检测到 {len(chapters)} 个章节，开始添加...")

            # 逐个添加拆分后的章节
            for raw_name, chapter_content in chapters:
                # 清理章节名称
                cleaned_name = self.clean_chapter_name(raw_name)
                
                # 如果勾选了包含文件名，则添加前缀
                if self.include_filename.get():
                    cleaned_name = f"{file_prefix}-{cleaned_name}"
                
                # 处理重复名称
                final_name = self.handle_duplicate_names(cleaned_name, self.chapter_order)
                
                # 保存章节内容到项目文件夹
                chapter_path = os.path.join(self.project_folder, f"{final_name}.txt")
                with open(chapter_path, 'w', encoding='utf-8') as f:
                    f.write(chapter_content)
                
                # 更新章节数据
                self.chapter_order.append(final_name)
                self.chapter_contents[final_name] = chapter_content
                self.log(f"添加章节: {final_name}")

            # 更新配置文件和列表显示
            self.update_config_ini()
            self.refresh_chapter_list()
            self.log(f"文件 {os.path.basename(file_path)} 的章节添加完成")

        except Exception as e:
            self.log(f"处理文件 {os.path.basename(file_path)} 时出错: {str(e)}")

    def delete_chapter(self):
        if not self.project_folder:
            self.log("没有加载项目，无法删除章节!")
            return
            
        selection = self.chapter_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.chapter_order):
                chapter_name = self.chapter_order[index]
                
                chapter_path = os.path.join(self.project_folder, f"{chapter_name}.txt")
                if os.path.exists(chapter_path):
                    os.remove(chapter_path)
                
                del self.chapter_contents[chapter_name]
                self.chapter_order.pop(index)
                
                self.update_config_ini()
                self.refresh_chapter_list()
                self.content_text.delete(1.0, tk.END)
                
                self.log(f"章节 '{chapter_name}' 已删除")
        else:
            self.log("请选择一个章节进行删除")

    # 章节排序（修复拖动功能）
    def move_up(self):
        selection = self.chapter_listbox.curselection()
        if selection and len(selection) == 1:
            index = selection[0]
            if index > 0 and index < len(self.chapter_order):
                self.chapter_order[index], self.chapter_order[index-1] = self.chapter_order[index-1], self.chapter_order[index]
                self.update_config_ini()
                self.refresh_chapter_list()
                self.chapter_listbox.selection_set(index-1)
                self.log(f"章节上移: {self.chapter_order[index-1]}")

    def move_down(self):
        selection = self.chapter_listbox.curselection()
        if selection and len(selection) == 1:
            index = selection[0]
            if index < len(self.chapter_order) - 1:
                self.chapter_order[index], self.chapter_order[index+1] = self.chapter_order[index+1], self.chapter_order[index]
                self.update_config_ini()
                self.refresh_chapter_list()
                self.chapter_listbox.selection_set(index+1)
                self.log(f"章节下移: {self.chapter_order[index+1]}")

    def toggle_drag(self):
        # 关键修复：通过self.drag_enabled_var获取状态
        state = "启用" if self.drag_enabled_var.get() else "禁用"
        self.log(f"章节拖动排序已{state}")

    def start_drag(self, event):
        # 关键修复：检查self.drag_enabled_var的状态
        if not self.drag_enabled_var.get():
            return
        
        # 获取点击位置的索引
        index = self.chapter_listbox.nearest(event.y)
        if 0 <= index < len(self.chapter_order):
            self.dragging_index = index
            self.chapter_listbox.selection_set(index)

    def on_drag(self, event):
        # 关键修复：检查self.drag_enabled_var的状态
        if not self.drag_enabled_var.get() or self.dragging_index == -1:
            return
        
        # 获取当前位置的索引
        current_index = self.chapter_listbox.nearest(event.y)
        if 0 <= current_index < len(self.chapter_order) and current_index != self.dragging_index:
            # 移动章节
            chapter = self.chapter_order.pop(self.dragging_index)
            self.chapter_order.insert(current_index, chapter)
            # 更新拖动索引
            self.dragging_index = current_index
            # 刷新列表并保持选中
            self.refresh_chapter_list()
            self.chapter_listbox.selection_set(current_index)

    def end_drag(self, event):
        if self.dragging_index != -1:
            self.update_config_ini()
            self.log("章节顺序已更新")
            self.dragging_index = -1

    def on_file_drop(self, event):
        """处理拖放文件（支持多文件拖放）"""
        file_paths = event.data.strip().split()
        if not file_paths:
            return

        for file_path in file_paths:
            if file_path.startswith('{') and file_path.endswith('}'):
                file_path = file_path[1:-1]
            
            if file_path.endswith(".txt") and self.project_folder:
                self.process_multiple_chapters(file_path)  # 复用多章节处理逻辑
            else:
                self.log(f"跳过非txt文件或未加载项目: {os.path.basename(file_path)}")

    def add_chapter_from_file(self, file_path):
        """从拖放的文件添加章节"""
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding']
            
            try:
                if encoding:
                    content = raw_data.decode(encoding, errors='ignore')
                else:
                    content = raw_data.decode('utf-8', errors='ignore')
            except UnicodeDecodeError:
                self.log("无法解码文件，添加失败")
                return
            
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            base_name = self.clean_chapter_name(base_name)
            
            # 如果勾选了包含文件名，则添加前缀
            if self.include_filename.get():
                base_name = f"{os.path.splitext(os.path.basename(file_path))[0]}-{base_name}"
            
            new_name = self.handle_duplicate_names(base_name, self.chapter_order)
            
            chapter_path = os.path.join(self.project_folder, f"{new_name}.txt")
            with open(chapter_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.chapter_order.append(new_name)
            self.chapter_contents[new_name] = content
            self.update_config_ini()
            self.refresh_chapter_list()
            
            self.log(f"从拖放添加章节: {new_name}")
        except Exception as e:
            self.log(f"添加章节失败: {str(e)}")

    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.yview(tk.END)


if __name__ == "__main__":
    ttk.Checkbutton.var = property(lambda self: self._var, lambda self, v: setattr(self, '_var', v))
    root = TkinterDnD.Tk()
    app = NovelMergerApp(root)
    root.mainloop()