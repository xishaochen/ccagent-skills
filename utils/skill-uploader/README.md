# Skill Uploader - 技能打包与推送工具 v2.0

> Claude Code 技能发布助手，支持敏感信息扫描、共享平台打包、GitHub 推送

## 🆕 v2.0 新特性

- **敏感信息扫描** - 推送前自动检测 API Key、密码等敏感信息
- **GitHub 推送** - 一键推送技能到个人 GitHub 仓库
- **安全审计报告** - 生成扫描报告，清晰展示风险项

## 使用场景

| 场景 | 说明 | 适用对象 |
|------|------|---------|
| 共享平台打包 | 生成 zip 包供手动上传 | 内部共享、ClawdHub |
| GitHub 推送 | 自动 git push 到仓库 | 个人备份、开源分享 |

---

## 快速开始

### 交互式使用

直接调用技能，按提示操作：

```
用户: 我想推送 skill-hub 到 GitHub
Claude: [执行敏感信息扫描...]
        [显示扫描结果...]
        [执行 git 推送...]
```

### 命令式使用

```
用户: 扫描 mammoth-sql 技能的敏感信息
用户: 把 guanbao-parser 打包成 zip
用户: 推送 skill-hub 到 GitHub
```

---

## 敏感信息扫描

### 检测规则

| 类型 | 模式 | 级别 | 示例 |
|------|------|------|------|
| API Key | 32+字母数字 | 🔴 高危 | `sk-ant-xxxx...` |
| AK/SK | access/secret key | 🔴 高危 | `access_key: "xxx"` |
| 密码 | password 字段 | 🔴 高危 | `"password": "123456"` |
| Token | token/bearer | 🟡 中危 | `bearer_token: "..."` |
| 内网IP | 私有网段 | 🟡 中危 | `192.168.1.100` |
| 私有配置 | config.json | 🟡 中危 | 包含凭证的配置 |

### 扫描示例

```bash
# 完整扫描脚本
scan_sensitive() {
  local skill_path=$1
  echo "🔍 扫描敏感信息: $skill_path"

  # API Key
  grep -rnE '[A-Za-z0-9]{32,}' "$skill_path" --include='*.py' --include='*.js' --include='*.json' && echo "⚠️ 发现可能的 API Key"

  # 密钥变量
  grep -rnEi '(access_key|secret_key|api_key)\s*[=:]' "$skill_path" && echo "⚠️ 发现密钥变量"

  # 密码
  grep -rnEi '(password|passwd|pwd)\s*[=:]\s*['\''"][^'\''"]+['\''"]' "$skill_path" && echo "⚠️ 发现密码字段"

  # config.json
  [ -f "$skill_path/config.json" ] && echo "⚠️ 发现 config.json"
}
```

### 处理建议

发现敏感信息后：

1. **硬编码密钥** → 改用环境变量
2. **config.json** → 创建 `.example` 模板，添加到 `.gitignore`
3. **测试密码** → 替换为占位符

---

## 共享平台打包

### 平台要求

#### SKILL.md 格式

```yaml
---
name: your-skill-name
description: 技能描述。如有反馈和建议，欢迎加入popo群：8193118
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---
```

### 打包命令

```bash
cd /path/to/skill/

# 创建 zip 包（排除敏感文件）
rm -f skill-name.zip && zip -r skill-name.zip . \
  -x "*.pyc" \
  -x "__pycache__/*" \
  -x ".DS_Store" \
  -x "config.json" \
  -x "*.secret" \
  -x ".env*" \
  -x ".git/*"

# 验证
unzip -l skill-name.zip
unzip -p skill-name.zip SKILL.md
```

### 必须排除的文件

| 文件/目录 | 原因 |
|----------|------|
| `config.json` | 可能包含 AK/SK 凭证 |
| `.env*` | 环境变量，通常有密钥 |
| `*.secret` | 显式标记的敏感文件 |
| `__pycache__/` | Python 缓存 |
| `.git/` | Git 历史 |

---

## GitHub 推送

### 前置条件

1. 技能在 git 仓库中
2. 已配置 origin 远程仓库
3. 有推送权限

### 推送流程

```bash
# 1. 敏感信息扫描（自动）
# 2. 确保 .gitignore 包含敏感文件
# 3. git add 技能文件（排除敏感文件）
# 4. git commit
# 5. git push
```

### 示例

```bash
# 添加技能文件
git add .claude/skills/skill-hub/SKILL.md
git add .claude/skills/skill-hub/README.md
git add .claude/skills/skill-hub/scripts/*.py
# 注意：不添加 config.json

# 提交并推送
git commit -m "feat: 更新 skill-hub 技能"
git push origin main
```

### 更新技能索引

推送后自动更新 `~/.claude/skill-usage.json`：

```json
{
  "skill-hub": {
    "source_type": "github",
    "github_url": "github.com/xishaochen",
    "github_hash": "abc123...",
    "pushed": true,
    "lifecycle": "上线迭代期"
  }
}
```

---

## 目录结构规范

### 推荐结构

```
skill-name/
├── SKILL.md              # 平台元数据 (必需)
├── README.md             # 详细文档
├── main.py               # 主代码
├── scripts/              # 脚本目录
│   └── helper.py
├── config.json.example   # 配置模板 (推荐)
├── .gitignore            # Git 忽略规则
└── tests/                # 测试文件
    └── test_main.py

# 本地存在但不提交:
# config.json             # 实际配置
# .env                    # 环境变量
```

### .gitignore 模板

```gitignore
# 敏感配置
config.json
.env
*.secret

# 缓存
__pycache__/
*.pyc
.DS_Store

# IDE
.idea/
.vscode/
```

---

## 常见问题

### Q: 扫描发现敏感信息怎么办？

1. 检查是否为误报（如示例代码中的占位符）
2. 如果是真实凭证，立即移除并轮换
3. 使用环境变量或 config.json.example 替代

### Q: 如何处理已有的 config.json？

```bash
# 创建模板
cp config.json config.json.example
# 脱敏处理
sed -i '' 's/"api_key": "xxx"/"api_key": "YOUR_API_KEY"/' config.json.example
# 添加到 .gitignore
echo "config.json" >> .gitignore
```

### Q: 推送到 GitHub 后如何验证？

```bash
# 检查远程仓库
git ls-remote origin

# 在 GitHub 网页检查文件内容
# 确认 config.json 等敏感文件未被提交
```

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v2.0 | 2026-03-18 | 敏感信息扫描、GitHub 推送支持 |
| v1.0 | 2026-03-05 | 初始版本，共享平台打包 |

---

**维护者**: Claude Code & 阿辰
**反馈渠道**: popo群 8193118
