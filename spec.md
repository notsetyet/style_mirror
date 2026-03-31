# Project Spec: StyleMirror - 小红书点点 Agent 多模态升级 (Prototype)

> **文档版本**: v2.1 Dotenv 集成版
> **最后更新**: 2026-03-31
> **同步状态**: ✅ 已与代码库同步
> **版本定位**: 从「Mock 模拟」到「真实 AI 调用」的平滑切换

---

## 1. 产品愿景 (Product Vision)

### 1.1 核心定位

构建一个具有 **"用户 Sense"** 的 AI 审美顾问。用户通过上传个人空间/人像照片，让点点 Agent 自动匹配小红书站内笔记中的单品，并实现 **"一键实景预览"**，缩短从 **"种草"** 到 **"决策"** 的链路。

### 1.2 v2.0 版本升华：从「关键词匹配」到「多模态审美对齐」

**v1.0 时代的局限**：
- 基于 `vibe_tag` 的精确标签匹配，召回率受限于标签覆盖度
- 无法理解用户的深层语义需求（如"适合约会"、"要有氛围感"）
- 搜索链路单一，缺乏语义泛化能力

**v2.0 RAG 语义检索增强的核心突破**：

| 维度 | v1.0 关键词匹配 | v2.0 多模态审美对齐 |
|------|----------------|-------------------|
| **感知层** | 单模态标签提取 | 视觉 + 文本多模态融合 |
| **检索层** | 精确标签匹配 | 向量语义召回 (Vector 70% + Tag 30%) |
| **理解层** | 浅层关键词 | 深度语义嵌入 (text-embedding-3-small) |
| **交互层** | 单次推荐 | 多轮意图修正回路 (Roadmap) |
| **业务价值** | 匹配准确率有限 | 召回率提升、长尾覆盖、用户体验优化 |

**技术亮点**：
- **向量检索引擎**：将风格描述、笔记内容嵌入 1536 维语义空间，支持相似度检索
- **混合召回策略**：向量语义 70% + 标签精确 30%，兼顾泛化与精准
- **优雅降级机制**：无 API Key 时自动切换 Mock 向量，保证 Demo 流畅

---

## 2. 项目目录结构 (Project Structure)

```
style-mirror/
├── app.py                      # Streamlit 主程序入口 (v4.1 Dotenv 集成)
├── requirements.txt            # 依赖库清单 (含 python-dotenv)
├── spec.md                     # 项目规范文档 (v2.1)
├── README.md                   # 项目说明文档
├── .env.example                # 环境变量配置模板
├── .gitignore                  # Git 忽略配置（含 .env）
│
├── components/                 # UI 组件模块
│   └── ui_styles.py            # CSS 样式和通用 UI 渲染函数
│
├── core/                       # 核心业务逻辑
│   ├── image_processor.py      # 视觉特征提取 (v2.0 多模态接入)
│   │                           # - preprocess_image(): 图像预处理
│   │                           # - analyze_vibe(): GPT-4o-mini 风格识别
│   │                           # - VibeResult: 风格分析结果 dataclass
│   ├── retriever.py            # 笔记检索引擎 (v2.0 向量检索)
│   │                           # - get_embedding(): 语义向量嵌入
│   │                           # - cosine_similarity(): 余弦相似度计算
│   │                           # - get_matching_notes_v2(): 混合召回接口
│   │                           # - semantic_search(): 纯语义搜索接口
│   └── virtual_tryon.py        # 图像合成与叠加预览（预留接口）
│                               # - virtual_tryon(): 试穿主函数 (待实现)
│                               # - TryOnModel: 模型接口类 (待实现)
│
├── data/                       # 静态资源与 Mock 数据
│   └── mock_notes.json         # 模拟小红书笔记库（3条数据）
│                               # - note_001: 法式復古
│                               # - note_002: 極簡工業
│                               # - note_003: 溫柔原木
│
├── prompts/                    # System Prompts
│   └── agent_prompts.py        # 点点 Agent 预设 Prompt
│                               # - DIANDIAN_SYSTEM_PROMPT: 人设定义
│
└── tests/                      # 测试用例与压测脚本
    ├── __init__.py             # 模块初始化
    ├── stress_test.py          # 并发压测脚本 (v1.0)
    │                           # - StressTester: 并发执行器
    │                           # - StressTestReport: 压测报告生成
    │                           # - 支持 Mock/Real API 切换
    └── reports/                # 压测报告输出目录
        └── stress_test_*.txt   # 自动生成的压测报告
```

---

## 3. 核心功能 (Core Features)

### 3.1 已实现功能 ✅

| 功能模块 | 状态 | 描述 |
|---------|------|------|
| **多模态 Vibe 理解** | ✅ 已完成 | AI 能够识别用户上传图片的风格（支持 GPT-4o-mini 真实分析 + Mock 降级） |
| **向量语义检索** | ✅ 已完成 | 从 Mock 数据中检索语义相似笔记（V2 升级：向量 70% + 标签 30% 混合召回） |
| **情绪化对话引导** | ✅ 已完成 | Agent 使用小红书特有的语气（Emoji、种草语）进行审美建议 |
| **小红书视觉风格** | ✅ 已完成 | Color Lab 色彩板、Scene Tags 场景标签、打字机效果 |
| **并发压测脚本** | ✅ 已完成 | 支持 5-100 并发压测，自动生成报告，鲁棒性验证 |
| **优雅降级机制** | ✅ 已完成 | API 调用失败时自动切换 Mock 模式，保证 Demo 流畅 |

### 3.2 待实现功能

| 功能模块 | 状态 | 预计版本 |
|---------|------|---------|
| **虚拟叠加预览** | 🚧 规划中 | v3.0 |
| **多轮意图修正** | 🚧 规划中 | v2.1 |
| **匹配度可视化** | 🚧 规划中 | v2.1 |

---

## 4. 技术栈 (Tech Stack)

### 4.1 已实现

| 模块 | 技术选型 | 版本 | 用途 |
|------|---------|------|------|
| Frontend | Streamlit | >=1.28.0 | Web 应用框架，快速交付 UI |
| Image Processing | Pillow (PIL) | >=10.0.0 | 图像读取、预处理、格式转换 |
| Data Processing | Pandas | >=2.0.0 | 数据处理与分析 |
| Network | Requests | >=2.31.0 | HTTP 请求（预留） |
| **Config** | **python-dotenv** | **>=1.0.0** | **环境变量管理 (.env)** |
| **LLM/VLM** | **OpenAI API** | >=1.0.0 | **GPT-4o-mini 多模态分析** |
| **Vector Computing** | **NumPy** | >=1.24.0 | **向量运算、余弦相似度** |
| **Embedding** | **text-embedding-3-small** | - | **文本向量嵌入 (1536维)** |

### 4.2 预留扩展

| 模块 | 技术选型 | 用途 |
|------|---------|------|
| Image Generation | DALL-E 3 / Flux.1 Inpainting | 重绘合成试穿效果 |
| Vector DB | Pinecone / Milvus | 大规模语义相似度检索 |
| Image Embedding | CLIP ViT-B/32 | 图像向量嵌入（Roadmap） |

---

## 5. 架构设计 (Architecture)

### 5.1 v2.0 核心逻辑流：从「识别-匹配」到「感知-检索-修正」

```
┌─────────────────────────────────────────────────────────────────────┐
│                     StyleMirror v2.0 核心架构                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│  用户上传  │───▶│  Step 1:     │───▶│  Step 2:     │───▶│ Step 3:  │
│  照片     │    │  图像预处理   │    │  多模态感知   │    │ 向量化   │
└──────────┘    └──────────────┘    └──────────────┘    └──────────┘
                     │                     │                  │
                     ▼                     ▼                  ▼
               ┌──────────┐         ┌────────────┐     ┌───────────┐
               │ 最大1024px│         │ GPT-4o-mini│     │ Embedding │
               │ RGB转换   │         │ 风格识别    │     │ 1536维向量 │
               │ LANCZOS  │         │ JSON输出    │     │ text-emb  │
               └──────────┘         └────────────┘     └───────────┘
                                                              │
┌──────────────────────────────────────────────────────────────┘
│
▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│  Step 4:     │───▶│  Step 5:     │───▶│  Step 6:     │───▶│ 输出结果  │
│  向量检索    │    │  混合召回    │    │  排序输出    │    │ 展示      │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────┘
       │                   │                   │
       ▼                   ▼                   ▼
 ┌───────────┐      ┌─────────────┐     ┌─────────────┐
 │ Cosine Sim│      │ Vector 70%  │     │ Top-K 结果  │
 │ 相似度计算 │      │ Tag 30%     │     │ Agent对话   │
 │ Mock降级  │      │ Keyword+10  │     │ 单品卡片    │
 └───────────┘      └─────────────┘     └─────────────┘
```

### 5.2 混合召回策略详解

**得分公式**：
```
hybrid_score = vector_score × 0.7 + tag_score × 0.3 + keyword_bonus
```

| 得分项 | 权重 | 计算方式 | 说明 |
|--------|------|---------|------|
| `vector_score` | 70% | 余弦相似度归一化 [0, 100] | 语义理解，泛化能力强 |
| `tag_score` | 30% | 精确匹配满分 100 | 保证精准召回 |
| `keyword_bonus` | +10/词 | 场景关键词命中加分 | 增强场景相关性 |

---

## 6. 数据定义 (Data Models)

### 6.1 VibeResult (风格识别结果)

使用 `dataclass` 定义，确保类型安全：

```python
@dataclass
class VibeResult:
    """
    风格分析结果数据结构

    文件位置: core/image_processor.py:114-135
    """
    vibe_tag: str              # 风格标签，如 "法式復古"
    description: str           # 风格描述（小红书语气）
    color_palette: List[str]   # 色彩板，如 ["#D4A574", "#8B7355", "#F5E6D3"]
    scene_keywords: List[str]  # 场景关键词，如 ["咖啡馆", "居家"]
    confidence: float          # 置信度 0.0-1.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，兼容现有接口"""
        return {
            "vibe_tag": self.vibe_tag,
            "description": self.description,
            "color_palette": self.color_palette,
            "scene_keywords": self.scene_keywords,
            "confidence": self.confidence
        }
```

### 6.2 UserInput (会话状态)

```python
st.session_state.uploaded_image   # PIL.Image - 用户上传的图片
st.session_state.vibe_result      # Dict - AI 识别的风格结果
st.session_state.recommended_notes # List[Dict] - 匹配的笔记列表
st.session_state.last_file_id     # str - 上次上传文件ID（用于检测新文件）
st.session_state.api_key          # str - 用户配置的 API Key
st.session_state.base_url         # str - 用户配置的 API Base URL
st.session_state.analysis_complete # bool - 分析是否完成
```

### 6.3 NoteMatchResult (检索结果)

```python
{
    "note_id": "note_001",
    "vector_score": 85.32,      # 向量相似度得分 [0, 100]
    "tag_score": 100,           # 标签精确匹配得分 [0, 100]
    "keyword_bonus": 20,        # 场景关键词加分
    "hybrid_score": 79.72,      # 混合得分（用于排序）
    "match_score": 79.72,       # 兼容旧接口字段
    "is_default": false         # 是否为默认推荐
}
```

### 6.4 XHSNote (Mock 数据结构)

```python
{
    "note_id": "note_001",
    "item_img_url": "https://example.com/images/xxx.jpg",
    "vibe_tags": ["法式復古", "復古浪漫", "溫柔優雅"],
    "caption": "笔记正文描述",
    "items": [
        {
            "item_name": "法式波點連衣裙",
            "category": "連衣裙",
            "color": "黑底白點",
            "style": "復古法式"
        }
    ],
    "author": "@法式穿搭日記",
    "likes": 12580,
    "collects": 3256
}
```

### 6.5 当前 Mock 数据 (3条)

| note_id | vibe_tags (主标签) | 风格描述 |
|---------|-------------------|---------|
| note_001 | 法式復古 | 复古法式穿搭（波点连衣裙+小香风外套） |
| note_002 | 極簡工業 | 极简工业风穿搭（西装外套+阔腿裤） |
| note_003 | 溫柔原木 | 温柔原木风穿搭（棉麻衬衫+阔腿裤） |

---

## 7. 核心逻辑流 (Implementation Logic)

### Step 1: 图像预处理 (Preprocessing)

**入口**: `core/image_processor.py::preprocess_image()`

```python
# 常量配置
MAX_IMAGE_SIZE = 1024    # 图片最大边长（像素）
JPEG_QUALITY = 85        # JPEG 压缩质量
MAX_FILE_SIZE_KB = 500   # 目标文件大小上限

def preprocess_image(image_file) -> Optional[Image.Image]:
    # 1. 使用 PIL 读取图像
    # 2. 转换为 RGB 模式（处理 RGBA 等格式）
    # 3. 限制最大尺寸为 1024px（提高处理速度）
    # 4. 使用 LANCZOS 算法保持画质
    # 5. 返回处理后的 PIL.Image 对象
```

### Step 2: 风格识别 (Vibe Analysis)

**入口**: `core/image_processor.py::analyze_vibe()`

```python
# API 调用参数
API_TIMEOUT = 30.0       # API 超时时间（秒）
MAX_RETRIES = 3          # 最大重试次数
RETRY_DELAY = 1.0        # 重试间隔（秒）
MODEL_TEMPERATURE = 0.7  # 模型温度
MAX_TOKENS = 500         # 最大输出 Token

def analyze_vibe(image, api_key=None, base_url=None) -> Dict:
    # 1. 检查 API Key，未配置则降级到 Mock 模式
    # 2. 构建多模态请求（Base64 编码图片）
    # 3. 调用 GPT-4o-mini 进行风格分析
    # 4. 使用 response_format={"type": "json_object"} 强制 JSON 输出
    # 5. 返回 VibeResult 字典
```

**重试与降级策略**:

| 异常类型 | 处理策略 |
|---------|---------|
| APITimeoutError | 指数退避重试（delay × attempt） |
| RateLimitError | 延长等待后重试（delay × 2 × attempt） |
| JSONDecodeError | 直接失败，不重试 |
| APIError | 线性退避重试 |
| 未配置 API Key | 降级到 Mock 模式 |

### Step 3: 向量嵌入 (Embedding)

**入口**: `core/retriever.py::get_embedding()`

```python
def get_embedding(
    text: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None
) -> List[float]:
    """
    获取文本的向量嵌入

    模式选择：
        - 有 api_key：调用 OpenAI text-embedding-3-small
        - 无 api_key：使用文本 hash 生成本地伪向量

    Returns:
        List[float]: 1536 维向量
    """
```

**向量模式对照**:

| 模式 | 触发条件 | 实现方式 | 向量维度 |
|------|---------|---------|---------|
| 真实模式 | 提供 api_key | 调用 OpenAI text-embedding-3-small | 1536 |
| Mock 模式 | 无 api_key | 基于 MD5 hash 生成本地伪向量 | 1536 |

### Step 4: 向量检索 (Vector Search)

**入口**: `core/retriever.py::get_matching_notes_v2()`

```python
def get_matching_notes_v2(
    vibe_description: str,
    user_text_modifier: str = "",
    vibe_tag: str = "",
    scene_keywords: List[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    top_k: int = 5
) -> List[Dict]:
    # 1. 构建查询文本 = vibe_description + user_text_modifier
    # 2. 获取查询向量（get_embedding）
    # 3. 遍历笔记计算向量相似度（cosine_similarity）
    # 4. 计算混合得分 = vector_score × 0.7 + tag_score × 0.3 + keyword_bonus
    # 5. 按 hybrid_score 排序返回 top_k 结果
```

### Step 5: UI 渲染与交互 (Rendering)

**入口**: `app.py`

**核心组件**:

| 组件 | 函数 | 功能 |
|------|------|------|
| CSS 注入 | `inject_xhs_styles()` | 注入小红书风格 CSS |
| 色彩实验室 | `render_color_lab()` | 30px 圆形色块，点击复制 |
| 场景标签 | `render_scene_tags()` | 胶囊形状 Pills 展示 |
| 打字机效果 | `typewriter_effect()` | 逐字输出 Agent 消息 |
| Agent 对话 | `render_agent_chat()` | 带头像和状态的对话区 |
| 笔记卡片 | `render_note_card()` | 单品瀑布流展示 |

---

## 8. API 规范 (API Specification)

### 8.1 多模态模型调用

**端点**: OpenAI Chat Completions API
**模型**: gpt-4o-mini
**关键配置**:

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    max_tokens=500,
    temperature=0.7,
    response_format={"type": "json_object"}  # 强制 JSON 输出
)
```

**图片传输**:
```python
{
    "type": "image_url",
    "image_url": {
        "url": f"data:image/jpeg;base64,{base64_image}",
        "detail": "low"  # 节省 Token，适合风格分析
    }
}
```

### 8.2 Embedding 调用

**端点**: OpenAI Embeddings API
**模型**: text-embedding-3-small
**向量维度**: 1536

```python
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=text
)
embedding = response.data[0].embedding  # List[float], 1536 维
```

---

## 9. Prompt 定义 (Prompt Engineering)

### 9.1 VIBE_SYSTEM_PROMPT

**文件**: `core/image_processor.py:77-107`

```
你是小红书「点点 Agent」的视觉分析引擎，专注于审美风格的精准识别。

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
   法式復古、極簡工業、溫柔原木、多巴胺、静奢风、美式复古...

2. description: 用小红书语气描述图片的光影、材质、情绪，强调「氛围感」和「出片率」。

3. color_palette: 提取图片中的 3 个主色调，以十六进制色号表示。

4. scene_keywords: 2-3 个场景关键词（如「咖啡馆」「居家」「街拍」）。

5. confidence: 分析置信度（0.0-1.0）。
```

### 9.2 DIANDIAN_SYSTEM_PROMPT

**文件**: `prompts/agent_prompts.py`

```python
DIANDIAN_SYSTEM_PROMPT = """
你是小红书「点点 Agent」，一个温暖、亲切的 AI 穿搭助手 💫

## 🎭 人设特点
- 语气亲切自然，像闺蜜一样交流
- 善用 Emoji 增添趣味性，但不过度堆砌 ✨
- 使用小红书社区特有的表达方式（集美、宝子们、氛围感、yyds 等）

## ✨ 核心能力
1. 视觉风格识别（Vibe Analysis）
2. 穿搭单品推荐
3. 虚拟试穿体验
"""
```

---

## 10. UI 组件 (UI Components)

**文件**: `components/ui_styles.py` + `app.py`

### 10.1 CSS 设计规范

| 变量 | 值 | 用途 |
|------|-----|------|
| --xhs-red | #FF2442 | 小红书主题色 |
| --xhs-red-light | #FF6B81 | 悬停高亮色 |
| --xhs-bg | #FAFAFA | 页面背景色 |
| --xhs-card | #FFFFFF | 卡片背景色 |
| border-radius | 15px | 卡片圆角 |
| box-shadow | 0 2px 12px rgba(0,0,0,0.08) | 卡片阴影 |

### 10.2 核心组件

| 函数 | 用途 |
|------|------|
| `inject_xhs_styles()` | 注入小红书风格 CSS |
| `render_color_lab(colors)` | 色彩实验室（30px 圆形色块） |
| `render_scene_tags(keywords)` | 场景标签（胶囊 Pills） |
| `typewriter_effect(text, placeholder)` | 打字机效果 |
| `render_agent_chat(vibe_result)` | Agent 对话区 |
| `render_note_card(note, show_items)` | 笔记卡片 |
| `render_item_card(item, note_id)` | 单品卡片 |

---

## 11. 质量保障与性能基准 (Quality Assurance)

### 11.1 压测脚本

**文件**: `tests/stress_test.py`

**功能特性**:
- 并发模拟：支持 5、10、20 个并发用户同时上传图片
- Mock/Real 切换：可选择测试真实 API 或本地 Mock
- 指标统计：自动生成压测报告（请求数、成功率、响应时长、Token消耗）
- 鲁棒性验证：随机插入损坏图片、超大图片，测试异常处理

**使用方式**:
```bash
# Mock 模式（默认）
python tests/stress_test.py --concurrency 10 --requests 50

# 真实 API 调用（需配置 OPENAI_API_KEY）
python tests/stress_test.py --real-api --concurrency 5 --requests 20
```

### 11.2 压测报告示例

**文件**: `tests/reports/stress_test_20260331_222454.txt`

```
============================================================
         StyleMirror 并发压测报告
============================================================
测试时间: 2026-03-31 22:24:53 ~ 2026-03-31 22:24:54
测试模式: Mock 模式
并发数: 5
总请求数: 20
------------------------------------------------------------
📊 请求统计
  ✅ 成功: 16 (80.0%)
  ❌ 失败: 4 (20.0%)
------------------------------------------------------------
⏱️  响应时长
  Min:  0.31 ms
  Max:  498.55 ms
  Avg:  179.40 ms
  P50:  177.73 ms
  P95:  498.55 ms
------------------------------------------------------------
🛡️  鲁棒性测试
  损坏图片测试: 4 次
  超大图片测试: 1 次
============================================================
```

### 11.3 性能基准（预期）

| 指标 | 目标值 | 备注 |
|------|--------|------|
| 图像预处理 | < 500ms | 1024px 限制 |
| 风格分析 (API) | < 3s | GPT-4o-mini |
| 向量检索 (Mock) | < 100ms | 3 条笔记 |
| 向量检索 (API) | < 500ms | text-embedding-3-small |
| 首屏加载 | < 2s | Streamlit 冷启动 |

### 11.4 错误处理矩阵

| 错误场景 | 处理方式 | 用户提示 |
|---------|---------|---------|
| 图片格式不支持 | 返回 None | "图片格式不支持，请上传 JPG/PNG" |
| API Key 未配置 | Mock 降级 | "未配置 API Key，使用演示模式" |
| API 超时 | 重试 3 次 | "网络超时，请稍后重试" |
| API 限流 | 指数退避 | "请求频繁，请稍后重试" |
| JSON 解析失败 | 返回默认值 | "分析异常，请重试" |

### 11.5 环境配置 (Environment Setup)

#### .env 文件结构

```bash
# OpenAI API 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，用于代理
```

#### 配置检查函数

```python
from core.image_processor import check_api_config, get_api_status_message

# 检查配置状态
is_ready, mode, config = check_api_config()
# is_ready: bool - API 是否就绪
# mode: str - "real_ai" 或 "mock_demo"
# config: dict - 配置详情

# 获取状态提示
message = get_api_status_message()
# 返回: "✅ 当前处于：真实 AI 模式" 或 "💡 当前处于：演示 Mock 模式"
```

#### 安全合规

| 文件 | 用途 | Git 状态 |
|------|------|---------|
| `.env` | 真实 API 密钥 | ❌ 已添加到 .gitignore |
| `.env.example` | 配置模板 | ✅ 提交到仓库 |

---

## 12. 路线图 (Roadmap)

### Phase 1: 基础原型 ✅ (已完成)

- [x] 项目骨架搭建
- [x] Streamlit UI 双列布局
- [x] 用户照片上传功能
- [x] 风格识别函数 (`analyze_vibe`)
- [x] 笔记检索函数 (`get_matching_notes`)
- [x] 点点 Agent 拟人化对话
- [x] 小红书风格 UI 组件

### Phase 2: RAG 与混合搜索增强 ✅ (已完成)

- [x] 接入 GPT-4o-mini 实现真实风格识别
- [x] 实现 JSON Mode 强制输出
- [x] 实现重试与降级策略
- [x] **实现 text-embedding-3-small 向量嵌入**
- [x] **实现余弦相似度检索**
- [x] **实现混合召回策略（向量 70% + 标签 30%）**
- [x] **新增 `get_matching_notes_v2()` 接口**
- [x] **新增 `semantic_search()` 纯语义搜索接口**
- [x] 小红书视觉风格重构（Color Lab、Scene Tags、打字机）
- [x] **并发压测脚本开发**
- [x] **鲁棒性测试覆盖**
- [x] **python-dotenv 环境变量集成**
- [x] **API 状态检测与可视化**

### Phase 2.1: RAG 增强迭代 (规划中)

- [ ] 向量数据库 Mock（Pinecone/Milvus 本地模拟）
- [ ] 多轮意图修正回路（用户反馈 -> 查询改写 -> 重新检索）
- [ ] 匹配度分值可视化（进度条 + 分数展示）
- [ ] 检索结果多样性优化（MMR 去重）
- [ ] 用户偏好记忆（会话级别）

### Phase 3: 虚拟试穿 (规划中)

- [ ] 接入 Stable Diffusion In-painting
- [ ] 实现 ControlNet + Pose 引导
- [ ] 或接入 VITON-HD 模型
- [ ] 实现真实试穿效果预览

### Phase 4: 对话增强 (规划中)

- [ ] 接入 GPT-4 / Claude 实现 LLM 对话
- [ ] 添加多轮对话上下文记忆
- [ ] 实现风格偏好学习

---

## 13. 运行指南

### 13.1 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（复制模板）
cp .env.example .env

# 3. 编辑 .env 文件，填入你的 API Key
# OPENAI_API_KEY=sk-your-api-key-here
# OPENAI_BASE_URL=https://api.openai.com/v1  # 可选

# 4. 启动应用
streamlit run app.py
```

### 13.2 运行模式

| 模式 | 条件 | 特点 |
|------|------|------|
| **真实 AI 模式** | .env 中配置了 OPENAI_API_KEY | 调用 GPT-4o-mini 进行真实分析 |
| **演示 Mock 模式** | 未配置 API Key | 使用本地 Mock 数据，适合演示 |

### 13.3 压测脚本

```bash
# 运行压测脚本
python tests/stress_test.py --concurrency 10 --requests 50
```

---

## 14. 更新日志 (Changelog)

### v2.0 (2026-03-31) - RAG 语义检索增强版

**架构升级**:
- ✅ 从「关键词匹配」升级为「多模态审美对齐」架构
- ✅ 核心流程升级：感知 -> 向量化 -> 语义召回 -> 交互修正

**向量检索引擎**:
- ✅ 升级 `retriever.py` 至 V2 版本
- ✅ 实现语义向量检索（get_embedding, cosine_similarity）
- ✅ 实现混合召回策略（向量 70% + 标签 30%）
- ✅ 新增 `get_matching_notes_v2()` 接口
- ✅ 新增 `semantic_search()` 纯语义搜索接口
- ✅ 兼容旧接口 `get_matching_notes()`

**质量保障**:
- ✅ 新增并发压测脚本 `tests/stress_test.py`
- ✅ 支持 Mock/Real API 双模式压测
- ✅ 鲁棒性测试覆盖（损坏图片、超大图片）
- ✅ 自动生成压测报告

**文档更新**:
- ✅ 更新 spec.md 数据定义章节（VibeResult dataclass）
- ✅ 新增 API 规范章节（JSON Mode、图片预处理参数）
- ✅ 新增质量保障与性能基准章节
- ✅ 新增架构设计章节（核心逻辑流、混合召回策略）

### v2.1 (2026-03-31) - Dotenv 集成

**环境配置重构**:
- ✅ 引入 `python-dotenv` 管理 `.env` 环境变量
- ✅ 新增 `check_api_config()` 全局配置检查函数
- ✅ 新增 `get_api_status_message()` 状态提示函数
- ✅ 更新 `MultiModalModel` 支持 OPENAI_BASE_URL 环境变量
- ✅ 更新 `get_embedding()` 支持环境变量读取

**状态可视化**:
- ✅ 启动时自动检测 API 环境，显示清晰状态提示
- ✅ 区分「真实 AI 模式」与「演示 Mock 模式」

**安全合规**:
- ✅ 创建 `.gitignore` 防止 `.env` 泄露
- ✅ 创建 `.env.example` 配置模板

### v1.1 (2026-03-31)

- ✅ 实现 `analyze_vibe()` 风格识别函数
- ✅ 实现 `get_matching_notes()` 笔记检索函数
- ✅ 完善交互逻辑：上传图片后自动触发分析
- ✅ 更新 Mock 数据，新增第 3 条笔记
- ✅ 优化 UI 布局，添加小红书风格单品卡片
- ✅ 同步 spec.md 文档

### v1.0 (初始版本)

- ✅ 项目骨架搭建
- ✅ 基础 UI 布局
- ✅ 预留接口定义

---

## 15. 附录：关键技术决策

### 15.1 为什么选择 text-embedding-3-small？

| 对比项 | text-embedding-3-small | text-embedding-3-large | 本地模型 |
|--------|----------------------|----------------------|---------|
| 向量维度 | 1536 | 3072 | 可变 |
| 价格 | $0.02/1M tokens | $0.13/1M tokens | 免费 |
| 质量 | 优秀 | 最佳 | 依赖模型 |
| **推荐** | **✅ 性价比之选** | 高预算场景 | 离线场景 |

### 15.2 为什么采用混合召回策略？

**纯向量检索的问题**：
- 语义相近但风格不符的内容可能被召回
- 缺乏精确匹配的保证

**纯标签匹配的问题**：
- 召回率受限于标签覆盖度
- 无法理解深层语义

**混合策略优势**：
- 向量 70%：保证语义泛化能力，提升召回率
- 标签 30%：保证精准匹配，覆盖核心需求
- 关键词加分：增强场景相关性

---

**文档维护**: StyleMirror Team
**最后同步**: 2026-03-31 22:30
