# Project Spec: StyleMirror - 小红书点点 Agent 多模态升级 (Prototype)

> **文档版本**: v1.1  
> **最后更新**: 2026-03-31  
> **同步状态**: ✅ 已与代码库同步

---

## 1. 产品愿景 (Product Vision)

构建一个具有"用户 Sense"的 AI 审美顾问。用户通过上传个人空间/人像照片，让点点 Agent 自动匹配小红书站内笔记中的单品，并实现"一键实景预览"，缩短从"种草"到"决策"的链路。

---

## 2. 项目目录结构 (Project Structure)

```
style-mirror/
├── app.py                      # Streamlit 主程序入口
├── requirements.txt            # 依赖库清单
├── components/                 # UI 组件模块
│   └── ui_styles.py            # CSS 样式和通用 UI 渲染函数
├── core/                       # 核心业务逻辑
│   ├── image_processor.py      # 视觉特征提取（已实现 analyze_vibe）
│   ├── retriever.py            # 笔记检索（已实现 get_matching_notes）
│   └── virtual_tryon.py        # 图像合成与叠加预览（预留接口）
├── data/                       # 静态资源与 Mock 数据
│   └── mock_notes.json         # 模拟小红书笔记库（3条数据）
└── prompts/                    # System Prompts
    └── agent_prompts.py        # 点点 Agent 预设 Prompt
```

---

## 3. 核心功能 (Core Features)

- [x] **多模态 Vibe 理解**: AI 能够识别用户上传图片的风格（已实现：法式復古、極簡工業、溫柔原木）。
- [x] **结构化笔记检索**: 从 Mock 数据中提取具有相似"视觉 Vibe"的笔记（基于标签匹配）。
- [ ] **虚拟叠加预览**: 在用户原图上，以高审美的方式呈现匹配单品的组合效果。
- [x] **情绪化对话引导**: Agent 使用小红书特有的语气（Emoji、种草语）进行审美建议。

---

## 4. 技术栈 (Tech Stack)

### 已实现
| 模块 | 技术选型 | 版本 | 用途 |
|------|---------|------|------|
| Frontend | Streamlit | >=1.28.0 | Web 应用框架，快速交付 UI |
| Image Processing | Pillow (PIL) | >=10.0.0 | 图像读取、预处理、格式转换 |
| Data Processing | Pandas | >=2.0.0 | 数据处理与分析 |
| Network | Requests | >=2.31.0 | HTTP 请求（预留） |

### 预留扩展
| 模块 | 技术选型 | 用途 |
|------|---------|------|
| LLM/VLM | GPT-4o / Claude 3.5 Sonnet | 图像语义分析及 Agent 对话 |
| Image Generation | DALL-E 3 / Flux.1 Inpainting | 重绘合成试穿效果 |
| Vector DB | Pinecone / Milvus | 语义相似度检索 |
| Embedding | CLIP / sentence-transformers | 图像/文本向量嵌入 |

---

## 5. 数据定义 (Data Models)

### UserInput (会话状态)
```python
st.session_state.uploaded_image   # PIL.Image - 用户上传的图片
st.session_state.vibe_result      # Dict - AI 识别的风格结果
st.session_state.recommended_notes # List[Dict] - 匹配的笔记列表
st.session_state.last_file_id     # str - 上次上传文件ID（用于检测新文件）
```

### VibeResult (风格识别结果)
```python
{
    "vibe_tag": "法式復古" | "極簡工業" | "溫柔原木",
    "description": "光影和材质的描述文本"
}
```

### XHSNote (Mock 数据结构)
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

### 当前 Mock 数据 (3条)
| note_id | vibe_tags (主标签) | 风格描述 |
|---------|-------------------|---------|
| note_001 | 法式復古 | 复古法式穿搭（波点连衣裙+小香风外套） |
| note_002 | 極簡工業 | 极简工业风穿搭（西装外套+阔腿裤） |
| note_003 | 溫柔原木 | 温柔原木风穿搭（棉麻衬衫+阔腿裤） |

---

## 6. 核心逻辑流 (Implementation Logic)

### Step 1: 图像预处理 (Preprocessing)
**入口**: `core/image_processor.py::preprocess_image()`

```python
def preprocess_image(image_file) -> Optional[Image.Image]:
    # 1. 使用 PIL 读取图像
    # 2. 转换为 RGB 模式（处理 RGBA 等格式）
    # 3. 限制最大尺寸为 1024px（提高处理速度）
    # 4. 返回处理后的 PIL.Image 对象
```

### Step 2: 风格识别 (Vibe Analysis)
**入口**: `core/image_processor.py::analyze_vibe()`

```python
def analyze_vibe(image: Image.Image) -> Dict:
    # 1. 随机选择风格标签：["法式復古", "極簡工業", "溫柔原木"]
    # 2. 返回对应的光影和材质描述
    # 3. 返回格式: {"vibe_tag": str, "description": str}
```

**风格描述映射**:
- **法式復古**: 柔和的暖色調光線透過窗簾灑落，搭配復古絲絨、黃銅材質的傢俱裝飾...
- **極簡工業**: 冷色調的自然光與室內金屬、混凝土材質形成鮮明對比...
- **溫柔原木**: 溫暖的日光與原木紋理相互映襯，棉麻織物與陶藝擺件點綴其中...

### Step 3: 笔记检索 (Matching)
**入口**: `core/retriever.py::get_matching_notes()`

```python
def get_matching_notes(vibe_tag: str) -> List[Dict]:
    # 1. 调用 load_mock_notes() 加载 data/mock_notes.json
    # 2. 遍历所有笔记，筛选 vibe_tags 包含该标签的笔记
    # 3. 返回匹配的笔记列表
```

### Step 4: UI 渲染与交互 (Rendering)
**入口**: `app.py`

**交互流程**:
1. 用户在侧边栏上传照片 → 自动触发 `analyze_vibe()`
2. 左侧展示：原图 + Vibe 标签 (`st.info`) + 光影描述
3. 右侧展示：点点 Agent 推荐理由 + 单品卡片（小红书风格边框）

---

## 7. Prompt 定义 (Prompt Engineering)

### Agent System Prompt
**文件**: `prompts/agent_prompts.py::DIANDIAN_SYSTEM_PROMPT`

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

## ⚠️ 注意事项
1. 不要过于正式，保持轻松愉快的交流氛围
2. 避免过于强硬的推销语气，多提供选择和建议
3. 适度使用 Emoji，每个回复 2-5 个即可
"""
```

### 预留 Prompts
- `VIBE_ANALYSIS_PROMPT`: Vibe 识别提示词（预留）
- `STYLE_RECOMMENDATION_PROMPT`: 穿搭建议提示词（预留）

---

## 8. UI 组件 (UI Components)

**文件**: `components/ui_styles.py`

| 函数 | 用途 |
|------|------|
| `apply_custom_styles()` | 应用小红书风格 CSS 样式 |
| `render_agent_message()` | 渲染 Agent 对话消息（带左边框） |
| `render_placeholder()` | 渲染占位符框 |

**CSS 特色**:
- 小红书主题色: `#ff2442`
- 卡片圆角: `12px`
- 渐变背景: `linear-gradient(135deg, #fff5f5 0%, #ffffff 100%)`

---

## 9. 路线图 (Roadmap)

### Phase 1: 基础原型 ✅ (已完成)
- [x] 项目骨架搭建
- [x] Streamlit UI 双列布局
- [x] 用户照片上传功能
- [x] 风格识别函数 (`analyze_vibe`)
- [x] 笔记检索函数 (`get_matching_notes`)
- [x] 点点 Agent 拟人化对话
- [x] 小红书风格 UI 组件

### Phase 2: 多模态升级 (待开发)
- [ ] 接入 GPT-4V / Gemini Vision 实现真实风格识别
- [ ] 实现 CLIP 向量嵌入
- [ ] 接入向量数据库（Pinecone/Milvus）
- [ ] 实现语义相似度检索

### Phase 3: 虚拟试穿 (待开发)
- [ ] 接入 Stable Diffusion In-painting
- [ ] 实现 ControlNet + Pose 引导
- [ ] 或接入 VITON-HD 模型
- [ ] 实现真实试穿效果预览

### Phase 4: 对话增强 (待开发)
- [ ] 接入 GPT-4 / Claude 实现 LLM 对话
- [ ] 添加多轮对话上下文记忆
- [ ] 实现风格偏好学习

---

## 10. 运行指南

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

---

## 11. 更新日志 (Changelog)

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
