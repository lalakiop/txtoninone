import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import re
import chardet
import ctypes
from datetime import datetime
import configparser  # 用于读取和写入 ini 文件

class NovelMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("小说整合工具")
        
        # 设置窗口尺寸
        window_width = 1650
        window_height = 850
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

        # 布局：第一行 - 按钮和历史记录下拉框放入一个容器中
        self.container_frame = ttk.Frame(root)  # 创建一个新的容器
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
        
        # 历史记录文本标签
        self.history_label = ttk.Label(self.container_frame, text="历史记录:")
        self.history_label.grid(row=0, column=1, padx=5)

        # 下拉框（暂时为空）
        self.history_dropdown = ttk.Combobox(self.container_frame, state="readonly")
        self.history_dropdown.grid(row=0, column=2, padx=5, sticky="ew")  # 增加sticky="ew"
        self.history_dropdown.bind("<<ComboboxSelected>>", self.select_history)
        # 初始化历史记录
        self.update_history_dropdown()
        # 布局：第二行 - 章节列表和内容显示放入一个容器中
        self.chapter_container_frame = ttk.Frame(root)  # 创建第二行的容器
        self.chapter_container_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # 章节列表和滚动条
        self.chapter_frame = ttk.Frame(self.chapter_container_frame)
        self.chapter_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.chapter_listbox = tk.Listbox(self.chapter_frame, height=20, width=40, font=font)
        self.chapter_listbox.grid(row=0, column=0, sticky="nsew")

        self.chapter_scrollbar = ttk.Scrollbar(self.chapter_frame, orient=tk.VERTICAL, command=self.chapter_listbox.yview)
        self.chapter_scrollbar.grid(row=0, column=1, sticky="ns")
        self.chapter_listbox.config(yscrollcommand=self.chapter_scrollbar.set)
        
        self.chapter_listbox.bind("<<ListboxSelect>>", self.show_chapter_content)

        # 章节内容显示和滚动条
        self.content_frame = ttk.Frame(self.chapter_container_frame)
        self.content_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.content_text = tk.Text(self.content_frame, height=20, width=100, font=font)
        self.content_text.grid(row=0, column=0, sticky="nsew")

        self.content_scrollbar = ttk.Scrollbar(self.content_frame, orient=tk.VERTICAL, command=self.content_text.yview)
        self.content_scrollbar.grid(row=0, column=1, sticky="ns")
        self.content_text.config(yscrollcommand=self.content_scrollbar.set)

        # 布局：第三行 - 添加和删除章节按钮放入一个容器中
        self.button_container_frame = ttk.Frame(root)  # 创建第三行的容器
        self.button_container_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.add_button = ttk.Button(self.button_container_frame, text="添加", command=self.add_chapter)
        self.add_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.delete_button = ttk.Button(self.button_container_frame, text="删除", command=self.delete_chapter)
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
        self.root.drop_target_register(DND_FILES)  # 注册拖放文件目标
        self.root.dnd_bind('<<Drop>>', self.on_file_drop)  # 绑定拖放事件
        self.chapter_listbox.bind("<Delete>", lambda event: self.delete_chapter())#绑定删除按钮
        # 自适应窗口大小
        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        root.grid_columnconfigure(1, weight=2)

        # 调整按钮列宽，确保每个按钮的大小相等
        self.container_frame.grid_columnconfigure(0, weight=1)
        self.container_frame.grid_columnconfigure(1, weight=1)
        self.container_frame.grid_columnconfigure(2, weight=1)
        self.container_frame.grid_columnconfigure(3, weight=1)
        self.container_frame.grid_columnconfigure(4, weight=2)

        self.chapter_container_frame.grid_rowconfigure(0, weight=1)
        self.chapter_container_frame.grid_columnconfigure(0, weight=1)
        self.chapter_container_frame.grid_columnconfigure(1, weight=2)

        self.button_container_frame.grid_columnconfigure(0, weight=1)
        self.button_container_frame.grid_columnconfigure(1, weight=1)



    def read_history(self):
        """读取历史记录"""
        if not os.path.exists("data.ini"):
            return {}
        
        config = configparser.ConfigParser()
        config.read("data.ini")
        history = {}
        
        for section in config.sections():
            history[section] = config.get(section, "path")
        
        return history
    
    def save_history(self, file_path):
        """保存历史记录，最多保留10个文件"""
        config = configparser.ConfigParser()

        # 读取现有历史记录
        history = self.read_history()

        # 获取文件名作为历史记录的键
        file_name = os.path.basename(file_path)

        # 避免重复记录
        if file_name in history:
            return  # 如果文件已在历史记录中，直接返回
        
        # 如果历史记录超过10个，移除最旧的记录
        if len(history) >= 10:
            oldest_file = list(history.keys())[0]
            history.pop(oldest_file)

        # 新文件记录
        history[file_name] = file_path
        
        # 清除原有历史记录并保存新记录
        for file_name, path in history.items():
            config[file_name] = {"path": path}

        # 保存到 data.ini 文件
        with open("data.ini", "w") as configfile:
            config.write(configfile)
    
    
    
    def update_history_dropdown(self):
        """更新历史记录下拉框"""
        history = self.read_history()
        history_list = list(history.keys())
        self.history_dropdown["values"] = history_list
        if history_list:
            self.history_dropdown.current(0)
            
    


    def select_history(self, event):
        """从历史记录中选择文件并显示内容"""
        selected_file = self.history_dropdown.get()
        if selected_file:
            # 获取选中文件的路径
            history = self.read_history()
            file_path = history.get(selected_file)
            
            if file_path:
                # 打开选中的文件
                self.open_file2(file_path)
                
            
    def rename_to_original(self,output_file):
        """将文件重命名为去除 _utf8_simplified 后缀的文件名"""
        try:
            # 检查文件名是否包含 "_utf8"
            if "_utf8" in output_file:
                # 构造新的文件路径，去除 "_utf8" 后缀
                new_file_path = output_file.replace("_utf8", "")
                
                # 重命名文件
                os.rename(output_file, new_file_path)
                self.log(f"文件已重命名为：{new_file_path}")
            else:
                self.log(f"文件名不包含 '_utf8' 后缀。")
        
        except Exception as e:
           self.log(f"重命名过程中出现错误：{str(e)}")
           
           
           
    def record_file_times(self,file_path):
        try:
            # 获取文件的创建时间
            creation_time = os.path.getctime(file_path)
            # 获取文件的修改时间
            modification_time = os.path.getmtime(file_path)

            # 将时间戳转换为可读格式
            creation_time = datetime.fromtimestamp(creation_time).strftime('%Y-%m-%d %H:%M:%S')
            modification_time = datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d %H:%M:%S') 
            # 如果需要返回，也可以选择返回
            return creation_time, modification_time
        except Exception as e:
            self.log(f"无法获取文件时间: {e}")  

    
    def restore_file_times(self,file_path, creation_time, modification_time):
        try:
            # 将创建时间和修改时间转换为时间戳
            creation_timestamp = datetime.strptime(creation_time, '%Y-%m-%d %H:%M:%S').timestamp()
            modification_timestamp = datetime.strptime(modification_time, '%Y-%m-%d %H:%M:%S').timestamp()

            # 恢复文件的访问时间和修改时间
            os.utime(file_path, (creation_timestamp, modification_timestamp))
            
            # 如果操作系统支持，也可以尝试恢复文件的创建时间（但是大多数操作系统不允许直接修改创建时间）
            # 在大多数操作系统上，创建时间是不可更改的。

            #print(f"文件 {file_path} 的时间已恢复！")
        except Exception as e:
            #print(f"无法恢复文件时间: {e}")    
            pass
    
    def open_file(self,file_path=None):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            # 更新历史记录
            self.save_history(file_path)   
            # 更新下拉框
            self.update_history_dropdown()
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            #print(encoding)
        if not encoding or encoding.lower() != 'utf-8':
            #记录文件的时间
            filecreation_time,filemodification_time=self.record_file_times(file_path)
            # 编码备选列表
            encodings = [encoding, 'utf-8', 'gbk', 'gb2312', 'big5']

            # 尝试逐个编码读取文件
            text = None
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        text = f.read()
                    self.log(f"成功使用编码 {enc} 读取文件")
                    break
                except (UnicodeDecodeError, TypeError):
                    self.log(f"使用编码 {enc} 读取文件失败")

            if text is None:
                self.log("所有编码尝试均失败，无法读取文件")
                return
            output_file = file_path.replace('.txt', '_utf8.txt')
            # 将内容保存为UTF-8编码
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            os.remove(file_path)
            self.rename_to_original(output_file) 
            #恢复文件的时间
            self.restore_file_times(file_path,filecreation_time,filemodification_time)

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
                    if re.match(r"^第(\d+|[一二三四五六七八九十]+)章|^正文$", line.strip()):
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
        else:
            self.log(f"文件是utf-8编码")
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
                    if re.match(r"^第(\d+|[一二三四五六七八九十]+)章|^正文$", line.strip()):
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
        
    def open_file2(self,file_path):
        file_path = file_path
       
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            #print(encoding)
        if not encoding or encoding.lower() != 'utf-8':
            #记录文件的时间
            filecreation_time,filemodification_time=self.record_file_times(file_path)
            # 编码备选列表
            encodings = [encoding, 'utf-8', 'gbk', 'gb2312', 'big5']

            # 尝试逐个编码读取文件
            text = None
            for enc in encodings:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        text = f.read()
                    self.log(f"成功使用编码 {enc} 读取文件")
                    break
                except (UnicodeDecodeError, TypeError):
                    self.log(f"使用编码 {enc} 读取文件失败")

            if text is None:
                self.log("所有编码尝试均失败，无法读取文件")
                return
            output_file = file_path.replace('.txt', '_utf8.txt')
            # 将内容保存为UTF-8编码
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            os.remove(file_path)
            self.rename_to_original(output_file) 
            #恢复文件的时间
            self.restore_file_times(file_path,filecreation_time,filemodification_time)

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
                    if re.match(r"^第(\d+|[一二三四五六七八九十]+)章|^正文$", line.strip()):
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
        else:
            self.log(f"文件是utf-8编码")
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
                    if re.match(r"^第(\d+|[一二三四五六七八九十]+)章.*|^\s*正文.*$", line.strip()):
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
                if re.match(r"^第(\d+|[一二三四五六七八九十]+)章|^正文$", line.strip()):
                    new_content_lines.pop(i)
                    
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
       # print(file_path)  # 打印拖拽的文件路径，检查路径是否正确

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
