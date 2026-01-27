# 产品需求文档（PRD）

## 学生规划书智能评分系统 - Streamlit Web 应用

---

## 一、功能名

**学生规划书智能评分系统（Planbook Scoring System）**

---

## 二、需求描述

将现有的命令行工具改造为一个用户友好的 Streamlit Web 应用，实现学生规划书 PDF 的全流程自动化处理：从 PDF 上传、OCR 识别、文本清洗、多模型 LLM 评分到结果导出，为教育机构提供高效、智能的规划书评估解决方案。

### 核心价值
- **降低使用门槛**：无需命令行操作，通过可视化界面完成全部流程
- **提升评分效率**：支持批量处理和多模型并行评分
- **结果可追溯**：完整的评分历史和详细报告
- **灵活可配置**：支持自定义评分标准（Prompt）和多种 LLM 模型

---

## 三、概述

### 3.1 项目背景

教育机构需要对学生提交的规划书进行评估，传统人工评分耗时且标准难以统一。本系统利用 OCR 技术和大语言模型（LLM），实现规划书的智能化、标准化评分。

### 3.2 整体目标

| 目标维度 | 描述 |
|---------|------|
| 功能目标 | 实现 PDF → OCR → Markdown → LLM 评分 → CSV 导出的完整流程 |
| 用户目标 | 提供简洁直观的操作界面，5 分钟内完成单份规划书评分 |
| 技术目标 | 基于 Streamlit 框架，支持多种 LLM 提供商（Gemini、OpenAI、Claude、DeepSeek 等） |

### 3.3 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web 应用                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ 上传模块 │→│ OCR模块 │→│ 清洗模块 │→│ 评分模块 │→ 导出  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
├─────────────────────────────────────────────────────────────┤
│  trim_pdf.py │ ocr_pdf.py │ clean_md.py│ api_client.py     │
├─────────────────────────────────────────────────────────────┤
│  TextIn OCR  │  Gemini / OpenAI / Claude / DeepSeek / ...   │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、相关页面设计

### 4.1 页面结构

```
├── 🏠 首页（Dashboard）
├── 📄 PDF 处理
│   ├── 上传 PDF
│   ├── PDF 裁剪设置
│   └── OCR 转换
├── 📝 文本管理
│   ├── Markdown 预览
│   └── 文本清洗
├── 🤖 智能评分
│   ├── 模型配置
│   ├── Prompt 管理
│   └── 批量评分
├── 📊 结果中心
│   ├── 评分详情
│   ├── 历史记录
│   └── 导出下载
└── ⚙️ 系统设置
    ├── API 配置
    └── 偏好设置
```

### 4.2 页面详细设计

#### 4.2.1 首页（Dashboard）

| 元素 | 类型 | 描述 |
|------|------|------|
| 统计卡片 | `st.metric` | 显示已处理文件数、平均分数、待处理数量 |
| 快捷操作 | `st.button` | 一键上传、快速评分、导出结果 |
| 最近记录 | `st.dataframe` | 最近 10 条评分记录 |
| 状态指示 | `st.status` | API 连接状态、服务健康度 |

#### 4.2.2 PDF 处理页

| 元素 | 类型 | 描述 |
|------|------|------|
| 文件上传 | `st.file_uploader` | 支持多文件上传，accept=["pdf"] |
| 裁剪选项 | `st.checkbox` | 是否删除首页/末两页 |
| 预览区域 | `st.image` | PDF 首页预览 |
| OCR 设置 | `st.selectbox` | DPI、解析模式、表格格式 |
| 处理进度 | `st.progress` | 实时显示处理进度 |

#### 4.2.3 智能评分页

| 元素 | 类型 | 描述 |
|------|------|------|
| 模型选择 | `st.multiselect` | 支持选择多个 LLM 提供商 |
| Prompt 编辑器 | `st.text_area` | 可编辑评分标准 |
| Prompt 模板 | `st.selectbox` | 预设 Prompt 模板选择 |
| 文件列表 | `st.checkbox` | 勾选待评分文件 |
| 开始评分 | `st.button` | 触发评分任务 |
| 实时日志 | `st.expander` | 展开查看详细处理日志 |

#### 4.2.4 结果中心页

| 元素 | 类型 | 描述 |
|------|------|------|
| 结果表格 | `st.dataframe` | 可排序、可筛选的评分结果 |
| 详情弹窗 | `st.dialog` | 查看单个学生的完整评分报告 |
| 图表分析 | `st.bar_chart` | 分数分布、维度对比 |
| 导出按钮 | `st.download_button` | 支持 CSV/JSON 格式导出 |

---

## 五、用户旅程

### 5.1 主流程用户旅程

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           用户旅程地图                                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [开始] → [配置API] → [上传PDF] → [OCR转换] → [选择模型] → [执行评分]    │
│                                                                          │
│     ↓         ↓           ↓           ↓           ↓           ↓         │
│                                                                          │
│  首次使用   设置页面    PDF处理页   自动处理    评分页面    等待结果     │
│  引导配置   填写密钥    拖拽上传    显示进度    选择Prompt  查看进度     │
│                                                                          │
│                                                                          │
│  → [查看结果] → [分析报告] → [导出CSV] → [结束]                          │
│                                                                          │
│        ↓           ↓           ↓                                         │
│                                                                          │
│    结果中心     可视化图表   下载文件                                     │
│    查看详情     维度分析     本地保存                                     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 5.2 详细用户旅程

| 阶段 | 用户行为 | 系统响应 | 情绪曲线 |
|------|----------|----------|----------|
| 1. 进入系统 | 访问 Web 应用 | 显示 Dashboard，检查 API 状态 | 😊 期待 |
| 2. 首次配置 | 填写 API Key | 验证并保存配置 | 😐 中性 |
| 3. 上传文件 | 拖拽或选择 PDF | 显示文件列表，预览首页 | 😊 顺利 |
| 4. PDF 处理 | 点击"开始处理" | 裁剪 → OCR → 生成 Markdown | 😊 期待 |
| 5. 配置评分 | 选择模型和 Prompt | 加载配置，显示预览 | 😐 专注 |
| 6. 执行评分 | 点击"开始评分" | 并行调用 LLM，实时显示进度 | 😰 等待 |
| 7. 查看结果 | 浏览评分表格 | 展示分数、评语、建议 | 😄 满意 |
| 8. 导出数据 | 点击"导出 CSV" | 生成并下载文件 | 😄 完成 |

---

## 六、用户故事

### 6.1 核心用户故事

| ID | 角色 | 故事 | 验收标准 |
|----|------|------|----------|
| US-01 | 教务人员 | 作为教务人员，我希望能批量上传学生规划书 PDF，以便快速处理多份文件 | 支持一次上传 50+ 个 PDF 文件 |
| US-02 | 教务人员 | 作为教务人员，我希望能自动去除规划书中的封面和附录页，以便获得纯内容 | 可配置裁剪首页和末 N 页 |
| US-03 | 评审专家 | 作为评审专家，我希望能自定义评分标准（Prompt），以便适应不同评分维度 | 支持 Prompt 模板的增删改 |
| US-04 | 评审专家 | 作为评审专家，我希望能对比不同 AI 模型的评分结果，以便选择最合适的模型 | 支持多模型并行评分对比 |
| US-05 | 管理员 | 作为管理员，我希望能导出评分结果为 CSV，以便进行后续数据分析 | 一键导出完整评分数据 |
| US-06 | 管理员 | 作为管理员，我希望能查看评分历史记录，以便追溯和审计 | 保留历史评分记录，支持按时间筛选 |

### 6.2 补充用户故事

| ID | 角色 | 故事 | 验收标准 |
|----|------|------|----------|
| US-07 | 教务人员 | 作为教务人员，我希望在评分过程中断时能够续传，以便不丢失进度 | 支持断点续传功能 |
| US-08 | 评审专家 | 作为评审专家，我希望能预览 OCR 转换后的文本，以便确认识别质量 | 提供 Markdown 预览功能 |
| US-09 | 所有用户 | 作为用户，我希望界面提供清晰的进度反馈，以便了解处理状态 | 显示进度条和预计剩余时间 |

---

## 七、实现逻辑

### 7.1 系统模块划分

```python
# 项目结构
streamlit_app/
├── app.py                 # Streamlit 主入口
├── pages/
│   ├── 1_📄_PDF处理.py
│   ├── 2_📝_文本管理.py
│   ├── 3_🤖_智能评分.py
│   ├── 4_📊_结果中心.py
│   └── 5_⚙️_系统设置.py
├── components/
│   ├── file_uploader.py   # 文件上传组件
│   ├── progress_tracker.py # 进度追踪组件
│   └── result_viewer.py   # 结果查看组件
├── services/
│   ├── pdf_service.py     # PDF 处理服务（封装 trim_pdf, ocr_pdf）
│   ├── text_service.py    # 文本处理服务（封装 clean_md）
│   ├── scoring_service.py # 评分服务（封装 api_client）
│   └── export_service.py  # 导出服务（封装 export_result）
├── utils/
│   ├── config.py          # 配置管理
│   ├── session.py         # Session State 管理
│   └── validators.py      # 输入验证
└── assets/
    └── styles.css         # 自定义样式
```

### 7.2 核心流程逻辑

#### 7.2.1 PDF 处理流程

```python
def process_pdf_pipeline(uploaded_files, settings):
    """
    PDF 处理管道

    流程：
    1. 保存上传文件到临时目录
    2. 调用 trim_pdf 裁剪页面（可选）
    3. 调用 ocr_pdf 进行 OCR 转换
    4. 返回生成的 Markdown 内容
    """
    results = []
    progress_bar = st.progress(0)

    for i, file in enumerate(uploaded_files):
        # 步骤 1：保存文件
        temp_path = save_temp_file(file)

        # 步骤 2：裁剪 PDF（如果启用）
        if settings.get("trim_enabled"):
            temp_path = trim_pdf_file(temp_path,
                                       trim_first=settings.get("trim_first", 1),
                                       trim_last=settings.get("trim_last", 2))

        # 步骤 3：OCR 转换
        markdown_content = ocr_to_markdown(temp_path,
                                           dpi=settings.get("dpi", 144),
                                           parse_mode=settings.get("parse_mode", "auto"))

        # 步骤 4：文本清洗（可选）
        if settings.get("clean_enabled"):
            markdown_content = clean_markdown_text(markdown_content)

        results.append({
            "filename": file.name,
            "markdown": markdown_content,
            "status": "success"
        })

        progress_bar.progress((i + 1) / len(uploaded_files))

    return results
```

#### 7.2.2 智能评分流程

```python
def scoring_pipeline(markdown_files, scoring_config):
    """
    智能评分管道

    流程：
    1. 加载选中的 Prompt 模板
    2. 创建 LLM 客户端（支持多模型）
    3. 并行执行评分任务
    4. 收集并保存结果
    """
    # 步骤 1：加载 Prompt
    prompts = load_prompts(scoring_config["prompt_paths"])

    # 步骤 2：创建客户端
    clients = create_clients(
        providers=scoring_config["providers"],
        env_values=st.session_state.api_config
    )

    # 步骤 3：执行评分（支持断点续传）
    run_id = scoring_config.get("run_id") or generate_run_id()
    completed_tasks = load_completed_tasks(run_id)

    results = []
    total_tasks = len(markdown_files) * len(prompts) * len(clients)

    for file_info in markdown_files:
        for prompt_path, prompt_content in prompts:
            for client in clients:
                task_key = (file_info["filename"], prompt_path, client.provider)

                if task_key in completed_tasks:
                    continue  # 跳过已完成任务

                result = process_single_file(
                    client=client,
                    prompt=prompt_content,
                    filename=file_info["filename"],
                    content=file_info["markdown"]
                )

                results.append(result)
                append_result(run_id, result)  # 实时保存

    return results, run_id
```

### 7.3 状态管理

```python
# Session State 结构
st.session_state = {
    # API 配置
    "api_config": {
        "TEXTIN_APP_ID": "",
        "TEXTIN_SECRET_CODE": "",
        "GEMINI_API_KEY": "",
        "OPENAI_API_KEY": "",
        "CLAUDE_API_KEY": "",
        "DEEPSEEK_API_KEY": "",
        # ...
    },

    # 处理状态
    "uploaded_files": [],
    "processed_markdowns": [],
    "scoring_results": [],

    # 运行状态
    "current_run_id": None,
    "is_processing": False,
    "progress": 0,

    # 历史记录
    "history": []
}
```

---

## 八、功能细节描述

### 8.1 文件上传模块

| 功能点 | 描述 | 边界条件 |
|--------|------|----------|
| 文件类型 | 仅支持 PDF 格式 | 非 PDF 文件显示错误提示 |
| 文件大小 | 单文件最大 50MB | 超限时提示并拒绝上传 |
| 批量上传 | 支持同时上传 100 个文件 | 超过 100 个时分批处理 |
| 文件命名 | 自动从文件名提取学生姓名 | 格式：`分数 planbook__姓名.pdf` |
| 重复检测 | 检测同名文件 | 提示用户选择覆盖或跳过 |

### 8.2 OCR 转换模块

| 功能点 | 描述 | 默认值 |
|--------|------|--------|
| DPI 设置 | 图像识别精度 | 144 |
| 解析模式 | auto / text / table | auto |
| 表格格式 | html / markdown | html |
| 超时时间 | 单文件处理超时 | 120 秒 |
| 重试次数 | OCR 失败重试 | 3 次 |

### 8.3 评分模块

| 功能点 | 描述 | 配置项 |
|--------|------|--------|
| 支持模型 | Gemini, OpenAI, Claude, DeepSeek, Qwen, Doubao, Kimi | 多选 |
| 并行度 | 多模型并行评分 | 最大 5 个并发 |
| 温度参数 | 控制输出随机性 | 默认 0（确定性输出） |
| 超时时间 | 单次 API 调用超时 | 300 秒 |
| 断点续传 | 支持中断后恢复 | 自动保存进度 |

### 8.4 结果输出模块

| 字段 | 类型 | 描述 |
|------|------|------|
| filename | string | 原始文件名 |
| student_name | string | 学生姓名 |
| provider | string | 评分模型提供商 |
| model | string | 具体模型名称 |
| score | number | 总分 |
| clearness_and_consistency | number | 清晰度与一致性评分 |
| detail_and_executable | number | 详细程度与可执行性评分 |
| depth_and_intensity | number | 深度与强度评分 |
| strengths | array | 优势列表 |
| gaps | array | 不足列表 |
| suggestions | array | 改进建议 |
| thinking | string | 模型思考过程（如有） |

### 8.5 错误处理

| 错误类型 | 处理方式 | 用户提示 |
|----------|----------|----------|
| API Key 无效 | 阻止操作 | "API 密钥验证失败，请检查配置" |
| OCR 服务不可用 | 重试 3 次后跳过 | "OCR 服务暂时不可用，已跳过该文件" |
| LLM 调用失败 | 记录错误，继续下一个 | "评分失败：[具体错误]，可稍后重试" |
| 网络超时 | 自动重试 | "网络连接超时，正在重试..." |
| JSON 解析失败 | 保存原始响应 | "结果格式异常，已保存原始数据" |

---

## 九、非功能性需求

### 9.1 性能要求

| 指标 | 目标值 |
|------|--------|
| 页面加载时间 | < 2 秒 |
| 单文件 OCR 处理 | < 30 秒（10 页 PDF） |
| 单文件评分 | < 60 秒 |
| 批量处理吞吐 | 50 文件/小时 |

### 9.2 可用性要求

| 指标 | 目标值 |
|------|--------|
| 学习成本 | 新用户 10 分钟内上手 |
| 操作步骤 | 核心流程不超过 5 步 |
| 错误恢复 | 所有操作可撤销或重试 |

### 9.3 安全要求

| 要求 | 实现方式 |
|------|----------|
| API Key 保护 | 密钥仅存储在本地 Session，不上传服务器 |
| 文件安全 | 临时文件处理完成后自动删除 |
| 数据隐私 | 学生信息仅在本地处理，不传输到第三方 |

---

## 十、技术依赖

### 10.1 Python 依赖

```toml
[project]
requires-python = ">=3.11"

[dependencies]
streamlit = ">=1.30.0"
pymupdf = ">=1.23.0"
requests = ">=2.31.0"
pandas = ">=2.0.0"
plotly = ">=5.18.0"
python-dotenv = ">=1.0.0"
```

### 10.2 外部服务

| 服务 | 用途 | 必需 |
|------|------|------|
| TextIn OCR | PDF 文字识别 | ✅ 是 |
| Gemini API | LLM 评分 | ✅ 至少一个 |
| OpenAI API | LLM 评分 | ❌ 可选 |
| Claude API | LLM 评分 | ❌ 可选 |
| DeepSeek API | LLM 评分 | ❌ 可选 |

---

## 十一、里程碑规划

| 阶段 | 时间 | 交付物 |
|------|------|--------|
| MVP | 2 周 | 基础上传、OCR、单模型评分、CSV 导出 |
| V1.0 | 4 周 | 多模型支持、Prompt 管理、结果可视化 |
| V1.5 | 6 周 | 断点续传、历史记录、批量处理优化 |
| V2.0 | 8 周 | 用户管理、API 代理、部署优化 |

---

## 十二、附录

### 12.1 术语表

| 术语 | 解释 |
|------|------|
| 规划书 | 学生提交的个人发展规划文档（PDF 格式） |
| OCR | 光学字符识别，将图片/PDF 转换为可编辑文本 |
| LLM | 大语言模型，如 GPT-4、Gemini、Claude 等 |
| Prompt | 提示词，指导 LLM 按特定标准进行评分的指令 |
| Markdown | 轻量级标记语言，用于存储结构化文本 |

### 12.2 参考文档

- [Streamlit 官方文档](https://docs.streamlit.io/)
- [TextIn OCR API 文档](https://www.textin.com/document/pdf_to_markdown)
- [Gemini API 文档](https://ai.google.dev/docs)
- 现有代码：`api_client.py`, `ocr_pdf.py`, `clean_md.py`, `export_result.py`

---

**文档版本**：v1.0
**创建日期**：2025-01-27
**作者**：产品经理 AI 助手
