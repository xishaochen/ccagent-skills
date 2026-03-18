---
name: mammoth-sql
description: |
  猛犸平台SQL生成助手。当用户需要生成Hive SQL时使用此技能，包括：创建表、INSERT语句、复杂查询、数据分析等场景。

  触发场景：
  - 用户明确要求生成SQL
  - 用户描述数据需求需要用SQL实现
  - 用户提到猛犸/Hive/Impala相关开发
  - 用户需要基于数据仓库表进行分析

  请确保在任何SQL生成场景中都使用此技能，即使用户没有明确提到"猛犸"或"SQL"。
---

# 猛犸SQL生成助手

为猛犸(EasyData)平台生成符合规范的Hive SQL代码。

## 核心原则

1. **SQL生成专家**，不执行SQL（用户自行执行）
2. **先确认理解**，再生成代码
3. **遵循规范**，确保兼容性

---

## 工作流程

```
用户需求 → 理解确认 → 获取表结构 → 生成SQL → 自检输出
```

### 步骤1：理解需求并确认

生成SQL前，**必须先输出期望的数据样式**：

```markdown
## 📋 理解确认

### 数据源
- 表名：xxx
- 筛选条件：xxx

### 结果字段
| 字段 | 类型 | 说明 |
|------|------|------|

### 期望数据样式
| 维度 | 指标1 | 指标2 |
|------|-------|-------|

请确认理解是否正确？
```

### 步骤2：获取表结构

用户确认后，调用 mammoth-ddl 获取表结构：

```bash
/mammoth-ddl <表名>
```

### 步骤3：生成SQL

基于表结构和业务规则生成SQL代码。

### 步骤4：自检输出

生成后执行自检（见下方自检清单）。

---

## 核心语法规范（必须遵守）

### ⚠️ CTE与INSERT顺序（最重要）

**Hive 2.x 要求CTE必须放在INSERT之前**

```sql
-- ✅ 正确
WITH cte AS (...)
INSERT OVERWRITE TABLE xxx PARTITION(pt_d='${pt_d}')
SELECT ... FROM cte;

-- ❌ 错误（会报ParseException）
INSERT OVERWRITE TABLE xxx PARTITION(pt_d='${pt_d}')
WITH cte AS (...)
SELECT ... FROM cte;
```

### 中文别名规则

- **SELECT最终输出**：可用中文别名（用反引号包围）
- **CTE/中间表**：必须用英文列名

```sql
-- ✅ 正确
WITH base AS (
    SELECT cid, type AS customer_type  -- 英文列名
    FROM table
)
SELECT customer_type AS `客户类型`  -- 中文别名
FROM base;

-- ❌ 错误
WITH base AS (
    SELECT cid, type AS `客户类型`  -- CTE中不能用中文
    FROM table
)
```

### 表命名规范

```sql
-- 中间表（带库名）
CREATE TABLE yidun_dw.tmp_analysis AS ...

-- 正式表（DROP + CREATE）
DROP TABLE IF EXISTS yidun_dw.ads_result_dd;
CREATE TABLE yidun_dw.ads_result_dd (...)
```

---

## SQL自检清单

生成SQL后必须检查：

```
□ CTE与INSERT顺序正确（WITH在最前）
□ CTE中使用英文列名
□ GROUP BY包含所有非聚合字段
□ 中文别名用反引号包围
□ 中间表带库名
□ 参数名正确（${pre_1day}等）
```

---

## 常用模板

### 正式表DDL

```sql
DROP TABLE IF EXISTS <库名>.<表名>_dd;

CREATE TABLE <库名>.<表名>_dd (
    cid         STRING        COMMENT '客户ID',
    time_value  STRING        COMMENT '时间',
    net_income  DECIMAL(18,4) COMMENT '净收入'
)
COMMENT '表说明'
PARTITIONED BY (pt_d STRING COMMENT '日期分区')
ROW FORMAT SERDE
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
TBLPROPERTIES ('SYNC_METASTORE'='on');
```

### INSERT语句（CTE模式）

```sql
WITH base_data AS (
    SELECT cid, time_value, SUM(net_income) AS income
    FROM source_table
    WHERE pt_d = '${pre_1day}'
    GROUP BY cid, time_value
)
INSERT OVERWRITE TABLE target_table PARTITION(pt_d='${pt_d}')
SELECT cid, time_value, income
FROM base_data
WHERE income > 0;
```

### 易盾收入查询

```sql
SELECT
    clouduserid,
    servicetype_one AS `产品线`,
    SUM(amount / 1.06) AS `收入金额`
FROM yidun_dw.dwd_yidun_income_record_dd
WHERE pt_d = '${pre_1day}'
    AND customersource NOT IN (1,2,4,5,10,9)
    AND substr(tradetime,1,10) <= '${pre_1day}'
GROUP BY clouduserid, servicetype_one
```

---

## 详细参考文档

当需要更详细的规范时，查阅以下文档：

| 文档 | 内容 |
|------|------|
| `references/hive-syntax.md` | Hive语法规范、CTE规则、自检清单 |
| `references/table-design.md` | 表设计规范、DDL模板、CSV导入 |
| `references/business-rules.md` | 业务规则、参数说明 |

---

## 配合使用的Skills

```bash
/mammoth-ddl <表名>       # 获取表结构
/mammoth-partition check  # 检查分区
/mammoth-partition latest # 查看最新分区
```

---

**版本**: v5.0 (重构精简版)
**最后更新**: 2026-03-16
**维护者**: 阿辰 & Claude

## 更新日志

### v5.0 (2026-03-16) - 重构精简版
1. **分层结构**：将详细规范拆分到references/目录
2. **精简核心文档**：SKILL.md从1322行精简到<300行
3. **强化核心规则**：突出CTE与INSERT顺序规则
4. **优化可读性**：清晰的目录结构和表格

### v4.4 (2026-03-16) - CTE-INSERT顺序版
1. 新增CTE与INSERT语句顺序规则
