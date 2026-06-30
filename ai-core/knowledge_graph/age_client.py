"""
Apache AGE 知识图谱客户端
Cypher 查询封装
"""
from typing import Any
import psycopg2
import psycopg2.extras
from config.settings import settings


class AGEClient:
    """AGE 图数据库客户端"""

    def __init__(self):
        self._conn = None
        self._graph = settings.PG_GRAPH_NAME

    @property
    def conn(self):
        if self._conn is None:
            self._conn = psycopg2.connect(
                host=settings.PG_HOST,
                port=settings.PG_PORT,
                dbname=settings.PG_DB,
                user=settings.PG_USER,
                password=settings.PG_PASSWORD,
            )
            self._conn.autocommit = True
            cur = self._conn.cursor()
            cur.execute("CREATE EXTENSION IF NOT EXISTS age;")
            cur.execute("LOAD 'age';")
            cur.execute("SET search_path = ag_catalog, '$user', public;")
            cur.close()
        return self._conn

    def query(self, cypher: str) -> list[dict[str, Any]]:
        """执行 Cypher 查询"""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = f"SELECT * FROM cypher('{self._graph}', $${cypher}$$) AS (result agtype);"
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def execute(self, cypher: str):
        """执行 Cypher 写操作"""
        cur = self.conn.cursor()
        sql = f"SELECT * FROM cypher('{self._graph}', $${cypher}$$) AS (result agtype);"
        cur.execute(sql)
        cur.close()

    def ensure_graph(self):
        """确保图和标签存在"""
        cur = self.conn.cursor()
        cur.execute(f"SELECT create_graph('{self._graph}');")
        cur.close()

    # ===== 业务查询 =====

    def get_part_info(self, part_name: str) -> list[dict]:
        """查询部件信息及关联操作步骤"""
        return self.query(f"""
            MATCH (p:部件 {{name: '{part_name}'}})
            OPTIONAL MATCH (p)-[:包含]->(step:操作步骤)
            OPTIONAL MATCH (step)-[:使用工具]->(t:工具)
            OPTIONAL MATCH (step)-[:参考参数]->(param:参数)
            OPTIONAL MATCH (step)-[:后序步骤]->(next:操作步骤)
            RETURN p.name AS 部件名称,
                   step.name AS 步骤名称,
                   step.operation_type AS 操作类型,
                   step.description AS 操作说明,
                   collect(DISTINCT t.name) AS 工具,
                   collect(DISTINCT param.name) AS 参数,
                   next.name AS 下一步骤
            ORDER BY step.sequence_number
        """)

    def get_workflow(self, part_name: str) -> list[dict]:
        """获取标准化作业指引 (步骤链)"""
        return self.query(f"""
            MATCH (p:部件 {{name: '{part_name}'}})-[:包含]->(step:操作步骤)
            OPTIONAL MATCH (step)-[:使用工具]->(t:工具)
            OPTIONAL MATCH (step)-[:参考参数]->(param:参数)
            OPTIONAL MATCH (step)-[:后序步骤]->(next:操作步骤)
            RETURN step.name AS 步骤名称,
                   step.operation_type AS 操作类型,
                   step.description AS 操作说明,
                   step.sequence_number AS 序号,
                   collect(DISTINCT t.name) AS 所需工具,
                   collect(DISTINCT param.name) AS 参考参数,
                   next.name AS 下一步
            ORDER BY step.sequence_number
        """)

    def get_fault_case(self, fault_name: str) -> list[dict]:
        """查询故障案例"""
        return self.query(f"""
            MATCH (symptom:故障现象 {{name: '{fault_name}'}})
            OPTIONAL MATCH (symptom)-[:诊断依据]->(param:参数)
            OPTIONAL MATCH (symptom)<-[:包含现象]-(case:维修案例)
            OPTIONAL MATCH (case)-[:包含原因]->(cause:故障原因)
            OPTIONAL MATCH (case)-[:包含方案]->(solution:解决方案)
            OPTIONAL MATCH (solution)-[:解决方案操作]->(step:操作步骤)
            RETURN symptom.name AS 故障现象,
                   symptom.description AS 现象描述,
                   param.name AS 异常参数,
                   param.standard_value AS 标准值,
                   cause.name AS 故障原因,
                   solution.name AS 解决方案,
                   step.name AS 标准操作
        """)

    def get_case_by_part(self, part_name: str) -> list[dict]:
        """查询某部件关联的所有案例"""
        return self.query(f"""
            MATCH (p:部件 {{name: '{part_name}'}})
            MATCH (case:维修案例)
            WHERE case.id IN p.关联案例
            OPTIONAL MATCH (case)-[:包含现象]->(symptom:故障现象)
            OPTIONAL MATCH (case)-[:包含原因]->(cause:故障原因)
            OPTIONAL MATCH (case)-[:包含方案]->(solution:解决方案)
            RETURN case.title AS 案例标题,
                   case.description AS 案例描述,
                   collect(DISTINCT symptom.name) AS 故障现象,
                   collect(DISTINCT cause.name) AS 可能原因,
                   collect(DISTINCT solution.name) AS 解决方案
        """)

    def verify_tools(self, part_name: str, step_name: str) -> list[dict]:
        """工具合规校验 (查询该步骤需要哪些工具)"""
        return self.query(f"""
            MATCH (p:部件 {{name: '{part_name}'}})-[:包含]->(step:操作步骤 {{name: '{step_name}'}})
            OPTIONAL MATCH (step)-[:使用工具]->(t:工具)
            RETURN t.name AS 需要工具, t.specification AS 规格
        """)

    def graph_stats(self) -> list[dict]:
        """图谱全局统计"""
        return self.query("""
            MATCH (n)
            RETURN labels(n) AS 节点类型, count(*) AS 数量
            ORDER BY 数量 DESC
        """)


age = AGEClient()
