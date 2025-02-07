import tkinter as tk
from tkinter import filedialog, ttk
import configparser
import os

class FileHistoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File History and Viewer")
        
        # 初始化 GUI 元素
        self.open_button = tk.Button(root, text="Open File", command=self.open_file)
        self.open_button.pack(pady=10)

        self.history_label = tk.Label(root, text="Select from History:")
        self.history_label.pack(pady=5)

        self.history_dropdown = ttk.Combobox(root, state="readonly")
        self.history_dropdown.pack(pady=5)
        self.history_dropdown.bind("<<ComboboxSelected>>", self.select_history)

        self.text_box = tk.Text(root, width=80, height=20)
        self.text_box.pack(pady=10)

        # 初始化历史记录
        self.update_history_dropdown()

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

    def open_file(self):
        """打开文件并显示内容"""
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            # 更新文本框显示文件内容
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                self.text_box.delete(1.0, tk.END)
                self.text_box.insert(tk.END, content)
            
            # 更新历史记录
            self.save_history(file_path)
            
            # 更新下拉框
            self.update_history_dropdown()

    def select_history(self, event):
        """从历史记录中选择文件并显示内容"""
        selected_file = self.history_dropdown.get()
        if selected_file:
            # 获取选中文件的路径
            history = self.read_history()
            file_path = history.get(selected_file)
            
            if file_path:
                # 打开选中的文件
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.text_box.delete(1.0, tk.END)
                    self.text_box.insert(tk.END, content)

    def update_history_dropdown(self):
        """更新历史记录下拉框"""
        history = self.read_history()
        history_list = list(history.keys())
        self.history_dropdown["values"] = history_list
        if history_list:
            self.history_dropdown.current(0)

# 创建主界面
root = tk.Tk()
app = FileHistoryApp(root)

# 运行 GUI
root.mainloop()
