# StyleMirror 项目初始化任务清单

## 任务概览
本项目将初始化 StyleMirror 小红书多模态试用原型的基础代码结构和占位文件，共 8 个任务。

---

## 具体任务列表

- [x] Task 1: 创建项目基础目录结构
    - 1.1: 创建 components/ 目录
    - 1.2: 创建 core/ 目录
    - 1.3: 创建 data/ 目录
    - 1.4: 创建 prompts/ 目录

- [x] Task 2: 生成 requirements.txt 依赖文件
    - 2.1: 添加 streamlit>=1.28.0 依赖
    - 2.2: 添加 pandas>=2.0.0 依赖
    - 2.3: 添加 pillow>=10.0.0 依赖
    - 2.4: 添加 requests>=2.31.0 依赖
    - 2.5: 添加注释说明后续可选依赖

- [x] Task 3: 生成 prompts/agent_prompts.py Agent提示词模块
    - 3.1: 定义 DIANDIAN_SYSTEM_PROMPT 常量
    - 3.2: 包含点点 Agent 拟人化人设要求
    - 3.3: 添加语气亲切、多用 Emoji 的对话风格说明
    - 3.4: 添加氛围感、穿搭建议等核心能力描述

- [x] Task 4: 生成 data/mock_notes.json 模拟数据文件
    - 4.1: 定义数据结构（note_id, item_img_url, vibe_tags, caption）
    - 4.2: 创建第 1 条 mock 数据（法式慵懒风格）
    - 4.3: 创建第 2 条 mock 数据（简约通勤风格）

- [x] Task 5: 生成 components/ui_styles.py UI样式组件
    - 5.1: 定义 apply_custom_styles() 函数
    - 5.2: 添加自定义 CSS 样式（小红书风格配色）
    - 5.3: 预留通用 UI 渲染函数接口

- [x] Task 6: 生成 core/ 核心逻辑模块
    - 6.1: 创建 image_processor.py 视觉特征提取模块（预留接口）
    - 6.2: 创建 retriever.py 笔记检索模块（预留接口）
    - 6.3: 创建 virtual_tryon.py 虚拟试穿模块（预留接口）

- [x] Task 7: 生成 app.py Streamlit 主程序入口
    - 7.1: 设置 Streamlit 页面配置（标题、布局）
    - 7.2: 应用自定义样式
    - 7.3: 创建侧边栏照片上传功能（支持 jpg/png）
    - 7.4: 创建主页面双列布局
    - 7.5: 左列展示原图和 Vibe 识别占位
    - 7.6: 右列展示 Agent 对话框和推荐单品占位

- [x] Task 8: 项目验证与文档完善
    - 8.1: 验证所有文件创建成功
    - 8.2: 检查代码注释完整性
    - 8.3: 确认项目结构符合要求

---

## 执行顺序说明
1. **Task 1** 必须先执行，创建目录结构
2. **Task 2-6** 可以并行执行，生成各个独立模块
3. **Task 7** 依赖 Task 2-6 完成的模块
4. **Task 8** 最后执行，验证整体项目
