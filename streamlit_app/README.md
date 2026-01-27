# 学生规划书智能评分系统 - Streamlit Web 应用

基于 Streamlit 框架的学生规划书智能评分系统，实现 PDF 上传、OCR 识别、多模型 LLM 评分、结果导出的完整流程。

## 功能特性

- 📄 **PDF 处理**: 上传 PDF，自动裁剪和 OCR 转换
- 📝 **文本管理**: 预览和清洗 Markdown 文本
- 🤖 **智能评分**: 支持 7 种 LLM 模型并行评分
- 📊 **结果中心**: 可视化分析和 CSV/JSON 导出
- ⚙️ **系统设置**: API 配置和偏好管理

## 支持的 LLM 模型

- Google Gemini
- OpenAI GPT-4
- Anthropic Claude
- DeepSeek
- 阿里云 Qwen
- 字节 Doubao
- Kimi (Moonshot)

## 快速开始

### 1. 安装依赖

```bash
cd streamlit_app
pip install streamlit pandas plotly requests pymupdf
```

### 2. 配置 API

在项目根目录创建 `.env` 文件：

```env
TEXTIN_APP_ID="your_textin_app_id"
TEXTIN_SECRET_CODE="your_textin_secret"
GEMINI_API_KEY="your_gemini_key"
# 其他 API Key...
```

或者在应用内的「系统设置」页面配置。

### 3. 启动应用

```bash
streamlit run app.py
```

应用将在 http://localhost:8501 启动。

## 目录结构

```
streamlit_app/
├── app.py                 # 主入口
├── pages/                 # 页面
│   ├── 1_📄_PDF处理.py
│   ├── 2_📝_文本管理.py
│   ├── 3_🤖_智能评分.py
│   ├── 4_📊_结果中心.py
│   └── 5_⚙️_系统设置.py
├── components/            # UI 组件
│   ├── file_uploader.py
│   ├── progress_tracker.py
│   └── result_viewer.py
├── services/              # 业务逻辑
│   ├── pdf_service.py
│   ├── text_service.py
│   ├── scoring_service.py
│   └── export_service.py
├── utils/                 # 工具函数
│   ├── config.py
│   ├── session.py
│   └── validators.py
└── assets/
    └── styles.css
```

## 使用流程

1. **配置 API**: 在「系统设置」页面配置 TextIn OCR 和 LLM API 密钥
2. **上传 PDF**: 在「PDF 处理」页面上传学生规划书
3. **OCR 转换**: 系统自动将 PDF 转换为可评分的 Markdown 文本
4. **执行评分**: 在「智能评分」页面选择模型和评分标准
5. **查看结果**: 在「结果中心」查看详细评分并导出

## 技术栈

- **前端框架**: Streamlit
- **PDF 处理**: PyMuPDF
- **OCR 服务**: TextIn
- **LLM 集成**: 多提供商 API
