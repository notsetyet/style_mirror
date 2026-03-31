# StyleMirror 引擎适配重构规格文档

## 项目概述
本次重构旨在适配新升级的 `core/image_processor.py`，更新 `app.py` 和 `core/retriever.py` 以支持更丰富的视觉分析结果和动态 API 配置。

## 需求场景

### 新增功能点
1. **API 配置侧边栏**：用户可动态配置 API Key 和 Base URL
2. **色彩板可视化**：以色块形式展示 `color_palette`
3. **场景关键词展示**：以小标签（pills）形式展示 `scene_keywords`
4. **增强检索逻辑**：支持 `scene_keywords` 作为匹配维度的加权项
5. **优雅降级**：无匹配笔记时返回默认推荐

### 数据流变化
```
用户配置 API Key / Base URL
    ↓
上传照片 → analyze_vibe(image, api_key, base_url)
    ↓
返回增强数据：
{
    "vibe_tag": "法式復古",
    "description": "风格描述",
    "color_palette": ["#D4A574", "#8B7355", "#F5E6D3"],
    "scene_keywords": ["咖啡馆", "居家"],
    "confidence": 0.85
}
    ↓
get_matching_notes(vibe_tag, scene_keywords)
    ↓
页面展示：
- 左侧：Vibe 标签 + 色块 + 场景标签
- 右侧：点点 Agent 开场白（description）
```

## 受影响的文件

### 1. app.py
- **类型**：修改
- **路径**：`/Users/rensiyu01/Desktop/style-mirror/app.py`

**修改内容**：
- 侧边栏新增 API Key 输入框（password 类型）
- 侧边栏新增 Base URL 输入框（选填）
- 调用 `analyze_vibe` 时传入 `api_key` 和 `base_url`
- 左侧新增色彩板可视化（HTML 色块圆圈）
- 左侧新增场景关键词展示（pills 标签）
- 右侧 Agent 开场白改用 `description` 字段

### 2. core/retriever.py
- **类型**：修改
- **路径**：`/Users/rensiyu01/Desktop/style-mirror/core/retriever.py`

**修改内容**：
- `get_matching_notes` 新增 `scene_keywords` 参数
- 实现基于 `scene_keywords` 的加权匹配逻辑
- 无匹配时返回默认推荐，避免前端报错

## 实现细节

### 1. 侧边栏 API 配置

```python
with st.sidebar:
    # ... 现有内容 ...
    
    st.divider()
    st.subheader("⚙️ API 配置")
    
    api_key = st.text_input(
        "API Key",
        type="password",
        placeholder="sk-...",
        help="OpenAI API Key，用于多模态模型调用"
    )
    
    base_url = st.text_input(
        "Base URL（选填）",
        placeholder="https://api.openai.com/v1",
        help="API 代理地址，支持国产模型中转"
    )
```

### 2. 色彩板可视化（HTML 色块）

```python
def render_color_palette(colors: List[str]):
    """渲染色彩板色块"""
    color_html = '<div style="display: flex; gap: 8px; margin: 12px 0;">'
    for color in colors:
        color_html += f'''
        <div style="
            width: 40px;
            height: 40px;
            background-color: {color};
            border-radius: 50%;
            border: 2px solid #fff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        " title="{color}"></div>
        '''
    color_html += '</div>'
    st.markdown(color_html, unsafe_allow_html=True)
```

### 3. 场景关键词展示（Pills 标签）

```python
def render_scene_keywords(keywords: List[str]):
    """渲染场景关键词标签"""
    html = '<div style="margin: 8px 0;">'
    for keyword in keywords:
        html += f'''
        <span style="
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 16px;
            margin: 4px;
            font-size: 13px;
        ">{keyword}</span>
        '''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
```

### 4. 增强检索逻辑

```python
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
    """
    all_notes = load_mock_notes()
    
    if not all_notes:
        return _get_default_recommendations()
    
    scored_notes = []
    for note in all_notes:
        score = 0
        
        # Vibe 标签匹配
        if vibe_tag in note.get("vibe_tags", []):
            score += 10
        
        # 场景关键词匹配（加权）
        if scene_keywords:
            note_caption = note.get("caption", "").lower()
            for keyword in scene_keywords:
                if keyword.lower() in note_caption:
                    score += 5
        
        if score > 0:
            scored_notes.append({**note, "match_score": score})
    
    # 排序
    scored_notes.sort(key=lambda x: x.get("match_score", 0), reverse=True)
    
    # 无匹配时返回默认
    if not scored_notes:
        return _get_default_recommendations()
    
    return scored_notes[:top_k]
```

### 5. 默认推荐逻辑

```python
def _get_default_recommendations() -> List[Dict]:
    """
    获取默认推荐（当无匹配时）
    
    返回最受欢迎的笔记作为兜底
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
    return sorted_notes[:2]
```

## 会话状态变更

新增以下会话状态：
```python
st.session_state.api_key = None      # API Key
st.session_state.base_url = None     # Base URL
```

## 边界条件与异常处理

1. **API Key 为空**：`analyze_vibe` 内部已处理降级逻辑
2. **无匹配笔记**：返回默认推荐，前端展示友好提示
3. **色彩板为空**：不展示色块区域
4. **场景关键词为空**：不展示标签区域

## 预期成果

1. ✅ 侧边栏支持动态配置 API
2. ✅ 左侧展示色彩板（色块圆圈）
3. ✅ 左侧展示场景关键词（pills 标签）
4. ✅ 右侧使用 description 作为点点开场白
5. ✅ 检索支持 scene_keywords 加权
6. ✅ 无匹配时优雅返回默认推荐
