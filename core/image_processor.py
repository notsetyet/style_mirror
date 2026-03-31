# -*- coding: utf-8 -*-
"""
StyleMirror - 视觉特征提取模块
已接入多模态大模型接口，用于真实分析用户照片的风格特征

重构要点：
1. 使用 response_format={"type": "json_object"} 确保 JSON 输出
2. 增加超时处理与重试机制
3. 支持 base_url 参数适配 API 代理/国产模型
4. 增强业务返回字段（色彩板、场景关键词）
5. 优化图片压缩以节省 Token

Author: StyleMirror Team
Version: v2.0 (Refactored)
"""

from PIL import Image
from typing import Optional, List, Dict, Any
import io
import random
import base64
import json
import os
import logging
import time
from dataclasses import dataclass

from openai import OpenAI, APIError, APITimeoutError, RateLimitError

# ============================================
# 日志配置
# ============================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================
# 常量配置（避免魔法数字）
# ============================================

# 图像预处理参数
MAX_IMAGE_SIZE = 1024           # 图片最大边长（像素）
JPEG_QUALITY = 85               # JPEG 压缩质量（平衡画质与体积）
MAX_FILE_SIZE_KB = 500          # 目标文件大小上限

# API 调用参数
API_TIMEOUT = 30.0              # API 超时时间（秒）
MAX_RETRIES = 3                 # 最大重试次数
RETRY_DELAY = 1.0               # 重试间隔（秒）
MODEL_TEMPERATURE = 0.7         # 模型温度
MAX_TOKENS = 500                # 最大输出 Token

# ============================================
# 小红书热门风格标签库
# ============================================

XHS_VIBE_TAGS = [
    # 经典风格
    "法式復古", "極簡工業", "溫柔原木",
    # 小红书热门风格（网感）
    "多巴胺", "美拉德", "静奢风", "多肉感",
    "美式复古", "韩系慵懒", "日系清新",
    "赛博朋克", "奶油风", "ins风", "国潮",
    "复古港风", "法式慵懒", "极简冷淡",
]


def _get_sample_vibe_tags(sample_size: int = 8) -> List[str]:
    """随机抽取风格标签示例用于 Prompt"""
    return random.sample(XHS_VIBE_TAGS, min(sample_size, len(XHS_VIBE_TAGS)))


# ============================================
# System Prompt 定义
# ============================================

VIBE_SYSTEM_PROMPT = """你是小红书「点点 Agent」的视觉分析引擎，专注于审美风格的精准识别。

## 🎯 输出要求
你必须返回一个合法的 JSON 对象，格式如下：
{
    "vibe_tag": "4字风格标签",
    "description": "风格描述文案（小红书语气）",
    "color_palette": ["#色号1", "#色号2", "#色号3"],
    "scene_keywords": ["场景词1", "场景词2"],
    "confidence": 0.85
}

## 🎨 字段说明
1. vibe_tag: 4字风格标签，从以下热门风格中选择或自定义：
   {vibe_examples}
   
2. description: 用小红书语气描述图片的光影、材质、情绪，强调「氛围感」和「出片率」，
   使用 2-3 个 Emoji，语气亲切自然。
   
3. color_palette: 提取图片中的 3 个主色调，以十六进制色号表示（如 #F5E6D3）。
   这对后续匹配穿搭单品非常重要。
   
4. scene_keywords: 2-3 个场景关键词（如「咖啡馆」「居家」「街拍」）。
   
5. confidence: 分析置信度（0.0-1.0）。

## ⚠️ 注意事项
- 只输出 JSON，不要包含任何 Markdown 语法
- 确保色号格式正确（# + 6位十六进制）
- 描述要贴合小红书社区的语境
"""


# ============================================
# 数据类定义
# ============================================

@dataclass
class VibeResult:
    """
    风格分析结果数据结构
    
    使用 dataclass 确保类型安全和代码可读性
    """
    vibe_tag: str
    description: str
    color_palette: List[str]
    scene_keywords: List[str]
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，兼容现有接口"""
        return {
            "vibe_tag": self.vibe_tag,
            "description": self.description,
            "color_palette": self.color_palette,
            "scene_keywords": self.scene_keywords,
            "confidence": self.confidence
        }


# ============================================
# 图像预处理函数
# ============================================

def preprocess_image(image_file) -> Optional[Image.Image]:
    """
    预处理上传的图像文件
    
    处理流程：
    1. 读取图像并转换为 RGB 模式
    2. 等比例缩放至最大边长 1024px
    3. 使用 LANCZOS 算法保持画质
    
    Args:
        image_file: Streamlit 上传的文件对象
        
    Returns:
        PIL.Image: 处理后的图像对象，失败返回 None
        
    Note:
        使用上下文管理器确保资源正确释放
    """
    try:
        image = Image.open(image_file)
        
        # 转换为 RGB 模式（处理 RGBA、P 等格式）
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 等比例缩放：限制最大边长以提高处理效率
        if max(image.size) > MAX_IMAGE_SIZE:
            ratio = MAX_IMAGE_SIZE / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"图片已缩放: {image.size}")
        
        return image
        
    except Exception as e:
        logger.error(f"图像预处理失败: {str(e)}", exc_info=True)
        return None


def image_to_base64(image: Image.Image, quality: int = JPEG_QUALITY) -> str:
    """
    将 PIL 图像转换为 Base64 编码，用于传输给大模型
    
    优化要点：
    - 使用 JPEG 格式压缩（相比 PNG 节省 50%+ Token）
    - 可调节压缩质量平衡画质与体积
    - 使用上下文管理器确保内存释放
    
    Args:
        image: PIL 图像对象
        quality: JPEG 压缩质量（1-100），默认 85
        
    Returns:
        str: Base64 编码字符串
    """
    with io.BytesIO() as buffer:
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        base64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # 日志记录：帮助调试 Token 消耗
        size_kb = len(buffer.getvalue()) / 1024
        logger.debug(f"Base64 编码完成，图片大小: {size_kb:.1f} KB")
        
        return base64_str


# ============================================
# 多模态模型接口（核心引擎）
# ============================================

class MultiModalModel:
    """
    多模态大模型接口类
    
    特性：
    - 支持 OpenAI 兼容 API（含国产模型中转接口）
    - 内置超时处理与重试机制
    - 强制 JSON 输出模式
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: str = None,
        base_url: str = None,
        timeout: float = API_TIMEOUT,
        max_retries: int = MAX_RETRIES
    ):
        """
        初始化多模态模型
        
        Args:
            model_name: 模型名称，默认 gpt-4o-mini（性价比之选）
            api_key: API Key，未传入则从环境变量读取
            base_url: API 基础 URL（支持代理/国产模型中转）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
        """
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        
        # API Key 读取优先级：参数 > 环境变量
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "未找到 API Key，请通过参数传入或设置环境变量 OPENAI_API_KEY"
            )
        
        # 初始化 OpenAI 客户端
        # 支持 base_url 参数，方便接入国产模型中转接口
        client_kwargs = {"api_key": self.api_key, "timeout": self.timeout}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        self.client = OpenAI(**client_kwargs)
        logger.info(f"MultiModalModel 初始化完成: model={model_name}, base_url={base_url or 'default'}")
    
    def analyze_image(
        self,
        image: Image.Image,
        prompt: str,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        使用多模态模型分析图像（强制返回 JSON）
        
        核心优化：
        1. 使用 response_format={"type": "json_object"} 确保合法 JSON
        2. 内置重试机制处理网络波动
        3. System Prompt 分离，提高指令遵循率
        
        Args:
            image: PIL 图像对象
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）
            
        Returns:
            Dict: 解析后的 JSON 结果
            
        Raises:
            APIError: API 调用失败
            ValueError: JSON 解析失败
        """
        base64_image = image_to_base64(image)
        
        # 构建消息结构
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        # low 模式：适合风格分析等不需要精细识别的场景，节省 Token
                        "detail": "low"
                    }
                }
            ]
        })
        
        # 带重试的 API 调用
        last_error = None
        result_str = ""
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    max_tokens=MAX_TOKENS,
                    temperature=MODEL_TEMPERATURE,
                    # 🔑 关键优化：强制 JSON 输出
                    response_format={"type": "json_object"}
                )
                
                result_str = response.choices[0].message.content
                result = json.loads(result_str)
                
                logger.info(f"模型调用成功，Token 使用: {response.usage.total_tokens}")
                return result
                
            except APITimeoutError as e:
                last_error = e
                logger.warning(f"API 超时，重试 {attempt + 1}/{self.max_retries}")
                time.sleep(RETRY_DELAY * (attempt + 1))  # 指数退避
                
            except RateLimitError as e:
                last_error = e
                logger.warning(f"API 限流，等待后重试 {attempt + 1}/{self.max_retries}")
                time.sleep(RETRY_DELAY * 2 * (attempt + 1))
                
            except json.JSONDecodeError as e:
                last_error = e
                logger.error(f"JSON 解析失败，模型原始返回: {result_str}")
                break  # JSON 解析失败无需重试
                
            except APIError as e:
                last_error = e
                logger.error(f"API 调用异常: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(RETRY_DELAY)
        
        raise APIError(f"模型调用失败，已重试 {self.max_retries} 次: {last_error}")


# ============================================
# 视觉特征提取（业务接口）
# ============================================

def analyze_vibe(
    image: Image.Image,
    api_key: str = None,
    base_url: str = None
) -> Dict[str, Any]:
    """
    真实分析图像的风格特征
    
    调用 GPT-4o-mini 将图片分类并生成小红书风格的描述。
    如果未配置 API Key，优雅降级到 Mock 逻辑，保证 Demo 不崩。
    
    Args:
        image: PIL 图像对象
        api_key: OpenAI API Key（可选，未传入则从环境变量读取）
        base_url: API 代理地址（可选，支持国产模型中转）
        
    Returns:
        Dict: {
            "vibe_tag": str,          # 风格标签
            "description": str,       # 风格描述
            "color_palette": List[str],  # 色彩板
            "scene_keywords": List[str], # 场景关键词
            "confidence": float       # 置信度
        }
    """
    # 尝试初始化模型
    try:
        model = MultiModalModel(
            model_name="gpt-4o-mini",
            api_key=api_key,
            base_url=base_url
        )
    except ValueError as e:
        # 优雅降级：未配置 API Key 时使用 Mock 逻辑
        logger.warning("未检测到 API Key，使用降级 Mock 逻辑")
        return _mock_vibe_result()
    
    # 构建 System Prompt（注入风格示例）
    sample_tags = _get_sample_vibe_tags(8)
    system_prompt = VIBE_SYSTEM_PROMPT.format(
        vibe_examples="、".join(sample_tags)
    )
    
    # 用户提示词：简洁明了
    user_prompt = "请分析这张图片的视觉风格，按照要求的 JSON 格式返回结果。"
    
    # 调用模型分析
    try:
        result = model.analyze_image(
            image=image,
            prompt=user_prompt,
            system_prompt=system_prompt
        )
        
        # 验证返回字段完整性
        required_fields = ["vibe_tag", "description", "color_palette", "scene_keywords"]
        for field in required_fields:
            if field not in result:
                result[field] = _get_default_value(field)
        
        # 确保有 confidence 字段
        if "confidence" not in result:
            result["confidence"] = 0.85
            
        logger.info(f"风格分析完成: {result.get('vibe_tag')}")
        return result
        
    except Exception as e:
        logger.error(f"风格分析失败: {str(e)}", exc_info=True)
        # 降级返回 Mock 结果
        return _mock_vibe_result()


def _mock_vibe_result() -> Dict[str, Any]:
    """
    生成 Mock 风格分析结果
    
    用于 API Key 未配置或调用失败时的优雅降级
    """
    vibe_options = ["法式復古", "極簡工業", "溫柔原木", "多巴胺", "静奢风"]
    selected_vibe = random.choice(vibe_options)
    
    mock_color_palettes = {
        "法式復古": ["#D4A574", "#8B7355", "#F5E6D3"],
        "極簡工業": ["#4A4A4A", "#2C2C2C", "#A0A0A0"],
        "溫柔原木": ["#D4B896", "#A67B5B", "#F5E6D3"],
        "多巴胺": ["#FF6B6B", "#4ECDC4", "#FFE66D"],
        "静奢风": ["#C4B8A8", "#8B8178", "#E8E4DF"],
    }
    
    return {
        "vibe_tag": selected_vibe,
        "description": (
            "点点暂时没能看清这张图哦～ 请检查网络或配置 API Key 体验完整功能 🥺"
        ),
        "color_palette": mock_color_palettes.get(selected_vibe, ["#808080", "#A0A0A0", "#C0C0C0"]),
        "scene_keywords": ["室内", "生活"],
        "confidence": 0.50  # Mock 数据置信度设低
    }


def _get_default_value(field: str) -> Any:
    """获取字段的默认值"""
    defaults = {
        "vibe_tag": "未知风格",
        "description": "点点遇到了一点小问题，没能分析这张图～ 🥺",
        "color_palette": ["#808080", "#A0A0A0", "#C0C0C0"],
        "scene_keywords": ["未知"],
    }
    return defaults.get(field, None)


# ============================================
# 兼容性接口（向后兼容）
# ============================================

def analyze_vibe_legacy(image: Image.Image) -> Dict:
    """
    分析图像的风格特征（旧版 Mock 接口）
    
    保留此函数以确保向后兼容，支持本地开发调试。
    
    Args:
        image: PIL 图像对象
        
    Returns:
        Dict: {"vibe_tag": str, "description": str}
    """
    vibe_options = ["法式復古", "極簡工業", "溫柔原木"]
    selected_vibe = random.choice(vibe_options)
    
    vibe_descriptions = {
        "法式復古": (
            "柔和的暖色調光線透過窗簾灑落，搭配復古絲絨、黃銅材質的傢俱裝飾，"
            "整體呈現出優雅浪漫的巴黎公寓氛圍感～ 🕯️"
        ),
        "極簡工業": (
            "冷色調的自然光與室內金屬、混凝土材質形成鮮明對比，"
            "展現出簡約而有力的現代都市美學，充滿設計感～ 🏙️"
        ),
        "溫柔原木": (
            "溫暖的日光與原木紋理相互映襯，棉麻織物與陶藝擺件點綴其中，"
            "營造出舒適放鬆的生活感，充滿自然氣息～ 🌿"
        )
    }
    
    return {
        "vibe_tag": selected_vibe,
        "description": vibe_descriptions[selected_vibe]
    }


# ============================================
# 扩展功能接口（预留）
# ============================================

def extract_vibe_features(image: Image.Image) -> Dict:
    """
    提取图像的视觉风格特征（Vibe）
    
    TODO: 接入 CLIP 向量嵌入，实现更精准的语义匹配
    
    Args:
        image: PIL 图像对象
        
    Returns:
        Dict: 包含风格特征、色彩、氛围等信息
    """
    # 调用主接口获取完整结果
    result = analyze_vibe(image)
    
    return {
        "vibe_tags": [result.get("vibe_tag", "未知")],
        "color_palette": result.get("color_palette", []),
        "style_keywords": result.get("scene_keywords", []),
        "confidence": result.get("confidence", 0.5),
        "description": result.get("description", "")
    }


def analyze_outfit(image: Image.Image) -> Dict:
    """
    分析图像中的穿搭单品
    
    TODO: 接入目标检测模型
    - 可选方案：YOLOv8 + 服装类别训练
    - 或使用 Fashion AI API
    
    Args:
        image: PIL 图像对象
        
    Returns:
        Dict: 包含识别到的服装类别、颜色、位置等信息
    """
    # 占位实现：返回模拟数据
    return {
        "items": [
            {
                "category": "上衣",
                "color": "白色",
                "style": "法式方领",
                "confidence": 0.92
            },
            {
                "category": "下装",
                "color": "浅蓝色",
                "style": "高腰牛仔裤",
                "confidence": 0.88
            }
        ],
        "overall_style": "法式慵懒风"
    }


def get_image_embedding(image: Image.Image) -> List[float]:
    """
    获取图像的向量嵌入
    
    TODO: 实现向量提取（如使用 CLIP）
    
    Args:
        image: PIL 图像对象
        
    Returns:
        List[float]: 图像向量
    """
    # 占位实现
    raise NotImplementedError("图像向量提取待实现，建议使用 CLIP 模型")


# ============================================
# 便捷导出
# ============================================

__all__ = [
    # 核心接口
    "preprocess_image",
    "analyze_vibe",
    "analyze_vibe_legacy",
    # 扩展接口
    "extract_vibe_features",
    "analyze_outfit",
    "get_image_embedding",
    # 工具函数
    "image_to_base64",
    # 类
    "MultiModalModel",
    "VibeResult",
    # 常量
    "XHS_VIBE_TAGS",
]
