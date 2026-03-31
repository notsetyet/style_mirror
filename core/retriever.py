# -*- coding: utf-8 -*-
"""
StyleMirror - 笔记检索模块
负责从小红书笔记库中检索与用户风格匹配的内容

重构要点：
1. 支持 scene_keywords 作为加权匹配维度
2. 无匹配时返回默认推荐，避免前端报错
3. 实现基于分数的排序逻辑
"""

import json
from typing import List, Dict, Optional
from pathlib import Path


# ============================================
# Mock 数据加载
# ============================================

def load_mock_notes() -> List[Dict]:
    """
    加载模拟的小红书笔记数据
    
    Returns:
        List[Dict]: 笔记数据列表
    """
    # 获取 data 目录路径
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
            "match_score": 0,
            "is_default": True
        })
    
    return result


# ============================================
# 笔记检索逻辑（核心接口）
# ============================================

def get_matching_notes(
    vibe_tag: str,
    scene_keywords: List[str] = None,
    top_k: int = 5
) -> List[Dict]:
    """
    根据风格标签和场景关键词匹配笔记
    
    匹配逻辑：
    1. 基础分：vibe_tag 完全匹配 +10 分
    2. 加成分：scene_keywords 每匹配一个 +5 分
    3. 按总分排序，返回 top_k 个结果
    4. 无匹配时返回默认推荐
    
    Args:
        vibe_tag: 风格标签，如 "法式復古"、"極簡工業"、"溫柔原木"
        scene_keywords: 场景关键词列表，如 ["咖啡馆", "居家"]
        top_k: 返回结果数量，默认 5
        
    Returns:
        List[Dict]: 匹配的笔记列表，每条包含 match_score 字段
    """
    # 加载 Mock 数据
    all_notes = load_mock_notes()
    
    if not all_notes:
        return _get_default_recommendations()
    
    # 计算每条笔记的匹配分数
    scored_notes = []
    for note in all_notes:
        score = 0
        
        # 1. Vibe 标签匹配（基础分）
        note_tags = note.get("vibe_tags", [])
        if vibe_tag in note_tags:
            score += 10
        
        # 2. 场景关键词匹配（加成分）
        if scene_keywords:
            # 在 caption 和 items 中搜索关键词
            note_caption = note.get("caption", "").lower()
            note_items = note.get("items", [])
            items_text = " ".join([
                item.get("item_name", "") + " " + item.get("style", "")
                for item in note_items
            ]).lower()
            combined_text = note_caption + " " + items_text
            
            for keyword in scene_keywords:
                if keyword.lower() in combined_text:
                    score += 5
        
        # 只保留有匹配的笔记
        if score > 0:
            scored_notes.append({
                **note,
                "match_score": score,
                "is_default": False
            })
    
    # 按匹配分数排序
    scored_notes.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    # 无匹配时返回默认推荐
    if not scored_notes:
        return _get_default_recommendations()
    
    return scored_notes[:top_k]


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


def retrieve_notes_by_embedding(
    query_embedding: List[float],
    top_k: int = 5
) -> List[Dict]:
    """
    基于向量相似度检索笔记
    
    TODO: 需要先为笔记生成向量嵌入
    - 使用 CLIP 或其他多模态模型生成图像向量
    - 存储到向量数据库
    - 实现向量相似度搜索
    
    Args:
        query_embedding: 查询向量
        top_k: 返回结果数量
        
    Returns:
        List[Dict]: 匹配的笔记列表
    """
    raise NotImplementedError("向量检索功能待实现")


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
        default_mark = "【热门推荐】" if is_default else ""
        result_parts.append(
            f"{i}. {default_mark}{note.get('caption', '')}\n"
            f"   风格标签：{tags_str}\n"
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
# 向量数据库接口（预留）
# ============================================

class VectorStore:
    """
    向量数据库接口类
    
    TODO: 实现具体的向量存储和检索逻辑
    - 可选方案：Pinecone、Milvus、Weaviate
    """
    
    def __init__(self, collection_name: str = "xhs_notes"):
        """
        初始化向量存储
        
        Args:
            collection_name: 集合名称
        """
        self.collection_name = collection_name
        # TODO: 初始化向量数据库连接
        pass
    
    def insert(self, note_id: str, embedding: List[float], metadata: Dict):
        """
        插入笔记向量
        
        Args:
            note_id: 笔记 ID
            embedding: 向量嵌入
            metadata: 元数据
        """
        raise NotImplementedError("向量存储功能待实现")
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
        """
        向量相似度搜索
        
        Args:
            query_embedding: 查询向量
            top_k: 返回结果数量
            
        Returns:
            List[Dict]: 搜索结果
        """
        raise NotImplementedError("向量搜索功能待实现")
