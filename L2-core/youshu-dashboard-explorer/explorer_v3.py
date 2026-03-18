import json
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    """HTML文本提取器，用于从HTML标签中提取纯文本"""
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return ''.join(self.text).strip()


class YoushuDashboardExplorerV3:
    """有数BI看板探索器 V3 - 优化搜索策略和输出格式"""

    def __init__(self, json_file_path: str, excel_file_path: Optional[str] = None):
        """
        初始化探索器

        Args:
            json_file_path: reportDepends.txt文件路径
            excel_file_path: Excel数据文件路径（可选，用于搜索数据值）
        """
        self.json_file_path = json_file_path
        self.excel_file_path = excel_file_path
        self.data = None
        self.dashboards = {}
        self.data_models = {}
        self.reports = {}
        self.components = []
        self.data_value_index = {}

        # 有数BI的URL模板
        self.youshu_url_template = "https://smartwe.youdata.netease.com/dash/folder/450201343?rid={report_id}&did={dashboard_id}"

        # 关键词同义词映射
        self.keyword_mapping = {
            '成本': ['consume', 'cost', 'cor_cost', '消耗', '费用', '净收入'],
            '回款': ['payamount', 'payment', 'remit', '收款'],
            '收入': ['income', 'revenue', 'arr', 'mrr', 'net_income'],
            '在服': ['is_using', 'service', 'cur_status'],
            '客户': ['customer', 'cid', 'clouduserid', 'corpname'],
            '流失': ['loss', 'churn', 'lost'],
            '新客': ['new_customer', 'new_cnt', 'fst_remittime'],
        }

        # 维度字段关键词
        self.dimension_keywords = ['index', 'type', 'category', 'name', 'label',
                                  '指标', '类型', '分类', '名称', '标签']

        self._load_data()
        if excel_file_path:
            self._build_data_value_index()

    def _load_data(self):
        """加载JSON数据"""
        with open(self.json_file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        export_map = self.data.get('exportObjectMap', {})

        # 构建索引
        self.dashboards = {d['id']: d for d in export_map.get('NEW_DASHBOARD', [])}

        # 数据模型索引：包含基础数据模型(DATA_MODEL)和报表级数据模型(NEW_REPORT_DATA_MODEL)
        self.data_models = {m['id']: m for m in export_map.get('DATA_MODEL', [])}
        # 报表级数据模型也加入索引（这些模型基于基础模型定制）
        for m in export_map.get('NEW_REPORT_DATA_MODEL', []):
            self.data_models[m['id']] = m

        self.reports = {r['id']: r for r in export_map.get('NEW_REPORT', [])}
        self.components = export_map.get('NEW_COMPONENT', [])

    def _build_data_value_index(self):
        """构建数据值索引（从Excel文件）"""
        if not self.excel_file_path or not Path(self.excel_file_path).exists():
            return

        try:
            excel_file = pd.ExcelFile(self.excel_file_path)

            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(self.excel_file_path, sheet_name=sheet_name)

                    for col in df.columns:
                        col_lower = str(col).lower()

                        if any(kw in col_lower for kw in self.dimension_keywords):
                            unique_values = df[col].dropna().unique()

                            for value in unique_values:
                                value_str = str(value)
                                if value_str not in self.data_value_index:
                                    self.data_value_index[value_str] = []

                                self.data_value_index[value_str].append({
                                    'sheet': sheet_name,
                                    'field': col,
                                    'value': value_str
                                })
                except Exception:
                    continue

        except Exception as e:
            print(f"⚠️  无法构建数据值索引: {e}")

    def search(self, keyword: str) -> Dict[str, List[Any]]:
        """
        智能搜索看板（V3版本）

        搜索优先级（按层级关系）：
        1. 报表名称
        2. 看板标题
        3. 组件标题
        4. 注释框内容（新增）
        5. 数据模型名称
        6. 字段别名
        7. 字段名
        8. 维度字段（可能包含数据值）

        Args:
            keyword: 搜索关键词

        Returns:
            搜索结果字典，按优先级排序
        """
        results = {
            'by_report_name': [],       # 优先级1: 报表名称
            'by_dashboard_title': [],   # 优先级2: 看板标题
            'by_component_title': [],   # 优先级3: 组件标题
            'by_comment_content': [],   # 优先级4: 注释框内容（新增）
            'by_model_name': [],        # 优先级5: 数据模型名称
            'by_field_alias': [],       # 优先级6: 字段别名
            'by_field_name': [],        # 优先级7: 字段名
            'by_dimension_field': [],   # 优先级8: 维度字段
            'by_data_value': []         # 优先级9: 数据值
        }

        keywords = self.expand_keywords(keyword)

        # 优先级1: 搜索报表名称
        for report in self.reports.values():
            name = report.get('name', '')
            if any(kw.lower() in name.lower() for kw in keywords):
                # 找到使用该报表的所有看板
                report_dashboards = [d for d in self.dashboards.values()
                                    if d.get('reportId') == report['id']]

                for dashboard in report_dashboards:
                    results['by_report_name'].append({
                        'report': report,
                        'dashboard': dashboard,
                        'confidence': 'very_high',
                        'priority': 1,
                        'match_keyword': keyword,
                        'url': self._generate_url(report['id'], dashboard['id'])
                    })

        # 优先级2: 搜索看板标题
        for dashboard in self.dashboards.values():
            title = dashboard.get('title', '')
            if any(kw.lower() in title.lower() for kw in keywords):
                report_id = dashboard.get('reportId')
                report = self.reports.get(report_id)

                results['by_dashboard_title'].append({
                    'report': report,
                    'dashboard': dashboard,
                    'confidence': 'high',
                    'priority': 2,
                    'match_keyword': keyword,
                    'url': self._generate_url(report_id, dashboard['id'])
                })

        # 优先级3: 搜索组件标题（仅搜索可见组件）
        visible_components = self._get_visible_components()

        for comp in visible_components:
            comp_title = comp.get('title', '')
            if any(kw.lower() in comp_title.lower() for kw in keywords):
                dashboard_id = comp.get('dashboardId')
                dashboard = self.dashboards.get(dashboard_id)
                report_id = dashboard.get('reportId') if dashboard else None
                report = self.reports.get(report_id) if report_id else None

                results['by_component_title'].append({
                    'report': report,
                    'dashboard': dashboard,
                    'component': comp,
                    'confidence': 'high',
                    'priority': 3,
                    'match_keyword': keyword,
                    'url': self._generate_url(report_id, dashboard_id)
                })

        # 优先级4: 搜索注释框内容（新增）
        comment_components = self._get_comment_components()

        for comp in comment_components:
            comment_text = self._extract_comment_text(comp)
            if comment_text and any(kw.lower() in comment_text.lower() for kw in keywords):
                dashboard_id = comp.get('dashboardId')
                dashboard = self.dashboards.get(dashboard_id)
                report_id = dashboard.get('reportId') if dashboard else None
                report = self.reports.get(report_id) if report_id else None

                results['by_comment_content'].append({
                    'report': report,
                    'dashboard': dashboard,
                    'component': comp,
                    'comment_text': comment_text,
                    'confidence': 'high',
                    'priority': 4,
                    'match_keyword': keyword,
                    'url': self._generate_url(report_id, dashboard_id)
                })

        # 优先级5: 搜索数据模型名称
        for model in self.data_models.values():
            name = model.get('name', '')
            if any(kw.lower() in name.lower() for kw in keywords):
                # 找到使用该模型的组件
                model_components = [c for c in visible_components
                                   if c.get('dataModelId') == model['id']]

                # 按看板分组
                dashboards_using_model = {}
                for comp in model_components:
                    dashboard_id = comp.get('dashboardId')
                    if dashboard_id not in dashboards_using_model:
                        dashboards_using_model[dashboard_id] = []
                    dashboards_using_model[dashboard_id].append(comp)

                for dashboard_id, comps in dashboards_using_model.items():
                    dashboard = self.dashboards.get(dashboard_id)
                    report_id = dashboard.get('reportId') if dashboard else None
                    report = self.reports.get(report_id) if report_id else None

                    results['by_model_name'].append({
                        'report': report,
                        'dashboard': dashboard,
                        'model': model,
                        'components': comps,
                        'confidence': 'medium',
                        'priority': 4,
                        'match_keyword': keyword,
                        'url': self._generate_url(report_id, dashboard_id)
                    })

        # 优先级5-7: 搜索字段（仅在可见组件中）
        for comp in visible_components:
            setting = comp.get('setting', {})
            data_config = setting.get('data', {})

            # 检查所有字段配置
            all_fields = []
            all_fields.extend(data_config.get('column', []))
            all_fields.extend(data_config.get('row', []))
            all_fields.extend(data_config.get('measures', []))

            matched_fields = self._search_in_fields(all_fields, keywords)
            dimension_fields = self._find_dimension_fields(comp, keywords)

            if matched_fields or dimension_fields:
                dashboard_id = comp.get('dashboardId')
                dashboard = self.dashboards.get(dashboard_id)
                report_id = dashboard.get('reportId') if dashboard else None
                report = self.reports.get(report_id) if report_id else None
                model_id = comp.get('dataModelId')
                model = self.data_models.get(model_id)

                result_entry = {
                    'report': report,
                    'dashboard': dashboard,
                    'component': comp,
                    'model': model,
                    'fields': matched_fields,
                    'dimension_fields': dimension_fields,
                    'url': self._generate_url(report_id, dashboard_id)
                }

                # 根据匹配类型分类
                if matched_fields:
                    if any(f['match_in_alias'] for f in matched_fields):
                        result_entry['confidence'] = 'medium'
                        result_entry['priority'] = 5
                        results['by_field_alias'].append(result_entry)
                    else:
                        result_entry['confidence'] = 'low'
                        result_entry['priority'] = 6
                        results['by_field_name'].append(result_entry)

                if dimension_fields:
                    result_entry['confidence'] = 'low'
                    result_entry['priority'] = 7
                    result_entry['hint'] = f'该组件包含维度字段，"{keyword}"可能是其数据值'
                    results['by_dimension_field'].append(result_entry)

        # 优先级8: 搜索数据值
        if self.data_value_index:
            for kw in keywords:
                if kw in self.data_value_index:
                    results['by_data_value'].extend(self.data_value_index[kw])

        return results

    def _get_visible_components(self) -> List[Dict]:
        """
        获取可见的组件

        过滤规则：
        - 排除comment类型（注释）
        - 排除rect类型（矩形容器）
        - 排除没有标题的组件
        """
        visible_types = ['table', 'crossTable', 'auto', 'line', 'meter',
                        'funnel', 'indicatorPanel', 'listFilter',
                        'dateTimeFilter', 'textQueryField', 'tab']

        visible_components = []
        for comp in self.components:
            comp_type = comp.get('type')
            comp_title = comp.get('title', '').strip()

            # 过滤条件
            if comp_type in visible_types and comp_title:
                # 排除"未命名"的组件
                if not comp_title.startswith('未命名'):
                    visible_components.append(comp)

        return visible_components

    def _get_comment_components(self) -> List[Dict]:
        """
        获取注释框组件

        返回所有注释类型的组件，包括：
        - comment: 注释框
        - text: 文本框
        - newText: 新版文本框
        - richText: 富文本框
        - markdown: Markdown文本框
        """
        comment_types = ['comment', 'text', 'newText', 'richText', 'markdown']

        comment_components = []
        for comp in self.components:
            comp_type = comp.get('type', '')
            if comp_type in comment_types:
                comment_components.append(comp)

        return comment_components

    def _extract_comment_text(self, component: Dict) -> str:
        """
        从注释框组件中提取纯文本内容

        Args:
            component: 组件对象

        Returns:
            提取的纯文本内容
        """
        setting = component.get('setting', {})

        # 尝试不同的文本存储位置
        text_content = None

        if 'text' in setting:
            text_content = setting.get('text')
        elif 'content' in setting:
            text_content = setting.get('content')
        elif 'data' in setting:
            data = setting.get('data', {})
            if 'text' in data:
                text_content = data.get('text')
            elif 'content' in data:
                text_content = data.get('content')

        if not text_content:
            return ""

        # 如果是HTML格式，提取纯文本
        if '<' in text_content and '>' in text_content:
            try:
                parser = HTMLTextExtractor()
                parser.feed(text_content)
                return parser.get_text()
            except Exception:
                # 如果HTML解析失败，使用正则表达式简单清理
                return re.sub(r'<[^>]+>', '', text_content).strip()

        return text_content.strip()

    def get_dashboard_comments(self, dashboard_id: int) -> List[Dict]:
        """
        获取指定看板的所有注释框内容

        Args:
            dashboard_id: 看板ID

        Returns:
            注释框列表，每个元素包含 {title, type, text}
        """
        comment_components = self._get_comment_components()
        dashboard_comments = []

        for comp in comment_components:
            if comp.get('dashboardId') == dashboard_id:
                comment_text = self._extract_comment_text(comp)
                if comment_text:
                    dashboard_comments.append({
                        'title': comp.get('title', '未命名'),
                        'type': comp.get('type', 'unknown'),
                        'text': comment_text,
                        'component_id': comp.get('id')
                    })

        return dashboard_comments

    def _generate_url(self, report_id: Optional[int], dashboard_id: Optional[int]) -> str:
        """生成有数BI看板URL"""
        if report_id and dashboard_id:
            return self.youshu_url_template.format(
                report_id=report_id,
                dashboard_id=dashboard_id
            )
        return ""

    def _search_in_fields(self, fields: List[Dict], keywords: List[str]) -> List[Dict]:
        """在字段列表中搜索关键词"""
        matched_fields = []

        for field in fields:
            alias = field.get('alias', '').lower()
            field_name = field.get('field', '').lower()

            match_in_alias = any(kw.lower() in alias for kw in keywords)
            match_in_field = any(kw.lower() in field_name for kw in keywords)

            if match_in_alias or match_in_field:
                matched_fields.append({
                    'field': field.get('field'),
                    'alias': field.get('alias'),
                    'dataType': field.get('dataType'),
                    'role': field.get('role'),
                    'match_in_alias': match_in_alias,
                    'match_in_field': match_in_field
                })

        return matched_fields

    def _find_dimension_fields(self, component: Dict, keywords: List[str]) -> List[Dict]:
        """查找可能包含搜索值的维度字段"""
        dimension_fields = []

        setting = component.get('setting', {})
        data_config = setting.get('data', {})

        all_fields = []
        all_fields.extend(data_config.get('column', []))
        all_fields.extend(data_config.get('row', []))

        for field in all_fields:
            field_name = field.get('field', '').lower()
            alias = field.get('alias', '').lower()

            if any(kw in field_name or kw in alias for kw in self.dimension_keywords):
                dimension_fields.append({
                    'field': field.get('field'),
                    'alias': field.get('alias'),
                    'role': field.get('role', 'Dimension')
                })

        return dimension_fields

    def expand_keywords(self, keyword: str) -> List[str]:
        """扩展关键词为同义词列表"""
        keywords = [keyword]
        for key, synonyms in self.keyword_mapping.items():
            if keyword in key or keyword in synonyms:
                keywords.extend([key] + synonyms)
        return list(set(keywords))


def format_model_info(model: Dict, data_models: Dict) -> str:
    """
    格式化数据模型信息

    Args:
        model: 数据模型对象
        data_models: 所有数据模型的字典（用于查找关联的基础模型）

    Returns:
        格式化的模型信息字符串
    """
    if not model:
        return "N/A"

    model_name = model.get('name', 'N/A')
    model_id = model.get('id')
    model_type = model.get('type', 'N/A')
    related_model_id = model.get('relatedDataModelId')

    output = [f"{model_name} (ID: {model_id})"]
    output.append(f"       类型: {model_type}")

    if related_model_id:
        related_model = data_models.get(related_model_id)
        if related_model:
            output.append(f"       基础模型: {related_model.get('name', 'N/A')} (ID: {related_model_id})")
        else:
            output.append(f"       基础模型ID: {related_model_id}")

    return "\n       ".join(output)


def format_search_results_v3(results: Dict, keyword: str) -> str:
    """格式化搜索结果（V3版本 - 按优先级排序）"""
    output = []
    output.append("=" * 80)
    output.append(f"🎯 搜索关键词: '{keyword}'")
    output.append("=" * 80)
    output.append("")

    # 统计总结果数
    total_results = sum(len(v) for k, v in results.items() if k != 'by_data_value')

    if total_results == 0:
        output.append("❌ 未找到匹配结果")
        output.append("")
        output.append("💡 建议:")
        output.append("  - 尝试使用同义词（如：成本 → 消耗、费用）")
        output.append("  - 使用更通用的关键词")
        output.append("  - 查看所有可用看板列表")
        return "\n".join(output)

    output.append(f"✅ 找到 {total_results} 个相关结果（按优先级排序）")
    output.append("")

    # 优先级1: 报表名称匹配
    if results['by_report_name']:
        output.append(f"🥇 报表名称匹配 ({len(results['by_report_name'])}个) - 最高优先级")
        output.append("")

        # 去重（同一个看板只显示一次）
        seen_dashboards = set()
        for item in results['by_report_name']:
            dashboard_id = item['dashboard']['id']
            if dashboard_id not in seen_dashboards:
                seen_dashboards.add(dashboard_id)
                report_title = item['report'].get('title', 'N/A')
                dashboard_title = item['dashboard']['title']
                url = item['url']

                output.append(f"  📊 {report_title}-【{dashboard_title}】")
                output.append(f"     🔗 {url}")
                output.append("")

    # 优先级2: 看板标题匹配
    if results['by_dashboard_title']:
        output.append(f"🥈 看板标题匹配 ({len(results['by_dashboard_title'])}个) - 高优先级")
        output.append("")

        for item in results['by_dashboard_title'][:5]:
            dashboard_title = item['dashboard']['title']
            report_title = item['report'].get('title', 'N/A') if item['report'] else 'N/A'
            url = item['url']

            output.append(f"  📊 {report_title}-【{dashboard_title}】")
            output.append(f"     🔗 {url}")
            output.append("")

    # 优先级3: 组件标题匹配
    if results['by_component_title']:
        output.append(f"🥉 组件标题匹配 ({len(results['by_component_title'])}个)")
        output.append("")

        # 按看板分组
        by_dashboard = defaultdict(list)
        for item in results['by_component_title']:
            dashboard_title = item['dashboard']['title'] if item['dashboard'] else 'N/A'
            by_dashboard[dashboard_title].append(item)

        for dashboard_title, items in list(by_dashboard.items())[:3]:
            first_item = items[0]
            report_title = first_item['report'].get('title', 'N/A') if first_item['report'] else 'N/A'
            url = first_item['url']

            output.append(f"  📊 {report_title}-【{dashboard_title}】")
            output.append(f"     包含组件:")
            for item in items[:3]:
                comp_title = item['component']['title']
                comp_type = item['component']['type']
                output.append(f"       • {comp_title} ({comp_type})")
            output.append(f"     🔗 {url}")
            output.append("")

    # 优先级4: 注释框内容匹配（新增）
    if results['by_comment_content']:
        output.append(f"💬 注释框内容匹配 ({len(results['by_comment_content'])}个) - 业务说明")
        output.append("   提示：注释框通常包含字段定义、计算公式、业务规则等重要说明")
        output.append("")

        # 按看板分组
        by_dashboard = defaultdict(list)
        for item in results['by_comment_content']:
            dashboard_title = item['dashboard']['title'] if item['dashboard'] else 'N/A'
            by_dashboard[dashboard_title].append(item)

        for dashboard_title, items in list(by_dashboard.items())[:3]:
            first_item = items[0]
            report_title = first_item['report'].get('title', 'N/A') if first_item['report'] else 'N/A'
            url = first_item['url']

            output.append(f"  📊 {report_title}-【{dashboard_title}】")
            for item in items[:2]:  # 每个看板最多显示2个注释框
                comp_title = item['component'].get('title', '未命名')
                comment_text = item['comment_text']
                # 截取注释内容，最多显示150个字符
                if len(comment_text) > 150:
                    comment_text = comment_text[:150] + '...'
                output.append(f"     └─ 注释: {comp_title}")
                output.append(f"        内容: {comment_text}")
            output.append(f"     🔗 {url}")
            output.append("")

    # 优先级5: 数据模型名称匹配
    if results['by_model_name']:
        output.append(f"📋 数据模型匹配 ({len(results['by_model_name'])}个)")
        output.append("")

        for item in results['by_model_name'][:3]:
            dashboard_title = item['dashboard']['title'] if item['dashboard'] else 'N/A'
            report_title = item['report'].get('title', 'N/A') if item['report'] else 'N/A'
            model = item['model']
            model_name = model['name']
            model_id = model['id']
            related_model_id = model.get('relatedDataModelId')
            url = item['url']

            output.append(f"  📊 {report_title}-【{dashboard_title}】")
            output.append(f"     数据模型: {model_name}")
            output.append(f"     模型ID: {model_id}")
            if related_model_id:
                output.append(f"     基础模型ID: {related_model_id}")
            output.append(f"     🔗 {url}")
            output.append("")

    # 优先级6: 字段别名匹配
    if results['by_field_alias']:
        output.append(f"🔍 字段别名匹配 ({len(results['by_field_alias'])}个组件)")
        output.append("")

        by_dashboard = defaultdict(list)
        for item in results['by_field_alias']:
            dashboard_title = item['dashboard']['title'] if item['dashboard'] else 'N/A'
            by_dashboard[dashboard_title].append(item)

        for dashboard_title, items in list(by_dashboard.items())[:3]:
            first_item = items[0]
            report_title = first_item['report'].get('title', 'N/A') if first_item['report'] else 'N/A'
            url = first_item['url']

            output.append(f"  📊 {report_title}-【{dashboard_title}】")
            for item in items[:2]:
                comp_title = item['component']['title']
                comp_type = item['component']['type']
                output.append(f"     └─ 组件: {comp_title} ({comp_type})")
                for field in item['fields'][:3]:
                    output.append(f"        • {field['alias']} (字段: {field['field']})")
            output.append(f"     🔗 {url}")
            output.append("")

    # 优先级7: 维度字段提示
    if results['by_dimension_field']:
        output.append(f"💡 可能包含该值的维度字段 ({len(results['by_dimension_field'])}个组件)")
        output.append(f"   提示：'{keyword}'可能是维度字段的数据值，而不是字段别名")
        output.append("")

        by_dashboard = defaultdict(list)
        for item in results['by_dimension_field']:
            dashboard_title = item['dashboard']['title'] if item['dashboard'] else 'N/A'
            by_dashboard[dashboard_title].append(item)

        for dashboard_title, items in list(by_dashboard.items())[:2]:
            first_item = items[0]
            report_title = first_item['report'].get('title', 'N/A') if first_item['report'] else 'N/A'
            url = first_item['url']

            output.append(f"  📊 {report_title}-【{dashboard_title}】")
            for item in items[:1]:
                comp_title = item['component']['title']
                output.append(f"     └─ 组件: {comp_title}")
                output.append(f"        维度字段: {', '.join([f['alias'] for f in item['dimension_fields'][:3]])}")
            output.append(f"     🔗 {url}")
            output.append("")

    return "\n".join(output)
