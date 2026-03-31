# -*- coding: utf-8 -*-
"""
StyleMirror - 笔记检索模块 V2
负责从小红书笔记库中检索与用户风格匹配的内容

V2 升级要点：
1. 引入语义向量检索（Vector Search）
2. 支持 OpenAI text-embedding-3-small 或本地 Mock 向量
3. 输入升级为 vibe_description + user_text_modifier 组合
4. 余弦相似度计算语义匹配度
5. 混合召回策略（向量 70% + 标签 30%）
6. 支持 python-dotenv 加载 .env 配置
"""

import json
import hashlib
import os
import numpy as np
from typing import List, Dict, Optional
from pathlib import Path

# 加载 .env 环境变量
from dotenv import load_dotenv

_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


# ============================================
# Mock 数据加载
# ============================================

def load_mock_notes() -> List[Dict]:
    """
    加载模拟的小红书笔记数据
    
    Returns:
        List[Dict]: 笔记数据列表
    """
    current_dir = Path(__file__).parent.parent
    data_path = current_dir / "data" / "mock_notes.json"
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            notes = json.load(f)
        return notes
    except FileNotFoundError:
        print(f"数据文件不存在: {data_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {str(e)}")
        return []


# ============================================
# 向量工具函数（Task 1）
# ============================================

def _generate_mock_embedding(text: str, dim: int = 1536) -> List[float]:
    """
    基于文本 hash 生成本地 Mock 向量（确定性，同文本同向量）
    
    使用 MD5 hash 作为随机种子，确保：
    - 相同文本生成相同向量
    - 不同文本生成不同向量
    
    Args:
        text: 输入文本
        dim: 向量维度，默认 1536（text-embedding-3-small 维度）
        
    Returns:
        List[float]: 归一化的向量
    """
    # 使用 hash 作为随机种子
    seed = int(hashlib.md5(text.encode('utf-8')).hexdigest(), 16) % (2**32)
    rng = np.random.default_rng(seed)
    
    # 生成归一化向量
    vec = rng.standard_normal(dim)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def get_embedding(
    text: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> List[float]:
    """
    获取文本的向量嵌入
    
    配置优先级：
        - api_key: 参数 > OPENAI_API_KEY 环境变量
        - base_url: 参数 > OPENAI_BASE_URL 环境变量
    
    模式选择：
        - 有 api_key（参数或环境变量）：调用 OpenAI text-embedding-3-small
        - 无 api_key：使用文本 hash 生成本地伪向量
    
    Args:
        text: 输入文本
        api_key: OpenAI API Key（可选，未传入则从环境变量读取）
        base_url: API Base URL（可选，未传入则从环境变量读取）
        
    Returns:
        List[float]: 1536 维向量
    """
    if not text or not text.strip():
        # 空文本返回零向量
        return [0.0] * 1536
    
    # 优先使用参数，其次使用环境变量
    effective_api_key = api_key or os.getenv("OPENAI_API_KEY")
    effective_base_url = base_url or os.getenv("OPENAI_BASE_URL")
    
    if effective_api_key:
        try:
            # 真实模式：调用 OpenAI API
            from openai import OpenAI
            client_kwargs = {"api_key": effective_api_key}
            if effective_base_url:
                client_kwargs["base_url"] = effective_base_url
            client = OpenAI(**client_kwargs)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            # API 调用失败，降级到 Mock 模式
            print(f"Embedding API 调用失败，使用 Mock 模式: {str(e)}")
            return _generate_mock_embedding(text)
    else:
        # Mock 模式：基于文本 hash 生成本地伪向量
        return _generate_mock_embedding(text)


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


# ============================================
# 笔记文本构建（Task 2）
# ============================================

def build_note_text(note: Dict) -> str:
    """
    将笔记内容转换为用于 embedding 的文本
    
    组合策略：
        - vibe_tags（风格标签）
        - caption（文案）
        - items 信息（单品名称 + 风格）
    
    Args:
        note: 笔记字典
        
    Returns:
        str: 组合后的文本
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
        item_text = f"{item.get('item_name', '')} {item.get('style', '')} {item.get('color', '')}"
        parts.append(item_text)
    
    return " ".join(parts)


# ============================================
# 默认推荐逻辑
# ============================================

def _get_default_recommendations() -> List[Dict]:
    """
    获取默认推荐（当无匹配时）
    
    返回最受欢迎的笔记作为兜底，确保前端不会报错
    
    Returns:
        List[Dict]: 默认推荐的笔记列表
    """
    all_notes = load_mock_notes()
    
    if not all_notes:
        return []
    
    # 按点赞数排序，返回热门笔记
    sorted_notes = sorted(
        all_notes,
        key=lambda x: x.get("likes", 0),
        reverse=True
    )
    
    # 标记为默认推荐
    result = []
    for note in sorted_notes[:2]:
        result.append({
            **note,
            "vector_score": 0,
            "tag_score": 0,
            "hybrid_score": 0,
            "is_default": True
        })
    
    return result


# ============================================
# V2 核心检索接口（Task 3）
# ============================================

def get_matching_notes_v2(
    vibe_description: str,
    user_text_modifier: str = "",
    vibe_tag: str = "",
    scene_keywords: List[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    top_k: int = 5
) -> List[Dict]:
    """
    V2 版本：语义向量检索 + 标签加权混合召回
    
    得分公式：
        hybrid_score = vector_score * 0.7 + tag_score * 0.3
        
    其中：
        - vector_score: 余弦相似度归一化到 [0, 100]
        - tag_score: 标签精确匹配得分 [0, 100]
    
    Args:
        vibe_description: 风格描述（如"法式復古，優雅浪漫"）
        user_text_modifier: 用户补充文本（如"适合约会"）
        vibe_tag: 精确标签（用于标签加权）
        scene_keywords: 场景关键词列表（额外加权）
        api_key: OpenAI API Key
        base_url: API Base URL
        top_k: 返回数量
        
    Returns:
        List[Dict]: 检索结果，包含 vector_score, tag_score, hybrid_score
    """
    # 构建查询文本
    query_text = f"{vibe_description} {user_text_modifier}".strip()
    
    if not query_text:
        return _get_default_recommendations()
    
    # Step 1: 构建查询向量
    query_embedding = get_embedding(query_text, api_key, base_url)
    
    # Step 2: 加载笔记并计算向量相似度
    all_notes = load_mock_notes()
    
    if not all_notes:
        return _get_default_recommendations()
    
    results = []
    for note in all_notes:
        # 2.1 获取笔记文本并计算向量
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
        
        # 2.4 场景关键词额外加分
        keyword_bonus = 0
        if scene_keywords:
            note_caption = note.get("caption", "").lower()
            note_items = note.get("items", [])
            items_text = " ".join([
                item.get("item_name", "") + " " + item.get("style", "")
                for item in note_items
            ]).lower()
            combined_text = note_caption + " " + items_text
            
            for keyword in scene_keywords:
                if keyword.lower() in combined_text:
                    keyword_bonus += 10  # 每个关键词 +10 分
        
        # Step 3: 混合得分计算
        # 向量分 70% + 标签分 30% + 关键词加分
        hybrid_score = vector_score * 0.7 + tag_score * 0.3 + keyword_bonus
        
        results.append({
            **note,
            "vector_score": round(vector_score, 2),
            "tag_score": tag_score,
            "keyword_bonus": keyword_bonus,
            "hybrid_score": round(hybrid_score, 2),
            "is_default": False
        })
    
    # Step 4: 按混合得分排序
    results.sort(key=lambda x: x["hybrid_score"], reverse=True)
    
    return results[:top_k]


# ============================================
# 兼容旧接口（Task 4）
# ============================================

def get_matching_notes(
    vibe_tag: str,
    scene_keywords: List[str] = None,
    top_k: int = 5,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> List[Dict]:
    """
    根据风格标签和场景关键词匹配笔记（兼容 V1 接口）
    
    内部调用 V2 版本，将 vibe_tag 作为 vibe_description 和 vibe_tag 使用
    
    匹配逻辑：
    1. 向量语义匹配（70% 权重）
    2. 标签精确匹配（30% 权重）
    3. 场景关键词加分（每个 +10 分）
    4. 按混合得分排序，返回 top_k 个结果
    5. 无匹配时返回默认推荐
    
    Args:
        vibe_tag: 风格标签，如 "法式復古"、"極簡工業"、"溫柔原木"
        scene_keywords: 场景关键词列表，如 ["咖啡馆", "居家"]
        top_k: 返回结果数量，默认 5
        api_key: OpenAI API Key（可选）
        base_url: API Base URL（可选）
        
    Returns:
        List[Dict]: 匹配的笔记列表，每条包含 score 字段
    """
    if not vibe_tag:
        return _get_default_recommendations()
    
    # 调用 V2 版本
    results = get_matching_notes_v2(
        vibe_description=vibe_tag,
        user_text_modifier="",
        vibe_tag=vibe_tag,
        scene_keywords=scene_keywords,
        api_key=api_key,
        base_url=base_url,
        top_k=top_k
    )
    
    # 兼容旧字段名：hybrid_score -> match_score
    for note in results:
        note["match_score"] = note.get("hybrid_score", 0)
    
    return results


def retrieve_notes_by_vibe(vibe_tags: List[str], top_k: int = 5) -> List[Dict]:
    """
    根据 Vibe 标签检索相关笔记（兼容旧接口）
    
    Args:
        vibe_tags: 风格标签列表，如 ["法式慵懒", "温柔优雅"]
        top_k: 返回结果数量
        
    Returns:
        List[Dict]: 匹配的笔记列表
    """
    if not vibe_tags:
        return _get_default_recommendations()
    
    # 使用第一个标签作为主标签
    primary_tag = vibe_tags[0]
    return get_matching_notes(primary_tag, top_k=top_k)


# ============================================
# 检索结果处理
# ============================================

def format_retrieved_notes(notes: List[Dict]) -> str:
    """
    格式化检索结果为可读文本
    
    Args:
        notes: 检索到的笔记列表
        
    Returns:
        str: 格式化后的文本
    """
    if not notes:
        return "暂无找到相关的穿搭推荐～"
    
    result_parts = []
    for i, note in enumerate(notes, 1):
        tags_str = "、".join(note.get("vibe_tags", []))
        is_default = note.get("is_default", False)
        score = note.get("hybrid_score") or note.get("match_score", 0)
        default_mark = "【热门推荐】" if is_default else ""
        result_parts.append(
            f"{i}. {default_mark}{note.get('caption', '')}\n"
            f"   风格标签：{tags_str}\n"
            f"   匹配得分：{score} 分\n"
            f"   👍 {note.get('likes', 0)} | ⭐ {note.get('collects', 0)}"
        )
    
    return "\n\n".join(result_parts)


def get_recommended_items(notes: List[Dict]) -> List[Dict]:
    """
    从检索结果中提取推荐单品
    
    Args:
        notes: 检索到的笔记列表
        
    Returns:
        List[Dict]: 单品列表
    """
    items = []
    for note in notes:
        note_items = note.get("items", [])
        items.extend(note_items)
    return items


# ============================================
# 高级检索接口（新增）
# ============================================

def semantic_search(
    query: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    top_k: int = 5
) -> List[Dict]:
    """
    纯语义搜索接口（无标签加权）
    
    适用于用户自由文本查询场景，如"适合约会的穿搭"
    
    Args:
        query: 用户查询文本
        api_key: OpenAI API Key
        base_url: API Base URL
        top_k: 返回数量
        
    Returns:
        List[Dict]: 检索结果
    """
    if not query or not query.strip():
        return _get_default_recommendations()
    
    # 构建查询向量
    query_embedding = get_embedding(query, api_key, base_url)
    
    # 加载笔记
    all_notes = load_mock_notes()
    
    if not all_notes:
        return _get_default_recommendations()
    
    results = []
    for note in all_notes:
        note_text = build_note_text(note)
        note_embedding = get_embedding(note_text, api_key, base_url)
        
        # 纯向量相似度
        vector_sim = cosine_similarity(query_embedding, note_embedding)
        vector_score = max(0, (vector_sim + 1) / 2) * 100
        
        results.append({
            **note,
            "vector_score": round(vector_score, 2),
            "hybrid_score": round(vector_score, 2),
            "is_default": False
        })
    
    # 按向量得分排序
    results.sort(key=lambda x: x["vector_score"], reverse=True)
    
    return results[:top_k]
