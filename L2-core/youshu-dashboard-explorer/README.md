# 有数BI看板探索器

## 技能概述

**youshu-dashboard-explorer** 是一个专门用于快速探索和熟悉有数BI看板体系的智能助手。通过分析有数导出的JSON配置文件，帮助你快速定位所需的看板、理解数据结构、掌握字段映射关系。

## 环境说明

本技能支持在不同环境中使用，调用方式略有不同：

### 方式1：在 Warp Agent Mode 中使用（推荐）
如果你使用的是 Warp Agent Mode，可以直接使用命令调用：
```bash
/youshu-dashboard-explorer search 回款
/youshu-dashboard-explorer field consume_amount
/youshu-dashboard-explorer detail --dashboard_id=244793
```

### 方式2：在 Claude Code CLI 中使用
如果你使用的是 Claude Code CLI，需要通过 Python import 方式调用：
```python
python3 -c "
import sys
sys.path.append('.claude/skills/youshu-dashboard-explorer')
from explorer_v3 import YoushuDashboardExplorerV3, format_search_results_v3

json_file = 'workspace/YidunTasks/易盾BI/易盾BI全图_extracted/reportDepends.txt'
explorer = YoushuDashboardExplorerV3(json_file)

# 搜索关键词
results = explorer.search('回款')
print(format_search_results_v3(results, '回款'))
"
```

### 方式3：在 Python 脚本中使用
你也可以在自己的 Python 脚本中导入使用：
```python
from explorer_v3 import YoushuDashboardExplorerV3, format_search_results_v3

# 初始化探索器
json_file = 'path/to/reportDepends.txt'
explorer = YoushuDashboardExplorerV3(json_file)

# 搜索看板
results = explorer.search('是否后付费')
print(format_search_results_v3(results, '是否后付费'))

# 查看看板详情
dashboard = explorer.get_dashboard_by_id(244793)
# ... 其他操作
```

**注意**：
- `explorer_v3.py` 是一个 Python 类库，不是命令行工具
- 需要确保 JSON 数据文件路径正确
- 建议优先使用 Warp Agent Mode，体验更好

## 使用场景

### 1. 快速定位看板
- "我想查看外部回款目标进度，应该看哪个看板？"
- "哪个看板包含成本相关的数据？"
- "在服客户数据在哪个看板？"

### 2. 理解看板结构
- "【回款】看板包含哪些组件？"
- "这个看板使用了哪些数据模型？"
- "看板上的字段都来自哪些表？"

### 3. 查找字段定义和计算公式（新增）
- "试用数是怎么计算的？"
- "这个指标的业务定义是什么？"
- "看板中有没有关于这个字段的说明？"
- **💡 重要经验**：当需要了解某个字段的计算逻辑时，除了查看数据模型和字段配置，还应该搜索注释框中的信息，因为注释框中通常包含业务定义、计算公式、口径说明等重要信息。

### 4. 通过URL查询看板
- "https://smartwe.youdata.netease.com/dash/folder/450201343?rid=117336&did=244793 这个看板用到了哪个模型？"
- "这个看板URL对应的数据模型是什么？"
- "从URL提取看板ID并查询详情"

### 5. 字段映射查询
- "consume_amount_y 在看板上显示为什么名称？"
- "哪些看板使用了'净收入'这个字段？"
- "成本相关的字段有哪些？"

### 6. 业务场景推荐
- "我需要分析客户流失，推荐哪些看板？"
- "销售业绩分析应该看哪些看板？"
- "AIGC业务的看板有哪些？"

## 核心功能

### 功能1：智能搜索看板（V3优化版）
**搜索优先级（按层级关系排序）**：
1. 🥇 **报表名称匹配**（最高优先级）- 匹配报表名称
2. 🥈 **看板标题匹配**（高优先级）- 匹配看板名称
3. 🥉 **组件标题匹配**（中高优先级）- 匹配组件名称
4. 💬 **注释框内容匹配**（中高优先级）- 匹配注释框中的业务说明（新增）
5. 📋 **数据模型名称匹配**（中优先级）- 匹配数据模型名称
6. 🔍 **字段别名匹配**（中低优先级）- 匹配用户看到的字段名
7. 📝 **字段名匹配**（低优先级）- 匹配技术字段名
8. 💡 **维度字段提示**（最低优先级）- 提示可能包含搜索值的维度字段

**关键优化**：
- ✅ 仅搜索可见的组件（过滤comment、rect等容器类型）
- ✅ **新增注释框内容搜索**，帮助快速找到字段定义、计算公式、业务规则等重要说明
- ✅ 搜索范围包含报表名称、看板标题、组件标题、注释框内容、数据模型名称、字段别名
- ✅ 结果按层级关系优先级排序
- ✅ 输出格式为可点击的URL链接

**注释框搜索的价值**：
- 💡 注释框通常包含字段的业务定义和计算公式
- 💡 注释框中的说明比字段名更容易理解
- 💡 可以快速找到业务规则和口径说明
- 💡 帮助理解复杂指标的计算逻辑

### 功能2：看板详情查看
- 看板包含的所有组件（表格、图表、筛选器等）
- 每个组件使用的数据模型
- 组件中的字段配置和别名映射
- 看板所属的报表信息
- **看板中的所有注释框内容**（新增）- 包含字段定义、计算公式、业务规则等重要说明

### 功能3：字段映射分析
- 原始字段名 → 用户看到的别名
- 字段在哪些看板、哪些组件中使用
- 字段的数据类型和角色（维度/度量）

### 功能4：业务场景推荐
基于业务关键词推荐相关看板：
- 客户分析：在服、流失、付费客户
- 销售业绩：回款、收入、业绩进展
- 行业分析：AIGC、游戏、国央企、广告素材
- 运营监控：客户等级、关键行为、折扣审批

## 技能参数

### 必需参数
- `action`: 操作类型
  - `search` - 搜索看板
  - `detail` - 查看看板详情
  - `field` - 字段映射查询
  - `recommend` - 业务场景推荐

### 可选参数
- `keyword`: 搜索关键词（用于search和field）
- `dashboard_id`: 看板ID（用于detail）
- `dashboard_title`: 看板标题（用于detail）
- `dashboard_url`: 看板URL（用于detail，自动提取dashboard_id）
- `scenario`: 业务场景（用于recommend）
- `json_file`: JSON配置文件路径（默认：workspace/Tasks/易盾BI/易盾BI全图_extracted/reportDepends.txt）

## 使用示例

### 示例1：搜索看板
```bash
/youshu-dashboard-explorer search 回款
```
输出：
```
🥈 看板标题匹配 (2个) - 高优先级

  📊 【总回款概览】
     报表: N/A
     🔗 https://smartwe.youdata.netease.com/dash/folder/450201343?rid=117348&did=244878

  📊 【回款】
     报表: N/A
     🔗 https://smartwe.youdata.netease.com/dash/folder/450201343?rid=117220&did=244465

🥉 组件标题匹配 (44个)
  📊 【关键行为】
     包含组件:
       • 首次回款时间 (dateTimeFilter)
     🔗 https://smartwe.youdata.netease.com/dash/folder/450201343?rid=117154&did=244218
```

### 示例2：搜索字段定义和计算公式（新增）
```bash
/youshu-dashboard-explorer search 试用
```
输出：
```
💬 注释框内容匹配 (6个) - 业务说明
   提示：注释框通常包含字段定义、计算公式、业务规则等重要说明

  📊 云商线上销售SOP看板-【销售过程总览】
     └─ 注释: 未命名注释框
        内容: 试用：当前仅包括七鱼智能客服的试用，暂时没有确定智能外呼的试用口径和数据
     └─ 注释: 未命名文本(2)
        内容: *线索试用率=试用数/线索数  （试用数 = 试用客户数+试用线索数）
*客户试用率=试用客户数/客户数
     🔗 https://smartwe.youdata.netease.com/dash/folder/450201343?rid=117228&did=244500
```

**💡 使用技巧**：
- 当搜索某个业务术语时，注释框匹配结果通常包含该术语的业务定义
- 注释框中的计算公式比字段配置更容易理解
- 可以快速了解指标的口径和业务规则

### 示例3：查看看板详情
```bash
/youshu-dashboard-explorer detail --dashboard_title="回款"
```
输出：
- 看板基本信息
- 包含的组件列表
- 使用的数据模型
- 字段配置详情
- **看板中的所有注释框内容**（包含业务说明）

### 示例4：字段映射查询
```bash
/youshu-dashboard-explorer field consume_amount
```
输出：
- 字段别名：今年净收入、去年净收入
- 使用该字段的看板和组件
- 字段的数据类型和角色

### 示例5：业务场景推荐
```bash
/youshu-dashboard-explorer recommend --scenario="客户流失分析"
```
输出：
- 推荐看板：【流失】、【在服】、【客户等级监控】
- 推荐理由和核心指标

### 示例6：通过URL查询看板
```bash
/youshu-dashboard-explorer detail --dashboard_url="https://smartwe.youdata.netease.com/dash/folder/450201343?rid=117336&did=244793"
```
或直接使用看板ID：
```bash
/youshu-dashboard-explorer detail --dashboard_id=244793
```
输出：
```
📊 看板: 【分日线索转化】

基本信息:
  - 看板ID: 244793
  - 看板标题: 分日线索转化
  - 所属报表: 未命名 (ID: 117336)
  - 🔗 https://smartwe.youdata.netease.com/dash/folder/450201343?rid=117336&did=244793

使用的数据模型 (1个):
  📋 易盾分日线索转化
     模型ID: 289363
     模型类型: NEW_REPORT_DATA_MODEL (报表级数据模型)
     关联基础模型: 102917 - 易盾分日线索转化
     使用次数: 4次
     使用组件:
       • 线索来源 (listFilter)
       • 日期 (dateTimeFilter)
       • 线索转化 (table)
       • pt_d (listFilter)

组件列表:
  1. [table] 线索转化
     数据模型: 易盾分日线索转化
     字段: 日期, 线索来源, 线索数, 有效线索, 转客户数
```

## 技术实现

### 数据结构理解

```
报表 (NEW_REPORT)
  ↓ reportId
看板 (NEW_DASHBOARD) ← 用户看到的"看板"
  ↓ dashboardId
组件 (NEW_COMPONENT) ← 看板上的图表、表格、筛选器等
  ↓ dataModelId
数据模型 (DATA_MODEL / NEW_REPORT_DATA_MODEL)
  ↓ config.tables.tableName
自定义表 (CUSTOM_TABLE) / Hive表
```

**重要发现：有数BI有两种数据模型**

1. **基础数据模型 (DATA_MODEL)**
   - 项目级别的通用数据模型
   - 可以被多个报表共享使用
   - 直接基于Hive表或自定义表创建

2. **报表级数据模型 (NEW_REPORT_DATA_MODEL)**
   - 基于基础数据模型的定制版本
   - 通过 `relatedDataModelId` 关联到基础模型
   - 可以添加报表特定的过滤、计算字段等
   - 组件的 `dataModelId` 通常指向这种模型

**数据流向**：
```
Hive表
  ↓
基础数据模型 (DATA_MODEL, id: 102917)
  ↓ relatedDataModelId
报表级数据模型 (NEW_REPORT_DATA_MODEL, id: 289363)
  ↓ dataModelId
组件 (Component)
```

### 关键发现

**字段别名存储在组件的column配置中**：
```json
NEW_COMPONENT {
  "setting": {
    "data": {
      "column": [
        {
          "field": "consume_amount_y",      // 原始字段名
          "alias": "今年净收入",             // 用户看到的别名！
          "fieldId": "xxx",
          "dataType": "Decimal",
          "role": "Measure"
        }
      ]
    }
  }
}
```

### 搜索策略

1. **直接搜索**：看板标题、数据模型名称
2. **字段级搜索**：遍历所有组件的column配置
3. **同义词扩展**：成本 → [consume, cost, 消耗, 费用]
4. **置信度评分**：根据匹配位置给出置信度

## 输出格式

### 搜索结果格式
```
🎯 搜索关键词: "回款"

✅ 看板标题匹配 (2个):
  • 【回款】(ID: 244465)
  • 【总回款概览】(ID: 244878)

✅ 数据模型匹配 (3个):
  • 易盾外部回款趋势 (ID: 103133)
  • 易盾回款明细数据-新 (ID: 102947)

✅ 字段别名匹配 (41个组件):
  📊 看板: 【回款】
     └─ 组件: 回款明细表
        • 回款金额 (字段: payamount)
        • 回款时间 (字段: remittime)
```

### 看板详情格式
```
📊 看板: 【回款】

基本信息:
  - 看板ID: 244465
  - 报表ID: 117220
  - 组件数量: 6个

使用的数据模型:
  1. 在服客户清单
  2. 易盾回款明细数据-新
  3. 易盾客户收入预测

组件列表:
  1. [table] 回款明细表
     - 数据模型: 易盾回款明细数据-新
     - 字段: 客户名称、回款金额、回款时间...

  2. [listFilter] 时间筛选器
     - 数据模型: 易盾回款明细数据-新
     - 字段: time_value
```

## 配置文件

技能依赖的配置文件：
- `reportDepends.txt` - 有数BI导出的JSON配置文件
- `keyword_mapping.json` - 关键词同义词映射表（可选）

## 注意事项

1. **JSON文件路径**：确保reportDepends.txt文件存在且路径正确
2. **字段别名**：字段别名存储在组件中，不在数据模型中
3. **同义词搜索**：成本相关字段可能显示为"净收入"、"消耗"等别名
4. **置信度理解**：高置信度结果更准确，低置信度结果需要人工确认
5. **数据模型类型**：组件可能使用基础数据模型(DATA_MODEL)或报表级数据模型(NEW_REPORT_DATA_MODEL)
6. **URL解析**：支持从有数BI的URL中自动提取dashboard_id进行查询
7. **注释框搜索**（新增）：注释框通常包含字段定义、计算公式、业务规则等重要说明，是理解复杂指标的关键信息源

## 扩展功能（未来）

- [ ] 支持多个业务线的看板体系（云商、七鱼、易盾）
- [ ] 看板使用频率统计
- [ ] 字段血缘关系追踪
- [ ] 看板依赖关系可视化
- [ ] 导出看板结构文档

## 维护说明

当有数BI看板更新时：
1. 重新导出reportDepends.txt文件
2. 更新keyword_mapping.json（如有新的业务术语）
3. 运行技能验证搜索结果准确性

---

**版本**: v1.3
**创建时间**: 2026-01-29
**最后更新**: 2026-02-05
**作者**: 阿辰 & Claude
**适用业务**: 易盾、云商、七鱼等有数BI看板体系

## 更新日志

### v1.3 (2026-02-05)
- ✅ 新增：注释框内容搜索功能，支持搜索看板中的业务说明、字段定义、计算公式
- ✅ 新增：`get_dashboard_comments()` 方法，获取指定看板的所有注释框内容
- ✅ 新增：`_get_comment_components()` 方法，获取所有注释类型的组件
- ✅ 新增：`_extract_comment_text()` 方法，从HTML格式的注释框中提取纯文本
- ✅ 优化：搜索优先级调整，注释框内容匹配位于第4优先级（中高优先级）
- ✅ 文档：新增注释框搜索的使用场景和示例
- 💡 **重要经验**：当需要了解字段的计算逻辑时，注释框中的信息往往比字段配置更有价值

### v1.2 (2026-02-02)
- ✅ 新增：显示数据模型层级关系（报表级模型ID + 基础模型ID）
- ✅ 新增：format_model_info函数，统一格式化模型信息
- ✅ 优化：搜索结果中显示relatedDataModelId（如果存在）

### v1.1 (2026-02-02)
- ✅ 新增：支持通过URL直接查询看板详情
- ✅ 修复：正确加载 NEW_REPORT_DATA_MODEL（报表级数据模型）
- ✅ 优化：完善数据模型层级关系说明
- ✅ 文档：新增数据模型类型说明和数据流向图

### v1.0 (2026-01-29)
- 初始版本发布
- 支持看板搜索、详情查看、字段映射、业务场景推荐
