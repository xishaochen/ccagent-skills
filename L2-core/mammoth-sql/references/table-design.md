# 表设计规范参考

> 本文档包含表结构设计的详细规范

## 1. 执行引擎选择

### Impala vs Hive

| 操作类型 | 表类型 | 推荐引擎 | SQL语法 |
|---------|--------|---------|---------|
| 创建中间表 | `tmp_xxx` | Impala | `CREATE TABLE db.tmp_xxx AS` |
| 创建正式表 | `dwd_xxx`, `dws_xxx`, `ads_xxx` | Hive | `DROP + CREATE TABLE` |
| 查询分析 | 任意 | Impala | `SELECT ...` |
| 定时调度 | 正式表 | Hive | `INSERT OVERWRITE` 或 `DROP + CREATE` |

### 中间表命名规范

```sql
-- ✅ 正确：带库名
CREATE TABLE yidun_dw.tmp_analysis AS ...
CREATE TABLE cb.tmp_analysis AS ...

-- ❌ 错误：缺少库名
CREATE TABLE tmp_analysis AS ...
```

**库名选择策略**：
- 用户明确指定：使用用户指定的库名
- 用户未指定：根据上下文推断
  - 易盾 → `yidun_dw`
  - 云商 → `cb`
  - 七鱼 → `dc_qiyu`
  - 智企 → `smart`

---

## 2. 正式表DDL模板

### 核心原则

正式表默认使用 **Parquet 格式**，方便 Impala 同步和查询。

### 标准模板

```sql
DROP TABLE IF EXISTS yidun_dw.ads_result_dd;

CREATE TABLE yidun_dw.ads_result_dd (
    cid               STRING        COMMENT '客户ID',
    time_value        STRING        COMMENT '时间',
    corpname          STRING        COMMENT '客户名称',
    net_income        DECIMAL(18,4) COMMENT '净收入'
    -- 其他字段...
)
COMMENT '表说明'
PARTITIONED BY (pt_d STRING COMMENT '日期分区')
ROW FORMAT SERDE
  'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
STORED AS INPUTFORMAT
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat'
OUTPUTFORMAT
  'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
TBLPROPERTIES (
  'SYNC_METASTORE'='on');
```

### 格式说明

| 配置项 | 值 | 说明 |
|-------|-----|------|
| 存储格式 | Parquet | 列式存储，查询性能好 |
| SerDe | ParquetHiveSerDe | Parquet序列化/反序列化 |
| SYNC_METASTORE | on | 自动同步元数据到Impala |

### 不推荐的格式

```sql
-- ❌ 不推荐：ORC格式（Impala需要手动REFRESH）
STORED AS ORC TBLPROPERTIES ('orc.compress'='SNAPPY');

-- ❌ 不推荐：TEXTFILE（性能差）
ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t' STORED AS TEXTFILE;
```

---

## 3. CSV导入表规范

### 命名规范

| 业务 | 库名 | 非分区表后缀 | 分区表后缀 |
|------|------|-------------|-----------|
| 易盾 | `yidun_dw` | `_nd` | `_dd` / `_mm` |
| 智企 | `smart` | `_nd` | `_dd` / `_mm` |
| 云商 | `cb` | `_nd` | `_dd` / `_mm` |
| 七鱼 | `dc_qiyu` | `_nd` | `_dd` / `_mm` |

### 字段类型规范

**核心原则**：导入CSV的表，**所有字段统一使用STRING类型**

```sql
-- ✅ 正确
CREATE TABLE yidun_dw.ods_budget_cost_nd (
    product STRING COMMENT '产品',
    amount STRING COMMENT '费用金额'  -- 数值也用STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
TBLPROPERTIES ('skip.header.line.count'='1');

-- ❌ 错误
CREATE TABLE yidun_dw.ods_budget_cost_nd (
    amount DECIMAL(18,2) COMMENT '费用金额'  -- 可能解析失败
)
```

### 查询时类型转换

```sql
SELECT
    product,
    CAST(amount AS DECIMAL(18,2)) AS amount_decimal,
    ROUND(CAST(amount AS DECIMAL(18,2)), 2) AS amount_rounded
FROM yidun_dw.ods_budget_cost_nd;
```

---

## 4. 表命名规范

### 分层命名

| 层级 | 前缀 | 说明 |
|------|------|------|
| ODS | `ods_` | 原始数据层 |
| DWD | `dwd_` | 明细数据层 |
| DWS | `dws_` | 汇总数据层 |
| ADS | `ads_` | 应用数据层 |
| TMP | `tmp_` | 临时/中间表 |

### 后缀规范

| 后缀 | 说明 |
|------|------|
| `_dd` | 日分区表 |
| `_mm` | 月分区表 |
| `_nd` | 非分区表 |

### 命名示例

```
yidun_dw.ods_yidun_source_dd      # ODS层，日分区
yidun_dw.dwd_yidun_order_detail_dd  # DWD层，日分区
yidun_dw.dws_yidun_customer_summary_mm  # DWS层，月分区
yidun_dw.ads_yidun_report_dd      # ADS层，日分区
yidun_dw.tmp_yidun_analysis       # 临时表
```
