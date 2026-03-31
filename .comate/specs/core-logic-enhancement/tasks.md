# StyleMirror 核心逻辑完善任务清单

## 任务概览
本次任务将完善 StyleMirror 的核心逻辑，实现从图片上传到风格识别、笔记匹配、Agent 推荐的完整交互流程，共 4 个任务。

---

## 具体任务列表

- [x] Task 1: 完善 core/image_processor.py 风格识别函数
    - 1.1: 定义 `analyze_vibe(image)` 函数
    - 1.2: 实现随机选择风格标签逻辑（法式復古/極簡工業/溫柔原木）
    - 1.3: 为每个风格生成光影和材质描述
    - 1.4: 返回包含 vibe_tag 和 description 的字典

- [x] Task 2: 完善 core/retriever.py 笔记匹配函数
    - 2.1: 定义 `get_matching_notes(vibe_tag)` 函数
    - 2.2: 调用 `load_mock_notes()` 读取 Mock 数据
    - 2.3: 实现 vibe_tags 列表的标签匹配逻辑
    - 2.4: 返回匹配的笔记列表

- [x] Task 3: 完善 app.py 交互逻辑
    - 3.1: 修改上传逻辑，上传图片后自动触发 `analyze_vibe()`
    - 3.2: 左侧使用 `st.info` 展示 Vibe 标签
    - 3.3: 左侧展示风格描述（光影和材质）
    - 3.4: 调用 `get_matching_notes()` 获取匹配笔记
    - 3.5: 右侧模拟点点 Agent 口吻输出推荐理由
    - 3.6: 右侧展示推荐单品图片（使用占位图或颜色块）

- [x] Task 4: 视觉优化与布局调整
    - 4.1: 使用 `st.container()` 优化整体布局结构
    - 4.2: 使用 `st.columns()` 实现更紧凑的双列布局
    - 4.3: 为推荐单品添加小红书风格边框和标签
    - 4.4: 优化 Agent 推荐消息的视觉呈现

---

## 执行顺序说明
1. **Task 1-2** 可并行执行，完善核心逻辑模块
2. **Task 3** 依赖 Task 1-2 完成的函数
3. **Task 4** 最后执行，进行视觉优化
