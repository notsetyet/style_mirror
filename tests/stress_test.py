# -*- coding: utf-8 -*-
"""
StyleMirror - 并发压测脚本

功能特性：
1. 并发模拟：支持 5、10、20 个并发用户同时上传图片
2. Mock/Real 切换：可选择测试真实 API 或本地 Mock
3. 指标统计：自动生成压测报告（请求数、成功率、响应时长、Token消耗）
4. 鲁棒性验证：随机插入损坏图片、超大图片，测试异常处理

Usage:
    # Mock 模式（默认）
    python tests/stress_test.py --concurrency 10 --requests 50

    # 真实 API 调用（需配置 OPENAI_API_KEY）
    python tests/stress_test.py --real-api --concurrency 5 --requests 20

Author: StyleMirror Team
Version: v1.0
"""

import sys
import os
import time
import random
import argparse
import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
import threading

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image
import numpy as np

# 导入被测模块
from core.image_processor import (
    analyze_vibe,
    preprocess_image,
    image_to_base64,
    MultiModalModel,
    MAX_IMAGE_SIZE,
)

# ============================================
# 压测配置常量
# ============================================

# 默认配置
DEFAULT_CONCURRENCY = 10
DEFAULT_REQUESTS = 50

# Token 价格（gpt-4o-mini，参考 OpenAI 官方定价 2024）
INPUT_TOKEN_PRICE_PER_1K = 0.00015   # $0.15 / 1M input tokens
OUTPUT_TOKEN_PRICE_PER_1K = 0.0006   # $0.60 / 1M output tokens

# 测试图片生成配置
TEST_IMAGE_WIDTH = 800
TEST_IMAGE_HEIGHT = 600

# 鲁棒性测试：异常图片概率
CORRUPTED_IMAGE_PROBABILITY = 0.1   # 10% 概率生成损坏图片
OVERSIZE_IMAGE_PROBABILITY = 0.05   # 5% 概率生成超大图片


# ============================================
# 数据类定义
# ============================================

@dataclass
class RequestResult:
    """单次请求结果"""
    request_id: int
    success: bool
    response_time_ms: float
    error_message: Optional[str] = None
    vibe_tag: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    is_corrupted_image: bool = False
    is_oversize_image: bool = False


@dataclass
class StressTestReport:
    """压测报告"""
    start_time: str
    end_time: str
    total_duration_sec: float
    concurrency: int
    total_requests: int
    success_count: int
    failure_count: int
    min_response_time_ms: float
    max_response_time_ms: float
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    is_real_api: bool = False
    corrupted_image_count: int = 0
    oversize_image_count: int = 0
    errors: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        """格式化报告输出"""
        lines = [
            "=" * 60,
            "         StyleMirror 并发压测报告",
            "=" * 60,
            f"测试时间: {self.start_time} ~ {self.end_time}",
            f"测试模式: {'真实 API 调用' if self.is_real_api else 'Mock 模式'}",
            f"并发数: {self.concurrency}",
            f"总请求数: {self.total_requests}",
            "-" * 60,
            "📊 请求统计",
            f"  ✅ 成功: {self.success_count} ({self.success_count/self.total_requests*100:.1f}%)",
            f"  ❌ 失败: {self.failure_count} ({self.failure_count/self.total_requests*100:.1f}%)",
            "-" * 60,
            "⏱️  响应时长",
            f"  Min:  {self.min_response_time_ms:.2f} ms",
            f"  Max:  {self.max_response_time_ms:.2f} ms",
            f"  Avg:  {self.avg_response_time_ms:.2f} ms",
            f"  P50:  {self.p50_response_time_ms:.2f} ms",
            f"  P95:  {self.p95_response_time_ms:.2f} ms",
            f"  P99:  {self.p99_response_time_ms:.2f} ms",
        ]
        
        if self.is_real_api:
            lines.extend([
                "-" * 60,
                "💰 Token 消耗与费用预估",
                f"  Input Tokens:  {self.total_input_tokens:,}",
                f"  Output Tokens: {self.total_output_tokens:,}",
                f"  预估费用: ${self.estimated_cost_usd:.4f} USD",
            ])
        
        lines.extend([
            "-" * 60,
            "🛡️  鲁棒性测试",
            f"  损坏图片测试: {self.corrupted_image_count} 次",
            f"  超大图片测试: {self.oversize_image_count} 次",
        ])
        
        if self.errors:
            lines.extend([
                "-" * 60,
                "❌ 错误详情 (前 5 条)",
            ])
            for i, error in enumerate(self.errors[:5], 1):
                lines.append(f"  {i}. {error}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


# ============================================
# 测试图片生成器
# ============================================

def generate_normal_image(width: int = TEST_IMAGE_WIDTH, height: int = TEST_IMAGE_HEIGHT) -> Image.Image:
    """
    生成正常的测试图片
    
    使用随机颜色和渐变效果，模拟用户上传的真实图片
    """
    # 创建随机渐变背景
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 随机选择两个颜色作为渐变端点
    color1 = np.array([random.randint(50, 200) for _ in range(3)])
    color2 = np.array([random.randint(50, 200) for _ in range(3)])
    
    # 创建水平渐变
    for x in range(width):
        ratio = x / width
        color = (color1 * (1 - ratio) + color2 * ratio).astype(np.uint8)
        img_array[:, x] = color
    
    # 添加一些随机形状（模拟图片内容）
    for _ in range(random.randint(3, 8)):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2 = min(x1 + random.randint(50, 200), width)
        y2 = min(y1 + random.randint(50, 200), height)
        fill_color = [random.randint(0, 255) for _ in range(3)]
        img_array[y1:y2, x1:x2] = fill_color
    
    return Image.fromarray(img_array, 'RGB')


def generate_oversize_image() -> Image.Image:
    """
    生成超大尺寸图片（用于测试边界处理）
    
    生成 3000x3000 以上的图片，测试缩放逻辑
    """
    width = random.randint(3000, 5000)
    height = random.randint(3000, 5000)
    
    # 使用简单的颜色块，避免内存溢出
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    
    # 分块填充颜色
    block_size = 500
    for y in range(0, height, block_size):
        for x in range(0, width, block_size):
            color = [random.randint(100, 200) for _ in range(3)]
            y_end = min(y + block_size, height)
            x_end = min(x + block_size, width)
            img_array[y:y_end, x:x_end] = color
    
    return Image.fromarray(img_array, 'RGB')


def generate_corrupted_image() -> bytes:
    """
    生成损坏的图片数据（用于测试异常处理）
    
    返回无效的字节数据，模拟损坏的图片文件
    """
    corruption_types = [
        # 随机字节序列
        bytes([random.randint(0, 255) for _ in range(random.randint(100, 1000))]),
        # 截断的 JPEG 头
        b'\xff\xd8\xff\xe0' + bytes([random.randint(0, 255) for _ in range(50)]),
        # 完全随机的二进制数据
        os.urandom(random.randint(500, 2000)),
        # 空 PNG 头
        b'\x89PNG\r\n\x1a\n' + b'\x00' * 100,
    ]
    return random.choice(corruption_types)


# ============================================
# Mock API 响应生成器
# ============================================

def create_mock_response(result: Dict[str, Any], input_tokens: int = 500, output_tokens: int = 150):
    """
    创建 Mock API 响应对象
    """
    class MockUsage:
        def __init__(self):
            self.prompt_tokens = input_tokens
            self.completion_tokens = output_tokens
            self.total_tokens = input_tokens + output_tokens
    
    class MockMessage:
        def __init__(self, content):
            self.content = content
    
    class MockChoice:
        def __init__(self, content):
            self.message = MockMessage(content)
    
    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
            self.usage = MockUsage()
    
    import json
    return MockResponse(json.dumps(result))


def get_mock_vibe_result() -> Dict[str, Any]:
    """生成 Mock 风格分析结果"""
    vibe_options = ["法式復古", "極簡工業", "溫柔原木", "多巴胺", "静奢风"]
    selected_vibe = random.choice(vibe_options)
    
    color_palettes = {
        "法式復古": ["#D4A574", "#8B7355", "#F5E6D3"],
        "極簡工業": ["#4A4A4A", "#2C2C2C", "#A0A0A0"],
        "溫柔原木": ["#D4B896", "#A67B5B", "#F5E6D3"],
        "多巴胺": ["#FF6B6B", "#4ECDC4", "#FFE66D"],
        "静奢风": ["#C4B8A8", "#8B8178", "#E8E4DF"],
    }
    
    descriptions = {
        "法式復古": "柔和的暖色调光线透过窗帘洒落，搭配复古丝绒、黄铜材质的家具装饰，整体呈现出优雅浪漫的巴黎公寓氛围感~",
        "極簡工業": "冷色调的自然光与室内金属、混凝土材质形成鲜明对比，展现出简约而有力的现代都市美学~",
        "溫柔原木": "温暖的日光与原木纹理相互映衬，棉麻织物与陶艺摆件点缀其中，营造出舒适放松的生活感~",
        "多巴胺": "明亮跳跃的色彩碰撞，充满活力与童趣，每一个角落都散发着快乐的气息~",
        "静奢风": "低调奢华的质感，精致的细节处理，优雅而不张扬的高级感~",
    }
    
    return {
        "vibe_tag": selected_vibe,
        "description": descriptions[selected_vibe],
        "color_palette": color_palettes[selected_vibe],
        "scene_keywords": random.sample(["咖啡馆", "居家", "街拍", "工作室", "户外", "办公室"], 2),
        "confidence": round(random.uniform(0.75, 0.95), 2)
    }


# ============================================
# 压测核心逻辑
# ============================================

class StressTester:
    """并发压测执行器"""
    
    def __init__(
        self,
        concurrency: int = DEFAULT_CONCURRENCY,
        total_requests: int = DEFAULT_REQUESTS,
        use_real_api: bool = False,
        api_key: str = None,
        base_url: str = None
    ):
        """
        初始化压测执行器
        
        Args:
            concurrency: 并发数
            total_requests: 总请求数
            use_real_api: 是否使用真实 API
            api_key: OpenAI API Key
            base_url: API 代理地址
        """
        self.concurrency = concurrency
        self.total_requests = total_requests
        self.use_real_api = use_real_api
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        
        # 结果收集
        self.results: List[RequestResult] = []
        self.lock = threading.Lock()
        
        # 统计计数器
        self.request_counter = 0
        self.corrupted_count = 0
        self.oversize_count = 0
    
    def _get_test_image(self, request_id: int) -> Tuple[Optional[Image.Image], bool, bool]:
        """
        获取测试图片（包含随机异常图片注入）
        
        Returns:
            Tuple[Optional[Image.Image], bool, bool]: (图片对象, 是否损坏, 是否超大)
        """
        rand = random.random()
        
        # 注入损坏图片
        if rand < CORRUPTED_IMAGE_PROBABILITY:
            with self.lock:
                self.corrupted_count += 1
            # 返回 None，标记为损坏图片
            return None, True, False
        
        # 注入超大图片
        if rand < CORRUPTED_IMAGE_PROBABILITY + OVERSIZE_IMAGE_PROBABILITY:
            with self.lock:
                self.oversize_count += 1
            return generate_oversize_image(), False, True
        
        # 正常图片
        return generate_normal_image(), False, False
    
    def _execute_single_request(self, request_id: int) -> RequestResult:
        """
        执行单次请求
        
        Args:
            request_id: 请求 ID
            
        Returns:
            RequestResult: 请求结果
        """
        # 获取测试图片
        image, is_corrupted, is_oversize = self._get_test_image(request_id)
        
        start_time = time.time()
        
        # 处理损坏图片场景
        if is_corrupted and image is None:
            try:
                # 尝试用损坏的数据创建图片
                corrupted_data = generate_corrupted_image()
                image = Image.open(BytesIO(corrupted_data))
            except Exception as e:
                # 预期的异常：损坏图片无法打开
                response_time = (time.time() - start_time) * 1000
                return RequestResult(
                    request_id=request_id,
                    success=False,
                    response_time_ms=response_time,
                    error_message=f"损坏图片测试 - 异常捕获成功: {type(e).__name__}",
                    is_corrupted_image=True
                )
        
        # 执行风格分析
        try:
            if self.use_real_api:
                # 真实 API 调用
                result = analyze_vibe(
                    image=image,
                    api_key=self.api_key,
                    base_url=self.base_url
                )
                
                response_time = (time.time() - start_time) * 1000
                
                # 真实调用无法直接获取 token 数，使用估算值
                # 实际可以通过 model.analyze_image 返回的 response.usage 获取
                estimated_input = 500  # 估算
                estimated_output = 150  # 估算
                
                return RequestResult(
                    request_id=request_id,
                    success=True,
                    response_time_ms=response_time,
                    vibe_tag=result.get("vibe_tag"),
                    input_tokens=estimated_input,
                    output_tokens=estimated_output,
                    is_corrupted_image=is_corrupted,
                    is_oversize_image=is_oversize
                )
            else:
                # Mock 模式：模拟 API 延迟
                mock_delay = random.uniform(0.05, 0.3)  # 50-300ms 模拟延迟
                time.sleep(mock_delay)
                
                # 使用内置 Mock 逻辑
                result = get_mock_vibe_result()
                
                response_time = (time.time() - start_time) * 1000
                
                return RequestResult(
                    request_id=request_id,
                    success=True,
                    response_time_ms=response_time,
                    vibe_tag=result.get("vibe_tag"),
                    input_tokens=random.randint(400, 600),
                    output_tokens=random.randint(100, 200),
                    is_corrupted_image=is_corrupted,
                    is_oversize_image=is_oversize
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return RequestResult(
                request_id=request_id,
                success=False,
                response_time_ms=response_time,
                error_message=f"{type(e).__name__}: {str(e)}",
                is_corrupted_image=is_corrupted,
                is_oversize_image=is_oversize
            )
    
    def run(self) -> StressTestReport:
        """
        执行并发压测
        
        Returns:
            StressTestReport: 压测报告
        """
        print(f"\n{'='*60}")
        print(f"  StyleMirror 并发压测启动")
        print(f"  模式: {'真实 API' if self.use_real_api else 'Mock'}")
        print(f"  并发数: {self.concurrency}")
        print(f"  总请求数: {self.total_requests}")
        print(f"{'='*60}\n")
        
        start_time = datetime.now()
        
        # 使用线程池执行并发请求
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = []
            
            for i in range(self.total_requests):
                future = executor.submit(self._execute_single_request, i + 1)
                futures.append(future)
                
                # 显示进度
                if (i + 1) % 10 == 0:
                    print(f"  📤 已提交 {i + 1}/{self.total_requests} 个请求...")
            
            # 收集结果
            print(f"\n  ⏳ 等待所有请求完成...\n")
            
            for future in as_completed(futures):
                result = future.result()
                with self.lock:
                    self.results.append(result)
                    
                    # 实时显示进度
                    completed = len(self.results)
                    if completed % 10 == 0 or completed == self.total_requests:
                        print(f"  ✅ 已完成 {completed}/{self.total_requests} 个请求")
        
        end_time = datetime.now()
        
        # 生成报告
        return self._generate_report(start_time, end_time)
    
    def _generate_report(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> StressTestReport:
        """生成压测报告"""
        
        # 计算统计指标
        success_count = sum(1 for r in self.results if r.success)
        failure_count = sum(1 for r in self.results if not r.success)
        
        response_times = [r.response_time_ms for r in self.results]
        
        # 计算百分位响应时间
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.5)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)]
        
        # Token 统计
        total_input_tokens = sum(r.input_tokens for r in self.results if r.success)
        total_output_tokens = sum(r.output_tokens for r in self.results if r.success)
        
        # 费用计算
        estimated_cost = (
            total_input_tokens * INPUT_TOKEN_PRICE_PER_1K / 1000 +
            total_output_tokens * OUTPUT_TOKEN_PRICE_PER_1K / 1000
        )
        
        # 收集错误信息
        errors = [r.error_message for r in self.results if r.error_message]
        
        # 统计异常图片测试
        corrupted_count = sum(1 for r in self.results if r.is_corrupted_image)
        oversize_count = sum(1 for r in self.results if r.is_oversize_image)
        
        return StressTestReport(
            start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
            total_duration_sec=(end_time - start_time).total_seconds(),
            concurrency=self.concurrency,
            total_requests=self.total_requests,
            success_count=success_count,
            failure_count=failure_count,
            min_response_time_ms=min(response_times) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            p50_response_time_ms=p50,
            p95_response_time_ms=p95,
            p99_response_time_ms=p99,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            estimated_cost_usd=estimated_cost,
            is_real_api=self.use_real_api,
            corrupted_image_count=corrupted_count,
            oversize_image_count=oversize_count,
            errors=errors
        )


# ============================================
# 命令行入口
# ============================================

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="StyleMirror 并发压测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Mock 模式压测（默认）
  python tests/stress_test.py --concurrency 10 --requests 50
  
  # 真实 API 压测（需配置 OPENAI_API_KEY）
  python tests/stress_test.py --real-api --concurrency 5 --requests 20
  
  # 高并发压测
  python tests/stress_test.py -c 20 -n 100
        """
    )
    
    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help=f"并发数 (默认: {DEFAULT_CONCURRENCY})"
    )
    
    parser.add_argument(
        "-n", "--requests",
        type=int,
        default=DEFAULT_REQUESTS,
        help=f"总请求数 (默认: {DEFAULT_REQUESTS})"
    )
    
    parser.add_argument(
        "--real-api",
        action="store_true",
        help="使用真实 API 调用（默认使用 Mock）"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="OpenAI API Key（也可通过环境变量 OPENAI_API_KEY 设置）"
    )
    
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="API 代理地址（也可通过环境变量 OPENAI_BASE_URL 设置）"
    )
    
    args = parser.parse_args()
    
    # 参数验证
    if args.real_api and not (args.api_key or os.getenv("OPENAI_API_KEY")):
        print("❌ 错误: 真实 API 模式需要配置 OPENAI_API_KEY")
        print("   请设置环境变量或使用 --api-key 参数")
        sys.exit(1)
    
    if args.concurrency < 1 or args.concurrency > 100:
        print("❌ 错误: 并发数必须在 1-100 之间")
        sys.exit(1)
    
    if args.requests < 1:
        print("❌ 错误: 请求数必须大于 0")
        sys.exit(1)
    
    # 创建压测执行器
    tester = StressTester(
        concurrency=args.concurrency,
        total_requests=args.requests,
        use_real_api=args.real_api,
        api_key=args.api_key,
        base_url=args.base_url
    )
    
    # 执行压测
    report = tester.run()
    
    # 输出报告
    print(report)
    
    # 保存报告到文件
    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    report_file = os.path.join(
        report_dir,
        f"stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(str(report))
    
    print(f"\n📄 报告已保存至: {report_file}")


if __name__ == "__main__":
    main()
