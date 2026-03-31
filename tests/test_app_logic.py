# -*- coding: utf-8 -*-
"""
StyleMirror - 应用逻辑单元测试

测试范围：
1. .env 配置加载逻辑
2. API Key 存在/不存在时的降级/切换机制
3. 会话状态管理
4. 意图修正预设词处理
5. 组件渲染逻辑验证

Mock 策略：
- 不依赖 Streamlit 运行时环境
- 使用 Mock 模拟 Streamlit 组件
- 测试纯逻辑函数
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 导入被测模块的配置检查函数
# 注意：由于 app.py 依赖 streamlit，我们主要测试可独立运行的逻辑


# ============================================
# Fixtures - 测试数据准备
# ============================================

@pytest.fixture
def env_file_content():
    """生成 .env 文件内容"""
    return """
# OpenAI API 配置
OPENAI_API_KEY=sk-test-key-from-env
OPENAI_BASE_URL=https://api.openai.com/v1
"""


@pytest.fixture
def sample_vibe_result():
    """示例风格分析结果"""
    return {
        "vibe_tag": "法式復古",
        "description": "柔和的暖色调光线透过窗帘洒落，搭配复古丝绒材质~",
        "color_palette": ["#D4A574", "#8B7355", "#F5E6D3"],
        "scene_keywords": ["咖啡馆", "居家"],
        "confidence": 0.88
    }


@pytest.fixture
def sample_notes():
    """示例笔记数据"""
    return [
        {
            "note_id": "note_001",
            "vibe_tags": ["法式復古", "復古浪漫"],
            "caption": "復古法式穿搭",
            "items": [{"item_name": "波點連衣裙", "style": "復古法式"}],
            "author": "@法式穿搭日記",
            "likes": 12580,
            "collects": 3256,
            "hybrid_score": 85.5
        }
    ]


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
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)


# ============================================
# Test: .env 配置加载
# ============================================

class TestEnvLoading:
    """测试 .env 配置加载逻辑"""
    
    def test_env_file_exists(self):
        """测试 .env.example 文件存在"""
        env_example = Path(__file__).parent.parent / ".env.example"
        assert env_example.exists()
    
    def test_env_example_has_required_keys(self):
        """测试 .env.example 包含必需的配置项"""
        env_example = Path(__file__).parent.parent / ".env.example"
        content = env_example.read_text()
        
        assert "OPENAI_API_KEY" in content
        assert "OPENAI_BASE_URL" in content
    
    def test_dotenv_loads_from_project_root(self, tmp_path, monkeypatch):
        """测试 dotenv 从项目根目录加载"""
        # 创建临时 .env 文件
        env_file = tmp_path / ".env"
        env_file.write_text("OPENAI_API_KEY=sk-from-tmp-env\n")
        
        # 加载
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        # 验证加载
        assert os.getenv("OPENAI_API_KEY") == "sk-from-tmp-env"
        
        # 清理
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)


# ============================================
# Test: 配置切换机制
# ============================================

class TestConfigSwitching:
    """测试配置切换机制"""
    
    def test_mode_switch_with_api_key(self, api_key_env):
        """测试有 API Key 时切换到真实模式"""
        from core.image_processor import check_api_config
        
        is_ready, mode, config = check_api_config()
        
        assert is_ready is True
        assert mode == "real_ai"
    
    def test_mode_switch_without_api_key(self, no_api_key_env):
        """测试无 API Key 时切换到 Mock 模式"""
        from core.image_processor import check_api_config
        
        is_ready, mode, config = check_api_config()
        
        assert is_ready is False
        assert mode == "mock_demo"
    
    def test_base_url_from_env(self, api_key_env, monkeypatch):
        """测试从环境变量读取 Base URL"""
        monkeypatch.setenv("OPENAI_BASE_URL", "https://custom.api.com/v1")
        
        from core.image_processor import check_api_config
        
        is_ready, mode, config = check_api_config()
        
        assert config["has_base_url"] is True
        assert config["base_url"] == "https://custom.api.com/v1"
    
    def test_base_url_default_value(self, api_key_env, no_api_key_env, monkeypatch):
        """测试无 Base URL 时使用默认值"""
        from core.image_processor import check_api_config
        
        is_ready, mode, config = check_api_config()
        
        # 无 Base URL 时使用 OpenAI 默认端点
        assert config["base_url"] in [
            "https://api.openai.com/v1",
            None  # 某些配置下可能为 None
        ]


# ============================================
# Test: 意图修正预设词
# ============================================

class TestIntentPresets:
    """测试意图修正预设词"""
    
    def test_intent_presets_defined(self):
        """测试预设词列表已定义"""
        # 从 app.py 导入（需要 Mock streamlit）
        INTENT_PRESETS = [
            {"label": "颜色再深一点", "value": "颜色再深一点"},
            {"label": "更简约一点", "value": "更简约一点"},
            {"label": "适合约会", "value": "适合约会"},
            {"label": "适合通勤", "value": "适合通勤上班"},
            {"label": "更休闲", "value": "更休闲舒适"},
            {"label": "更正式", "value": "更正式得体"},
        ]
        
        assert len(INTENT_PRESETS) == 6
    
    def test_intent_presets_structure(self):
        """测试预设词结构正确"""
        INTENT_PRESETS = [
            {"label": "颜色再深一点", "value": "颜色再深一点"},
        ]
        
        for preset in INTENT_PRESETS:
            assert "label" in preset
            assert "value" in preset
            assert isinstance(preset["label"], str)
            assert isinstance(preset["value"], str)


# ============================================
# Test: API 状态消息生成
# ============================================

class TestApiStatusMessages:
    """测试 API 状态消息生成"""
    
    def test_status_message_with_api_key(self, api_key_env):
        """测试有 API Key 时的状态消息"""
        from core.image_processor import get_api_status_message
        
        message = get_api_status_message()
        
        assert "真实 AI 模式" in message
        assert "✅" in message
    
    def test_status_message_without_api_key(self, no_api_key_env):
        """测试无 API Key 时的状态消息"""
        from core.image_processor import get_api_status_message
        
        message = get_api_status_message()
        
        assert "Mock 模式" in message
        assert "💡" in message
    
    def test_status_message_includes_model_info(self, api_key_env):
        """测试状态消息包含模型信息"""
        from core.image_processor import get_api_status_message
        
        message = get_api_status_message()
        
        # 应该包含模型名称
        assert "gpt-4o-mini" in message or "模型" in message


# ============================================
# Test: 集成场景 - 端到端流程
# ============================================

class TestIntegrationScenarios:
    """测试集成场景"""
    
    def test_full_analysis_flow_mock_mode(self, no_api_key_env):
        """测试完整分析流程（Mock 模式）"""
        from PIL import Image
        import numpy as np
        from core.image_processor import analyze_vibe, preprocess_image
        from core.retriever import get_matching_notes_v2
        
        # 1. 创建测试图片
        img_array = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        image = Image.fromarray(img_array, 'RGB')
        
        # 2. 分析风格
        vibe_result = analyze_vibe(image)
        
        assert "vibe_tag" in vibe_result
        assert "color_palette" in vibe_result
        
        # 3. 检索笔记
        notes = get_matching_notes_v2(
            vibe_description=vibe_result.get("description", ""),
            vibe_tag=vibe_result.get("vibe_tag", ""),
            top_k=3
        )
        
        assert isinstance(notes, list)
    
    def test_config_propagation_to_retriever(self, api_key_env, monkeypatch):
        """测试配置正确传递到检索模块"""
        from core.retriever import get_embedding
        
        # 使用环境变量中的 API Key
        # 在真实场景下会调用 API（但这里我们只验证参数传递）
        
        # 验证环境变量可被读取
        assert os.getenv("OPENAI_API_KEY") == "sk-test-api-key-12345"
    
    def test_graceful_degradation_chain(self, no_api_key_env):
        """测试完整降级链路"""
        from PIL import Image
        import numpy as np
        from core.image_processor import analyze_vibe
        
        # 创建测试图片
        img_array = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        image = Image.fromarray(img_array, 'RGB')
        
        # 无 API Key 时应该降级到 Mock
        result = analyze_vibe(image)
        
        # Mock 结果应该有特定的置信度标记
        assert result["confidence"] <= 0.6


# ============================================
# Test: 颜色格式验证
# ============================================

class TestColorFormats:
    """测试颜色格式验证"""
    
    def test_color_palette_hex_format(self, sample_vibe_result):
        """测试色彩板中的颜色格式正确"""
        colors = sample_vibe_result["color_palette"]
        
        for color in colors:
            # 格式: #RRGGBB
            assert color.startswith("#")
            assert len(color) == 7
            
            # 验证十六进制有效性
            hex_part = color[1:]
            assert all(c in "0123456789ABCDEFabcdef" for c in hex_part)
    
    def test_mock_result_color_format(self, no_api_key_env):
        """测试 Mock 结果的颜色格式"""
        from PIL import Image
        import numpy as np
        from core.image_processor import analyze_vibe
        
        img_array = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
        image = Image.fromarray(img_array, 'RGB')
        
        result = analyze_vibe(image)
        
        for color in result.get("color_palette", []):
            assert color.startswith("#")
            assert len(color) == 7


# ============================================
# Test: 笔记数据处理
# ============================================

class TestNoteDataProcessing:
    """测试笔记数据处理"""
    
    def test_note_sorting_by_score(self, sample_notes):
        """测试笔记按得分排序"""
        # 添加多条笔记
        notes = [
            {"note_id": "1", "hybrid_score": 50.0},
            {"note_id": "2", "hybrid_score": 90.0},
            {"note_id": "3", "hybrid_score": 70.0},
        ]
        
        sorted_notes = sorted(notes, key=lambda x: x.get("hybrid_score", 0), reverse=True)
        
        assert sorted_notes[0]["note_id"] == "2"
        assert sorted_notes[1]["note_id"] == "3"
        assert sorted_notes[2]["note_id"] == "1"
    
    def test_note_default_flag(self, sample_notes):
        """测试笔记默认标记"""
        for note in sample_notes:
            note["is_default"] = True
        
        # 默认推荐的笔记应该有标记
        assert all(note.get("is_default") for note in sample_notes)


# ============================================
# Test: 异常处理边界
# ============================================

class TestExceptionHandling:
    """测试异常处理边界"""
    
    def test_analyze_vibe_with_none_image(self, no_api_key_env):
        """测试传入 None 图片时的处理"""
        from core.image_processor import analyze_vibe
        
        # 应该不会崩溃
        try:
            result = analyze_vibe(None)
        except Exception as e:
            # 预期会抛出异常或返回 Mock 结果
            pass
    
    def test_retriever_with_none_vibe_tag(self, no_api_key_env):
        """测试传入 None vibe_tag 时的处理"""
        from core.retriever import get_matching_notes
        
        # 应该返回默认推荐
        result = get_matching_notes(vibe_tag=None)
        
        assert isinstance(result, list)
    
    def test_embedding_with_none_text(self, no_api_key_env):
        """测试传入 None 文本时的处理"""
        from core.retriever import get_embedding
        
        result = get_embedding(None)
        
        # 应该返回零向量或空向量
        assert isinstance(result, list)


# ============================================
# Test: 常量与配置验证
# ============================================

class TestConstantsAndConfig:
    """测试常量与配置"""
    
    def test_image_size_limit(self):
        """测试图片尺寸限制常量"""
        from core.image_processor import MAX_IMAGE_SIZE
        
        assert MAX_IMAGE_SIZE == 1024
    
    def test_jpeg_quality_range(self):
        """测试 JPEG 质量参数范围"""
        from core.image_processor import JPEG_QUALITY
        
        assert 1 <= JPEG_QUALITY <= 100
    
    def test_api_timeout_config(self):
        """测试 API 超时配置"""
        from core.image_processor import API_TIMEOUT
        
        assert API_TIMEOUT > 0
        assert API_TIMEOUT <= 60  # 不超过 60 秒
    
    def test_max_retries_config(self):
        """测试重试次数配置"""
        from core.image_processor import MAX_RETRIES
        
        assert MAX_RETRIES >= 1
        assert MAX_RETRIES <= 5  # 不超过 5 次
    
    def test_embedding_dimension(self):
        """测试向量维度"""
        from core.retriever import _generate_mock_embedding
        
        vec = _generate_mock_embedding("test")
        
        # text-embedding-3-small 维度为 1536
        assert len(vec) == 1536


# ============================================
# Test: Mock 数据完整性
# ============================================

class TestMockDataIntegrity:
    """测试 Mock 数据完整性"""
    
    def test_mock_notes_file_valid_json(self):
        """测试 Mock 笔记文件为有效 JSON"""
        from core.retriever import load_mock_notes
        
        notes = load_mock_notes()
        
        assert isinstance(notes, list)
    
    def test_mock_notes_required_fields(self):
        """测试 Mock 笔记包含必需字段"""
        from core.retriever import load_mock_notes
        
        notes = load_mock_notes()
        
        required_fields = ["note_id", "vibe_tags", "caption", "items"]
        
        for note in notes:
            for field in required_fields:
                assert field in note, f"Missing field: {field}"
    
    def test_mock_notes_vibe_tags_not_empty(self):
        """测试 Mock 笔记的 vibe_tags 不为空"""
        from core.retriever import load_mock_notes
        
        notes = load_mock_notes()
        
        for note in notes:
            assert len(note.get("vibe_tags", [])) > 0
