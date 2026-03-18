#!/usr/bin/env python3
"""
猛犸平台数据表探索器 - API客户端
支持表结构查询、血缘分析、分区查看等功能

认证方式: AK/SK + MD5签名
时间戳格式: 毫秒级 (13位数字)
签名算法: MD5(secret_key + timestamp)
"""

import hashlib
import json
import time
import socket
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests


class MammothClientError(Exception):
    """猛犸客户端异常"""
    pass


class NetworkError(MammothClientError):
    """网络连接异常"""
    pass


class AuthError(MammothClientError):
    """认证异常"""
    pass


class MammothTableExplorer:
    """猛犸数据表探索器"""

    def __init__(self, config_path: str = None):
        """
        初始化客户端

        Args:
            config_path: 配置文件路径，默认为同级目录的 config.json
        """
        if config_path is None:
            config_path = str(Path(__file__).parent / "config.json")

        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MammothTableExplorer/1.0',
            'Accept': 'application/json'
        })

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 验证必要字段
            required_fields = ['base_url', 'access_key', 'secret_key', 'user']
            missing = [f for f in required_fields if not config.get(f)]
            if missing:
                raise AuthError(f"配置文件缺少必要字段: {', '.join(missing)}")

            return config
        except FileNotFoundError:
            raise AuthError(
                f"配置文件不存在: {config_path}\n"
                f"请复制 config.example.json 为 config.json 并填入认证信息"
            )
        except json.JSONDecodeError as e:
            raise AuthError(f"配置文件格式错误: {e}")

    def check_network(self) -> bool:
        """
        检查网络连通性

        Returns:
            True: 网络连通
            False: 网络不通
        """
        try:
            parsed_url = urlparse(self.config['base_url'])
            hostname = parsed_url.hostname
            port = parsed_url.port or 80

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((hostname, port))
            sock.close()

            return result == 0
        except Exception:
            return False

    def ensure_network(self):
        """确保网络连接就绪，否则抛出异常"""
        if not self.check_network():
            raise NetworkError(f"""
❌ 网络连接失败！

无法连接到猛犸API服务器: {self.config['base_url']}

可能原因：
1. 未连接VPN - 猛犸API需要通过内网访问
2. 网络不稳定 - 请检查网络连接
3. API服务器维护中

解决方案：
1. 请先连接公司VPN
2. 确认网络连接正常
3. 如果问题持续，请联系管理员
""")

    def _generate_sig(self, timestamp: int) -> str:
        """生成MD5签名"""
        sign_str = f"{self.config['secret_key']}{timestamp}"
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    def _build_auth_params(self) -> dict:
        """构建认证参数"""
        timestamp = int(time.time() * 1000)
        return {
            "authType": "AKSK",
            "timestamp": timestamp,
            "accessKey": self.config["access_key"],
            "sig": self._generate_sig(timestamp),
            "product": self.config.get("product", "smart_ep"),
            "user": self.config["user"]
        }

    def _call_api(self, endpoint: str, params: dict = None) -> Dict:
        """
        调用API

        Args:
            endpoint: API端点
            params: 业务参数

        Returns:
            API响应结果
        """
        self.ensure_network()

        all_params = self._build_auth_params()
        if params:
            all_params.update(params)

        url = f"{self.config['base_url']}/openapi/easymetahub/{endpoint}"

        try:
            response = self.session.get(url, params=all_params, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "code": -1,
                    "msg": f"HTTP错误: {response.status_code}"
                }
        except requests.Timeout:
            return {"code": -1, "msg": "请求超时"}
        except requests.RequestException as e:
            return {"code": -1, "msg": f"请求异常: {str(e)}"}

    # ==================== 表结构相关 ====================

    def get_table_info(self, db: str, table: str) -> Dict:
        """
        获取表详情

        Args:
            db: 数据库名
            table: 表名

        Returns:
            表的完整信息，包括字段列表、注释等
        """
        return self._call_api("table/v1/get", {
            "datasourceId": self.config.get("datasource_id", 832),
            "db": db,
            "table": table
        })

    def list_tables(self, db: str, page_size: int = 50, page_num: int = 1) -> Dict:
        """
        获取数据库中的表列表

        Args:
            db: 数据库名
            page_size: 每页数量
            page_num: 页码
        """
        return self._call_api("table/v1/list", {
            "datasourceId": self.config.get("datasource_id", 832),
            "db": db,
            "pageSize": page_size,
            "pageNum": page_num
        })

    # ==================== 血缘相关 ====================

    def get_field_lineage(
        self,
        db: str,
        table: str,
        field_name: str,
        direction: str = "up",
        page_size: int = 10
    ) -> Dict:
        """
        获取字段血缘

        Args:
            db: 数据库名
            table: 表名
            field_name: 字段名
            direction: up(上游) / down(下游)
            page_size: 返回数量
        """
        return self._call_api("lineage/v1/field/get", {
            "datasourceId": self.config.get("datasource_id", 832),
            "db": db,
            "table": table,
            "fieldName": field_name,
            "direction": direction,
            "pageSize": page_size
        })

    def get_table_lineage(
        self,
        db: str,
        table: str,
        direction: str = "up",
        page_size: int = 10
    ) -> Dict:
        """
        获取表血缘

        Args:
            db: 数据库名
            table: 表名
            direction: up(上游) / down(下游)
            page_size: 返回数量
        """
        return self._call_api("lineage/v1/table/get", {
            "datasourceId": self.config.get("datasource_id", 832),
            "db": db,
            "table": table,
            "direction": direction,
            "pageSize": page_size
        })

    # ==================== 分区相关 ====================

    def list_partitions(self, db: str, table: str) -> Dict:
        """
        获取表分区列表

        Args:
            db: 数据库名
            table: 表名
        """
        catalog = self.config.get("catalog_name", "hz8-hive-catalog")
        return self._call_api("table/v1/partition/list", {
            "datasourceId": self.config.get("datasource_id", 832),
            "catalog": catalog,
            "db": db,
            "table": table
        })

    def get_latest_partition(self, db: str, table: str) -> Optional[str]:
        """
        获取最新分区名

        Args:
            db: 数据库名
            table: 表名

        Returns:
            最新分区名，如 "pt_d=2026-03-13"
        """
        result = self.list_partitions(db, table)
        if result.get("code") == 0 and result.get("result"):
            partitions = result["result"]
            if isinstance(partitions, list) and partitions:
                return partitions[0].get("partition")
        return None

    # ==================== 格式化输出 ====================

    @staticmethod
    def format_table_info(result: Dict) -> str:
        """格式化表信息输出"""
        if result.get("code") != 0:
            return f"❌ 查询失败: {result.get('msg', '未知错误')}"

        info = result.get("result", {})
        lines = []
        lines.append("=" * 80)
        lines.append(f"表名: {info.get('table', 'N/A')}")
        lines.append(f"注释: {info.get('comment', 'N/A')}")
        lines.append(f"所有者: {info.get('owner', 'N/A')}")
        lines.append(f"创建时间: {info.get('createdTime', 'N/A')}")
        lines.append("=" * 80)

        fields = info.get("fields", [])
        columns = [f for f in fields if not f.get("partitionKey", False)]
        partitions = [f for f in fields if f.get("partitionKey", False)]

        if columns:
            lines.append(f"\n{'列名':<30} {'类型':<20} {'注释'}")
            lines.append("-" * 80)
            for col in columns:
                name = col.get("fieldName", "")
                col_type = col.get("fieldType", "")
                comment = col.get("comment", "")
                lines.append(f"{name:<30} {col_type:<20} {comment}")

        if partitions:
            lines.append("\n" + "=" * 80)
            lines.append("分区字段:")
            lines.append("-" * 80)
            for part in partitions:
                name = part.get("fieldName", "")
                col_type = part.get("fieldType", "")
                lines.append(f"{name:<30} {col_type:<20}")

        lines.append("=" * 80)
        lines.append(f"共 {len(columns)} 列" + (f", {len(partitions)} 个分区字段" if partitions else ""))

        return "\n".join(lines)

    @staticmethod
    def format_lineage(result: Dict, direction: str = "up") -> str:
        """格式化血缘输出"""
        if result.get("code") != 0:
            return f"❌ 查询失败: {result.get('msg', '未知错误')}"

        info = result.get("result", {})
        lines = []

        if direction == "up":
            items = info.get("parentList", {}).get("list", [])
            title = "上游血缘"
        else:
            items = info.get("childList", {}).get("list", [])
            title = "下游血缘"

        total = info.get("parentList" if direction == "up" else "childList", {}).get("totalCount", 0)

        lines.append(f"{'='*60}")
        lines.append(f"{title}: 共 {total} 个")
        lines.append(f"{'='*60}")

        for item in items:
            db = item.get("db", "")
            table = item.get("table", "")
            field = item.get("fieldName", "")
            relation = item.get("fieldRelation", "")

            if field:
                lines.append(f"  {db}.{table}.{field} ({relation})")
            else:
                lines.append(f"  {db}.{table}")

        lines.append(f"{'='*60}")
        return "\n".join(lines)

    @staticmethod
    def format_partitions(result: Dict, limit: int = 10) -> str:
        """格式化分区输出"""
        if result.get("code") != 0:
            return f"❌ 查询失败: {result.get('msg', '未知错误')}"

        partitions = result.get("result", [])

        if not partitions:
            return "ℹ️ 该表没有分区（非分区表）"

        lines = []
        lines.append(f"{'='*60}")
        lines.append(f"分区列表: 共 {len(partitions)} 个分区")
        lines.append(f"{'='*60}")

        for i, part in enumerate(partitions[:limit]):
            partition = part.get("partition", "")
            create_time = part.get("createTime", "")
            num_rows = part.get("metadata", {}).get("numRows", "N/A")
            size = part.get("metadata", {}).get("totalSize", "N/A")

            lines.append(f"  {partition}")
            lines.append(f"    创建时间: {create_time} | 行数: {num_rows} | 大小: {size} bytes")

        if len(partitions) > limit:
            lines.append(f"  ... 还有 {len(partitions) - limit} 个分区未显示")

        lines.append(f"{'='*60}")
        return "\n".join(lines)

    @staticmethod
    def to_json(data: dict) -> str:
        """转换为JSON字符串"""
        return json.dumps(data, indent=2, ensure_ascii=False)


# ==================== 命令行入口 ====================

def main():
    """命令行入口"""
    import sys

    if len(sys.argv) < 2:
        print("""
猛犸数据表探索器 v1.0

用法:
    python mammoth_client.py <命令> [参数...]

命令:
    get_table <数据库> <表名>              # 获取表结构
    field_lineage <库> <表> <字段> <up|down>  # 字段血缘
    table_lineage <库> <表> <up|down>         # 表血缘
    partitions <数据库> <表名>              # 分区列表
    list_tables <数据库>                   # 表列表

示例:
    python mammoth_client.py get_table yidun_dw dws_yidun_cst_service_income_dd
    python mammoth_client.py field_lineage yidun_dw dws_table total_income up
    python mammoth_client.py partitions yidun_dw dws_table
        """)
        sys.exit(1)

    try:
        client = MammothTableExplorer()
        command = sys.argv[1]

        if command == "get_table":
            if len(sys.argv) < 4:
                print("用法: get_table <数据库> <表名>")
                sys.exit(1)
            result = client.get_table_info(sys.argv[2], sys.argv[3])
            print(client.format_table_info(result))

        elif command == "field_lineage":
            if len(sys.argv) < 6:
                print("用法: field_lineage <数据库> <表名> <字段名> <up|down>")
                sys.exit(1)
            result = client.get_field_lineage(
                sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
            )
            print(client.format_lineage(result, sys.argv[5]))

        elif command == "table_lineage":
            if len(sys.argv) < 5:
                print("用法: table_lineage <数据库> <表名> <up|down>")
                sys.exit(1)
            result = client.get_table_lineage(
                sys.argv[2], sys.argv[3], sys.argv[4]
            )
            print(client.format_lineage(result, sys.argv[4]))

        elif command == "partitions":
            if len(sys.argv) < 4:
                print("用法: partitions <数据库> <表名>")
                sys.exit(1)
            result = client.list_partitions(sys.argv[2], sys.argv[3])
            print(client.format_partitions(result))

        elif command == "list_tables":
            if len(sys.argv) < 3:
                print("用法: list_tables <数据库>")
                sys.exit(1)
            result = client.list_tables(sys.argv[2])
            print(client.to_json(result))

        else:
            print(f"未知命令: {command}")
            sys.exit(1)

    except NetworkError as e:
        print(str(e))
        sys.exit(1)
    except AuthError as e:
        print(f"❌ 认证错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
