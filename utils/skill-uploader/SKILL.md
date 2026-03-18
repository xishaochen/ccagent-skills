---
name: skill-uploader
description: Claude Code技能打包与推送工具。支持敏感信息扫描、打包上传共享平台、推送到GitHub仓库。推送前自动检查API密钥、密码等敏感信息，确保安全发布。如有反馈和建议，欢迎加入popo群：8193118
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Edit
  - AskUserQuestion
---

## 何时使用

当用户需要：
- 将技能分享到共享平台（打包下载）
- 将技能推送到 GitHub 仓库（自动同步）
- 在推送前检查敏感信息

## 主流程

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────┐
│ 1.选择技能  │ →  │ 2.敏感信息扫描  │ →  │ 3.选择场景  │
└─────────────┘    └─────────────────┘    └─────────────┘
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          ▼                                           ▼
                 ┌─────────────────┐                        ┌─────────────────┐
                 │ A. 共享平台打包 │                        │ B. GitHub 推送  │
                 └─────────────────┘                        └─────────────────┘
```

## 步骤1：选择技能

询问用户要推送哪个技能，列出可选的技能：

```bash
# 列出用户级技能
ls -d ~/.claude/skills/*/ 2>/dev/null | xargs -n1 basename

# 列出项目级技能
ls -d .claude/skills/*/ 2>/dev/null | xargs -n1 basename
```

## 步骤2：敏感信息扫描

### 扫描规则

| 类型 | 检测模式 | 严重级别 |
|------|---------|---------|
| API Key | 32位以上字母数字组合 | 🔴 高危 |
| AK/SK | access_key/secret_key 变量 | 🔴 高危 |
| 密码 | password/passwd 字段赋值 | 🔴 高危 |
| Token | token/bearer 字段赋值 | 🟡 中危 |
| 内网IP | 10.x / 172.16-31.x / 192.168.x | 🟡 中危 |
| 私有配置 | config.json (未在排除列表) | 🟡 中危 |

### 执行扫描

```bash
# 扫描所有文件中的敏感信息
cd /path/to/skill/

# 检查 API Key 模式 (32位以上连续字母数字)
grep -rnE '[A-Za-z0-9]{32,}' --include='*.py' --include='*.js' --include='*.json' --include='*.md' .

# 检查密钥变量名
grep -rnEi '(access_key|secret_key|api_key|apikey|private_key)\s*[=:]' --include='*.py' --include='*.js' --include='*.json' .

# 检查密码字段
grep -rnEi '(password|passwd|pwd)\s*[=:]\s*['\''"][^'\''"]+['\''"]' --include='*.py' --include='*.js' --include='*.json' .

# 检查内网IP
grep -rnE '(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)' --include='*.py' --include='*.js' --include='*.json' --include='*.md' .

# 检查 config.json 是否存在
ls config.json 2>/dev/null && echo "⚠️ 发现 config.json"
```

### 扫描结果处理

1. **发现高危信息** → 停止推送，提示用户处理
2. **发现中危信息** → 警告用户，询问是否继续
3. **无敏感信息** → 继续推送流程

## 步骤3：选择推送场景

### 场景A：共享平台打包

适用于手动上传到技能共享平台。

```bash
cd /path/to/skill/

# 确保有 SKILL.md
if [ ! -f "SKILL.md" ]; then
  echo "❌ 缺少 SKILL.md 文件"
  exit 1
fi

# 打包，排除敏感文件
SKILL_NAME=$(basename $(pwd))
rm -f ${SKILL_NAME}.zip
zip -r ${SKILL_NAME}.zip . \
  -x "*.pyc" \
  -x "__pycache__/*" \
  -x ".DS_Store" \
  -x "config.json" \
  -x "*.secret" \
  -x ".env*" \
  -x ".git/*"

# 验证
echo "📦 打包完成: ${SKILL_NAME}.zip"
unzip -l ${SKILL_NAME}.zip
```

### 场景B：GitHub 推送

适用于自动同步到个人 GitHub 仓库。

#### 前置检查

```bash
# 检查是否在 git 仓库中
git rev-parse --git-dir > /dev/null 2>&1 || {
  echo "❌ 当前不在 git 仓库中"
  exit 1
}

# 检查远程仓库配置
git remote -v | grep origin || {
  echo "❌ 未配置 origin 远程仓库"
  exit 1
}
```

#### 执行推送

```bash
# 1. 确保敏感文件在 .gitignore 中
SKILL_PATH=".claude/skills/skill-name"
if ! grep -q "config.json" .gitignore 2>/dev/null; then
  echo "config.json" >> .gitignore
fi

# 2. 添加技能文件（排除敏感文件）
git add ${SKILL_PATH}/SKILL.md
git add ${SKILL_PATH}/README.md
git add ${SKILL_PATH}/*.py
git add ${SKILL_PATH}/*.js
# 不添加 config.json

# 3. 提交
git commit -m "feat: 更新 skill-uploader 技能"

# 4. 推送
git push origin $(git branch --show-current)
```

#### 更新技能索引

推送成功后，更新 skill-usage.json：

```json
{
  "skills": {
    "skill-name": {
      "source_type": "github",
      "github_url": "github.com/username",
      "github_hash": "<commit-hash>",
      "pushed": true,
      "lifecycle": "上线迭代期"
    }
  }
}
```

## 敏感信息处理指南

### 发现敏感信息后的处理方式

| 情况 | 处理方式 |
|------|---------|
| 硬编码的密钥 | 移除，改用环境变量或配置文件 |
| config.json | 添加到排除列表，创建 config.json.example |
| 内网地址 | 脱敏处理或移除 |
| 测试用密码 | 替换为占位符如 `your_password_here` |

### 推荐的目录结构

```
skill-name/
├── SKILL.md           # 平台元数据 (必需)
├── README.md          # 使用文档
├── main.py            # 主代码
├── config.json.example # 配置模板 (推荐)
├── .gitignore         # Git 忽略规则
└── tests/             # 测试文件
    └── test_main.py

# 本地有但不提交的文件:
# config.json          # 实际配置 (敏感)
# .env                 # 环境变量 (敏感)
```

## 版本信息

- **版本**: v2.0
- **更新时间**: 2026-03-18
- **新功能**: 敏感信息扫描、GitHub 推送支持
- **维护者**: Claude Code & 阿辰
