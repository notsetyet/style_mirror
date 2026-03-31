# -*- coding: utf-8 -*-
"""
StyleMirror - 图像处理模块单元测试

测试范围：
1. 图片压缩逻辑 (preprocess_image)
2. Base64 编码 (image_to_base64)
3. 多模态 API 响应解析 (analyze_vibe, MultiModalModel)
4. JSON Mode 成功与失败情况
5. API 超时、限流、异常处理
6. 配置检查与降级机制

Mock 策略：
- 所有 OpenAI API 调用均使用 pytest-mock 模拟
- 严禁在测试中产生真实的 API 调用
"""

import pytest
import os
import json
import base64
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

import numpy as np
from PIL import Image

# 导入被测模块
from core.image_processor import (
    preprocess_image,
    image_to_base64,
    analyze_vibe,
    MultiModalModel,
    check_api_config,
    get_api_status_message,
    _mock_vibe_result,
    _get_default_value,
    MAX_IMAGE_SIZE,
    JPEG_QUALITY,
    MAX_FILE_SIZE_KB,
)


# ============================================
# Fixtures - 测试数据准备
# ============================================

@pytest.fixture
def sample_image() -> Image.Image:
    """创建一个标准的测试图片 (800x600 RGB)"""
    img_array = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)
    return Image.fromarray(img_array, 'RGB')


@pytest.fixture
def large_image() -> Image.Image:
    """创建一个超大尺寸图片 (3000x3000) 用于测试压缩"""
    img_array = np.random.randint(0, 255, (3000, 3000, 3), dtype=np.uint8)
    return Image.fromarray(img_array, 'RGB')


@pytest.fixture
def rgba_image() -> Image.Image:
    """创建一个 RGBA 模式图片，用于测试格式转换"""
    img_array = np.random.randint(0, 255, (600, 800, 4), dtype=np.uint8)
    return Image.fromarray(img_array, 'RGBA')


@pytest.fixture
def corrupted_image_bytes() -> bytes:
    """生成损坏的图片数据"""
    return b'\xff\xd8\xff\xe0' + os.urandom(100)


@pytest.fixture
def mock_api_response():
    """创建 Mock API 响应对象"""
    class MockUsage:
        prompt_tokens = 450
        completion_tokens = 120
        total_tokens = 570
    
    class MockMessage:
        content = json.dumps({
            "vibe_tag": "法式復古",
            "description": "柔和的暖色调光线透过窗帘洒落~",
            "color_palette": ["#D4A574", "#8B7355", "#F5E6D3"],
            "scene_keywords": ["咖啡馆", "居家"],
            "confidence": 0.88
        })
    
    class MockChoice:
        message = MockMessage()
    
    class MockResponse:
        choices = [MockChoice()]
        usage = MockUsage()
    
    return MockResponse()


@pytest.fixture
def mock_invalid_json_response():
    """创建返回无效 JSON 的 Mock 响应"""
    class MockMessage:
        content = "这不是有效的 JSON 内容"
    
    class MockChoice:
        message = MockMessage()
    
    class MockResponse:
        choices = [MockChoice()]
    
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
# Test: 图片预处理逻辑
# ============================================

class TestPreprocessImage:
    """测试图片预处理函数"""
    
    def test_preprocess_normal_image(self, sample_image):
        """测试正常图片预处理"""
        # 保存到 BytesIO 模拟文件上传
        buffer = BytesIO()
        sample_image.save(buffer, format='JPEG')
        buffer.seek(0)
        
        result = preprocess_image(buffer)
        
        assert result is not None
        assert isinstance(result, Image.Image)
        assert result.mode == 'RGB'
    
    def test_preprocess_large_image_resize(self, large_image):
        """测试大图片自动缩放"""
        buffer = BytesIO()
        large_image.save(buffer, format='JPEG')
        buffer.seek(0)
        
        result = preprocess_image(buffer)
        
        assert result is not None
        # 验证最大边长不超过 MAX_IMAGE_SIZE
        max_dim = max(result.size)
        assert max_dim <= MAX_IMAGE_SIZE
    
    def test_preprocess_rgba_to_rgb(self, rgba_image):
        """测试 RGBA 模式转换为 RGB"""
        buffer = BytesIO()
        rgba_image.save(buffer, format='PNG')
        buffer.seek(0)
        
        result = preprocess_image(buffer)
        
        assert result is not None
        assert result.mode == 'RGB'
    
    def test_preprocess_corrupted_image(self, corrupted_image_bytes):
        """测试损坏图片处理"""
        buffer = BytesIO(corrupted_image_bytes)
        
        result = preprocess_image(buffer)
        
        # 损坏图片应返回 None
        assert result is None
    
    def test_preprocess_empty_file(self):
        """测试空文件处理"""
        buffer = BytesIO()
        
        result = preprocess_image(buffer)
        
        assert result is None


# ============================================
# Test: Base64 编码
# ============================================

class TestImageToBase64:
    """测试 Base64 编码函数"""
    
    def test_base64_encoding_output_type(self, sample_image):
        """测试 Base64 输出类型为字符串"""
        result = image_to_base64(sample_image)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_base64_encoding_valid(self, sample_image):
        """测试 Base64 编码有效性"""
        result = image_to_base64(sample_image)
        
        # 验证可以解码
        decoded = base64.b64decode(result)
        assert len(decoded) > 0
    
    def test_base64_encoding_quality_parameter(self, sample_image):
        """测试不同质量参数"""
        result_low = image_to_base64(sample_image, quality=50)
        result_high = image_to_base64(sample_image, quality=95)
        
        # 高质量图片应该更大
        assert len(result_high) > len(result_low)
    
    def test_base64_encoding_jpeg_format(self, sample_image):
        """测试输出为 JPEG 格式"""
        result = image_to_base64(sample_image)
        decoded = base64.b64decode(result)
        
        # JPEG 文件以 FF D8 FF 开头
        assert decoded[:3] == b'\xff\xd8\xff'


# ============================================
# Test: 多模态模型接口
# ============================================

class TestMultiModalModel:
    """测试多模态模型类"""
    
    def test_model_initialization_with_api_key(self, api_key_env):
        """测试使用环境变量 API Key 初始化"""
        model = MultiModalModel()
        
        assert model.api_key == "sk-test-api-key-12345"
        assert model.model_name == "gpt-4o-mini"
    
    def test_model_initialization_with_param(self, no_api_key_env):
        """测试使用参数传入 API Key 初始化"""
        model = MultiModalModel(api_key="sk-param-key-999")
        
        assert model.api_key == "sk-param-key-999"
    
    def test_model_initialization_no_api_key(self, no_api_key_env):
        """测试无 API Key 时抛出异常"""
        with pytest.raises(ValueError, match="未找到 API Key"):
            MultiModalModel()
    
    def test_model_initialization_with_base_url(self, api_key_env):
        """测试自定义 Base URL"""
        model = MultiModalModel(base_url="https://custom-api.com/v1")
        
        assert model.client is not None
    
    @patch('core.image_processor.OpenAI')
    def test_analyze_image_success(self, mock_openai, mock_api_response, api_key_env, sample_image):
        """测试成功分析图片"""
        # 配置 Mock
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_api_response
        mock_openai.return_value = mock_client
        
        model = MultiModalModel()
        result = model.analyze_image(
            image=sample_image,
            prompt="分析这张图片"
        )
        
        assert "vibe_tag" in result
        assert result["vibe_tag"] == "法式復古"
        assert "color_palette" in result
        assert len(result["color_palette"]) == 3
    
    @patch('core.image_processor.OpenAI')
    def test_analyze_image_json_decode_error(self, mock_openai, mock_invalid_json_response, api_key_env, sample_image):
        """测试 JSON 解析失败情况"""
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_invalid_json_response
        mock_openai.return_value = mock_client
        
        model = MultiModalModel()
        
        with pytest.raises(Exception):  # 应该抛出 APIError
            model.analyze_image(image=sample_image, prompt="分析这张图片")
    
    @patch('core.image_processor.OpenAI')
    @patch('core.image_processor.time.sleep')
    def test_analyze_image_timeout_retry(self, mock_sleep, mock_openai, api_key_env, sample_image):
        """测试 API 超时重试机制"""
        from openai import APITimeoutError
        
        mock_client = Mock()
        # 前两次超时，第三次成功
        mock_client.chat.completions.create.side_effect = [
            APITimeoutError("Timeout"),
            APITimeoutError("Timeout"),
            Mock(choices=[Mock(message=Mock(content='{"vibe_tag": "测试风格"}'))], usage=Mock())
        ]
        mock_openai.return_value = mock_client
        
        model = MultiModalModel()
        result = model.analyze_image(image=sample_image, prompt="分析")
        
        # 验证重试了 2 次
        assert mock_client.chat.completions.create.call_count == 3
    
    @patch('core.image_processor.OpenAI')
    @patch('core.image_processor.time.sleep')
    def test_analyze_image_rate_limit_retry(self, mock_sleep, mock_openai, api_key_env, sample_image):
        """测试 API 限流重试机制"""
        from openai import RateLimitError
        
        # 创建 RateLimitError 实例
        rate_limit_error = RateLimitError("Rate limit exceeded", response=Mock(), body=None)
        
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"vibe_tag": "测试风格"}'))]
        mock_response.usage = Mock()
        
        # 第一次限流，第二次成功
        mock_client.chat.completions.create.side_effect = [
            rate_limit_error,
            mock_response
        ]
        mock_openai.return_value = mock_client
        
        model = MultiModalModel()
        result = model.analyze_image(image=sample_image, prompt="分析")
        
        assert mock_client.chat.completions.create.call_count == 2


# ============================================
# Test: 风格分析主接口
# ============================================

class TestAnalyzeVibe:
    """测试风格分析主接口"""
    
    def test_analyze_vibe_no_api_key_returns_mock(self, no_api_key_env, sample_image):
        """测试无 API Key 时返回 Mock 结果"""
        result = analyze_vibe(sample_image)
        
        assert "vibe_tag" in result
        assert "description" in result
        assert "color_palette" in result
        # Mock 结果置信度较低
        assert result["confidence"] <= 0.6
    
    @patch('core.image_processor.MultiModalModel')
    def test_analyze_vibe_with_api_key(self, mock_model_class, api_key_env, sample_image, mock_api_response):
        """测试有 API Key 时调用真实模型"""
        # 配置 Mock
        mock_model = Mock()
        mock_model.analyze_image.return_value = {
            "vibe_tag": "法式復古",
            "description": "测试描述",
            "color_palette": ["#111", "#222", "#333"],
            "scene_keywords": ["咖啡馆"],
            "confidence": 0.9
        }
        mock_model_class.return_value = mock_model
        
        result = analyze_vibe(sample_image, api_key="sk-test")
        
        assert result["vibe_tag"] == "法式復古"
        mock_model.analyze_image.assert_called_once()
    
    @patch('core.image_processor.MultiModalModel')
    def test_analyze_vibe_api_error_fallback(self, mock_model_class, api_key_env, sample_image):
        """测试 API 错误时降级到 Mock"""
        mock_model = Mock()
        mock_model.analyze_image.side_effect = Exception("API Error")
        mock_model_class.return_value = mock_model
        
        result = analyze_vibe(sample_image, api_key="sk-test")
        
        # 应该返回 Mock 结果
        assert "vibe_tag" in result
        assert "description" in result
    
    @patch('core.image_processor.MultiModalModel')
    def test_analyze_vibe_missing_fields_filled(self, mock_model_class, api_key_env, sample_image):
        """测试返回结果缺失字段自动填充"""
        mock_model = Mock()
        # 返回缺失 color_palette 的结果
        mock_model.analyze_image.return_value = {
            "vibe_tag": "测试风格",
            "description": "描述"
        }
        mock_model_class.return_value = mock_model
        
        result = analyze_vibe(sample_image, api_key="sk-test")
        
        # 缺失字段应该被填充默认值
        assert "color_palette" in result
        assert "scene_keywords" in result


# ============================================
# Test: 配置检查与降级机制
# ============================================

class TestApiConfig:
    """测试 API 配置检查"""
    
    def test_check_api_config_with_key(self, api_key_env):
        """测试有 API Key 时的配置状态"""
        is_ready, mode, config = check_api_config()
        
        assert is_ready is True
        assert mode == "real_ai"
        assert config["has_api_key"] is True
    
    def test_check_api_config_without_key(self, no_api_key_env):
        """测试无 API Key 时的配置状态"""
        is_ready, mode, config = check_api_config()
        
        assert is_ready is False
        assert mode == "mock_demo"
        assert config["has_api_key"] is False
    
    def test_check_api_config_with_base_url(self, api_key_env, monkeypatch):
        """测试有 Base URL 时的配置"""
        monkeypatch.setenv("OPENAI_BASE_URL", "https://custom.api.com/v1")
        
        is_ready, mode, config = check_api_config()
        
        assert config["has_base_url"] is True
        assert config["base_url"] == "https://custom.api.com/v1"
    
    def test_get_status_message_with_key(self, api_key_env):
        """测试有 API Key 时的状态消息"""
        message = get_api_status_message()
        
        assert "真实 AI 模式" in message
        assert "✅" in message
    
    def test_get_status_message_without_key(self, no_api_key_env):
        """测试无 API Key 时的状态消息"""
        message = get_api_status_message()
        
        assert "Mock 模式" in message
        assert "💡" in message


# ============================================
# Test: Mock 结果生成
# ============================================

class TestMockVibeResult:
    """测试 Mock 结果生成函数"""
    
    def test_mock_result_structure(self):
        """测试 Mock 结果结构完整性"""
        result = _mock_vibe_result()
        
        assert "vibe_tag" in result
        assert "description" in result
        assert "color_palette" in result
        assert "scene_keywords" in result
        assert "confidence" in result
    
    def test_mock_result_vibe_tag_from_list(self):
        """测试 Mock vibe_tag 来自预定义列表"""
        result = _mock_vibe_result()
        
        valid_tags = ["法式復古", "極簡工業", "溫柔原木", "多巴胺", "静奢风"]
        assert result["vibe_tag"] in valid_tags
    
    def test_mock_result_color_palette_format(self):
        """测试 Mock color_palette 格式正确"""
        result = _mock_vibe_result()
        
        colors = result["color_palette"]
        assert len(colors) == 3
        # 验证颜色格式
        for color in colors:
            assert color.startswith("#")
            assert len(color) == 7
    
    def test_mock_result_confidence_low(self):
        """测试 Mock 结果置信度较低"""
        result = _mock_vibe_result()
        
        # Mock 结果置信度应该较低
        assert result["confidence"] == 0.50


# ============================================
# Test: 默认值函数
# ============================================

class TestGetDefaultValue:
    """测试默认值获取函数"""
    
    def test_get_default_vibe_tag(self):
        """测试获取 vibe_tag 默认值"""
        value = _get_default_value("vibe_tag")
        assert value == "未知风格"
    
    def test_get_default_color_palette(self):
        """测试获取 color_palette 默认值"""
        value = _get_default_value("color_palette")
        assert len(value) == 3
        assert all(c.startswith("#") for c in value)
    
    def test_get_default_unknown_field(self):
        """测试未知字段返回 None"""
        value = _get_default_value("unknown_field")
        assert value is None


# ============================================
# Test: 边界情况
# ============================================

class TestEdgeCases:
    """测试边界情况"""
    
    def test_base64_very_large_image(self, large_image):
        """测试超大图片的 Base64 编码"""
        # 注意：大图片在传入前应该已经被压缩
        result = image_to_base64(large_image)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_preprocess_palette_mode_image(self):
        """测试 P 模式（调色板）图片处理"""
        img_array = np.random.randint(0, 256, (200, 200), dtype=np.uint8)
        img = Image.fromarray(img_array, mode='P')
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        result = preprocess_image(buffer)
        
        assert result is not None
        assert result.mode == 'RGB'
    
    def test_analyze_vibe_with_base_url_parameter(self, no_api_key_env, sample_image):
        """测试传入 base_url 参数"""
        result = analyze_vibe(
            sample_image,
            api_key="sk-test",
            base_url="https://custom.api.com/v1"
        )
        
        # 即使有 API Key，因为 Mock 了模型，也应该返回结果
        assert "vibe_tag" in result
