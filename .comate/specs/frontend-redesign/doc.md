# StyleMirror 前端重构规格文档

## 项目概述
本次重构旨在彻底重写 `app.py` 的渲染逻辑，完美适配升级后的 `image_processor.py`，实现小红书（XHS）风格的视觉体验。

## 需求场景

### 视觉风格目标
1. **小红书红**：全局主色调 #FF2442
2. **圆角容器**：15px 圆角 + 微弱阴影
3. **字体**：系统无衬线字体，字间距收缩
4. **背景**：纯白背景，干净清爽

### 核心组件
1. **Color Lab**：色彩实验室，圆形色块横向排列
2. **Scene Tags**：场景标签，胶囊形状灰色背景
3. **点点打字机**：流式输出效果

### 布局结构
```
┌─────────────────────────────────────────────────────────┐
│  侧边栏（API 设置）                                        │
├─────────────────────────────────────────────────────────┤
│  主界面                                                  │
│  ┌────────────────────┬────────────────────────────────┐│
│  │ 左侧               │ 右侧                            ││
│  │ • 上传区           │ • 点点对话区（带头像）           ││
│  │ • 原图预览         │ • 单品推荐瀑布流卡片            ││
│  │ • AI 视觉感知区    │                                 ││
│  │   - 风格标签       │                                 ││
│  │   - 色块           │                                 ││
│  │   - 场景词         │                                 ││
│  └────────────────────┴────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

## 技术架构

### CSS 注入策略
```python
def inject_xhs_styles():
    """注入小红书风格 CSS"""
    st.markdown("""
    <style>
        /* 全局样式 */
        :root {
            --xhs-red: #FF2442;
            --xhs-red-light: #FF6B81;
            --xhs-bg: #FAFAFA;
            --xhs-card: #FFFFFF;
            --xhs-text: #333333;
            --xhs-gray: #999999;
        }
        
        /* 字体 */
        body, .stMarkdown, .stButton {
            font-family: -apple-system, BlinkMacSystemFont, 
                         'Segoe UI', 'PingFang SC', 
                         'Hiragino Sans GB', sans-serif;
            letter-spacing: -0.02em;
        }
        
        /* 容器圆角 */
        .xhs-card {
            background: var(--xhs-card);
            border-radius: 15px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            padding: 20px;
            margin: 12px 0;
        }
    </style>
    """, unsafe_allow_html=True)
```

### 核心组件实现

#### 1. Color Lab（色彩实验室）
```python
def render_color_lab(colors: List[str]):
    """
    渲染色彩实验室
    
    特性：
    - 30px 直径圆形色块
    - 横向排列
    - 悬停显示色号
    - 点击复制功能
    """
    html = '<div class="color-lab">'
    for color in colors:
        html += f'''
        <div class="color-dot" 
             style="background-color: {color};"
             onclick="navigator.clipboard.writeText('{color}')"
             title="点击复制: {color}">
        </div>
        '''
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
```

#### 2. Scene Tags（场景标签）
```python
def render_scene_tags(keywords: List[str]):
    """
    渲染场景标签
    
    特性：
    - 胶囊形状
    - 灰色背景
    - 小红书风格
    """
    html = '<div class="scene-tags">'
    for keyword in keywords:
        html += f'<span class="scene-tag">{keyword}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
```

#### 3. 点点打字机
```python
def typewriter_effect(text: str, container, speed: float = 0.03):
    """
    打字机效果
    
    特性：
    - time.sleep 控制速度
    - 流式输出
    - 模拟思考过程
    """
    placeholder = container.empty()
    displayed = ""
    for char in text:
        displayed += char
        placeholder.markdown(f"<div class='typewriter'>{displayed}</div>", 
                           unsafe_allow_html=True)
        time.sleep(speed)
```

## 受影响的文件

### app.py
- **类型**：重写
- **路径**：`/Users/rensiyu01/Desktop/style-mirror/app.py`

**重构内容**：
1. CSS 注入函数 `inject_xhs_styles()`
2. 核心组件：`render_color_lab()`, `render_scene_tags()`, `typewriter_effect()`
3. 布局重构：侧边栏 + 双列主界面
4. 点点对话区带头像
5. 单品推荐瀑布流卡片

## 实现细节

### 1. 视觉风格 CSS

```css
/* 小红书主色 */
--xhs-red: #FF2442;

/* 圆角容器 */
.xhs-card {
    border-radius: 15px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    background: #FFFFFF;
}

/* 色彩实验室 */
.color-lab {
    display: flex;
    gap: 10px;
    margin: 16px 0;
}

.color-dot {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    cursor: pointer;
    transition: transform 0.2s;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

.color-dot:hover {
    transform: scale(1.15);
}

/* 场景标签 */
.scene-tag {
    display: inline-block;
    background: #F5F5F5;
    color: #666;
    padding: 6px 14px;
    border-radius: 16px;
    margin: 4px;
    font-size: 13px;
}

/* 点点头像 */
.agent-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #FF2442, #FF6B81);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
}

/* 打字机效果 */
.typewriter {
    font-size: 15px;
    line-height: 1.8;
    color: #333;
}

/* 瀑布流卡片 */
.waterfall-card {
    break-inside: avoid;
    margin-bottom: 16px;
    border-radius: 15px;
    overflow: hidden;
}
```

### 2. 布局结构

```python
# 侧边栏：API 设置
with st.sidebar:
    st.title("⚙️ API 配置")
    api_key = st.text_input("API Key", type="password")
    base_url = st.text_input("Base URL")
    # ...

# 主界面：双列
col1, col2 = st.columns([1, 1.2])

with col1:
    # 左侧
    render_upload_area()
    render_image_preview()
    render_vibe_analysis()

with col2:
    # 右侧
    render_agent_chat()
    render_waterfall_cards()
```

### 3. 点点对话区

```python
def render_agent_chat(vibe_result: dict):
    """渲染点点对话区"""
    st.markdown("""
    <div class="xhs-card agent-chat">
        <div class="agent-header">
            <div class="agent-avatar">🎀</div>
            <div class="agent-info">
                <span class="agent-name">點點 Agent</span>
                <span class="agent-status">正在分析...</span>
            </div>
        </div>
        <div class="agent-message">
            {description}
        </div>
    </div>
    """, unsafe_allow_html=True)
```

### 4. 瀑布流卡片

```python
def render_waterfall_cards(notes: List[dict]):
    """渲染瀑布流单品卡片"""
    st.markdown('<div class="waterfall-container">', unsafe_allow_html=True)
    
    for note in notes:
        st.markdown(f"""
        <div class="waterfall-card xhs-card">
            <div class="card-header">
                <img src="{note['author_avatar']}" class="author-avatar">
                <span class="author-name">{note['author']}</span>
            </div>
            <div class="card-content">
                {note['caption']}
            </div>
            <div class="card-items">
                <!-- 单品列表 -->
            </div>
            <div class="card-footer">
                <span>❤️ {note['likes']}</span>
                <span>⭐ {note['collects']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
```

## 边界条件

1. **色彩板为空**：不显示 Color Lab 区域
2. **场景词为空**：不显示 Scene Tags 区域
3. **无匹配笔记**：显示友好提示
4. **API 未配置**：显示 Mock 模式提示

## 预期成果

1. ✅ 完美的小红书视觉风格
2. ✅ Color Lab 色彩实验室
3. ✅ Scene Tags 场景标签
4. ✅ 点点打字机效果
5. ✅ 瀑布流单品卡片
6. ✅ 整体布局简洁美观
