# Retriever V2 升级任务计划

## 任务概览
将 `core/retriever.py` 升级为 v2 版本，引入语义向量检索（Vector Search）逻辑。

---

## 任务列表

- [x] Task 1: 实现基础向量工具函数
    - 1.1: 添加 numpy 导入和类型注解
    - 1.2: 实现 `_generate_mock_embedding()` - 基于 hash 的确定性伪向量生成
    - 1.3: 实现 `get_embedding()` - 支持 OpenAI API 和 Mock 双模式
    - 1.4: 实现 `cosine_similarity()` - 余弦相似度计算

- [x] Task 2: 实现笔记文本构建函数
    - 2.1: 实现 `build_note_text()` - 将笔记内容转换为 embedding 文本
    - 2.2: 组合 vibe_tags + caption + items 信息

- [x] Task 3: 实现 V2 核心检索接口
    - 3.1: 实现 `get_matching_notes_v2()` 主函数
    - 3.2: 构建查询向量（vibe_description + user_text_modifier）
    - 3.3: 计算向量相似度得分（归一化到 0-100）
    - 3.4: 计算标签匹配得分（精确匹配 +30%）
    - 3.5: 混合得分计算与排序
    - 3.6: 返回带 vector_score、tag_score、hybrid_score 的结果

- [x] Task 4: 兼容旧接口与清理
    - 4.1: 重构 `get_matching_notes()` 调用 v2 版本
    - 4.2: 删除废弃的 `retrieve_notes_by_embedding()` 占位函数
    - 4.3: 更新模块文档和函数注释

- [x] Task 5: 更新依赖配置
    - 5.1: 检查 requirements.txt 是否包含 numpy
    - 5.2: 如缺少则添加 numpy>=1.24.0

---

## 执行顺序
Task 1 → Task 2 → Task 3 → Task 4 → Task 5

## 验收标准
- [x] `get_embedding()` 无 API Key 时使用 Mock 模式
- [x] `cosine_similarity()` 返回正确的相似度值
- [x] `get_matching_notes_v2()` 返回包含 score 字段的笔记列表
- [x] 旧接口 `get_matching_notes()` 正常工作
