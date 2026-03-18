#!/usr/bin/env python3
"""
Thoughts 桌面应用
直接读取 entries/ 目录，无需浏览器或服务器
"""

import re
import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
from datetime import datetime
import threading
import time

# ========== 高DPI适配 ==========
from ctypes import windll
try:
    windll.shcore.SetProcessDpiAwareness(1)
except:
    try:
        windll.user32.SetProcessDPIAware()
    except:
        pass

# ========== 路径配置 ==========
def get_app_dir():
    """获取应用程序所在目录（兼容开发和打包环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后的 EXE 环境
        return Path(sys.executable).parent
    else:
        # 开发环境
        return Path(__file__).parent

# ========== 解析 Markdown 条目 ==========
ENTRY_PATTERN = re.compile(
    r'### \[([^\]]+)\] (.+?) @(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\n\n(.+?)\n\n(#.+?)\n\n---',
    re.DOTALL
)

class ThoughtsApp:
    def __init__(self, root):
        self.root = root
        self.app_dir = get_app_dir()

        # 获取DPI缩放比例
        self.dpi_scale = self.get_dpi_scale()

        self.root.title("Thoughts - 第二大脑")
        w, h = self.scaled(1200, 800)
        mw, mh = self.scaled(900, 600)
        self.root.minsize(mw, mh)

        # 窗口居中显示
        self.center_window(w, h)

        # 数据
        self.all_entries = []
        self.all_tags = set()
        self.current_filter = 'all'
        self.last_modified = {}

        # 颜色配置
        self.colors = {
            'bg': '#f5f5f5',
            'card': '#ffffff',
            'primary': '#667eea',
            'primary_gradient': '#764ba2',
            'text': '#333333',
            'text_secondary': '#666666',
            'text_muted': '#999999',
            'border': '#eeeeee',
            'tag_bg': '#f0f0f0',
            'hover': '#e8e8e8'
        }

        self.root.configure(bg=self.colors['bg'])

        # 创建UI
        self.create_ui()

        # 初始加载
        self.load_data()
        self.render_entries()

        # 启动自动刷新线程
        self.running = True
        self.refresh_thread = threading.Thread(target=self.auto_refresh, daemon=True)
        self.refresh_thread.start()

    def scaled(self, value, value2=None):
        """根据DPI缩放值"""
        if value2 is not None:
            return (int(value * self.dpi_scale), int(value2 * self.dpi_scale))
        return int(value * self.dpi_scale)

    def center_window(self, width, height):
        """将窗口居中显示"""
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # 计算居中位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        # 确保窗口不会超出屏幕边界
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))

        # 设置窗口位置和大小
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def get_dpi_scale(self):
        """获取DPI缩放比例"""
        try:
            from ctypes import windll
            dc = windll.user32.GetDC(0)
            dpi = windll.gdi32.GetDeviceCaps(dc, 88)  # LOGPIXELSX
            windll.user32.ReleaseDC(0, dc)
            return dpi / 96.0
        except:
            return 1.0

    def create_ui(self):
        """创建用户界面"""
        # 主容器
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=self.scaled(20), pady=self.scaled(20))

        # === Header ===
        header_height = self.scaled(140)  # 增加高度避免重叠
        header = tk.Frame(main_container, bg=self.colors['primary'], height=header_height)
        header.pack(fill=tk.X, pady=(0, self.scaled(20)))
        header.pack_propagate(False)

        # 渐变背景
        header_canvas = tk.Canvas(header, height=header_height, highlightthickness=0)
        header_canvas.pack(fill=tk.BOTH, expand=True)

        # 绘制渐变
        width = 2000
        for i in range(header_height):
            ratio = i / header_height
            r = int(102 + (118 - 102) * ratio)
            g = int(126 + (75 - 126) * ratio)
            b = int(234 + (162 - 234) * ratio)
            color = f'#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}'
            header_canvas.create_line(0, i, width, i, fill=color)

        # 标题 - 使用中心点避免重叠
        center_x = int(self.scaled(600))
        title_font_size = min(self.scaled(32), 48)
        subtitle_font_size = min(self.scaled(12), 16)

        # 主标题 (中心偏上)
        header_canvas.create_text(
            center_x, self.scaled(60),
            text="🧠 Thoughts",
            font=('Segoe UI', title_font_size, 'bold'),
            fill='white',
            anchor='center'
        )
        # 副标题 (主标题下方，留出足够间距)
        header_canvas.create_text(
            center_x, self.scaled(115),
            text="第二大脑 - 捕获一切想法、灵感与感受",
            font=('Segoe UI', subtitle_font_size),
            fill='white',
            anchor='center'
        )

        # === Stats Bar ===
        stats_frame = tk.Frame(main_container, bg=self.colors['bg'])
        stats_frame.pack(fill=tk.X, pady=(0, self.scaled(20)))

        self.stat_labels = {}
        stat_configs = [
            ('total', '总条目'),
            ('tags', '标签数'),
            ('days', '记录天数'),
            ('month', '本月条目')
        ]

        for i, (key, label) in enumerate(stat_configs):
            card = tk.Frame(
                stats_frame,
                bg=self.colors['card'],
                highlightbackground=self.colors['border'],
                highlightthickness=1
            )
            card.grid(row=0, column=i, padx=(0, self.scaled(20) if i < 3 else 0), sticky='nsew')
            # 增加高度确保文字不被截断
            card_height = max(self.scaled(100), self.scaled(32) + self.scaled(10) + self.scaled(40))
            card.configure(width=self.scaled(250), height=card_height)
            card.grid_propagate(False)
            card.pack_propagate(False)

            # 数字标签（使用place精确定位，避免被截断）
            num_label = tk.Label(
                card,
                text='0',
                font=('Segoe UI', self.scaled(32), 'bold'),
                fg=self.colors['primary'],
                bg=self.colors['card']
            )
            num_label.place(relx=0.5, y=self.scaled(35), anchor='center')

            # 文字标签（在数字下方）
            text_label = tk.Label(
                card,
                text=label,
                font=('Segoe UI', self.scaled(10)),
                fg=self.colors['text_secondary'],
                bg=self.colors['card']
            )
            text_label.place(relx=0.5, y=self.scaled(75), anchor='center')

            self.stat_labels[key] = num_label

        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        # === Main Layout ===
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True)

        # === Sidebar ===
        sidebar_width = self.scaled(250)
        sidebar = tk.Frame(
            content_frame,
            bg=self.colors['card'],
            width=sidebar_width,
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self.scaled(20)))
        sidebar.pack_propagate(False)

        # 标签标题
        tag_header = tk.Frame(sidebar, bg=self.colors['card'], height=self.scaled(50))
        tag_header.pack(fill=tk.X, padx=self.scaled(15), pady=(self.scaled(15), 0))
        tag_header.pack_propagate(False)

        tk.Label(
            tag_header,
            text='🏷️ 标签',
            font=('Segoe UI', self.scaled(14), 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card']
        ).pack(side=tk.LEFT)

        # 分隔线
        tk.Frame(sidebar, bg=self.colors['primary'], height=2).pack(
            fill=tk.X, padx=self.scaled(15), pady=(self.scaled(10), self.scaled(15))
        )

        # 标签列表容器
        tag_container = tk.Frame(sidebar, bg=self.colors['card'])
        tag_container.pack(fill=tk.BOTH, expand=True, padx=self.scaled(15))

        tag_scrollbar = tk.Scrollbar(tag_container, width=self.scaled(12))
        tag_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tag_canvas = tk.Canvas(
            tag_container,
            bg=self.colors['card'],
            highlightthickness=0,
            yscrollcommand=tag_scrollbar.set
        )
        self.tag_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tag_scrollbar.config(command=self.tag_canvas.yview)

        self.tag_list_frame = tk.Frame(self.tag_canvas, bg=self.colors['card'])
        self.tag_canvas_window = self.tag_canvas.create_window(
            (0, 0), window=self.tag_list_frame, anchor='nw',
            width=sidebar_width - self.scaled(40)
        )

        self.tag_list_frame.bind('<Configure>',
            lambda e: self.tag_canvas.configure(scrollregion=self.tag_canvas.bbox('all')))

        # === Main Content ===
        self.content_frame = tk.Frame(
            content_frame,
            bg=self.colors['card'],
            highlightbackground=self.colors['border'],
            highlightthickness=1
        )
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条
        self.scrollbar = tk.Scrollbar(self.content_frame, width=self.scaled(12))
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.entries_canvas = tk.Canvas(
            self.content_frame,
            bg=self.colors['card'],
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set
        )
        self.entries_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.entries_canvas.yview)

        self.entries_frame = tk.Frame(self.entries_canvas, bg=self.colors['card'])
        self.entries_canvas_window = self.entries_canvas.create_window(
            (0, 0), window=self.entries_frame, anchor='nw'
        )

        self.entries_frame.bind('<Configure>',
            lambda e: self.entries_canvas.configure(scrollregion=self.entries_canvas.bbox('all')))

        # 更新时间
        self.update_label = tk.Label(
            main_container,
            text='',
            font=('Segoe UI', self.scaled(9)),
            fg=self.colors['text_muted'],
            bg=self.colors['bg']
        )
        self.update_label.pack(pady=(self.scaled(15), 0))

        # 绑定窗口大小变化
        self.entries_canvas.bind('<Configure>', self.on_canvas_resize)

        # 绑定鼠标滚轮到整个窗口（无论鼠标在哪都能滚动）
        self.setup_scroll_binding(self.root, self.entries_canvas)
        self.setup_scroll_binding(self.tag_canvas, self.tag_canvas)

    def setup_scroll_binding(self, widget, target_canvas):
        """绑定鼠标滚轮事件到目标canvas"""
        def on_mousewheel(event):
            # 确定滚动方向
            if event.delta:
                delta = -int(event.delta / 120)
            elif event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            else:
                return
            target_canvas.yview_scroll(delta, 'units')
            return 'break'  # 阻止事件冒泡导致重复滚动

        # Windows
        widget.bind('<MouseWheel>', on_mousewheel, add='+')
        # Linux
        widget.bind('<Button-4>', on_mousewheel, add='+')
        widget.bind('<Button-5>', on_mousewheel, add='+')

    def on_canvas_resize(self, event):
        """Canvas大小变化时更新条目宽度"""
        self.entries_canvas.itemconfig(self.entries_canvas_window, width=event.width - self.scaled(20))

    def load_data(self):
        """加载数据"""
        entries_dir = self.app_dir / 'entries'

        if not entries_dir.exists():
            messagebox.showwarning("警告", f"找不到 entries 目录: {entries_dir}")
            return

        self.all_entries = []
        self.last_modified = {}

        for md_file in sorted(entries_dir.glob('*.md'), reverse=True):
            try:
                mtime = md_file.stat().st_mtime
                self.last_modified[str(md_file)] = mtime

                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for match in ENTRY_PATTERN.finditer(content):
                    entry_type = match.group(1)
                    full_title = match.group(2)
                    time_str = match.group(3)
                    entry_content = match.group(4).strip()
                    tags_str = match.group(5)
                    tags = [t.strip() for t in tags_str.split() if t.startswith('#')]

                    # 标题已在写入时凝练，直接显示
                    self.all_entries.append({
                        'type': entry_type,
                        'title': full_title,
                        'full_title': full_title,
                        'time': time_str,
                        'content': entry_content,
                        'tags': tags
                    })

                    self.all_tags.update(tags)
            except Exception as e:
                print(f"读取文件失败 {md_file}: {e}")

        # 更新统计
        self.update_stats()

        # 更新标签列表
        self.update_tag_list()

        # 更新时间
        self.update_label.config(text=f"最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def update_stats(self):
        """更新统计数字"""
        total = len(self.all_entries)
        tags_count = len(self.all_tags)
        active_days = len(set(e['time'][:10] for e in self.all_entries))
        this_month = len([e for e in self.all_entries if e['time'][:7] == datetime.now().strftime('%Y-%m')])

        self.stat_labels['total'].config(text=str(total))
        self.stat_labels['tags'].config(text=str(tags_count))
        self.stat_labels['days'].config(text=str(active_days))
        self.stat_labels['month'].config(text=str(this_month))

    def update_tag_list(self):
        """更新标签列表"""
        for widget in self.tag_list_frame.winfo_children():
            widget.destroy()

        self.create_tag_button('全部', 'all', True)

        for tag in sorted(self.all_tags):
            tag_name = tag[1:]
            self.create_tag_button(tag, tag_name, False)

        self.tag_canvas.configure(scrollregion=self.tag_canvas.bbox('all'))

    def create_tag_button(self, display_text, tag_value, is_active):
        """创建标签按钮"""
        btn = tk.Label(
            self.tag_list_frame,
            text=display_text,
            font=('Segoe UI', self.scaled(10)),
            bg=self.colors['primary'] if is_active else self.colors['tag_bg'],
            fg='white' if is_active else self.colors['text_secondary'],
            cursor='hand2',
            padx=self.scaled(12),
            pady=self.scaled(6)
        )
        btn.pack(fill=tk.X, pady=(0, self.scaled(8)))
        btn.tag_value = tag_value

        def on_enter(e):
            if self.current_filter != tag_value:
                btn.config(bg=self.colors['hover'])

        def on_leave(e):
            if self.current_filter != tag_value:
                btn.config(bg=self.colors['tag_bg'])
            else:
                btn.config(bg=self.colors['primary'])

        def on_click(e):
            self.current_filter = tag_value
            self.update_tag_styles()
            self.render_entries()

        btn.bind('<Enter>', on_enter)
        btn.bind('<Leave>', on_leave)
        btn.bind('<Button-1>', on_click)

    def update_tag_styles(self):
        """更新标签样式"""
        for widget in self.tag_list_frame.winfo_children():
            if hasattr(widget, 'tag_value'):
                if widget.tag_value == self.current_filter:
                    widget.config(bg=self.colors['primary'], fg='white')
                else:
                    widget.config(bg=self.colors['tag_bg'], fg=self.colors['text_secondary'])

    def render_entries(self):
        """渲染条目列表"""
        for widget in self.entries_frame.winfo_children():
            widget.destroy()

        if self.current_filter == 'all':
            filtered = self.all_entries
        else:
            filtered = [e for e in self.all_entries if any(self.current_filter in t for t in e['tags'])]

        if not filtered:
            empty_label = tk.Label(
                self.entries_frame,
                text='暂无条目',
                font=('Segoe UI', self.scaled(14)),
                fg=self.colors['text_muted'],
                bg=self.colors['card']
            )
            empty_label.pack(pady=self.scaled(100))
            return

        for entry in filtered:
            self.create_entry_card(entry)

        self.entries_canvas.configure(scrollregion=self.entries_canvas.bbox('all'))

    def create_entry_card(self, entry):
        """创建单个条目卡片"""
        card = tk.Frame(self.entries_frame, bg=self.colors['card'])
        card.pack(fill=tk.X, padx=self.scaled(30), pady=(0, self.scaled(20)))

        # 左侧色条
        left_bar = tk.Frame(card, bg=self.colors['primary'], width=self.scaled(4))
        left_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, self.scaled(15)))

        # 内容区
        content = tk.Frame(card, bg=self.colors['card'])
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 头部信息
        header = tk.Frame(content, bg=self.colors['card'])
        header.pack(fill=tk.X, pady=(0, self.scaled(10)))

        # 类型标签
        type_label = tk.Label(
            header,
            text=entry['type'],
            font=('Segoe UI', self.scaled(9), 'bold'),
            bg=self.colors['primary'],
            fg='white',
            padx=self.scaled(10),
            pady=self.scaled(3)
        )
        type_label.pack(side=tk.LEFT)

        # 标题
        title_label = tk.Label(
            header,
            text=entry['title'],
            font=('Segoe UI', self.scaled(12), 'bold'),
            fg=self.colors['text'],
            bg=self.colors['card']
        )
        title_label.pack(side=tk.LEFT, padx=(self.scaled(10), 0))

        # 时间
        time_label = tk.Label(
            header,
            text=entry['time'],
            font=('Segoe UI', self.scaled(9)),
            fg=self.colors['text_muted'],
            bg=self.colors['card']
        )
        time_label.pack(side=tk.RIGHT)

        # 内容
        content_text = tk.Label(
            content,
            text=entry['content'],
            font=('Segoe UI', self.scaled(10)),
            fg=self.colors['text_secondary'],
            bg=self.colors['card'],
            wraplength=self.scaled(750),
            justify=tk.LEFT,
            anchor='w'
        )
        content_text.pack(fill=tk.X, pady=(0, self.scaled(10)))

        # 标签
        tags_frame = tk.Frame(content, bg=self.colors['card'])
        tags_frame.pack(fill=tk.X)

        for tag in entry['tags']:
            tag_label = tk.Label(
                tags_frame,
                text=tag,
                font=('Segoe UI', self.scaled(9)),
                bg=self.colors['tag_bg'],
                fg=self.colors['primary'],
                padx=self.scaled(8),
                pady=self.scaled(2)
            )
            tag_label.pack(side=tk.LEFT, padx=(0, self.scaled(8)))

        # 分隔线
        tk.Frame(content, bg=self.colors['border'], height=1).pack(fill=tk.X, pady=(self.scaled(15), 0))

    def check_for_updates(self):
        """检查文件是否有更新"""
        entries_dir = self.app_dir / 'entries'
        if not entries_dir.exists():
            return False

        for md_file in entries_dir.glob('*.md'):
            mtime = md_file.stat().st_mtime
            file_path = str(md_file)

            if file_path not in self.last_modified or self.last_modified[file_path] != mtime:
                return True

        current_files = set(str(f) for f in entries_dir.glob('*.md'))
        if current_files != set(self.last_modified.keys()):
            return True

        return False

    def auto_refresh(self):
        """自动刷新线程"""
        while self.running:
            time.sleep(2)
            if self.check_for_updates():
                self.root.after(0, self.refresh_data)

    def refresh_data(self):
        """刷新数据"""
        self.load_data()
        self.render_entries()

    def on_closing(self):
        """关闭窗口"""
        self.running = False
        self.root.destroy()

def main():
    root = tk.Tk()
    app = ThoughtsApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == '__main__':
    main()
