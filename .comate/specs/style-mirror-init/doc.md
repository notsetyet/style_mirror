# StyleMirror 项目初始化规格文档

## 项目概述
StyleMirror 是一个小红书"点点 Agent"的多模态升级概念原型（Prototype），主要技术栈为 Python + Streamlit。该项目旨在实现用户照片上传、AI视觉特征提取、小红书笔记检索和虚拟试穿效果预览等功能。

## 需求场景

### 核心功能
1. **用户照片上传**：支持用户上传 jpg/png 格式的照片
2. **视觉特征提取**：通过多模态大模型接口识别用户照片的 Vibe（氛围感、风格等）
3. **笔记检索**：基于视觉特征从小红书笔记库中检索相关穿搭推荐
4. **虚拟试穿**：将推荐单品与用户照片进行合成预览
5. **Agent 对话**：点点 Agent 提供拟人化的穿搭建议和推荐

### 用户交互流程
1. 用户在侧边栏上传照片
2. 系统自动提取照片的视觉特征（Vibe）
3. 点点 Agent 识别用户风格并给出建议
4. 推荐相关小红书笔记单品
5. 展示虚拟试穿效果

## 技术架构

### 项目结构
```
style-mirror-xhs/
├── app.py                    # Streamlit 主程序入口
├── components/               # UI 组件
│   └── ui_styles.py          # CSS 样式和通用 UI 渲染函数
├── core/                     # 核心逻辑
│   ├── image_processor.py    # 视觉特征提取（预留多模态大模型接口）
│   ├── retriever.py          # 模拟小红书笔记检索
│   └── virtual_tryon.py      # 图像合成与叠加预览逻辑
├── data/                     # 静态资源与 Mock 数据
│   └── mock_notes.json       # 模拟小红书笔记库数据
├── prompts/                  # System Prompts 文件夹
│   └── agent_prompts.py      # Agent 预设 Prompt
└── requirements.txt          # 依赖库
```

### 技术栈
- **前端框架**: Streamlit
- **图像处理**: Pillow
- **数据处理**: Pandas
- **网络请求**: Requests
- **多模态接口**: 预留接口（后续可接入 CLIP、BLIP 等模型）

## 受影响的文件

### 新增文件（共8个）
1. **requirements.txt** - 依赖库清单
   - 类型：新增
   - 路径：`/Users/rensiyu01/Desktop/style-mirror/requirements.txt`

2. **app.py** - Streamlit 主程序入口
   - 类型：新增
   - 路径：`/Users/rensiyu01/Desktop/style-mirror/app.py`
   - 包含：页面配置、侧边栏（照片上传）、主页面双列布局

3. **components/ui_styles.py** - UI样式组件
   - 类型：新增
   - 路径：`/Users/rensiyu01/Desktop/style-mirror/components/ui_styles.py`
   - 包含：CSS样式定义、通用UI渲染函数

4. **core/image_processor.py** - 视觉特征提取模块
   - 类型：新增
   - 路径：`/Users/rensiyu01/Desktop/style-mirror/core/image_processor.py`
   - 包含：图像预处理函数、多模态模型接口预留

5. **core/retriever.py** - 笔记检索模块
   - 类型：新增
   - 路径：`/Users/rensiyu01/Desktop/style-mirror/core/retriever.py`
   - 包含：Mock 数据加载函数、检索逻辑预留

6. **core/virtual_tryon.py** - 虚拟试穿模块
   - 类型：新增
   - 路径：`/Users/rensiyu01/Desktop/style-mirror/core/virtual_tryon.py`
   - 包含：图像合成函数预留

7. **data/mock_notes.json** - 模拟笔记数据
   - 类型：新增
   - 路径：`/Users/rensiyu01/Desktop/style-mirror/data/mock_notes.json`
   - 包含：2条示例笔记数据

8. **prompts/agent_prompts.py** - Agent提示词
   - 类型：新增
   - 路径：`/Users/rensiyu01/Desktop/style-mirror/prompts/agent_prompts.py`
   - 包含：点点 Agent 系统提示词常量

## 实现细节

### 1. requirements.txt
```python
# 基础依赖
streamlit>=1.28.0
pandas>=2.0.0
pillow>=10.0.0
requests>=2.31.0

# 可选：多模态模型相关（后续扩展）
# torch>=2.0.0
# transformers>=4.30.0
```

### 2. app.py 核心结构
```python
import streamlit as st
from components.ui_styles import apply_custom_styles

# 页面配置
st.set_page_config(
    page_title="✨ 点点 StyleMirror - 小红书多模态试用",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 应用自定义样式
apply_custom_styles()

# 侧边栏：用户照片上传
with st.sidebar:
    st.header("📸 上传你的照片")
    uploaded_file = st.file_uploader(
        "选择照片",
        type=['jpg', 'png'],
        help="支持 JPG 和 PNG 格式"
    )

# 主页面：双列布局
col1, col2 = st.columns(2)

with col1:
    st.header("📷 原图与 Vibe 识别")
    # 原图展示
    # Vibe 识别结果展示（占位）

with col2:
    st.header("👗 点点 Agent 推荐")
    # Agent 对话框
    # 推荐单品合成效果（占位）
```

### 3. prompts/agent_prompts.py
```python
DIANDIAN_SYSTEM_PROMPT = """
你是小红书点点 Agent，一个温暖、亲切的穿搭助手 💫

## 人设特点：
- 语气亲切自然，像朋友一样交流
- 善用 Emoji 增添趣味性 ✨
- 强调"氛围感"、"穿搭灵感"、"风格定位"
- 用小红书特有的语言风格（集美、宝子们等）

## 核心能力：
1. 识别用户照片的视觉风格（Vibe）
2. 推荐适合的穿搭单品
3. 提供搭配建议和灵感

## 对话风格示例：
"宝子，我看到了你的照片～ 这个氛围感太绝了！✨ 
我觉得很适合慵懒法式风哦，要不要试试看？"
"""
```

### 4. data/mock_notes.json 数据结构
```json
[
  {
    "note_id": "note_001",
    "item_img_url": "https://example.com/item1.jpg",
    "vibe_tags": ["法式慵懒", "复古浪漫", "温柔优雅"],
    "caption": "复古法式穿搭 | 这套太有氛围感了✨ 波点连衣裙+小香风外套，优雅又浪漫～"
  },
  {
    "note_id": "note_002",
    "item_img_url": "https://example.com/item2.jpg",
    "vibe_tags": ["简约通勤", "知性优雅", "职场穿搭"],
    "caption": "职场通勤穿搭分享 👔 白衬衫+阔腿裤，简约又不失气质，轻松打造知性优雅范儿～"
  }
]
```

## 边界条件与异常处理

1. **文件上传**
   - 限制文件类型：仅支持 jpg/png
   - 文件大小限制：建议不超过 10MB
   - 异常提示：上传错误时给出友好提示

2. **图像处理**
   - 空文件处理：检查文件是否为空
   - 格式验证：验证图像格式是否正确
   - 异常捕获：捕获 PIL 处理异常

3. **数据加载**
   - JSON 文件不存在：提供默认空数据
   - JSON 格式错误：捕获异常并提示

## 数据流路径

```
用户上传照片 
  ↓
app.py 接收文件
  ↓
image_processor.py 预处理图像
  ↓
（预留）多模态模型提取 Vibe 特征
  ↓
retriever.py 检索相关笔记
  ↓
virtual_tryon.py 合成试穿效果
  ↓
Agent 对话 + 结果展示
```

## 预期成果

完成项目初始化后，应具备：
1. ✅ 完整的项目目录结构
2. ✅ 可运行的 Streamlit 应用骨架
3. ✅ 用户照片上传功能
4. ✅ 清晰的模块划分和接口预留
5. ✅ Mock 数据和 Agent 提示词
6. ✅ 带有中文注释的代码，便于后续扩展

## 后续扩展方向

1. **多模态模型集成**
   - 接入 CLIP、BLIP 等视觉语言模型
   - 实现真实的 Vibe 特征提取

2. **检索优化**
   - 接入向量数据库（如 Pinecone、Milvus）
   - 实现基于向量相似度的检索

3. **虚拟试穿**
   - 接入图像生成模型（如 Stable Diffusion）
   - 实现 In-painting 试穿效果

4. **Agent 能力增强**
   - 集成 LLM（如 GPT-4、Claude）
   - 实现多轮对话和上下文记忆
