# BGE 模型下载指南

BGE-base-zh-v1.5 是文本向量化模型，用于知识检索的语义匹配。

---

## 下载

打开 CMD 执行：

```bash
conda activate mm-ai
cd ai-core
python -c "
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('BAAI/bge-base-zh-v1.5', cache_folder='models')
print('下载完成，向量维度:', m.get_embedding_dimension())
"
```

模型文件会下载到 `ai-core/models/models--BAAI--bge-base-zh-v1.5/`，约 400MB。

## 验证

```bash
conda activate mm-ai
cd ai-core
python -c "
from sentence_transformers import SentenceTransformer
m = SentenceTransformer('BAAI/bge-base-zh-v1.5', cache_folder='models')
emb = m.encode('火花塞间隙标准值', normalize_embeddings=True)
print('向量维度:', len(emb))
print('前5个值:', emb[:5])
"
```

输出类似：

```
向量维度: 768
前5个值: [0.02, -0.01, 0.03, ...]
```

## 修改 .env

下载完成后，打开 `ai-core/.env`，将：

```ini
EMBEDDING_MODEL_PATH=BAAI/bge-base-zh-v1.5
```

改成模型实际路径。先查看实际目录名：

```bash
dir ai-core\models\models--BAAI--bge-base-zh-v1.5\snapshots\
```

会有一个类似 `47e1ae1c3c3e602a403b60b663982ec35e25b20c` 的哈希目录，然后改为：

```ini
EMBEDDING_MODEL_PATH=./models/models--BAAI--bge-base-zh-v1.5/snapshots/47e1ae1c3c3e602a403b60b663982ec35e25b20c
```

## 测试搜索

重启 ai-core 后，测试搜索：

```bash
conda activate mm-ai
python -c "
import requests
r = requests.post('http://localhost:8001/api/v1/retrieve', json={'query': '火花塞'})
print(r.status_code, r.text[:500])
"
```

返回 200 并有 results 即成功。
