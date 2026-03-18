# GitHub 集成指南

## 仓库信息

| 项目 | 仓库地址 | GitHub Pages |
|------|---------|-------------|
| finance-ledger | https://github.com/wuyaorui2001-crypto/finance-ledger-v3 | https://wuyaorui2001-crypto.github.io/finance-ledger-v3/ |
| thoughts | https://github.com/wuyaorui2001-crypto/thoughts | https://wuyaorui2001-crypto.github.io/thoughts/ |

## 新设备/新Agent快速上手

### 1. 克隆仓库

```bash
# finance-ledger
git clone https://github.com/wuyaorui2001-crypto/finance-ledger-v3.git

# thoughts
git clone https://github.com/wuyaorui2001-crypto/thoughts.git
```

### 2. 读取项目文档

```bash
# 进入项目目录
cd finance-ledger-v3  # 或 thoughts

# 读取 AI 操作指南
cat SYSTEM.md

# 读取项目说明
cat README.md
```

### 3. 开始工作

根据 SYSTEM.md 中的 SOP 流程开始工作。

---

## 日常同步流程

### 推送更改到 GitHub

```bash
# 添加所有更改
git add .

# 提交
git commit -m "更新说明: $(date +%Y-%m-%d)"

# 推送到远程
git push origin main
```

### 自动触发

推送后 GitHub Actions 会自动：
1. 运行可视化脚本
2. 生成 HTML 报表
3. 部署到 GitHub Pages

---

## 另一个 AI 接手流程

当新 Agent 需要接手项目时：

1. **克隆仓库** → 获取完整项目历史
2. **读取 SYSTEM.md** → 理解项目结构和操作规则
3. **读取 MEMORY.md** → 了解项目历史和决策
4. **开始工作** → 按照 SOP 执行

无需用户额外解释，实现无缝交接。

---

## 故障排查

### GitHub Pages 未更新

1. 检查 Actions 状态: 仓库页面 → Actions 标签
2. 确认已启用 Pages: Settings → Pages → Source: GitHub Actions

### 推送失败

```bash
# 先拉取最新更改
git pull origin main

# 解决冲突后重新推送
git push origin main
```

---

*此文件帮助新 Agent 快速理解 GitHub 集成方案*
