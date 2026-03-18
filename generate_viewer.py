#!/usr/bin/env python3
"""
生成 viewer.html 的脚本
读取 entries/ 目录下的所有 Markdown 文件，生成包含最新数据的 HTML
"""

import re
import os
from pathlib import Path
from datetime import datetime

# 解析 Markdown 条目
ENTRY_PATTERN = re.compile(
    r'### \[([^\]]+)\] (.+?) @(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\n\n(.+?)\n\n(#.+?)\n\n---',
    re.DOTALL
)

def parse_entry_file(filepath):
    """解析单个条目文件"""
    entries = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    for match in ENTRY_PATTERN.finditer(content):
        entry_type = match.group(1)
        full_title = match.group(2)
        time = match.group(3)
        entry_content = match.group(4).strip()
        tags_str = match.group(5)
        tags = [t.strip() for t in tags_str.split() if t.startswith('#')]

        # 标题自动总结：超过15字截断
        if len(full_title) > 15:
            short_title = full_title[:15] + "..."
        else:
            short_title = full_title

        entries.append({
            'type': entry_type,
            'title': short_title,
            'full_title': full_title,  # 保留完整标题
            'time': time,
            'content': entry_content,
            'tags': tags
        })

    return entries

def generate_html():
    """生成 HTML 文件"""
    entries_dir = Path(__file__).parent / 'entries'
    all_entries = []

    # 读取所有条目文件
    for md_file in sorted(entries_dir.glob('*.md'), reverse=True):
        entries = parse_entry_file(md_file)
        all_entries.extend(entries)

    # 统计信息
    total_entries = len(all_entries)
    all_tags = set()
    active_days = len(set(e['time'][:10] for e in all_entries))
    this_month = len([e for e in all_entries if e['time'][:7] == datetime.now().strftime('%Y-%m')])

    for e in all_entries:
        all_tags.update(e['tags'])

    # 生成标签列表 HTML
    tag_list_html = '<li><a href="#" class="active" data-tag="all">全部</a></li>\n'
    for tag in sorted(all_tags):
        tag_name = tag[1:]  # 去掉 #
        tag_list_html += f'                    <li><a href="#" data-tag="{tag_name}">{tag}</a></li>\n'

    # 生成条目数据 JSON
    import json
    entries_json = json.dumps(all_entries, ensure_ascii=False, indent=4)

    html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Thoughts - 第二大脑</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }}
        header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        header p {{ opacity: 0.9; font-size: 1.1em; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-card h3 {{ color: #667eea; font-size: 2em; margin-bottom: 5px; }}
        .stat-card p {{ color: #666; font-size: 0.9em; }}
        .main-layout {{
            display: grid;
            grid-template-columns: 250px 1fr;
            gap: 30px;
        }}
        .sidebar {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            height: fit-content;
            position: sticky;
            top: 20px;
        }}
        .sidebar h3 {{
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .tag-list {{ list-style: none; }}
        .tag-list li {{ margin-bottom: 8px; }}
        .tag-list a {{
            display: block;
            padding: 8px 12px;
            background: #f0f0f0;
            border-radius: 6px;
            text-decoration: none;
            color: #555;
            transition: all 0.3s;
        }}
        .tag-list a:hover, .tag-list a.active {{
            background: #667eea;
            color: white;
        }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .entry {{
            border-left: 4px solid #667eea;
            padding-left: 20px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }}
        .entry:last-child {{ border-bottom: none; }}
        .entry-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }}
        .entry-type {{
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
        }}
        .entry-title {{ font-size: 1.2em; font-weight: 600; color: #333; }}
        .entry-time {{ color: #999; font-size: 0.85em; margin-left: auto; }}
        .entry-content {{ color: #555; margin-bottom: 15px; white-space: pre-wrap; }}
        .entry-tags {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }}
        .entry-tag {{
            background: #f0f0f0;
            padding: 4px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            color: #667eea;
            cursor: pointer;
        }}
        .entry-tag:hover {{ background: #667eea; color: white; }}
        .update-time {{
            text-align: center;
            color: #999;
            font-size: 0.85em;
            margin-top: 20px;
        }}
        @media (max-width: 768px) {{
            .main-layout {{ grid-template-columns: 1fr; }}
            .sidebar {{ position: static; }}
            header h1 {{ font-size: 1.8em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧠 Thoughts</h1>
            <p>第二大脑 - 捕获一切想法、灵感与感受</p>
        </header>

        <div class="stats">
            <div class="stat-card">
                <h3>{total_entries}</h3>
                <p>总条目</p>
            </div>
            <div class="stat-card">
                <h3>{len(all_tags)}</h3>
                <p>标签数</p>
            </div>
            <div class="stat-card">
                <h3>{active_days}</h3>
                <p>记录天数</p>
            </div>
            <div class="stat-card">
                <h3>{this_month}</h3>
                <p>本月条目</p>
            </div>
        </div>

        <div class="main-layout">
            <aside class="sidebar">
                <h3>🏷️ 标签</h3>
                <ul class="tag-list" id="tag-list">
{tag_list_html}                </ul>
            </aside>

            <main class="content">
                <div id="entries-container">
                    <!-- 条目会在这里渲染 -->
                </div>
                <div class="update-time">
                    最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    <br>
                    <small>运行 generate_viewer.py 刷新数据</small>
                </div>
            </main>
        </div>
    </div>

    <script>
        const entries = {entries_json};

        function renderEntries(filterTag = 'all') {{
            const container = document.getElementById('entries-container');

            let filtered = entries;
            if (filterTag !== 'all') {{
                filtered = entries.filter(e => e.tags.some(t => t.includes('#' + filterTag)));
            }}

            container.innerHTML = filtered.map(entry => `
                <article class="entry">
                    <div class="entry-header">
                        <span class="entry-type">${{entry.type}}</span>
                        <span class="entry-title">${{entry.title}}</span>
                        <time class="entry-time">${{entry.time}}</time>
                    </div>
                    <div class="entry-content">${{entry.content}}</div>
                    <div class="entry-tags">
                        ${{entry.tags.map(tag => `<span class="entry-tag">${{tag}}</span>`).join('')}}
                    </div>
                </article>
            `).join('');
        }}

        document.getElementById('tag-list').addEventListener('click', (e) => {{
            if (e.target.tagName === 'A') {{
                e.preventDefault();
                document.querySelectorAll('.tag-list a').forEach(a => a.classList.remove('active'));
                e.target.classList.add('active');
                renderEntries(e.target.dataset.tag);
            }}
        }});

        renderEntries();
    </script>
</body>
</html>
'''

    # 写入文件
    output_path = Path(__file__).parent / 'reports' / 'index.html'
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"[OK] 已生成 reports/index.html")
    print(f"   条目数: {total_entries}")
    print(f"   标签数: {len(all_tags)}")
    print(f"   记录天数: {active_days}")

if __name__ == '__main__':
    generate_html()
