# StyleMirror 核心逻辑完善规格文档

## 项目概述
本次任务旨在完善 StyleMirror 项目的核心逻辑，实现从用户上传图片到风格识别、笔记检索、Agent推荐的完整交互流程。

## 需求场景

### 用户交互流程
1. 用户上传照片 → 触发 `analyze_vibe()` 分析风格
2. 页面左侧展示 AI 识别到的 Vibe 标签（法式復古/極簡工業/溫柔原木）
3. 调用 `get_matching_notes()` 检索匹配的笔记
4. 页面右侧展示点点 Agent 的推荐理由和单品图片
5. 整体布局优化，增加小红书风格的视觉效果

### 核心功能点
1. **风格识别**：模拟多模态模型返回风格标签和描述
2. **笔记匹配**：根据 Vibe 标签从 mock_notes.json 中筛选笔记
3. **Agent 对话**：结合系统提示词生成拟人化推荐理由
4. **视觉优化**：紧凑布局、小红书风格边框标签

## 技术架构

### 数据流
```
用户上传图片
    ↓
analyze_vibe(image)
    → 随机返回风格标签（法式復古/極簡工業/溫柔原木）
    → 生成光影和材质描述
    ↓
get_matching_notes(vibe_tag)
    → 读取 data/mock_notes.json
    → 筛选 vibe_tags 包含该标签的笔记
    ↓
页面展示
    → 左侧：Vibe 标签（st.info）
    → 右侧：Agent 推荐理由 + 单品图片
```

## 受影响的文件

### 修改文件（共3个）

#### 1. core/image_processor.py
- **类型**：修改
- **路径**：`/Users/rensiyu01/Desktop/style-mirror/core/image_processor.py`
- **修改内容**：
  - 新增 `analyze_vibe(image)` 函数
  - 随机从 ["法式復古", "極簡工業", "溫柔原木"] 中返回风格标签
  - 生成光影和材质描述

#### 2. core/retriever.py
- **类型**：修改
- **路径**：`/Users/rensiyu01/Desktop/style-mirror/core/retriever.py`
- **修改内容**：
  - 新增 `get_matching_notes(vibe_tag)` 函数
  - 读取 mock_notes.json 并匹配 vibe_tags

#### 3. app.py
- **类型**：修改
- **路径**：`/Users/rensiyu01/Desktop/style-mirror/app.py`
- **修改内容**：
  - 完善交互逻辑：上传图片后触发分析
  - 左侧展示 Vibe 标签（st.info）
  - 右侧展示 Agent 推荐和单品图片
  - 优化布局（container、columns）
  - 添加小红书风格边框和标签

## 实现细节

### 1. analyze_vibe 函数
```python
def analyze_vibe(image: Image.Image) -> Dict:
    """
    分析图像的风格特征（模拟多模态模型）
    
    Args:
        image: PIL 图像对象
        
    Returns:
        Dict: {
            "vibe_tag": "法式復古" | "極簡工業" | "溫柔原木",
            "description": "光影与材质描述"
        }
    """
    import random
    
    vibe_options = ["法式復古", "極簡工業", "溫柔原木"]
    selected_vibe = random.choice(vibe_options)
    
    # 根据不同风格生成描述
    descriptions = {
        "法式復古": "柔和的暖色調光線，搭配復古材質的傢俱和裝飾，整體呈現出優雅浪漫的氛圍感～",
        "極簡工業": "冷色調的自然光，搭配金屬和混凝土材質，展現簡約而有力的現代美學～",
        "溫柔原木": "溫暖的日光灑落，原木紋理與棉麻材質交織，營造出舒適放鬆的生活感～"
    }
    
    return {
        "vibe_tag": selected_vibe,
        "description": descriptions[selected_vibe]
    }
```

### 2. get_matching_notes 函数
```python
def get_matching_notes(vibe_tag: str) -> List[Dict]:
    """
    根据风格标签匹配笔记
    
    Args:
        vibe_tag: 风格标签
        
    Returns:
        List[Dict]: 匹配的笔记列表
    """
    notes = load_mock_notes()
    matched = [note for note in notes if vibe_tag in note.get("vibe_tags", [])]
    return matched
```

### 3. app.py 核心逻辑修改

#### 上传图片后触发分析
```python
if uploaded_file is not None:
    image = preprocess_image(uploaded_file)
    if image:
        st.session_state.uploaded_image = image
        
        # 自动触发分析
        if st.session_state.vibe_result is None:
            vibe_result = analyze_vibe(image)
            st.session_state.vibe_result = vibe_result
            
            matched_notes = get_matching_notes(vibe_result["vibe_tag"])
            st.session_state.recommended_notes = matched_notes
            st.rerun()
```

#### 左侧展示 Vibe 标签
```python
with col1:
    if st.session_state.vibe_result:
        vibe = st.session_state.vibe_result
        st.info(f"🎨 AI 識別到的 Vibe 標籤：**{vibe['vibe_tag']}**")
        st.write(f"**風格描述：** {vibe['description']}")
```

#### 右侧展示 Agent 推荐
```python
with col2:
    if st.session_state.recommended_notes:
        # 生成 Agent 推荐理由
        agent_msg = f"寶子～ 我覺得你的風格很適合「{vibe_tag}」！✨\n\n{description}\n\n為你推薦以下穿搭靈感～"
        render_agent_message(agent_msg)
        
        # 展示推荐单品图片
        for note in notes:
            # ... 展示图片和标签
```

### 4. 视觉优化

#### 小红书风格单品卡片
```python
def render_item_card(item_name: str, category: str, color: str):
    """渲染小红书风格单品卡片"""
    st.markdown(f"""
    <div style="
        border: 2px solid #ff2442;
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
    ">
        <p style="margin: 0; font-weight: bold; color: #333;">👗 {item_name}</p>
        <p style="margin: 4px 0 0 0; font-size: 12px; color: #666;">
            {category} | {color}
        </p>
    </div>
    """, unsafe_allow_html=True)
```

## 边界条件与异常处理

1. **图片上传**
   - 空文件检查
   - 格式验证

2. **风格匹配**
   - 无匹配笔记时的友好提示
   - Mock 数据为空的处理

3. **会话状态**
   - 上传新图片时重置旧状态
   - 避免重复分析

## 预期成果

1. ✅ 上传图片后自动识别风格
2. ✅ 左侧清晰展示 Vibe 标签和描述
3. ✅ 右侧展示 Agent 推荐和单品
4. ✅ 布局紧凑美观
5. ✅ 小红书风格视觉效果
