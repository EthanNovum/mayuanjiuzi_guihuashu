mayuanjiuzi_guihuashu
=====================

本项目用于将学生“规划书”PDF 转为 Markdown，再用 Gemini 做结构化评分，最后导出 CSV。整体流程包含：PDF 预处理 -> OCR 转写 -> Markdown 清洗 -> LLM 评分 -> 结果导出。

功能概览
--------
- `trim_pdf.py`：批量裁剪 PDF，删除首页和末两页，保留中间内容。
- `ocr_pdf.py`：调用 TextIn OCR 将 PDF 转 JSON，并生成 Markdown（支持直接把已有 JSON 转成 Markdown）。
- `clean_md.py`：清理 Markdown 中的图片和 HTML 标签，并去掉多余空白。
- `api_client.py`：多 LLM 提供商客户端，支持 Gemini、OpenAI、Claude、DeepSeek、Qwen、Doubao、Kimi。支持多个 prompt 文件批量评分。
- `export_result.py`：把评分结果 JSON 导出为 `result.csv`。
- `test.py`：调试用的长字符串样例，便于本地快速验证文本处理。

目录说明
--------
- `pdfs/`：原始 PDF 输入目录。
- `pdf_result/json/`：OCR 输出的 JSON 文件。
- `pdf_result/md/`：OCR 输出的 Markdown 文件。
- `mds/`：用于评分的 Markdown 文件目录（可手动整理或由 OCR 输出拷贝）。
- `prompts/`：评分提示词目录。
- `results/`：评分结果 JSON 输出目录。
- `result.csv`：评分结果 CSV 汇总。

依赖与配置
----------
- Python >= 3.11
- 依赖见 `pyproject.toml`，主要包含 `requests`、`pymupdf` 等
- 需要配置以下环境变量（建议放在 `.env`）：
  - `TEXTIN_APP_ID` / `TEXTIN_SECRET_CODE`：TextIn OCR 账号
  - `GEMINI_API_KEY`：Gemini API Key
  - `OPENAI_API_KEY`：OpenAI API Key（可选）
  - `CLAUDE_API_KEY`：Claude API Key（可选）
  - `DEEPSEEK_API_KEY`：DeepSeek API Key（可选）
  - `QWEN_API_KEY`：Qwen API Key（可选）
  - `DOUBAO_API_KEY`：Doubao API Key（可选）
  - `KIMI_API_KEY`：Kimi API Key（可选）

使用流程（建议顺序）
-------------------
1. 裁剪 PDF（可选）
   ```bash
   python trim_pdf.py
   ```
   默认处理 `pdfs/` 下的所有 PDF。

2. OCR 转 Markdown
   ```bash
   python ocr_pdf.py pdfs --env .env
   ```
   输出到 `pdf_result/json/` 和 `pdf_result/md/`。

3. 清洗 Markdown（可选）
   ```bash
   python clean_md.py pdf_result/md --output-dir mds
   ```
   生成更干净的 Markdown 放到 `mds/`。

4. 调用 LLM 评分
   ```bash
   # 单个 prompt
   python api_client.py --env .env --mds mds --prompt prompts/prompt_v2.txt

   # 多个 prompt（用逗号分隔）
   python api_client.py --env .env --mds mds --prompt prompts/prompt_v1.txt,prompts/prompt_v2.txt,prompts/prompt_v3.txt

   python api_client.py --providers gemini --mds mds --prompt prompts/prompt_mayuan_7_1a.txt,prompts/prompt_mayuan_7_1b.txt,prompts/prompt_mayuan_7_2a.txt,prompts/prompt_mayuan_7_2b.txt

   # 指定多个 provider
   python api_client.py --env .env --mds mds --prompt prompts/prompt_v2.txt --providers gemini,deepseek
   ```
   结果输出到 `results/` 目录。

5. 导出 CSV
   ```bash
   python export_result.py --input results/result_xxx.json --output result.csv
   ```

脚本说明（细节）
---------------
- `trim_pdf.py`：
  - 对每个 PDF 删除第一页和末两页。
  - 页面不足 4 页时跳过。
- `ocr_pdf.py`：
  - 走 TextIn 的 `pdf_to_markdown` 接口。
  - 优先使用结构化 `detail/pages` 生成 Markdown；如果不存在，则回退到 `result.markdown`。
  - `--from-json` 可直接把已有 JSON 目录转 Markdown，不再请求 OCR。
- `clean_md.py`：
  - 去除 Markdown 图片、引用图片和 HTML 标签。
  - 去除所有空白字符，适合做纯文本评分输入。
- `api_client.py`：
  - 支持多个 LLM 提供商：gemini, openai, claude, deepseek, qwen, doubao, kimi。
  - 支持多个 prompt 文件，用逗号分隔。
  - 遍历 `mds/` 下所有 `.md` 文件，对每个文件使用每个 prompt 进行评分。
  - 结果包含 `prompt_name`、`prompt_path` 字段，便于区分不同 prompt 的评分结果。
  - 支持从返回文本中提取 JSON，并补充 `filename`、`student_name`、`provider`、`model` 字段。
- `export_result.py`：
  - 解析 JSON，自动合并列表字段为多行文本。
  - 默认字段：`filename`、`student_name`、`score`、`strengths`、`gaps`、`suggestions`。

备注
----
- OCR 和 Gemini 都是外部服务，请注意 API Key 及配额。
- `clean_md.py` 会移除所有空白字符，如需保留段落结构可修改实现。
