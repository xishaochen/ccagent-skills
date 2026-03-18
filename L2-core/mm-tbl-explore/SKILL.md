---
name: mm-tbl-explore
description: 猛犸数据表探索器 - 查询Hive表的元数据信息，包括表结构、字段血缘、表血缘、分区列表。当用户需要查看猛犸/Hive表结构、查询数据血缘关系、查看表分区、了解表上下游依赖时使用此技能。触发词：表结构、DDL、DESCRIBE、血缘、分区、猛犸表、Hive表、字段来源、表依赖。
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# 猛犸数据表探索器 (Mammoth Table Explorer)

快速探索猛犸平台Hive表的元数据信息，支持表结构查询、血缘分析、分区查看等功能。

## 核心功能

| 功能 | 命令 | 说明 |
|------|------|------|
| 表结构查询 | `get_table` | 获取表的完整字段列表、类型、注释 |
| 字段血缘 | `field_lineage` | 查询字段的上游/下游来源 |
| 表血缘 | `table_lineage` | 查询表的上游/下游依赖关系 |
| 分区列表 | `partitions` | 查看表的所有分区信息 |
| 表列表 | `list_tables` | 列出数据库中的所有表 |

## 使用方式

```bash
/mm-tbl-explore <命令> [参数...]
```

### 命令详情

#### 1. 查询表结构
```bash
/mm-tbl-explore get_table <数据库> <表名>
```
**示例**: `/mm-tbl-explore get_table yidun_dw dws_yidun_cst_service_income_dd`

#### 2. 查询字段血缘
```bash
/mm-tbl-explore field_lineage <数据库> <表名> <字段名> <up|down>
```
- `up` - 查询上游血缘（字段来自哪里）
- `down` - 查询下游血缘（字段被哪些表使用）

**示例**: `/mm-tbl-explore field_lineage yidun_dw dws_table total_income up`

#### 3. 查询表血缘
```bash
/mm-tbl-explore table_lineage <数据库> <表名> <up|down>
```
**示例**: `/mm-tbl-explore table_lineage yidun_dw dws_table up`

#### 4. 查看分区列表
```bash
/mm-tbl-explore partitions <数据库> <表名>
```
**示例**: `/mm-tbl-explore partitions yidun_dw dws_table`

#### 5. 列出数据库中的表
```bash
/mm-tbl-explore list_tables <数据库>
```
**示例**: `/mm-tbl-explore list_tables yidun_dw`

## 配置说明

### 首次使用配置

1. 复制配置模板：
   ```bash
   cp config.example.json config.json
   ```

2. 编辑 `config.json`，填入你的认证信息：
   ```json
   {
     "description": "猛犸平台 AK/SK 认证配置",
     "base_url": "http://easyopenapi-gy.service.163.org",
     "access_key": "你的AccessKey",
     "secret_key": "你的SecretKey",
     "product": "smart_ep",
     "user": "你的邮箱@corp.netease.com",
     "datasource_id": 832,
     "catalog_name": "hz8-hive-catalog"
   }
   ```

### 获取 AK/SK

请联系猛犸平台管理员获取 AccessKey 和 SecretKey。

## 常见问题

### 网络连接失败
- 确保已连接公司VPN
- 检查 `base_url` 是否正确

### 认证失败
- 检查 AK/SK 是否正确
- 确认时间戳同步（系统时间需准确）

### 分区查询返回空
- 确认表是否为分区表
- 非分区表会返回空列表

## 技术细节

- **认证方式**: AK/SK + MD5签名
- **时间戳格式**: 毫秒级 (13位)
- **签名算法**: `MD5(secret_key + timestamp)`

## 反馈与支持

如有问题或建议，欢迎加入 popo群：**8193118**

---

**版本**: v1.0.0
**作者**: 网易数据团队
