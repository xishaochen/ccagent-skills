# Hive 语法规范参考

> 本文档包含Hive SQL编写的详细语法规范

## 1. CTE与INSERT语句顺序（重要⭐）

### 核心规则

Hive 2.x 要求CTE必须放在整个语句的**最前面**，INSERT语句放在CTE**之后**。

### 正确写法

```sql
-- ✅ 正确：CTE放在INSERT之前
WITH monthly_base AS (
    SELECT cid, time_value, SUM(net_income) AS income
    FROM source_table
    GROUP BY cid, time_value
),
rolling_income AS (
    SELECT t1.cid, t1.time_value, SUM(t2.income) AS total_income
    FROM monthly_base t1
    LEFT JOIN monthly_base t2 ON t1.cid = t2.cid
    GROUP BY t1.cid, t1.time_value
)
INSERT OVERWRITE TABLE target_table PARTITION(pt_d='${pt_d}')
SELECT cid, time_value, total_income
FROM rolling_income;
```

### 错误写法

```sql
-- ❌ 错误：CTE放在INSERT之后（Hive 2.x 不支持）
INSERT OVERWRITE TABLE target_table PARTITION(pt_d='${pt_d}')
WITH monthly_base AS (
    SELECT ...
)
SELECT ... FROM monthly_base;
-- 报错：ParseException: cannot recognize input near 'WITH' 'cte_name' 'AS' in statement
```

### 兼容性对照表

| 语句类型 | CTE位置 | Hive 2.x |
|---------|--------|----------|
| `CREATE TABLE ... WITH` | CTE在CREATE之后 | ✅ 支持 |
| `SELECT ... (无INSERT)` | CTE在SELECT之前 | ✅ 支持 |
| `INSERT ... WITH` | CTE在INSERT之后 | ❌ **不支持** |
| `WITH ... INSERT` | CTE在INSERT之前 | ✅ 支持 |

**核心原则**：当CTE与INSERT OVERWRITE一起使用时，**永远把WITH放在最前面**。

---

## 2. 中文别名规范

### 核心规则

Impala不支持中文作为列名（column name），只能作为别名（alias）。

### 正确用法

```sql
-- ✅ SELECT最终输出可用中文别名
SELECT
    corp_name AS `客户名称`,
    product_line AS `产品线`,
    SUM(amount) AS `收入金额`
FROM table_name;

-- ✅ CTE和中间表必须使用英文列名
WITH base_data AS (
    SELECT
        cid,
        CASE WHEN type = '个人' THEN '个人认证' ELSE '企业认证' END AS customer_type,
        amount AS income
    FROM source_table
)
SELECT customer_type AS `客户类型`, SUM(income) AS `总收入`
FROM base_data
GROUP BY customer_type;
```

### 错误用法

```sql
-- ❌ CTE中使用中文列名
WITH base_data AS (
    SELECT cid, CASE WHEN ... END AS `客户类型`  -- Impala不支持
    FROM source_table
)
SELECT * FROM base_data;  -- 报错：Invalid column/field name: 客户类型
```

### 字段命名映射

| 中文 | 英文 |
|------|------|
| 客户类型 | customer_type |
| 客户规模 | customer_scale |
| 税后收入 | income |
| 年份 | year |
| 产品线 | product_line |
| 收入金额 | income_amount |
| 客户数 | customer_count |

---

## 3. 分区字段比较规范

### 核心原则

分区字段（如 `pt_d`）是STRING类型，与日期函数比较时需要显式类型转换。

### 推荐做法

```sql
-- ✅ 正确：使用 date_format() 将DATE转为STRING
WHERE pt_d = date_format(last_day(add_months('${pre_1day}', -2)), 'yyyy-MM-dd')

-- ❌ 错误：依赖隐式转换
WHERE pt_d = last_day(add_months('${pre_1day}', -2))
```

### 为什么需要显式转换

- Hive行为：严格字符串比较
- Spark行为：尝试类型转换为DATE
- 两者行为不一致可能导致结果差异

---

## 4. CTE编写规范

### 优化原则

1. **段落数量限制**：CTE段落不超过3-4个
2. **嵌套层级限制**：每段CTE最多允许2层嵌套
3. **逻辑清晰**：每个CTE有明确的职责

### 推荐写法

```sql
WITH
-- CTE1: 基础数据提取
base_data AS (
    SELECT cid, product, amount, SUBSTR(date, 1, 4) AS year
    FROM source_table
    WHERE condition
),
-- CTE2: 聚合计算
aggregated_data AS (
    SELECT cid, year, SUM(amount) AS total_amount
    FROM base_data
    GROUP BY cid, year
)
SELECT b.cid, a.total_amount
FROM base_data b
LEFT JOIN aggregated_data a ON b.cid = a.cid;
```

### 不推荐写法

```sql
-- ❌ CTE段落过多（5个）
WITH cte1 AS (...), cte2 AS (...), cte3 AS (...), cte4 AS (...), cte5 AS (...)
SELECT ...

-- ❌ 嵌套层级过深（3层以上）
WITH base AS (
    SELECT ... FROM (
        SELECT ... FROM (
            SELECT ... FROM table
        )
    )
)
SELECT ...
```

---

## 5. SQL自检清单

生成SQL后必须执行自检：

### 检查项

```
□ 1. 字段名一致性
   - CTE中重命名的字段，外部引用是否同步更新
   - SELECT字段与GROUP BY是否匹配

□ 2. CTE与INSERT顺序
   - CTE是否放在INSERT之前（Hive 2.x 必须）

□ 3. UNION ALL结构
   - 各Part字段数量是否一致
   - 字段类型是否兼容

□ 4. 语法检查
   - 括号是否匹配
   - 中文别名是否用反引号包围

□ 5. 参数检查
   - ${pre_1day}, ${cur_day}等参数名是否正确
   - 中间表是否带库名
```

### 常见错误案例

**案例1：CTE字段重命名后引用未更新**
```sql
-- ❌ 错误
WITH dim_corp_info AS (
    SELECT account_name_id AS customer_id, ...
    FROM ...
)
SELECT ... FROM dim_corp_info
WHERE account_name_id != '';  -- 错误！应改为 customer_id

-- ✅ 正确
WHERE customer_id != ''
```

**案例2：UNION ALL字段数量不一致**
```sql
-- ❌ 错误
SELECT a, b, c, d, e FROM t1
UNION ALL
SELECT a, b, c, d FROM t2    -- 少了e字段！

-- ✅ 正确
SELECT a, b, c, d, NULL AS e FROM t2
```

**案例3：GROUP BY字段遗漏**
```sql
-- ❌ 错误
SELECT clouduserid, servicetype_two, SUM(amount)
FROM table
GROUP BY clouduserid;  -- 遗漏servicetype_two！

-- ✅ 正确
GROUP BY clouduserid, servicetype_two;
```
