"""
案例自动挂载到知识图谱
审核通过后调用，将案例实体关联到 AGE 图谱节点
"""
from knowledge_graph.age_client import age


class CaseAttacher:
    """案例自动挂载器"""

    def attach(self, case_data: dict) -> dict:
        """
        案例挂载到图谱

        case_data 格式:
        {
            "id": "CASE-002",
            "title": "发动机异响——凸轮轴磨损",
            "equipment": "摩托车发动机-XXX型",
            "technician": "李工",
            "description": "发动机异响，拆检发现凸轮轴磨损",
            "process": "拆卸凸轮轴后发现凸轮面有磨损痕迹",
            "solution_detail": "更换凸轮轴，调整气门间隙",
            "fault_name": "凸轮轴磨损",
            "part_name": "凸轮轴",
            "param_name": "",  # 关联的参数名，可选
            "images": ["/cases/images/case002_1.jpg"]
        }
        """
        case_id = case_data["id"]
        part_name = case_data.get("part_name", "")

        # 1. 创建案例节点 + 故障现象 + 故障原因 + 解决方案
        age.execute(f"""
            CREATE (case:维修案例 {{
                id: '{case_id}',
                title: '{case_data["title"]}',
                equipment: '{case_data.get("equipment", "")}',
                technician: '{case_data.get("technician", "")}',
                description: '{case_data["description"]}',
                process: '{case_data["process"]}',
                solution_detail: '{case_data["solution_detail"]}'
            }})
            CREATE (symptom:故障现象 {{
                name: '{case_data.get("fault_name", "")}',
                description: '{case_data["description"]}'
            }})
            CREATE (cause:故障原因 {{
                name: '{case_data.get("fault_name", "")}',
                description: '{case_data["process"]}'
            }})
            CREATE (solution:解决方案 {{
                name: '{"更换/修复" + part_name if part_name else "检修"}',
                description: '{case_data["solution_detail"]}'
            }})
            CREATE (case)-[:包含现象]->(symptom)
            CREATE (case)-[:包含原因]->(cause)
            CREATE (case)-[:包含方案]->(solution)
        """)

        # 2. 关联到部件
        if part_name:
            age.execute(f"""
                MATCH (p:部件 {{name: '{part_name}'}})
                MATCH (cause:故障原因 {{name: '{case_data.get("fault_name", "")}'}})
                CREATE (cause)-[:原因关联部件]->(p)
                SET p.关联案例 = COALESCE(p.关联案例, []) + '{case_id}'
                SET p.常见故障 = COALESCE(p.常见故障, []) + '{case_data.get("fault_name", "")}'
            """)

        # 3. 关联到参数 (如果有)
        param_name = case_data.get("param_name", "")
        if param_name:
            age.execute(f"""
                MATCH (param:参数 {{name: '{param_name}'}})
                MATCH (symptom:故障现象 {{name: '{case_data.get("fault_name", "")}'}})
                CREATE (symptom)-[:诊断依据]->(param)
                SET param.关联案例 = COALESCE(param.关联案例, []) + '{case_id}'
            """)

        # 4. 关联到操作步骤
        age.execute(f"""
            MATCH (step:操作步骤)
            WHERE step.name CONTAINS '检查' AND step.name CONTAINS '{part_name[:2]}'
            MATCH (solution:解决方案 {{description: '{case_data["solution_detail"]}'}})
            CREATE (solution)-[:解决方案操作]->(step)
            SET step.关联案例 = COALESCE(step.关联案例, []) + '{case_id}'
        """)

        # 5. 添加案例图片
        for img_path in case_data.get("images", []):
            age.execute(f"""
                MATCH (case:维修案例 {{id: '{case_id}'}})
                CREATE (img:案例图片 {{path: '{img_path}', description: ''}})
                CREATE (case)-[:关联图片]->(img)
            """)

        return {"status": "ok", "case_id": case_id, "message": "案例已挂载到知识图谱"}


attacher = CaseAttacher()
