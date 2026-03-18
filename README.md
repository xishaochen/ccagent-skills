# CCAgent Skills

> Claude Code 技能集合 - CCAgent 项目技能库

## 目录结构

```
ccagent-skills/
├── L3-smart/              # 高阶决策技能
│   │
│   └── [策略/架构/治理类技能]
│
├── L2-core/               # 领域核心技能
│   │
│   ├── mammoth-sql/           # 猛犸 SQL 执行器
│   ├── mammoth-tbl-explorer/  # 猛犸表探索器
│   ├── youshu-explorer/       # 有数看板探索器
│   └── ...
│
├── L1-utils/              # 公共工具技能
│   │
│   ├── skill-uploader/        # 技能打包推送工具
│   ├── guanbao-parser/        # 管报解析器
│   ├── glm-quota-check/       # 智谱配额查询
│   └── ...
│
└── Backup-archived/       # 归档技能
    │
    └── [已下线技能备份]
```

## 层级分类

| 目录 | 层级 | 特征 | 示例 |
|------|------|------|------|
| **L3-smart** | 高阶决策 | 规划、架构、治理、策略 | cto-advisor, brainstorming |
| **L2-core** | 领域核心 | 岗位独有专业技能 | mammoth-sql, youshu-explorer |
| **L1-utils** | 公共工具 | 通用工具、流程执行 | docx, xlsx, skill-uploader |
| **Backup-archived** | 已归档 | 过期/替代技能 | 旧版本备份 |

## 分类规则

### 优先级

```
1. SKILL.md 显式声明 level 字段  (最高优先级)
2. 目录位置隐式分类
3. skill-hub 规则推断           (兜底)
```

### 目录 → 层级映射

```python
LEVEL_FROM_DIR = {
    "L3-smart": "L3-高阶决策技能",
    "L2-core": "L2-领域核心技能",
    "L1-utils": "L1-公共技能",
    "Backup-archived": "已归档"
}
```

## 使用方式

### 安装技能

```bash
# 复制到用户级技能目录
cp -r L2-core/mammoth-sql ~/.claude/skills/

# 或复制到项目级技能目录
cp -r L2-core/mammoth-sql your-project/.claude/skills/
```

### 技能管家

推荐配合 [skill-hub](https://github.com/xishaochen/skill-hub) 使用，实现技能的统一管理。

## 相关链接

- [skill-hub](https://github.com/xishaochen/skill-hub) - 技能管家
- [CCAgent](https://github.com/xishaochen/CCAgent) - Claude 协作伙伴系统

## 维护者

- 阿辰 & Claude
- popo群: 8193118
