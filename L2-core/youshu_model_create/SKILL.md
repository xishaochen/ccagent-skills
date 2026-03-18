---
name: youshu_model_create
description: 将猛犸/Hive表结构转换为有数BI模型SQL。当用户需要为有数BI创建数据模型、生成SELECT语句、将表字段转换为"原名AS中文注释名"格式时使用此技能。触发场景：用户提到"有数模型"、"有数BI模型"、"生成模型SQL"、"表结构转SELECT"、或直接提供表名需要转换时。
---

# 有数BI模型SQL生成器

## 功能说明

将猛犸数据平台的表结构自动转换为有数BI平台兼容的 SELECT 语句。

## 工作流程

1. **调用 mammoth-ddl 技能** 查询指定表的完整结构（字段名、类型、注释）
2. **生成 SELECT 语句** 将每个字段转换为 `原名 AS 中文注释名` 格式
3. **添加有数BI WHERE 条件** 使用固定的动态日期过滤

## 使用方式

```
/youshu_model_create <完整表名>
```

**示例：**
```
/youshu_model_create yidun_dw.ads_yidun_cst_aigc_rolling_12m_dd
```

## 输出格式

直接输出可用的 SQL 语句（中文别名使用反引号包围）：

```sql
SELECT
    field1 AS `字段1注释`,
    field2 AS `字段2注释`,
    ...
FROM 库名.表名
WHERE pt_d >= to_date(date_sub(now(), 2))
```

## 实现步骤

### Step 1: 查询表结构

使用 mammoth-ddl 技能获取表的 DDL 信息：
- 字段名（column_name）
- 字段类型（data_type）
- 字段注释（comment）

### Step 2: 生成字段映射

对每个字段生成映射语句：
- 提取字段注释中的核心描述（去除"格式YYYY-MM-DD"等格式说明）
- 格式化为 `column_name AS \`中文注释\``（中文别名必须用反引号包围）

注释简化规则：
- "客户ID" → `客户ID`
- "月份，格式YYYY-MM" → `月份`
- "分区日期，格式YYYY-MM-DD" → `分区日期`

### Step 3: 组装完整SQL

```sql
SELECT
    <字段映射列表，每行一个，逗号分隔，中文别名用反引号>
FROM <表名>
WHERE pt_d >= to_date(date_sub(now(), 2))
```

## WHERE 条件说明

有数BI模型使用动态日期过滤：
- `to_date(date_sub(now(), 2))` - 获取2天前的日期
- 这是固定配置，确保模型自动获取最近数据

## 注意事项

- **包含所有字段**：默认输出表中全部字段，包括分区字段
- **完整表名**：用户必须提供完整的 `库名.表名` 格式
- **注释为空**：如果字段没有注释，使用字段名本身作为别名
