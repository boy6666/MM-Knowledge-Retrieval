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

    def query(self, cypher: str, cols: str = "result agtype") -> list[dict[str, Any]]:
        """执行 Cypher 查询并返回结果
        cols: 返回列定义，默认单列 result agtype
        """
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        sql = f"SELECT * FROM cypher('{self._graph}', $${cypher}$$) AS ({cols});"
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def execute(self, cypher: str, cols: str = "result agtype"):
        """执行 Cypher 写操作"""
        cur = self.conn.cursor()
        sql = f"SELECT * FROM cypher('{self._graph}', $${cypher}$$) AS ({cols});"
        cur.execute(sql)
        cur.close()

    def query_raw(self, sql: str) -> list[dict]:
        """执行原始 SQL（含 AGE cypher 包裹后的完整 SQL）"""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def ensure_graph(self):
        """确保图和标签存在（已存在则跳过，不报错）"""
        cur = self.conn.cursor()
        cur.execute("LOAD 'age';")
        cur.execute("SET search_path = ag_catalog, '$user', public;")
        try:
            cur.execute(f"SELECT create_graph('{self._graph}');")
        except Exception:
            # 图已存在，忽略
            pass
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
            RETURN {{part: p.name, step: step.name, type: step.operation_type,
                    desc: step.description, tools: collect(DISTINCT t.name),
                    params: collect(DISTINCT param.name), nstep: next.name}}
            ORDER BY step.sequence_number
        """)

    def get_workflow(self, part_name: str) -> list[dict]:
        """获取标准化作业指引 (步骤链)"""
        sql = f"SELECT * FROM cypher('motor_knowledge', $$ MATCH (p:部件 {{name: '{part_name}'}})-[:包含]->(step:操作步骤) OPTIONAL MATCH (step)-[:使用工具]->(t:工具) OPTIONAL MATCH (step)-[:参考参数]->(param:参数) OPTIONAL MATCH (step)-[:后序步骤]->(next:操作步骤) RETURN step.name, step.operation_type, step.description, step.sequence_number, collect(DISTINCT t.name), collect(DISTINCT param.name), next.name ORDER BY step.sequence_number $$) AS (name agtype, optype agtype, descr agtype, seq agtype, tools agtype, params agtype, nstep agtype);"
        return self.query_raw(sql)

    def get_fault_case(self, fault_name: str) -> list[dict]:
        """查询故障案例"""
        return self.query(f"""
            MATCH (symptom:故障现象 {{name: '{fault_name}'}})
            OPTIONAL MATCH (symptom)-[:诊断依据]->(param:参数)
            OPTIONAL MATCH (symptom)<-[:包含现象]-(case:维修案例)
            OPTIONAL MATCH (case)-[:包含原因]->(cause:故障原因)
            OPTIONAL MATCH (case)-[:包含方案]->(solution:解决方案)
            OPTIONAL MATCH (solution)-[:解决方案操作]->(step:操作步骤)
            RETURN {{fault: symptom.name, fdesc: symptom.description,
                    pname: param.name, pval: param.standard_value,
                    cause: cause.name, sol: solution.name,
                    sop: step.name}}
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
            RETURN {{title: case.title, desc: case.description,
                    symps: collect(DISTINCT symptom.name),
                    causes: collect(DISTINCT cause.name),
                    sols: collect(DISTINCT solution.name)}}
        """)

    def verify_tools(self, part_name: str, step_name: str) -> list[dict]:
        """工具合规校验 (查询该步骤需要哪些工具)"""
        return self.query(f"""
            MATCH (p:部件 {{name: '{part_name}'}})-[:包含]->(step:操作步骤 {{name: '{step_name}'}})
            OPTIONAL MATCH (step)-[:使用工具]->(t:工具)
            RETURN {{tool: t.name, spec: t.specification}}
        """)

    def graph_stats(self) -> list[dict]:
        """图谱全局统计"""
        return self.query("""
            MATCH (n)
            RETURN {{label: labels(n), cnt: count(*)}}
            ORDER BY count(*) DESC
        """)


age = AGEClient()
