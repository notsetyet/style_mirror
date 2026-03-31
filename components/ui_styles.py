# -*- coding: utf-8 -*-
"""
StyleMirror - UI 样式组件模块
定义自定义 CSS 样式和通用 UI 渲染函数
"""

import streamlit as st

# ============================================
# 自定义 CSS 样式（小红书风格配色）
# ============================================

CUSTOM_CSS = """
<style>
    /* 全局样式 */
    .main {
        background-color: #fafafa;
    }
    
    /* 标题样式 */
    h1, h2, h3 {
        color: #333333;
        font-weight: 600;
    }
    
    /* 小红书主题色 */
    .xhs-primary {
        color: #ff2442;
    }
    
    .xhs-secondary {
        color: #fe2c55;
    }
    
    /* 卡片样式 */
    .card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 16px;
    }
    
    /* 上传区域样式 */
    .upload-area {
        border: 2px dashed #ff2442;
        border-radius: 12px;
        padding: 30px;
        text-align: center;
        background-color: #fff5f5;
    }
    
    /* Vibe 标签样式 */
    .vibe-tag {
        display: inline-block;
        background: linear-gradient(135deg, #ff2442 0%, #fe2c55 100%);
        color: white;
        padding: 6px 16px;
        border-radius: 20px;
        margin: 4px;
        font-size: 14px;
    }
    
    /* Agent 对话框样式 */
    .agent-message {
        background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
        border-left: 4px solid #ff2442;
        padding: 16px;
        border-radius: 0 12px 12px 0;
        margin: 12px 0;
    }
    
    /* 推荐卡片样式 */
    .recommend-card {
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    
    .recommend-card:hover {
        transform: translateY(-4px);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: linear-gradient(135deg, #ff2442 0%, #fe2c55 100%);
        color: white;
        border: none;
        border-radius: 24px;
        padding: 12px 32px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(255,36,66,0.3);
    }
    
    /* 侧边栏样式 */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
    }
    
    /* 图片容器 */
    .image-container {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* 占位符样式 */
    .placeholder-box {
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        color: #999999;
    }
</style>
"""


# ============================================
# 样式应用函数
# ============================================

def apply_custom_styles():
    """
    应用自定义 CSS 样式到 Streamlit 应用
    在 app.py 的页面配置后调用
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================
# 通用 UI 渲染函数
# ============================================

def render_card(content: str, title: str = None):
    """
    渲染卡片样式的容器
    
    Args:
        content: 卡片内容（支持 HTML）
        title: 可选的卡片标题
    """
    html = '<div class="card">'
    if title:
        html += f'<h4>{title}</h4>'
    html += content
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_vibe_tags(tags: list):
    """
    渲染 Vibe 标签列表
    
    Args:
        tags: 标签列表，如 ["法式慵懒", "复古浪漫"]
    """
    html = '<div style="margin: 12px 0;">'
    for tag in tags:
        html += f'<span class="vibe-tag">{tag}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_agent_message(message: str):
    """
    渲染 Agent 对话消息
    
    Args:
        message: Agent 的回复内容
    """
    html = f'''
    <div class="agent-message">
        <p style="margin: 0; line-height: 1.8;">{message}</p>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def render_placeholder(text: str = "功能开发中，敬请期待 ✨"):
    """
    渲染占位符框
    
    Args:
        text: 占位提示文本
    """
    html = f'''
    <div class="placeholder-box">
        <p style="font-size: 16px; margin: 0;">{text}</p>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)


def render_recommend_card(note_data: dict):
    """
    渲染推荐笔记卡片
    
    Args:
        note_data: 笔记数据字典
    """
    html = f'''
    <div class="recommend-card">
        <div style="padding: 16px;">
            <p style="font-weight: 600; margin-bottom: 8px;">{note_data.get("caption", "")[:50]}...</p>
            <div style="margin: 8px 0;">
                {" ".join([f'<span class="vibe-tag" style="font-size: 12px;">{tag}</span>' for tag in note_data.get("vibe_tags", [])])}
            </div>
            <p style="color: #999; font-size: 12px;">❤️ {note_data.get("likes", 0)} · ⭐ {note_data.get("collects", 0)}</p>
        </div>
    </div>
    '''
    st.markdown(html, unsafe_allow_html=True)
