# WSL2 安装 PostgreSQL + Apache AGE + pgvector 指南

---

## 一、安装 WSL2

### 1.1 启用 WSL2

**管理员 PowerShell** 运行：

```powershell
# 启用 WSL 功能
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# 启用虚拟机平台
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# 重启电脑
Restart-Computer
```

### 1.2 重启后设置 WSL2 为默认

```powershell
# 设置 WSL 版本为 2
wsl --set-default-version 2

# 安装 Ubuntu 22.04 LTS
wsl --install -d Ubuntu-22.04
```

安装过程会提示创建 Linux 用户名和密码，记好。

### 1.3 验证

```powershell
wsl -l -v
```

输出应该类似：

```
  NAME                   STATE           VERSION
* Ubuntu-22.04           Running         2
```

---

## 二、在 WSL2 中安装 PostgreSQL 16

### 2.1 进入 WSL2

```powershell
wsl
```

现在你已经在 Linux 环境下了，后面的命令都在 WSL2 终端里执行。

### 2.2 安装 PostgreSQL

> Ubuntu 22.04 默认源只有 PostgreSQL 14，需要先添加 PostgreSQL 官方源才能装 16。

```bash
# 更新包管理器
sudo apt update && sudo apt upgrade -y

# 添加 PostgreSQL 官方 16 源
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# 导入官方签名密钥
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg

# 再次更新（现在会包含 PG16 的包）
sudo apt update

# 安装 PostgreSQL 16
sudo apt install -y postgresql-16 postgresql-server-dev-16

# 验证
psql --version
# 应输出: psql (PostgreSQL) 16.x
```

### 2.3 启动 PostgreSQL

```bash
# 启动 PG 服务
sudo pg_ctlcluster 16 main start

# 设置开机自启
sudo update-rc.d postgresql enable

# 验证
sudo -u postgres psql -c "SELECT version();"
```

### 2.4 创建数据库和用户

```bash
# 创建数据库
sudo -u postgres createdb motor_maintenance

# 设置 postgres 用户的密码
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '1234';"

# 允许密码登录 (改 pg_hba.conf)
sudo sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' /etc/postgresql/16/main/pg_hba.conf

# 重启 PG 使配置生效
sudo pg_ctlcluster 16 main restart

# 用密码测试连接
psql -h localhost -U postgres -d motor_maintenance -c "SELECT 1;"
# 输入密码 1234，返回 1 即成功
```

---

## 三、安装 pgvector

### 3.1 从源码编译安装

```bash
# 安装编译工具
sudo apt install -y build-essential git

# 克隆 pgvector
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector

# 编译安装 (指定 PG 16)
make PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config
sudo make install

# 验证
sudo -u postgres psql -d motor_maintenance -c "CREATE EXTENSION vector;"
```

看到 `CREATE EXTENSION` 即成功。

### 3.2 验证 pgvector

```bash
sudo -u postgres psql -d motor_maintenance -c "
CREATE TABLE test_vec (id serial, embedding vector(768));
INSERT INTO test_vec (embedding) VALUES ('[1,2,3]'::vector);
SELECT * FROM test_vec;
DROP TABLE test_vec;
"
```

---

## 四、安装 Apache AGE

### 4.1 从源码编译安装

```bash
# 安装额外依赖
sudo apt install -y flex bison

# 克隆 Apache AGE（支持 PG 16 的分支）
cd /tmp
git clone https://github.com/apache/age.git
cd age

# 切换到与 PG 16 兼容的分支 (release/PG16/1.5.0)
git checkout release/PG16/1.5.0

# 编译
make PG_CONFIG=/usr/lib/postgresql/16/bin/pg_config
sudo make install

# 验证
sudo -u postgres psql -d motor_maintenance -c "CREATE EXTENSION age;"
```

看到 `CREATE EXTENSION` 即成功。

### 4.2 创建图

```bash
sudo -u postgres psql -d motor_maintenance -c "
LOAD 'age';
SET search_path = ag_catalog, '\$user', public;
SELECT create_graph('motor_knowledge');
"
```

### 4.3 验证 AGE

```bash
sudo -u postgres psql -d motor_maintenance -c "
LOAD 'age';
SET search_path = ag_catalog, '\$user', public;
SELECT * FROM cypher('motor_knowledge', \$\$ CREATE (n:测试节点 {name: 'hello'}) RETURN n \$\$) AS (result agtype);
"
```

看到 `("hello"::vertex)` 即成功。

---

## 五、配置 Windows 访问 WSL2 的 PostgreSQL

### 5.1 开放 WSL2 端口

在 WSL2 终端中：

```bash
# 查看 WSL2 的 IP
ip addr show eth0 | grep inet

# 让 PostgreSQL 监听所有接口
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/16/main/postgresql.conf

# 允许 Windows 的 IP 连接 (把 Windows 的网段加入 pg_hba.conf)
sudo bash -c 'echo "host    all             all             0.0.0.0/0               md5" >> /etc/postgresql/16/main/pg_hba.conf'

# 重启
sudo pg_ctlcluster 16 main restart
```

### 5.2 查看 WSL2 的 IP

```bash
# 在 WSL2 中运行
ip addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}'
```

会输出类似 `172.23.xxx.xxx` 的地址。

### 5.3 在 Windows 上测试连接

打开 Windows CMD：

```bash
# 把 xxx.xxx 替换成刚才看到的 IP
psql -h 172.23.xxx.xxx -U postgres -d motor_maintenance -c "SELECT 1;"
```

---

## 六、更新 ai-core 配置

修改 `ai-core/.env` 中的数据库连接：

```ini
# Windows + WSL2 混合模式
PG_HOST=172.23.xxx.xxx    # ← 改成 WSL2 的 IP
PG_PORT=5432
PG_DB=motor_maintenance
PG_USER=postgres
PG_PASSWORD=1234
```

如果只想在 WSL2 内部开发（不跨 Windows），`PG_HOST=localhost` 即可——WSL2 内部可以直接连接。

---

## 七、启动验证

### 7.1 确认 PostgreSQL 已就绪

```bash
# 在 WSL2 中
sudo pg_ctlcluster 16 main status
# 应输出: pg_ctl: server is running
```

### 7.2 启动 ai-core 并验证扩展

```bash
# 在 Windows CMD 中
conda activate mm-ai
cd ai-core
python main.py
```

启动日志中应看到：

```
[AICore] AGE 图 'motor_knowledge' 已就绪
[AICore] pgvector 已就绪
[AICore] 启动完成
```

不再有"未就绪"的警告。

---

## 八、常用命令速查

### WSL2 管理

```powershell
# Windows PowerShell
wsl --shutdown                        # 关闭 WSL2
wsl                                  # 进入 WSL2
wsl -d Ubuntu-22.04                  # 指定发行版进入
```

### PostgreSQL 管理（WSL2 内）

```bash
sudo pg_ctlcluster 16 main start     # 启动
sudo pg_ctlcluster 16 main stop      # 停止
sudo pg_ctlcluster 16 main restart   # 重启
sudo pg_ctlcluster 16 main status    # 状态
```

### AGE 验证（WSL2 内）

```bash
sudo -u postgres psql -d motor_maintenance -c "
LOAD 'age';
SET search_path = ag_catalog, '\$user', public;
SELECT * FROM cypher('motor_knowledge', \$\$ MATCH (n) RETURN labels(n), count(*) ORDER BY count(*) DESC \$\$) AS (result agtype);
"
```

---

## 九、冷启动知识图谱（AGE 数据初始化）

以下步骤在 WSL2 终端中执行，逐一复制粘贴即可。

### 9.1 注册标签类型

```sql
sudo -u postgres psql -d motor_maintenance -c "
LOAD 'age';
SET search_path = ag_catalog, '\$user', public;
SELECT create_vlabel('motor_knowledge', '系统');
SELECT create_vlabel('motor_knowledge', '部件');
SELECT create_vlabel('motor_knowledge', '子部件');
SELECT create_vlabel('motor_knowledge', '操作步骤');
SELECT create_vlabel('motor_knowledge', '工具');
SELECT create_vlabel('motor_knowledge', '参数');
SELECT create_vlabel('motor_knowledge', '注意事项');
SELECT create_vlabel('motor_knowledge', '图片');
SELECT create_vlabel('motor_knowledge', '维修案例');
SELECT create_vlabel('motor_knowledge', '故障现象');
SELECT create_vlabel('motor_knowledge', '故障原因');
SELECT create_vlabel('motor_knowledge', '解决方案');
SELECT create_vlabel('motor_knowledge', '案例图片');
"
```

### 9.2 创建实体节点

```sql
sudo -u postgres psql -d motor_maintenance -c "
LOAD 'age';
SET search_path = ag_catalog, '\$user', public;

-- 系统
SELECT * FROM cypher('motor_knowledge', \$\$
    CREATE (:系统 {name: '发动机', description: '摩托车发动机总成', manual_section: '三'})
\$\$) AS (result agtype);

-- 部件
SELECT * FROM cypher('motor_knowledge', \$\$
    CREATE (:部件 {name: '火花塞', belongs_to: '发动机', manual_section: '一'}),
    (:部件 {name: '起动电机', belongs_to: '发动机', manual_section: '二'}),
    (:部件 {name: '气缸头', belongs_to: '发动机', manual_section: '四'}),
    (:部件 {name: '气门', belongs_to: '气缸头', manual_section: '四'}),
    (:部件 {name: '凸轮轴', belongs_to: '气缸头', manual_section: '四'}),
    (:部件 {name: '涨紧器', belongs_to: '气缸头', manual_section: '四'}),
    (:部件 {name: '气缸头盖', belongs_to: '气缸头', manual_section: '四'}),
    (:部件 {name: '气缸', belongs_to: '发动机', manual_section: '五'}),
    (:部件 {name: '活塞', belongs_to: '发动机', manual_section: '五'}),
    (:部件 {name: '离合器', belongs_to: '发动机', manual_section: '六'}),
    (:部件 {name: '机油泵', belongs_to: '发动机', manual_section: '六'}),
    (:部件 {name: '水泵', belongs_to: '发动机', manual_section: '六'})
\$\$) AS (result agtype);

-- 操作步骤 (火花塞部分)
SELECT * FROM cypher('motor_knowledge', \$\$
    CREATE (:操作步骤 {name: '拆卸火花塞', operation_type: '拆卸', sequence_number: 1,
        description: '1. 用尖嘴钳将高压帽拔出。2. 用火花塞专用套筒将火花塞拆下。注意：逆时针转动。'}),
    (:操作步骤 {name: '检查火花塞', operation_type: '检查', sequence_number: 2,
        description: '用塞尺测量火花塞间隙a，超出范围须更换火花塞。'}),
    (:操作步骤 {name: '安装火花塞', operation_type: '安装', sequence_number: 3,
        description: '预紧3圈后再转1/4圈，或使用定扭扳手拧紧至20±2 N·m。'}),
    (:操作步骤 {name: '测量压缩压力', operation_type: '测量', sequence_number: 4,
        description: '安装压力表，用起动电机带动发动机转动，直至压力表读数稳定。'})
\$\$) AS (result agtype);

-- 工具
SELECT * FROM cypher('motor_knowledge', \$\$
    CREATE (:工具 {name: '尖嘴钳'}),
    (:工具 {name: '火花塞专用套筒', specification: '16mm'}),
    (:工具 {name: '定扭扳手'}),
    (:工具 {name: '塞尺'}),
    (:工具 {name: '压力表'})
\$\$) AS (result agtype);

-- 参数
SELECT * FROM cypher('motor_knowledge', \$\$
    CREATE (:参数 {name: '火花塞间隙', standard_value: '0.7~0.9', unit: 'mm'}),
    (:参数 {name: '拧紧力矩', standard_value: '20±2', unit: 'N·m'}),
    (:参数 {name: '标准压缩压力', standard_value: '1300~1900', unit: 'kPa', condition: '转速1500 r/min'})
\$\$) AS (result agtype);

-- 注意事项
SELECT * FROM cypher('motor_knowledge', \$\$
    CREATE (:注意事项 {content: '逆时针转动火花塞将其拆下', severity: '注意'}),
    (:注意事项 {content: '必须使用定扭扳手', severity: '警示'})
\$\$) AS (result agtype);
"
```

### 9.3 创建关系

```sql
sudo -u postgres psql -d motor_maintenance -c "
LOAD 'age';
SET search_path = ag_catalog, '\$user', public;

-- 系统包含部件
SELECT * FROM cypher('motor_knowledge', \$\$
    MATCH (s:系统 {name: '发动机'}), (c:部件)
    WHERE c.belongs_to = '发动机'
    CREATE (s)-[:包含]->(c)
\$\$) AS (result agtype);

-- 部件包含操作步骤 (火花塞)
SELECT * FROM cypher('motor_knowledge', \$\$
    MATCH (c:部件 {name: '火花塞'}), (op:操作步骤)
    WHERE op.name IN ['拆卸火花塞', '检查火花塞', '安装火花塞', '测量压缩压力']
    CREATE (c)-[:包含]->(op)
\$\$) AS (result agtype);

-- 操作步骤使用工具
SELECT * FROM cypher('motor_knowledge', \$\$
    MATCH (op:操作步骤 {name: '拆卸火花塞'})
    MATCH (t1:工具 {name: '尖嘴钳'}), (t2:工具 {name: '火花塞专用套筒'})
    CREATE (op)-[:使用工具]->(t1), (op)-[:使用工具]->(t2)
\$\$) AS (result agtype);

SELECT * FROM cypher('motor_knowledge', \$\$
    MATCH (op:操作步骤 {name: '检查火花塞'})
    MATCH (t:工具 {name: '塞尺'})
    CREATE (op)-[:使用工具]->(t)
\$\$) AS (result agtype);

SELECT * FROM cypher('motor_knowledge', \$\$
    MATCH (op:操作步骤 {name: '安装火花塞'})
    MATCH (t1:工具 {name: '火花塞专用套筒'}), (t2:工具 {name: '定扭扳手'})
    CREATE (op)-[:使用工具]->(t1), (op)-[:使用工具]->(t2)
\$\$) AS (result agtype);

-- 操作步骤参考参数
SELECT * FROM cypher('motor_knowledge', \$\$
    MATCH (op:操作步骤 {name: '检查火花塞'})
    MATCH (p:参数 {name: '火花塞间隙'})
    CREATE (op)-[:参考参数]->(p)
\$\$) AS (result agtype);

SELECT * FROM cypher('motor_knowledge', \$\$
    MATCH (op:操作步骤 {name: '安装火花塞'})
    MATCH (p:参数 {name: '拧紧力矩'})
    CREATE (op)-[:参考参数]->(p)
\$\$) AS (result agtype);

-- 操作步骤后序关系
SELECT * FROM cypher('motor_knowledge', \$\$
    MATCH (op1:操作步骤 {name: '拆卸火花塞'})
    MATCH (op2:操作步骤 {name: '检查火花塞'})
    MATCH (op3:操作步骤 {name: '安装火花塞'})
    CREATE (op1)-[:后序步骤]->(op2), (op2)-[:后序步骤]->(op3)
\$\$) AS (result agtype);
"
```

### 9.4 验证图谱

```sql
sudo -u postgres psql -d motor_maintenance -c "
LOAD 'age';
SET search_path = ag_catalog, '\$user', public;

-- 查询火花塞完整检修流程
SELECT * FROM cypher('motor_knowledge', \$\$
    MATCH (c:部件 {name: '火花塞'})-[:包含]->(step:操作步骤)
    OPTIONAL MATCH (step)-[:使用工具]->(t:工具)
    OPTIONAL MATCH (step)-[:参考参数]->(p:参数)
    OPTIONAL MATCH (step)-[:后序步骤]->(next:操作步骤)
    RETURN step.name, step.operation_type,
           collect(DISTINCT t.name),
           collect(DISTINCT p.name),
           next.name
\$\$) AS (name agtype, optype agtype, tools agtype, params agtype, nstep agtype);
"
```

正常应返回类似：

```
步骤名称       | 操作类型 | 所需工具                        | 参考参数     | 下一步骤
---------------|---------|--------------------------------|-------------|---------
拆卸火花塞     | 拆卸     | [尖嘴钳, 火花塞专用套筒]        | []          | 检查火花塞
检查火花塞     | 检查     | [塞尺]                         | [火花塞间隙]  | 安装火花塞
安装火花塞     | 安装     | [火花塞专用套筒, 定扭扳手]      | [拧紧力矩]   |
```

### 9.5 图谱全局统计

```sql
sudo -u postgres psql -d motor_maintenance -c "
LOAD 'age';
SET search_path = ag_catalog, '\$user', public;
SELECT * FROM cypher('motor_knowledge', \$\$
    MATCH (n) RETURN labels(n) AS 节点类型, count(*) AS 数量 ORDER BY 数量 DESC
\$\$) AS (类型 agtype, 数量 agtype);
"
```

---

## 十、测试 AGE 查询接口

启动 ai-core 后验证：

```bash
curl -s -X POST http://localhost:8001/api/v1/guidance/workflow \
  -H "Content-Type: application/json" \
  -d '{"part_name": "火花塞"}'
```

应返回包含步骤链的 JSON。再测试检索：

```bash
curl -s -X POST http://localhost:8001/api/v1/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "火花塞", "top_k": 3}'
```

---

## 十一、问题排查

| 问题 | 解决 |
|------|------|
| `wsl --install` 报错 0x800701bc | 需要安装 Linux 内核更新包 → https://aka.ms/wsl2kernel |
| `CREATE EXTENSION age` 报错 `could not open extension control file` | AGE 版本不对，`git checkout release/PG16/1.5.0` 确认分支 |
| `psql: 错误: 连接失败` | 先 `sudo pg_ctlcluster 16 main start` |
| Windows 连不上 WSL2 的 PostgreSQL | 检查 `postgresql.conf` 中 `listen_addresses = '*'` |
| ai-core 连不上 PostgreSQL | 检查 `.env` 中的 `PG_HOST` 是否填了正确的 WSL2 IP |
| 重启电脑后 WSL2 IP 变了 | 每次重启 WSL2 IP 会变，查看新 IP 更新 `.env`。或用 `localhost`（Windows 11 22H2+ WSL2 支持 localhost 直连） |
