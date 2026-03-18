# 业务规则参考

> 本文档包含各业务的详细规则

## 1. 易盾收入表使用规范

### 核心规则

使用 `yidun_dw.dwd_yidun_income_record_dd` 时**必须**遵守：

```sql
-- ✅ 正确的收入表查询模板
SELECT
    clouduserid,
    servicetype_one AS `产品线`,
    servicetype_two AS `产品`,
    SUM(amount / 1.06) AS `收入金额`  -- 税前金额除以1.06
FROM yidun_dw.dwd_yidun_income_record_dd
WHERE pt_d = '${pre_1day}'                          -- 必须：最新分区
    AND customersource NOT IN (1,2,4,5,10,9)       -- 必须：排除内部客户
    AND substr(tradetime,1,10) <= '${pre_1day}'    -- 必须：收入日期限制
GROUP BY clouduserid, servicetype_one, servicetype_two
```

### 三大必须条件

| 条件 | 说明 |
|------|------|
| `pt_d = '${pre_1day}'` | 使用最新分区 |
| `customersource NOT IN (1,2,4,5,10,9)` | 排除内部/测试客户 |
| `substr(tradetime,1,10) <= '${pre_1day}'` | 限制收入日期 |

### 客户来源过滤

| 值 | 含义 |
|---|------|
| 1 | 内部客户 |
| 2 | 测试客户 |
| 4 | 外部双创 |
| 5 | 审核团队 |
| 9 | 其他 |
| 10 | 合作伙伴易盾 |

### 产品字段映射

| 字段 | 含义 | 示例 |
|------|------|------|
| `servicetype_one` | 产品线（一级） | 内容安全、业务安全 |
| `servicetype_two` | 产品（二级） | 机审、风控 |
| `servicetype_big` | 产品分类（大类） | - |

---

## 2. 常见业务场景模板

### 客户增量收入分析

```sql
SELECT
    clouduserid AS `客户ID`,
    servicetype_one AS `产品线`,
    MAX(CASE WHEN year = 2024 THEN income ELSE 0 END) AS `2024年收入`,
    MAX(CASE WHEN year = 2025 THEN income ELSE 0 END) AS `2025年收入`,
    CASE
        WHEN MAX(CASE WHEN year = 2025 THEN income ELSE 0 END) >
             MAX(CASE WHEN year = 2024 THEN income ELSE 0 END)
        THEN MAX(CASE WHEN year = 2025 THEN income ELSE 0 END) -
             MAX(CASE WHEN year = 2024 THEN income ELSE 0 END)
        ELSE 0
    END AS `2025年增量收入`
FROM (
    SELECT
        clouduserid,
        servicetype_one,
        YEAR(tradetime) AS year,
        SUM(amount / 1.06) AS income
    FROM yidun_dw.dwd_yidun_income_record_dd
    WHERE pt_d = '${pre_1day}'
        AND customersource NOT IN (1,2,4,5,10,9)
        AND substr(tradetime,1,10) <= '${pre_1day}'
    GROUP BY clouduserid, servicetype_one, YEAR(tradetime)
) t
GROUP BY clouduserid, servicetype_one;
```

### 产品增购判断

```sql
SELECT
    clouduserid AS `客户ID`,
    servicetype_two AS `产品`,
    MAX(CASE WHEN year = 2024 THEN income ELSE 0 END) AS `2024年收入`,
    MAX(CASE WHEN year = 2025 THEN income ELSE 0 END) AS `2025年收入`,
    CASE
        WHEN MAX(CASE WHEN year = 2024 THEN income ELSE 0 END) = 0
             AND MAX(CASE WHEN year = 2025 THEN income ELSE 0 END) > 0
        THEN 'Y'
        ELSE 'N'
    END AS `2025年是否增购`
FROM (
    SELECT
        clouduserid,
        servicetype_two,
        YEAR(tradetime) AS year,
        SUM(amount / 1.06) AS income
    FROM yidun_dw.dwd_yidun_income_record_dd
    WHERE pt_d = '${pre_1day}'
        AND customersource NOT IN (1,2,4,5,10,9)
        AND substr(tradetime,1,10) <= '${pre_1day}'
        AND incometype = 0
    GROUP BY clouduserid, servicetype_two, YEAR(tradetime)
) t
GROUP BY clouduserid, servicetype_two;
```

---

## 3. 参数说明

猛犸平台支持的参数：

| 参数名 | 说明 | 示例（今天2026-01-28） |
|--------|------|------------------------|
| `${cur_day}` | 当天 | 2026-01-28 |
| `${pre_1day}` | 前1天 | 2026-01-27 |
| `${pre_2day}` | 前2天 | 2026-01-26 |
| `${pre_7day}` | 前7天 | 2026-01-21 |
| `${cur_m}` | 当前月第一天 | 2026-01-01 |
| `${pre_1m}` | 上月第一天 | 2025-12-01 |
| `${pre_1m_end}` | 上月最后一天 | 2025-12-31 |
