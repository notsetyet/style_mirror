# -*- coding: utf-8 -*-
"""
StyleMirror - 小红书点点 Agent 多模态试用原型
Streamlit 主程序入口

视觉风格：完美适配小红书（XHS）设计语言
核心组件：Color Lab / Scene Tags / 点点打字机 / 匹配度可视化
布局结构：侧边栏 API 配置 + 双列主界面 + 图文混合搜索

Author: StyleMirror Team
Version: v4.1 (Dotenv Integration + API 状态显示)
"""

import streamlit as st
from PIL import Image
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入自定义模块
from components.ui_styles import apply_custom_styles
from prompts.agent_prompts import DIANDIAN_SYSTEM_PROMPT
from core.image_processor import (
    preprocess_image, 
    analyze_vibe,
    check_api_config,
    get_api_status_message
)
from core.retriever import get_matching_notes, get_matching_notes_v2

# ============================================
# 页面配置（必须放在最前面）
# ============================================

st.set_page_config(
    page_title="點點 StyleMirror - 小紅書多模態試用",
    page_icon="🎀",
    layout="wide",
    initial_sidebar_state="collapsed",  # 默认收起侧边栏
    menu_items={
        'About': "StyleMirror - 小紅書點點 Agent 多模態試用原型 | Made with ❤️"
    }
)

# ============================================
# Task 1: CSS 注入与全局样式定义
# ============================================

def inject_xhs_styles():
    """注入小红书风格 CSS"""
    st.markdown("""
    <style>
        /* ========== 全局变量 ========== */
        :root {
            --xhs-red: #FF2442;
            --xhs-red-light: #FF6B81;
            --xhs-red-dark: #E91E45;
            --xhs-bg: #FAFAFA;
            --xhs-card: #FFFFFF;
            --xhs-text: #333333;
            --xhs-text-secondary: #666666;
            --xhs-gray: #999999;
            --xhs-border: #EEEEEE;
            --xhs-green: #52C41A;
            --xhs-orange: #FA8C16;
        }
        
        /* ========== 全局样式 ========== */
        body, .stMarkdown, .stButton, p, span, div {
            font-family: -apple-system, BlinkMacSystemFont, 
                         'Segoe UI', 'PingFang SC', 
                         'Hiragino Sans GB', 'Microsoft YaHei',
                         sans-serif !important;
            letter-spacing: -0.02em;
        }
        
        /* 隐藏 Streamlit 默认元素 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* 主容器背景 */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            background-color: var(--xhs-bg);
        }
        
        /* ========== XHS 卡片容器 ========== */
        .xhs-card {
            background: var(--xhs-card);
            border-radius: 15px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            padding: 20px;
            margin: 12px 0;
            transition: box-shadow 0.3s ease;
        }
        
        .xhs-card:hover {
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
        }
        
        /* ========== 上传区域 ========== */
        .upload-zone {
            border: 2px dashed var(--xhs-red);
            border-radius: 15px;
            padding: 40px 20px;
            text-align: center;
            background: linear-gradient(135deg, #FFF5F5 0%, #FFFFFF 100%);
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .upload-zone:hover {
            border-color: var(--xhs-red-dark);
            background: linear-gradient(135deg, #FFE8E8 0%, #FFF5F5 100%);
        }
        
        /* ========== 用户输入区 ========== */
        .user-input-container {
            background: linear-gradient(135deg, #FFF9E6 0%, #FFFFFF 100%);
            border-radius: 15px;
            padding: 16px;
            margin: 16px 0;
            border: 1px solid #FFE7BA;
        }
        
        .user-input-title {
            font-size: 14px;
            color: #666;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        /* ========== 意图修正按钮组 ========== */
        .intent-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 12px;
        }
        
        .intent-btn {
            background: #F5F5F5;
            border: 1px solid #E8E8E8;
            border-radius: 20px;
            padding: 6px 14px;
            font-size: 13px;
            color: #666;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .intent-btn:hover {
            background: var(--xhs-red);
            color: white;
            border-color: var(--xhs-red);
        }
        
        /* ========== 风格标签 ========== */
        .vibe-tag {
            display: inline-flex;
            align-items: center;
            background: linear-gradient(135deg, var(--xhs-red) 0%, var(--xhs-red-light) 100%);
            color: white;
            padding: 10px 24px;
            border-radius: 25px;
            font-size: 18px;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(255, 36, 66, 0.3);
            margin: 8px 0;
        }
        
        /* ========== 色彩实验室 (Color Lab) ========== */
        .color-lab {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 16px 0;
            flex-wrap: wrap;
        }
        
        .color-lab-title {
            font-size: 14px;
            color: var(--xhs-gray);
            margin-right: 8px;
        }
        
        .color-dot {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            border: 2px solid white;
            position: relative;
        }
        
        .color-dot:hover {
            transform: scale(1.2);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
        }
        
        .color-dot-wrapper {
            position: relative;
            display: inline-block;
        }
        
        .color-tooltip {
            position: absolute;
            bottom: -28px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            white-space: nowrap;
            opacity: 0;
            transition: opacity 0.2s;
            pointer-events: none;
        }
        
        .color-dot-wrapper:hover .color-tooltip {
            opacity: 1;
        }
        
        /* ========== 场景标签 (Scene Tags) ========== */
        .scene-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 12px 0;
        }
        
        .scene-tag {
            display: inline-block;
            background: #F5F5F5;
            color: #666;
            padding: 6px 14px;
            border-radius: 16px;
            font-size: 13px;
            transition: all 0.2s ease;
        }
        
        .scene-tag:hover {
            background: #EEEEEE;
            color: var(--xhs-red);
        }
        
        /* ========== 点点 Agent 对话区 ========== */
        .agent-chat-container {
            background: linear-gradient(135deg, #FFF5F5 0%, #FFFFFF 100%);
            border-radius: 15px;
            padding: 20px;
            margin: 12px 0;
            border-left: 4px solid var(--xhs-red);
        }
        
        .agent-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }
        
        .agent-avatar {
            width: 48px;
            height: 48px;
            border-radius: 50%;
            background: linear-gradient(135deg, var(--xhs-red) 0%, var(--xhs-red-light) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            box-shadow: 0 4px 15px rgba(255, 36, 66, 0.3);
        }
        
        .agent-info {
            display: flex;
            flex-direction: column;
        }
        
        .agent-name {
            font-weight: 600;
            font-size: 16px;
            color: var(--xhs-text);
        }
        
        .agent-status {
            font-size: 12px;
            color: var(--xhs-gray);
        }
        
        .agent-message {
            font-size: 15px;
            line-height: 1.8;
            color: var(--xhs-text);
            padding: 12px 16px;
            background: white;
            border-radius: 12px;
        }
        
        /* ========== 打字机效果 ========== */
        .typewriter-cursor {
            display: inline-block;
            width: 2px;
            height: 1em;
            background: var(--xhs-red);
            animation: blink 0.8s infinite;
            margin-left: 2px;
            vertical-align: middle;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        
        /* ========== 单品瀑布流卡片 ========== */
        .waterfall-container {
            column-count: 2;
            column-gap: 16px;
        }
        
        .item-card {
            break-inside: avoid;
            background: var(--xhs-card);
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 16px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .item-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        .item-image {
            width: 100%;
            aspect-ratio: 1;
            object-fit: cover;
            background: linear-gradient(135deg, #F5F5F5 0%, #E8E8E8 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--xhs-gray);
            font-size: 14px;
        }
        
        .item-info {
            padding: 16px;
        }
        
        .item-name {
            font-weight: 600;
            font-size: 14px;
            color: var(--xhs-text);
            margin-bottom: 8px;
        }
        
        .item-meta {
            display: flex;
            gap: 8px;
            font-size: 12px;
            color: var(--xhs-gray);
        }
        
        .item-tag {
            background: #F5F5F5;
            padding: 2px 8px;
            border-radius: 4px;
        }
        
        /* ========== 笔记卡片 ========== */
        .note-card {
            background: var(--xhs-card);
            border-radius: 15px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
            position: relative;
        }
        
        .note-card:hover {
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
        }
        
        .note-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        
        .note-author {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .author-avatar {
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 12px;
        }
        
        .note-caption {
            font-size: 14px;
            color: var(--xhs-text);
            line-height: 1.6;
            margin-bottom: 12px;
        }
        
        .note-footer {
            display: flex;
            gap: 16px;
            font-size: 12px;
            color: var(--xhs-gray);
        }
        
        /* ========== 匹配度徽章 ========== */
        .match-badge {
            position: absolute;
            top: 12px;
            right: 12px;
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .match-badge.high {
            background: linear-gradient(135deg, #52C41A 0%, #73D13D 100%);
            color: white;
        }
        
        .match-badge.medium {
            background: linear-gradient(135deg, #FA8C16 0%, #FFA940 100%);
            color: white;
        }
        
        .match-badge.low {
            background: #F5F5F5;
            color: #999;
        }
        
        .match-badge-bar {
            width: 60px;
            height: 4px;
            background: rgba(255,255,255,0.3);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 4px;
        }
        
        .match-badge-fill {
            height: 100%;
            background: white;
            border-radius: 2px;
        }
        
        /* ========== 置信度进度条 ========== */
        .confidence-bar {
            background: #F5F5F5;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
            margin-top: 8px;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--xhs-red) 0%, var(--xhs-red-light) 100%);
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        
        /* ========== 空状态 ========== */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: var(--xhs-gray);
        }
        
        .empty-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        
        /* ========== 侧边栏样式 ========== */
        section[data-testid="stSidebar"] {
            background: var(--xhs-card);
        }
        
        section[data-testid="stSidebar"] .block-container {
            padding: 2rem 1rem;
        }
        
        /* ========== 按钮样式 ========== */
        .stButton > button {
            background: linear-gradient(135deg, var(--xhs-red) 0%, var(--xhs-red-light) 100%);
            color: white;
            border: none;
            border-radius: 25px;
            padding: 12px 32px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 36, 66, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 36, 66, 0.4);
        }
        
        /* ========== 分隔线 ========== */
        .divider {
            height: 1px;
            background: var(--xhs-border);
            margin: 20px 0;
        }
        
        /* ========== 搜索按钮 ========== */
        .search-button-container {
            display: flex;
            gap: 12px;
            margin-top: 16px;
        }
        
        /* ========== 检索状态 ========== */
        .search-status {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 16px;
            background: #F6FFED;
            border-radius: 10px;
            margin-bottom: 16px;
            border: 1px solid #B7EB8F;
        }
        
        .search-status-icon {
            font-size: 18px;
        }
        
        .search-status-text {
            font-size: 13px;
            color: #52C41A;
        }
    </style>
    """, unsafe_allow_html=True)


# 注入样式
inject_xhs_styles()


# ============================================
# Task 2: 核心组件开发
# ============================================

def render_color_lab(colors: List[str]):
    """
    渲染色彩实验室 (Color Lab)
    
    特性：
    - 30px 直径圆形色块
    - 横向排列
    - 悬停显示色号
    - 点击复制功能
    
    Args:
        colors: 十六进制色号列表
    """
    if not colors:
        return
    
    html = '<div class="color-lab">'
    html += '<span class="color-lab-title">🎨 提取色彩</span>'
    
    for color in colors:
        html += f'''
        <div class="color-dot-wrapper">
            <div class="color-dot" 
                 style="background-color: {color};"
                 onclick="navigator.clipboard.writeText('{color}')"
                 title="点击复制"></div>
            <span class="color-tooltip">{color}</span>
        </div>
        '''
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_scene_tags(keywords: List[str]):
    """
    渲染场景标签 (Scene Tags)
    
    特性：
    - 胶囊形状
    - 灰色背景
    - 悬停效果
    
    Args:
        keywords: 场景关键词列表
    """
    if not keywords:
        return
    
    html = '<div class="scene-tags">'
    html += '<span style="font-size: 14px; color: #999; margin-right: 8px;">📍 場景</span>'
    
    for keyword in keywords:
        html += f'<span class="scene-tag">{keyword}</span>'
    
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_vibe_tag(vibe_tag: str):
    """
    渲染风格标签
    
    Args:
        vibe_tag: 风格标签文本
    """
    st.markdown(f'''
    <div style="margin: 16px 0;">
        <span class="vibe-tag">✨ {vibe_tag}</span>
    </div>
    ''', unsafe_allow_html=True)


def render_confidence_bar(confidence: float):
    """
    渲染置信度进度条
    
    Args:
        confidence: 置信度 (0.0 - 1.0)
    """
    percentage = int(confidence * 100)
    st.markdown(f'''
    <div style="margin-top: 12px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
            <span style="font-size: 13px; color: #666;">分析置信度</span>
            <span style="font-size: 13px; color: #FF2442; font-weight: 600;">{percentage}%</span>
        </div>
        <div class="confidence-bar">
            <div class="confidence-fill" style="width: {percentage}%;"></div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def typewriter_effect(text: str, placeholder, speed: float = 0.02):
    """
    打字机效果输出
    
    Args:
        text: 要输出的文本
        placeholder: Streamlit placeholder 对象
        speed: 输出速度（秒/字符）
    """
    displayed = ""
    for char in text:
        displayed += char
        placeholder.markdown(f'''
        <div class="agent-message">
            {displayed}<span class="typewriter-cursor"></span>
        </div>
        ''', unsafe_allow_html=True)
        time.sleep(speed)
    
    # 完成后移除光标
    placeholder.markdown(f'''
    <div class="agent-message">
        {displayed}
    </div>
    ''', unsafe_allow_html=True)


def render_match_badge(hybrid_score: float):
    """
    渲染匹配度徽章
    
    根据得分显示不同样式：
    - 高匹配 (>= 70): 绿色
    - 中匹配 (>= 40): 橙色
    - 低匹配 (< 40): 灰色
    
    Args:
        hybrid_score: 混合得分 (0-100+)
    """
    # 归一化到 0-100
    score = min(100, max(0, hybrid_score))
    
    if score >= 70:
        badge_class = "high"
        icon = "🎯"
    elif score >= 40:
        badge_class = "medium"
        icon = "💫"
    else:
        badge_class = "low"
        icon = "📌"
    
    st.markdown(f'''
    <div class="match-badge {badge_class}">
        <span>{icon}</span>
        <span>{int(score)}%</span>
    </div>
    ''', unsafe_allow_html=True)


# ============================================
# 单品卡片渲染
# ============================================

def render_item_card(item: dict, note_id: str):
    """
    渲染单品卡片
    
    Args:
        item: 单品数据
        note_id: 笔记 ID
    """
    item_name = item.get("item_name", "未知單品")
    category = item.get("category", "")
    color = item.get("color", "")
    
    # 颜色映射
    color_map = {
        "黑色": "#1a1a1a", "白色": "#f5f5f5", "米白色": "#f5f0e6",
        "米色": "#f5e6d3", "卡其色": "#c4a77d", "深灰色": "#4a4a4a",
        "淺藍色": "#87ceeb", "黑底白點": "#1a1a1a"
    }
    bg_color = color_map.get(color, "#f0f0f0")
    
    st.markdown(f'''
    <div class="item-card">
        <div class="item-image" style="background: linear-gradient(135deg, {bg_color} 0%, #ffffff 100%);">
            <span>📷 {item_name}</span>
        </div>
        <div class="item-info">
            <div class="item-name">{item_name}</div>
            <div class="item-meta">
                <span class="item-tag">{category}</span>
                <span>🎨 {color}</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_note_card(note: dict, show_items: bool = True):
    """
    渲染笔记卡片（带匹配度徽章）
    
    Args:
        note: 笔记数据
        show_items: 是否展示单品
    """
    caption = note.get("caption", "")
    author = note.get("author", "@匿名")
    likes = note.get("likes", 0)
    collects = note.get("collects", 0)
    items = note.get("items", [])
    is_default = note.get("is_default", False)
    hybrid_score = note.get("hybrid_score", note.get("match_score", 0))
    
    # 作者头像首字母
    avatar_text = author[1] if len(author) > 1 else "👤"
    
    default_badge = "🔥 熱門推薦" if is_default else ""
    
    # 卡片容器（带匹配度徽章）
    st.markdown(f'''
    <div class="note-card">
        <div class="match-badge {"low" if is_default else ("high" if hybrid_score >= 70 else "medium")}">
            <span>{"🎯" if hybrid_score >= 70 else "💫" if hybrid_score >= 40 else "📌"}</span>
            <span>{int(min(100, hybrid_score))}% 匹配</span>
        </div>
        <div class="note-header">
            <div class="note-author">
                <div class="author-avatar">{avatar_text}</div>
                <span style="font-size: 13px; color: #666;">{author}</span>
            </div>
            <span style="font-size: 12px; color: #FF2442; font-weight: 600;">{default_badge}</span>
        </div>
        <div class="note-caption">{caption[:60]}...</div>
        <div class="note-footer">
            <span>❤️ {likes:,}</span>
            <span>⭐ {collects:,}</span>
            <span>📊 得分: {hybrid_score:.1f}</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # 展示单品
    if show_items and items:
        for item in items:
            render_item_card(item, note.get("note_id", ""))


# ============================================
# Task 3: 侧边栏重构
# ============================================

def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.markdown("### ⚙️ API 配置")
        st.caption("配置多模態模型接口")
        
        st.divider()
        
        # API Key
        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="sk-...",
            help="OpenAI API Key 或其他兼容接口",
            key="sidebar_api_key"
        )
        
        # Base URL
        base_url = st.text_input(
            "Base URL（選填）",
            placeholder="https://api.openai.com/v1",
            help="API 代理地址，支持國產模型中轉",
            key="sidebar_base_url"
        )
        
        # 状态指示
        st.divider()
        if api_key:
            st.success("✅ API 已配置")
        else:
            st.info("💡 未配置 API，使用模擬模式")
        
        st.divider()
        
        # 关于
        st.markdown("### 🎀 關於點點")
        with st.expander("查看詳情"):
            st.markdown(DIANDIAN_SYSTEM_PROMPT[:400] + "...")
        
        return api_key, base_url


# ============================================
# Task 4: 主界面布局重构
# ============================================

def render_upload_area():
    """渲染上传区域"""
    st.markdown('''
    <div class="upload-zone">
        <div style="font-size: 48px; margin-bottom: 12px;">📸</div>
        <div style="font-size: 16px; color: #FF2442; font-weight: 600; margin-bottom: 8px;">
            點擊或拖拽上傳照片
        </div>
        <div style="font-size: 13px; color: #999;">
            支持 JPG / PNG 格式，建議 10MB 以內
        </div>
    </div>
    ''', unsafe_allow_html=True)


def render_empty_state():
    """渲染空状态"""
    st.markdown('''
    <div class="empty-state">
        <div class="empty-icon">🎀</div>
        <div style="font-size: 18px; color: #666; margin-bottom: 8px;">
            歡迎來到點點 StyleMirror
        </div>
        <div style="font-size: 14px; color: #999;">
            上傳一張照片，讓 AI 分析你的風格 Vibe
        </div>
    </div>
    ''', unsafe_allow_html=True)


# ============================================
# 意图修正预设词
# ============================================

INTENT_PRESETS = [
    {"label": "颜色再深一点", "value": "颜色再深一点"},
    {"label": "更简约一点", "value": "更简约一点"},
    {"label": "适合约会", "value": "适合约会"},
    {"label": "适合通勤", "value": "适合通勤上班"},
    {"label": "更休闲", "value": "更休闲舒适"},
    {"label": "更正式", "value": "更正式得体"},
]


def render_intent_buttons():
    """渲染意图修正按钮"""
    st.markdown("💡 **快速微调**")
    
    cols = st.columns(3)
    for i, preset in enumerate(INTENT_PRESETS):
        col_idx = i % 3
        with cols[col_idx]:
            if st.button(preset["label"], key=f"intent_{i}"):
                st.session_state.user_text_modifier = preset["value"]
                st.rerun()


# ============================================
# Task 5: 点点 Agent 对话区
# ============================================

def render_agent_chat(vibe_result: dict, use_typewriter: bool = True):
    """
    渲染点点 Agent 对话区
    
    Args:
        vibe_result: 风格分析结果
        use_typewriter: 是否使用打字机效果
    """
    vibe_tag = vibe_result.get("vibe_tag", "未知風格")
    description = vibe_result.get("description", "")
    
    # 头部
    st.markdown('''
    <div class="agent-chat-container">
        <div class="agent-header">
            <div class="agent-avatar">🎀</div>
            <div class="agent-info">
                <span class="agent-name">點點 Agent</span>
                <span class="agent-status">在線 · 已完成分析</span>
            </div>
        </div>
    ''', unsafe_allow_html=True)
    
    # 开场白
    greeting = f"哈嘍寶子～ ✨ 我看了你的照片，覺得你的風格很有「**{vibe_tag}**」的感覺！\n\n"
    
    # 打字机效果
    if use_typewriter:
        placeholder = st.empty()
        typewriter_effect(greeting + description, placeholder)
    else:
        st.markdown(f'''
        <div class="agent-message">
            {greeting}{description}
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_search_status(user_text: str, vibe_description: str, result_count: int):
    """
    渲染搜索状态
    
    Args:
        user_text: 用户输入的文本
        vibe_description: 风格描述
        result_count: 检索结果数量
    """
    combined_query = f"{vibe_description} {user_text}".strip()
    
    st.markdown(f'''
    <div class="search-status">
        <span class="search-status-icon">✅</span>
        <span class="search-status-text">
            已完成语义检索 · 找到 <strong>{result_count}</strong> 条匹配笔记
        </span>
    </div>
    <div style="font-size: 12px; color: #999; margin-bottom: 16px; padding: 0 12px;">
        <strong>检索意图：</strong>{combined_query[:50]}{"..." if len(combined_query) > 50 else ""}
    </div>
    ''', unsafe_allow_html=True)


# ============================================
# 会话状态初始化
# ============================================

if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

if "vibe_result" not in st.session_state:
    st.session_state.vibe_result = None

if "recommended_notes" not in st.session_state:
    st.session_state.recommended_notes = []

if "last_file_id" not in st.session_state:
    st.session_state.last_file_id = None

if "api_key" not in st.session_state:
    st.session_state.api_key = None

if "base_url" not in st.session_state:
    st.session_state.base_url = None

if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False

if "user_text_modifier" not in st.session_state:
    st.session_state.user_text_modifier = ""

if "search_triggered" not in st.session_state:
    st.session_state.search_triggered = False


# ============================================
# 主程序
# ============================================

def main():
    """主程序入口"""
    
    # 渲染侧边栏
    api_key, base_url = render_sidebar()
    st.session_state.api_key = api_key if api_key else None
    st.session_state.base_url = base_url if base_url else None
    
    # 页面标题
    st.markdown('''
    <div style="text-align: center; margin-bottom: 24px;">
        <h1 style="font-size: 32px; margin-bottom: 8px;">
            <span style="color: #FF2442;">點點</span> StyleMirror
        </h1>
        <p style="color: #999; font-size: 14px;">
            小紅書多模態穿搭試用原型 | Powered by AI ✨
        </p>
    </div>
    ''', unsafe_allow_html=True)
    
    # ========== API 状态提示 ==========
    is_ready, mode, config = check_api_config()
    status_message = get_api_status_message()
    
    if is_ready:
        st.success(status_message)
    else:
        st.info(status_message)
    
    # 双列布局
    col1, col2 = st.columns([1, 1.2], gap="large")
    
    # ========== 左侧：上传 + 分析 ==========
    with col1:
        st.markdown("### 📸 上傳照片")
        
        # 上传区域
        uploaded_file = st.file_uploader(
            "選擇照片",
            type=['jpg', 'jpeg', 'png'],
            help="支持 JPG 和 PNG 格式",
            key="main_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            current_file_id = uploaded_file.file_id
            
            # 预处理图像
            image = preprocess_image(uploaded_file)
            if image:
                st.session_state.uploaded_image = image
                
                # 显示图片
                st.image(image, use_container_width=True)
                
                # 新文件触发分析
                if st.session_state.last_file_id != current_file_id:
                    st.session_state.last_file_id = current_file_id
                    st.session_state.analysis_complete = False
                    st.session_state.search_triggered = False
                    
                    with st.spinner("🎨 點點正在分析你的風格..."):
                        # 调用分析
                        vibe_result = analyze_vibe(
                            image,
                            api_key=st.session_state.api_key,
                            base_url=st.session_state.base_url
                        )
                        st.session_state.vibe_result = vibe_result
                    
                    st.rerun()
        
        else:
            render_empty_state()
        
        # ========== 图文混合搜索输入区 ==========
        if st.session_state.vibe_result:
            st.divider()
            
            # 用户文字输入
            st.markdown("### 💬 想對點點說什麼？")
            
            user_text = st.text_input(
                "补充你的需求",
                placeholder="如：颜色再深一点、要更小户型一点、适合约会...",
                value=st.session_state.user_text_modifier,
                key="user_text_input",
                label_visibility="collapsed"
            )
            
            # 意图修正按钮
            render_intent_buttons()
            
            # 搜索按钮
            col_search1, col_search2 = st.columns([1, 1])
            with col_search1:
                search_clicked = st.button("🔍 重新搜索", use_container_width=True)
            with col_search2:
                clear_clicked = st.button("🗑️ 清空输入", use_container_width=True)
            
            if clear_clicked:
                st.session_state.user_text_modifier = ""
                st.rerun()
            
            if search_clicked:
                st.session_state.user_text_modifier = user_text
                st.session_state.search_triggered = True
                
                # 调用 V2 检索
                vibe = st.session_state.vibe_result
                with st.spinner("🔍 正在进行语义检索..."):
                    matched_notes = get_matching_notes_v2(
                        vibe_description=vibe.get("description", ""),
                        user_text_modifier=user_text,
                        vibe_tag=vibe.get("vibe_tag", ""),
                        scene_keywords=vibe.get("scene_keywords", []),
                        api_key=st.session_state.api_key,
                        base_url=st.session_state.base_url,
                        top_k=5
                    )
                    st.session_state.recommended_notes = matched_notes
                
                st.rerun()
        
        # AI 视觉感知区
        if st.session_state.vibe_result:
            st.divider()
            st.markdown("### 🎨 AI 視覺感知")
            
            vibe = st.session_state.vibe_result
            
            # 风格标签
            render_vibe_tag(vibe.get("vibe_tag", "未知"))
            
            # 色彩实验室
            color_palette = vibe.get("color_palette", [])
            if color_palette:
                render_color_lab(color_palette)
            
            # 场景标签
            scene_keywords = vibe.get("scene_keywords", [])
            if scene_keywords:
                render_scene_tags(scene_keywords)
            
            # 置信度
            confidence = vibe.get("confidence", 0)
            if confidence > 0:
                render_confidence_bar(confidence)
    
    # ========== 右侧：Agent + 推荐 ==========
    with col2:
        # 点点对话区
        if st.session_state.vibe_result:
            st.markdown("### 💬 點點分析")
            render_agent_chat(
                st.session_state.vibe_result,
                use_typewriter=not st.session_state.analysis_complete
            )
            
            st.divider()
            
            # 单品推荐
            st.markdown("### 🌟 穿搭推薦")
            
            # 显示搜索状态
            if st.session_state.search_triggered and st.session_state.recommended_notes:
                render_search_status(
                    st.session_state.user_text_modifier,
                    st.session_state.vibe_result.get("description", ""),
                    len(st.session_state.recommended_notes)
                )
            
            if st.session_state.recommended_notes:
                for note in st.session_state.recommended_notes:
                    render_note_card(note, show_items=True)
            else:
                st.info("暫無匹配的穿搭推薦 ✨")
        else:
            st.markdown("### 💬 點點對話")
            st.markdown('''
            <div class="empty-state" style="padding: 40px 20px;">
                <div class="empty-icon">🎀</div>
                <div style="font-size: 14px; color: #999;">
                    上傳照片後，點點會給你穿搭建議
                </div>
            </div>
            ''', unsafe_allow_html=True)
    
    # 页脚
    st.divider()
    st.markdown('''
    <div style="text-align: center; padding: 20px;">
        <span style="color: #999; font-size: 12px;">
            💡 StyleMirror v4.0 - 圖文混合搜索 + 匹配度可視化 | 
            Made with ❤️ using Streamlit
        </span>
    </div>
    ''', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
