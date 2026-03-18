---
name: youshu-dashboard-explorer
description: 有数BI看板探索器 - 通过分析有数BI导出的JSON配置文件，帮助用户快速定位所需看板、理解数据结构、掌握字段映射关系。支持智能搜索看板、查看看板详情、字段映射查询、业务场景推荐等功能。如有反馈和建议，欢迎加入popo群：8193118
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# 有数BI ID层级结构

## 重要约定

**用户说的"模型ID"或"mid"默认指的是 `DATA_MODEL` 层级的 id。**

## ID层级说明

有数BI中存在多种ID层级：

| 层级 | 对象类型 | 说明 | 示例 |
|------|----------|------|------|
| **DATA_MODEL** | 数据模型 | 用户在界面上看到的模型，**这是默认的"模型ID"** | id: 102847 |
| CUSTOM_TABLE | 自定义表 | 底层SQL自定义表，被DATA_MODEL引用 | id: 45404 |
| DATA_SET | 数据集 | 数据集层级 | - |
| REPORT | 报表 | 看板/报表层级 | - |

## 查询优先级

1. 用户问"模型ID"时，优先查找 `DATA_MODEL` 类型的 id
2. 用户明确要其他层级时，再查找对应类型
