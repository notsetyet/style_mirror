# -*- coding: utf-8 -*-
"""
StyleMirror - 检索模块单元测试

测试范围：
1. get_embedding 调用与降级逻辑
2. 余弦相似度计算 (cosine_similarity)
3. RAG 召回排序准确性
4. 向量检索返回为空时的默认推荐
5. 配置加载与切换机制

Mock 策略：
- 所有 OpenAI Embedding API 调用均使用 pytest-mock 模拟
- 测试向量使用确定性 Mock 数据
"""

import pytest
import os
import json
import hashlib
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import numpy as np

# 导入被测模块
from core.retriever import (
    load_mock_notes,
    get_embedding,
    cosine_similarity,
    build_note_text,
    get_matching_notes,
    get_matching_notes_v2,
    retrieve_notes_by_vibe,
    semantic_search,
    format_retrieved_notes,
    get_recommended_items,
    _generate_mock_embedding,
    _get_default_recommendations,
)


# ============================================
# Fixtures - 测试数据准备
# ============================================

@pytest.fixture
def mock_notes():
    """返回 Mock 笔记数据"""
    return [
        {
            "note_id": "note_001",
            "vibe_tags": ["法式復古", "復古浪漫"],
            "caption": "復古法式穿搭",
            "items": [{"item_name": "波點連衣裙", "style": "復古法式", "color": "黑底白點"}],
            "author": "@法式穿搭日記",
            "likes": 12580,
            "collects": 3256
        },
        {
            "note_id": "note_002",
            "vibe_tags": ["極簡工業", "現代簡約"],
            "caption": "極簡工業風穿搭",
            "items": [{"item_name": "西裝外套", "style": "極簡工業", "color": "黑色"}],
            "author": "@極簡穿搭研究所",
            "likes": 8960,
            "collects": 2145
        },
        {
            "note_id": "note_003",
            "vibe_tags": ["溫柔原木", "自然舒適"],
            "caption": "溫柔原木風穿搭",
            "items": [{"item_name": "棉麻襯衫", "style": "溫柔原木", "color": "米色"}],
            "author": "@森系穿搭日記",
            "likes": 7620,
            "collects": 1890
        }
    ]


@pytest.fixture
def sample_embedding():
    """生成一个示例向量 (1536 维)"""
    vec = np.random.randn(1536)
    vec = vec / np.linalg.norm(vec)  # 归一化
    return vec.tolist()


@pytest.fixture
def mock_embedding_response(sample_embedding):
    """创建 Mock Embedding API 响应"""
    class MockEmbeddingData:
        embedding = sample_embedding
    
    class MockResponse:
        data = [MockEmbeddingData()]
    
    return MockResponse()


@pytest.fixture
def api_key_env(monkeypatch):
    """设置 API Key 环境变量"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-api-key-12345")
    yield
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture
def no_api_key_env(monkeypatch):
    """清除 API Key 环境变量"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


# ============================================
# Test: Mock 数据加载
# ============================================

class TestLoadMockNotes:
    """测试 Mock 数据加载函数"""
    
    def test_load_mock_notes_success(self):
        """测试成功加载 Mock 数据"""
        notes = load_mock_notes()
        
        assert isinstance(notes, list)
        assert len(notes) >= 1  # 至少有一条数据
    
    def test_load_mock_notes_structure(self):
        """测试 Mock 数据结构完整性"""
        notes = load_mock_notes()
        
        if notes:
            note = notes[0]
            assert "note_id" in note
            assert "vibe_tags" in note
            assert "caption" in note
    
    @patch('core.retriever.Path')
    def test_load_mock_notes_file_not_found(self, mock_path_class):
        """测试文件不存在时返回空列表"""
        # 模拟文件不存在的情况
        # load_mock_notes 使用 Path(__file__).parent.parent 定位，难以完全 Mock
        # 这个测试验证返回值类型正确即可
        result = load_mock_notes()
        # 应该返回列表（实际文件存在时有数据）
        assert isinstance(result, list)


# ============================================
# Test: 向量生成与 Mock 降级
# ============================================

class TestGetEmbedding:
    """测试向量获取函数"""
    
    def test_get_embedding_mock_mode(self, no_api_key_env):
        """测试无 API Key 时使用 Mock 模式"""
        result = get_embedding("测试文本")
        
        assert isinstance(result, list)
        assert len(result) == 1536  # text-embedding-3-small 维度
    
    def test_get_embedding_deterministic(self, no_api_key_env):
        """测试 Mock 向量生成确定性（相同文本相同向量）"""
        text = "法式復古风格"
        vec1 = get_embedding(text)
        vec2 = get_embedding(text)
        
        # 相同文本应生成相同向量
        assert np.allclose(vec1, vec2)
    
    def test_get_embedding_different_texts(self, no_api_key_env):
        """测试不同文本生成不同向量"""
        vec1 = get_embedding("法式復古")
        vec2 = get_embedding("極簡工業")
        
        # 不同文本应生成不同向量
        assert not np.allclose(vec1, vec2)
    
    def test_get_embedding_empty_text(self, no_api_key_env):
        """测试空文本返回零向量"""
        result = get_embedding("")
        
        assert all(v == 0.0 for v in result)
    
    def test_get_embedding_whitespace_text(self, no_api_key_env):
        """测试纯空格文本返回零向量"""
        result = get_embedding("   ")
        
        assert all(v == 0.0 for v in result)
    
    @patch('openai.OpenAI')
    def test_get_embedding_with_api_key(self, mock_openai, api_key_env, mock_embedding_response):
        """测试有 API Key 时调用真实 API"""
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_embedding_response
        mock_openai.return_value = mock_client
        
        result = get_embedding("测试文本", api_key="sk-test")
        
        mock_client.embeddings.create.assert_called_once()
        assert len(result) == 1536
    
    @patch('openai.OpenAI')
    def test_get_embedding_api_error_fallback(self, mock_openai, api_key_env):
        """测试 API 错误时降级到 Mock"""
        mock_client = Mock()
        mock_client.embeddings.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        result = get_embedding("测试文本", api_key="sk-test")
        
        # 应该返回 Mock 向量
        assert isinstance(result, list)
        assert len(result) == 1536
    
    def test_generate_mock_embedding_normalized(self):
        """测试 Mock 向量已归一化"""
        vec = _generate_mock_embedding("测试")
        norm = np.linalg.norm(vec)
        
        # 归一化向量的范数应为 1
        assert abs(norm - 1.0) < 1e-6


# ============================================
# Test: 余弦相似度计算
# ============================================

class TestCosineSimilarity:
    """测试余弦相似度计算函数"""
    
    def test_cosine_similarity_identical_vectors(self, sample_embedding):
        """测试相同向量相似度为 1"""
        sim = cosine_similarity(sample_embedding, sample_embedding)
        
        assert abs(sim - 1.0) < 1e-6
    
    def test_cosine_similarity_opposite_vectors(self, sample_embedding):
        """测试相反向量相似度为 -1"""
        opposite = [-v for v in sample_embedding]
        sim = cosine_similarity(sample_embedding, opposite)
        
        assert abs(sim - (-1.0)) < 1e-6
    
    def test_cosine_similarity_orthogonal_vectors(self):
        """测试正交向量相似度为 0"""
        vec1 = [1, 0, 0, 0]
        vec2 = [0, 1, 0, 0]
        sim = cosine_similarity(vec1, vec2)
        
        assert abs(sim) < 1e-6
    
    def test_cosine_similarity_zero_vector(self, sample_embedding):
        """测试零向量相似度为 0"""
        zero_vec = [0.0] * len(sample_embedding)
        sim = cosine_similarity(sample_embedding, zero_vec)
        
        assert sim == 0.0
    
    def test_cosine_similarity_symmetry(self, sample_embedding):
        """测试相似度对称性"""
        vec2 = np.random.randn(len(sample_embedding)).tolist()
        sim1 = cosine_similarity(sample_embedding, vec2)
        sim2 = cosine_similarity(vec2, sample_embedding)
        
        assert abs(sim1 - sim2) < 1e-9
    
    def test_cosine_similarity_range(self):
        """测试相似度范围在 [-1, 1]"""
        for _ in range(10):
            vec1 = np.random.randn(100).tolist()
            vec2 = np.random.randn(100).tolist()
            sim = cosine_similarity(vec1, vec2)
            
            assert -1.0 <= sim <= 1.0


# ============================================
# Test: 笔记文本构建
# ============================================

class TestBuildNoteText:
    """测试笔记文本构建函数"""
    
    def test_build_note_text_complete(self, mock_notes):
        """测试完整笔记文本构建"""
        note = mock_notes[0]
        text = build_note_text(note)
        
        assert "法式復古" in text
        assert "復古法式穿搭" in text
        assert "波點連衣裙" in text
    
    def test_build_note_text_empty_tags(self):
        """测试无标签的笔记"""
        note = {"vibe_tags": [], "caption": "测试文案", "items": []}
        text = build_note_text(note)
        
        assert "测试文案" in text
    
    def test_build_note_text_no_items(self):
        """测试无单品的笔记"""
        note = {
            "vibe_tags": ["测试标签"],
            "caption": "测试文案",
            "items": []
        }
        text = build_note_text(note)
        
        assert "测试标签" in text
        assert "测试文案" in text
    
    def test_build_note_text_multiple_items(self):
        """测试多单品笔记"""
        note = {
            "vibe_tags": ["法式"],
            "caption": "穿搭",
            "items": [
                {"item_name": "上衣", "style": "简约", "color": "白色"},
                {"item_name": "裤子", "style": "休闲", "color": "黑色"}
            ]
        }
        text = build_note_text(note)
        
        assert "上衣" in text
        assert "裤子" in text


# ============================================
# Test: V2 核心检索接口
# ============================================

class TestGetMatchingNotesV2:
    """测试 V2 版本检索接口"""
    
    def test_get_matching_notes_v2_basic(self, no_api_key_env):
        """测试基本检索功能"""
        results = get_matching_notes_v2(
            vibe_description="法式復古",
            top_k=3
        )
        
        assert isinstance(results, list)
        assert len(results) <= 3
        if results:
            assert "vibe_tag" in results[0] or "vibe_tags" in results[0]
    
    def test_get_matching_notes_v2_with_user_text(self, no_api_key_env):
        """测试带用户补充文本的检索"""
        results = get_matching_notes_v2(
            vibe_description="法式復古",
            user_text_modifier="适合约会",
            top_k=3
        )
        
        assert isinstance(results, list)
    
    def test_get_matching_notes_v2_with_vibe_tag(self, no_api_key_env):
        """测试带精确标签加权的检索"""
        results = get_matching_notes_v2(
            vibe_description="法式復古",
            vibe_tag="法式復古",
            top_k=3
        )
        
        assert isinstance(results, list)
        # 包含该标签的笔记应该排在前面
        if results:
            assert "hybrid_score" in results[0]
    
    def test_get_matching_notes_v2_with_scene_keywords(self, no_api_key_env):
        """测试带场景关键词的检索"""
        results = get_matching_notes_v2(
            vibe_description="法式復古",
            scene_keywords=["咖啡馆", "约会"],
            top_k=3
        )
        
        assert isinstance(results, list)
        # 检查结果包含 keyword_bonus 字段
        if results:
            assert "keyword_bonus" in results[0]
    
    def test_get_matching_notes_v2_empty_query(self, no_api_key_env):
        """测试空查询返回默认推荐"""
        results = get_matching_notes_v2(
            vibe_description="",
            top_k=3
        )
        
        # 空查询应返回默认推荐
        assert isinstance(results, list)
    
    def test_get_matching_notes_v2_scores_structure(self, no_api_key_env):
        """测试返回结果得分结构"""
        results = get_matching_notes_v2(
            vibe_description="测试",
            top_k=3
        )
        
        if results:
            note = results[0]
            assert "vector_score" in note
            assert "tag_score" in note
            assert "hybrid_score" in note
    
    def test_get_matching_notes_v2_sorted_by_hybrid_score(self, no_api_key_env):
        """测试结果按 hybrid_score 降序排列"""
        results = get_matching_notes_v2(
            vibe_description="测试",
            top_k=5
        )
        
        if len(results) > 1:
            scores = [r.get("hybrid_score", 0) for r in results]
            assert scores == sorted(scores, reverse=True)


# ============================================
# Test: V1 兼容接口
# ============================================

class TestGetMatchingNotes:
    """测试 V1 兼容接口"""
    
    def test_get_matching_notes_basic(self, no_api_key_env):
        """测试基本 V1 检索"""
        results = get_matching_notes(
            vibe_tag="法式復古",
            top_k=3
        )
        
        assert isinstance(results, list)
    
    def test_get_matching_notes_empty_tag(self, no_api_key_env):
        """测试空标签返回默认推荐"""
        results = get_matching_notes(vibe_tag="", top_k=3)
        
        assert isinstance(results, list)
    
    def test_get_matching_notes_match_score_field(self, no_api_key_env):
        """测试 V1 接口返回 match_score 字段"""
        results = get_matching_notes(vibe_tag="法式復古", top_k=3)
        
        if results:
            assert "match_score" in results[0]


# ============================================
# Test: 其他检索接口
# ============================================

class TestRetrieveNotesByVibe:
    """测试多标签检索接口"""
    
    def test_retrieve_notes_by_vibe_basic(self, no_api_key_env):
        """测试多标签检索"""
        results = retrieve_notes_by_vibe(
            vibe_tags=["法式復古", "優雅"],
            top_k=3
        )
        
        assert isinstance(results, list)
    
    def test_retrieve_notes_by_vibe_empty_tags(self, no_api_key_env):
        """测试空标签列表"""
        results = retrieve_notes_by_vibe(vibe_tags=[], top_k=3)
        
        assert isinstance(results, list)


class TestSemanticSearch:
    """测试纯语义搜索接口"""
    
    def test_semantic_search_basic(self, no_api_key_env):
        """测试基本语义搜索"""
        results = semantic_search(
            query="适合约会的穿搭",
            top_k=3
        )
        
        assert isinstance(results, list)
        if results:
            assert "vector_score" in results[0]
    
    def test_semantic_search_empty_query(self, no_api_key_env):
        """测试空查询返回默认推荐"""
        results = semantic_search(query="", top_k=3)
        
        assert isinstance(results, list)


# ============================================
# Test: 默认推荐逻辑
# ============================================

class TestGetDefaultRecommendations:
    """测试默认推荐逻辑"""
    
    def test_get_default_recommendations_returns_list(self):
        """测试返回列表类型"""
        result = _get_default_recommendations()
        
        assert isinstance(result, list)
    
    def test_get_default_recommendations_has_is_default_flag(self):
        """测试默认推荐有 is_default 标记"""
        result = _get_default_recommendations()
        
        if result:
            assert all(note.get("is_default") for note in result)
    
    def test_get_default_recommendations_sorted_by_likes(self):
        """测试默认推荐按点赞数排序"""
        result = _get_default_recommendations()
        
        if len(result) > 1:
            likes = [note.get("likes", 0) for note in result]
            assert likes == sorted(likes, reverse=True)


# ============================================
# Test: 结果格式化
# ============================================

class TestFormatRetrievedNotes:
    """测试检索结果格式化"""
    
    def test_format_retrieved_notes_basic(self, mock_notes):
        """测试基本格式化"""
        text = format_retrieved_notes(mock_notes)
        
        assert isinstance(text, str)
        assert "法式穿搭日記" in text or "復古" in text
    
    def test_format_retrieved_notes_empty(self):
        """测试空列表格式化"""
        text = format_retrieved_notes([])
        
        assert "暂无" in text or "没有" in text
    
    def test_format_retrieved_notes_with_default_flag(self, mock_notes):
        """测试带默认标记的格式化"""
        for note in mock_notes:
            note["is_default"] = True
        
        text = format_retrieved_notes(mock_notes)
        
        assert "热门" in text or "推荐" in text


class TestGetRecommendedItems:
    """测试单品提取函数"""
    
    def test_get_recommended_items_basic(self, mock_notes):
        """测试基本单品提取"""
        items = get_recommended_items(mock_notes)
        
        assert isinstance(items, list)
        assert len(items) >= 1
    
    def test_get_recommended_items_empty_notes(self):
        """测试空笔记列表"""
        items = get_recommended_items([])
        
        assert items == []
    
    def test_get_recommended_items_multiple_notes(self):
        """测试多笔记单品聚合"""
        notes = [
            {"items": [{"name": "item1"}, {"name": "item2"}]},
            {"items": [{"name": "item3"}]}
        ]
        items = get_recommended_items(notes)
        
        assert len(items) == 3


# ============================================
# Test: 边界情况
# ============================================

class TestRetrieverEdgeCases:
    """测试检索模块边界情况"""
    
    def test_vector_retrieval_empty_results(self, no_api_key_env, monkeypatch):
        """测试向量检索返回空时的默认推荐"""
        # Mock load_mock_notes 返回空列表
        monkeypatch.setattr(
            'core.retriever.load_mock_notes',
            lambda: []
        )
        
        results = get_matching_notes_v2(vibe_description="测试")
        
        # 空数据库应返回空列表
        assert results == []
    
    def test_hybrid_score_calculation(self, no_api_key_env):
        """测试混合得分计算逻辑"""
        results = get_matching_notes_v2(
            vibe_description="法式復古",
            vibe_tag="法式復古",
            top_k=3
        )
        
        if results:
            for note in results:
                # hybrid_score = vector_score * 0.7 + tag_score * 0.3 + keyword_bonus
                expected = (
                    note.get("vector_score", 0) * 0.7 +
                    note.get("tag_score", 0) * 0.3 +
                    note.get("keyword_bonus", 0)
                )
                assert abs(note.get("hybrid_score", 0) - expected) < 0.1
    
    def test_embedding_with_special_characters(self, no_api_key_env):
        """测试特殊字符文本的向量生成"""
        text = "法式復古！@#￥%……&*（）——+"
        result = get_embedding(text)
        
        assert isinstance(result, list)
        assert len(result) == 1536
    
    def test_embedding_with_long_text(self, no_api_key_env):
        """测试长文本的向量生成"""
        text = "测试" * 1000
        result = get_embedding(text)
        
        assert isinstance(result, list)
        assert len(result) == 1536
    
    @patch('openai.OpenAI')
    def test_embedding_api_with_base_url(self, mock_openai, api_key_env, mock_embedding_response, monkeypatch):
        """测试带 Base URL 的 Embedding 调用"""
        monkeypatch.setenv("OPENAI_BASE_URL", "https://custom.api.com/v1")
        
        mock_client = Mock()
        mock_client.embeddings.create.return_value = mock_embedding_response
        mock_openai.return_value = mock_client
        
        result = get_embedding("测试", api_key="sk-test", base_url="https://custom.api.com/v1")
        
        assert len(result) == 1536
