# 猛犸数据表探索器 (Mammoth Table Explorer)

快速探索猛犸平台Hive表的元数据信息，支持表结构查询、血缘分析、分区查看等功能。

## 功能特性

- 🔍 **表结构查询** - 快速获取表字段、类型、注释
- 🔗 **血缘分析** - 查询字段/表的上游和下游依赖
- 📊 **分区查看** - 列出表的所有分区及元数据
- 🚀 **网络检测** - 自动检测VPN连接状态

## 安装

1. 复制技能目录到你的 Claude Code skills 目录

2. 配置认证信息：
   ```bash
   cd mm-tbl-explore
   cp config.example.json config.json
   ```

3. 编辑 `config.json`，填入你的 AK/SK：
   ```json
   {
     "access_key": "你的AccessKey",
     "secret_key": "你的SecretKey",
     "user": "你的邮箱@corp.netease.com"
   }
   ```

## 使用方式

### 在 Claude Code 中使用

```bash
/mm-tbl-explore get_table yidun_dw dws_yidun_cst_service_income_dd
/mm-tbl-explore field_lineage yidun_dw dws_table total_income up
/mm-tbl-explore partitions yidun_dw dws_table
```

### 命令行使用

```bash
python mammoth_client.py get_table yidun_dw dws_table
python mammoth_client.py field_lineage yidun_dw dws_table field_name down
```

## 支持的命令

| 命令 | 说明 | 示例 |
|------|------|------|
| `get_table` | 获取表结构 | `get_table yidun_dw table_name` |
| `field_lineage` | 字段血缘 | `field_lineage db table field up` |
| `table_lineage` | 表血缘 | `table_lineage db table down` |
| `partitions` | 分区列表 | `partitions yidun_dw table_name` |
| `list_tables` | 表列表 | `list_tables yidun_dw` |

## 获取 AK/SK

请联系猛犸平台管理员获取 AccessKey 和 SecretKey。

## 常见问题

### Q: 提示网络连接失败？
A: 请确保已连接公司VPN，猛犸API需要通过内网访问。

### Q: 认证失败怎么办？
A: 检查 AK/SK 是否正确，确保系统时间同步。

### Q: 分区查询返回空？
A: 该表可能不是分区表，非分区表会返回空列表。

## 技术支持

- Popo群: **8193118**
- 问题反馈: 联系猛犸平台管理员

## 版本信息

- **版本**: v1.0.0
- **更新时间**: 2026-03-13
- **兼容性**: Python 3.7+
