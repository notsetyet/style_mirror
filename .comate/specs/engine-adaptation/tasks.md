# StyleMirror 引擎适配重构任务清单

## 任务概览
本次任务将适配新升级的多模态引擎，更新 `app.py` 和 `core/retriever.py`，共 4 个任务。

---

## 具体任务列表

- [x] Task 1: 升级 core/retriever.py 检索逻辑
    - 1.1: 修改 `get_matching_notes` 函数签名，新增 `scene_keywords` 参数
    - 1.2: 实现基于 `vibe_tag` 的基础匹配（权重 10 分）
    - 1.3: 实现基于 `scene_keywords` 的加权匹配（每匹配一个 +5 分）
    - 1.4: 新增 `_get_default_recommendations()` 默认推荐函数
    - 1.5: 无匹配时返回默认推荐，避免前端报错

- [x] Task 2: 升级 app.py 侧边栏配置
    - 2.1: 新增 API Key 输入框（type="password"）
    - 2.2: 新增 Base URL 输入框（选填，带 placeholder）
    - 2.3: 将配置存入 `st.session_state`
    - 2.4: 调用 `analyze_vibe` 时传入 `api_key` 和 `base_url`

- [x] Task 3: 升级 app.py 视觉感知展示
    - 3.1: 新增 `render_color_palette()` 函数，渲染色块圆圈
    - 3.2: 新增 `render_scene_keywords()` 函数，渲染 pills 标签
    - 3.3: 左侧展示区集成色彩板可视化
    - 3.4: 左侧展示区集成场景关键词标签
    - 3.5: 调用 `get_matching_notes` 时传入 `scene_keywords`

- [x] Task 4: 升级 app.py Agent 展示逻辑
    - 4.1: 右侧 Agent 开场白改用 `description` 字段
    - 4.2: 优化无匹配笔记时的友好提示
    - 4.3: 确保整体布局紧凑美观

---

## 执行顺序说明
1. **Task 1** 先执行，更新检索逻辑
2. **Task 2-4** 可并行执行，更新 UI 层
