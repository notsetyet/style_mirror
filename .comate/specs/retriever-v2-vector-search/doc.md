# Retriever V2 升级规范文档

## 需求场景

将 `core/retriever.py` 从基于标签的关键词匹配升级为语义向量检索（Vector Search）版本，提升检索精度和用户体验。

### 当前问题
- 仅支持 vibe_tag 精确匹配，语义理解能力弱
- 无法处理用户自由文本输入（如"适合约会的穿搭"）
- 缺乏向量语义相似度计算

### 目标能力
- 支持 OpenAI text-embedding-3-small 或本地 Mock 向量
- 输入升级为 `vibe_description` + `user_text_modifier` 组合
- 余弦相似度计算语义匹配度
- 混合召回策略（向量 + 标签加权）

---

## 架构设计

### 核心模块

```
core/retriever.py (v2)
├── get_embedding(text, api_key, base_url) -> List[float]
│   ├── 真实模式：调用 OpenAI text-embedding-3-small
│   └── Mock 模式：基于文本 hash 生成伪向量
│
├── cosine_similarity(vec1, vec2) -> float
│   └── numpy 实现：dot(a, b) / (norm(a) * norm(b))
│
├── build_note_embedding(note) -> List[float]
│   └── 组合 caption + vibe_tags + items 生成笔记向量
│
├── get_matching_notes_v2(vibe_description, user_text_modifier, ...) -> List[Dict]
│   ├── Step 1: 构建查询向量（vibe_desc + user_modifier）
│   ├── Step 2: 向量相似度计算（语义匹配）
│   ├── Step 3: 标签匹配加权（精确匹配加成）
│   ├── Step 4: 混合得分排序
│   └── Step 5: 返回 top_k 结果
│
└── 兼容旧接口 get_matching_notes() -> 调用 v2 版本
```

### 数据流

```
用户输入                    检索系统                    返回结果
    │                          │                          │
    ├─ vibe_description ──────►│                          │
    ├─ user_text_modifier ────►├─► get_embedding()        │
    │                          │      │                   │
    │                          │      ▼                   │
    │                          │  query_vector            │
    │                          │      │                   │
    │                          │      ▼                   │
    │                          │  cosine_similarity()     │
    │                          │      │                   │
    │                          │      ▼                   │
    │                          │  混合得分计算             │
    │                          │  (向量分 + 标签加权)      │
    │                          │      │                   │
    │                          │      ▼                   │
    │                          ├─────────────────────────►├─ sorted_notes
    │                          │                          │  (含 score 字段)
```

---

## 影响范围

### 修改文件

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `/Users/rensiyu01/Desktop/style-mirror/core/retriever.py` | 重构 | 核心检索逻辑升级 |
| `/Users/rensiyu01/Desktop/style-mirror/data/mock_notes.json` | 增强 | 添加 `embedding` 字段（可选预计算） |

### 兼容性保证

- 保留 `get_matching_notes()` 旧接口签名，内部调用 v2 版本
- 新增 `get_matching_notes_v2()` 作为主接口
- 返回格式保持一致（List[Dict]），新增 `vector_score` 和 `hybrid_score` 字段

---

## 实现细节

### 1. Embedding 函数

```python
import numpy as np
from typing import List, Optional
import hashlib

def get_embedding(
    text: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> List[float]:
    """
    获取文本的向量嵌入
    
    Args:
        text: 输入文本
        api_key: OpenAI API Key（可选）
        base_url: API Base URL（可选）
        
    Returns:
        List[float]: 1536 维向量（text-embedding-3-small 维度）
        
    模式选择：
        - 有 api_key：调用 OpenAI text-embedding-3-small
        - 无 api_key：使用文本 hash 生成本地伪向量
    """
    if api_key:
        # 真实模式：调用 OpenAI API
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    else:
        # Mock 模式：基于文本 hash 生成确定性伪向量
        return _generate_mock_embedding(text)


def _generate_mock_embedding(text: str, dim: int = 1536) -> List[float]:
    """
    基于 hash 生成本地 Mock 向量（确定性，同文本同向量）
    """
    # 使用 hash 作为随机种子
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    np.random.seed(seed)
    
    # 生成归一化向量
    vec = np.random.randn(dim)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()
```

### 2. 余弦相似度

```python
def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的余弦相似度
    
    公式：cos(θ) = (A·B) / (||A|| × ||B||)
    
    Args:
        vec1: 向量1
        vec2: 向量2
        
    Returns:
        float: 相似度 [-1, 1]，越接近 1 越相似
    """
    a = np.array(vec1)
    b = np.array(vec2)
    
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot_product / (norm_a * norm_b))
```

### 3. 笔记向量构建

```python
def build_note_text(note: Dict) -> str:
    """
    将笔记内容转换为用于 embedding 的文本
    
    组合策略：
        - vibe_tags（风格标签）
        - caption（文案）
        - items 信息（单品名称 + 风格）
    """
    parts = []
    
    # 风格标签
    tags = note.get("vibe_tags", [])
    if tags:
        parts.append(" ".join(tags))
    
    # 文案
    caption = note.get("caption", "")
    if caption:
        parts.append(caption)
    
    # 单品信息
    items = note.get("items", [])
    for item in items:
        item_text = f"{item.get('item_name', '')} {item.get('style', '')}"
        parts.append(item_text)
    
    return " ".join(parts)
```

### 4. 混合召回策略

```python
def get_matching_notes_v2(
    vibe_description: str,
    user_text_modifier: str = "",
    vibe_tag: str = "",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    top_k: int = 5
) -> List[Dict]:
    """
    V2 版本：语义向量检索 + 标签加权混合召回
    
    得分公式：
        hybrid_score = vector_score * 0.7 + tag_score * 0.3
        
    Args:
        vibe_description: 风格描述（如"法式復古，優雅浪漫"）
        user_text_modifier: 用户补充文本（如"适合约会"）
        vibe_tag: 精确标签（用于标签加权）
        api_key: OpenAI API Key
        base_url: API Base URL
        top_k: 返回数量
        
    Returns:
        List[Dict]: 检索结果，包含 vector_score, tag_score, hybrid_score
    """
    # Step 1: 构建查询向量
    query_text = f"{vibe_description} {user_text_modifier}".strip()
    query_embedding = get_embedding(query_text, api_key, base_url)
    
    # Step 2: 加载笔记并计算向量相似度
    all_notes = load_mock_notes()
    
    results = []
    for note in all_notes:
        # 2.1 获取/计算笔记向量
        note_text = build_note_text(note)
        note_embedding = get_embedding(note_text, api_key, base_url)
        
        # 2.2 向量相似度得分 (归一化到 0-100)
        vector_sim = cosine_similarity(query_embedding, note_embedding)
        vector_score = max(0, (vector_sim + 1) / 2) * 100  # [-1,1] -> [0,100]
        
        # 2.3 标签匹配得分
        tag_score = 0
        if vibe_tag:
            note_tags = note.get("vibe_tags", [])
            if vibe_tag in note_tags:
                tag_score = 100  # 精确匹配满分
        
        # Step 3: 混合得分计算
        hybrid_score = vector_score * 0.7 + tag_score * 0.3
        
        results.append({
            **note,
            "vector_score": round(vector_score, 2),
            "tag_score": tag_score,
            "hybrid_score": round(hybrid_score, 2),
            "is_default": False
        })
    
    # Step 4: 按混合得分排序
    results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    
    return results[:top_k]
```

---

## 边界条件与异常处理

### 1. API 调用失败
- 网络超时：自动降级到 Mock 模式
- API 限流：记录日志，使用 Mock 模式

### 2. 空输入处理
- `vibe_description` 为空：使用默认推荐
- `user_text_modifier` 为空：仅使用 vibe_description

### 3. 向量维度不一致
- Mock 模式确保维度固定为 1536

### 4. 性能考量
- 笔记数量 < 100：实时计算向量
- 笔记数量 > 100：建议预计算并缓存

---

## 预期效果

### 检索精度提升

| 场景 | V1 结果 | V2 结果 |
|------|--------|--------|
| "适合约会的法式穿搭" | 随机匹配 | 语义匹配到"法式復古"笔记 |
| "上班通勤穿什么" | 无匹配 | 匹配"極簡工業"笔记 |
| "自然舒适的周末穿搭" | 无匹配 | 匹配"溫柔原木"笔记 |

### 返回字段示例

```json
{
  "note_id": "note_001",
  "caption": "復古法式穿搭...",
  "vector_score": 85.32,
  "tag_score": 100,
  "hybrid_score": 89.72,
  "is_default": false
}
```

---

## 依赖变更

需要在 `requirements.txt` 添加：

```
numpy>=1.24.0
```

如使用 OpenAI Embedding：
```
openai>=1.0.0
```
