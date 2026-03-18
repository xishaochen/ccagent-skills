# CCAgent Skills

> Claude Code 技能集合 - CCAgent 项目技能库

## 目录结构

```
ccagent-skills/
├── core/           # 核心工作技能
│   ├── mammoth-sql/          # 猛犸 SQL 执行器
│   ├── mammoth-tbl-explorer/ # 猛犸表探索器
│   └── youshu-explorer/      # 有数看板探索器
│
├── utils/          # 工具类技能
│   ├── skill-uploader/       # 技能打包推送工具
│   ├── guanbao-parser/       # 管报解析器
│   └── glm-quota-check/      # 智谱配额查询
│
├── archived/       # 归档技能
│   └── ...
│
└── docs/           # 共享文档
    └── shared-scripts/
```

## 技能分类

### L2-领域核心技能

| 技能 | 分类 | 说明 |
|------|------|------|
| mammoth-sql | 需求转化开发 | 猛犸平台 SQL 执行器 |
| mammoth-tbl-explorer | 需求转化开发 | 猛犸表结构、血缘查询 |
| youshu-dashboard-explorer | 看板改造 | 有数 BI 看板探索 |
| skill-uploader | 技能管理 | 技能打包与推送 |

### L1-公共技能

| 技能 | 说明 |
|------|------|
| guanbao-parser | 管报 Excel 解析 |
| glm-quota-check | 智谱 AI 配额查询 |

## 使用方式

### 安装技能

```bash
# 复制到用户级技能目录
cp -r core/mammoth-sql ~/.claude/skills/

# 或复制到项目级技能目录
cp -r core/mammoth-sql your-project/.claude/skills/
```

### 技能管家

推荐配合 [skill-hub](https://github.com/xishaochen/skill-hub) 使用，实现技能的统一管理。

## 相关链接

- [skill-hub](https://github.com/xishaochen/skill-hub) - 技能管家
- [CCAgent](https://github.com/xishaochen/CCAgent) - Claude 协作伙伴系统

## 维护者

- 阿辰 & Claude
- popo群: 8193118
