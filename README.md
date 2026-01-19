mayuanjiuzi_guihuashu
=====================

本项目用于将学生“规划书”PDF 转为 Markdown，再用 Gemini 做结构化评分，最后导出 CSV。整体流程包含：PDF 预处理 -> OCR 转写 -> Markdown 清洗 -> LLM 评分 -> 结果导出。

功能概览
--------
- `trim_pdf.py`：批量裁剪 PDF，删除首页和末两页，保留中间内容。
- `ocr_pdf.py`：调用 TextIn OCR 将 PDF 转 JSON，并生成 Markdown（支持直接把已有 JSON 转成 Markdown）。
- `clean_md.py`：清理 Markdown 中的图片和 HTML 标签，并去掉多余空白。
- `gemini_client.py`：读取提示词和 Markdown 内容，调用 Gemini 生成 JSON 评分结果，写入 `result.jsonl`。
- `export_result.py`：把 `result.jsonl` 导出为 `result.csv`。
- `main.py`：示例入口，目前只打印提示信息。
- `test.py`：调试用的长字符串样例，便于本地快速验证文本处理。

目录说明
--------
- `pdfs/`：原始 PDF 输入目录。
- `pdf_result/json/`：OCR 输出的 JSON 文件。
- `pdf_result/md/`：OCR 输出的 Markdown 文件。
- `mds/`：用于评分的 Markdown 文件目录（可手动整理或由 OCR 输出拷贝）。
- `prompts/`：评分提示词，默认使用 `prompts/prompt_v2.txt`。
- `result.jsonl`：Gemini 评分输出（逐行 JSON）。
- `result.csv`：评分结果 CSV 汇总。

依赖与配置
----------
- Python >= 3.11
- 依赖见 `pyproject.toml`，主要包含 `requests`、`pymupdf` 等
- 需要配置以下环境变量（建议放在 `.env`）：
  - `TEXTIN_APP_ID` / `TEXTIN_SECRET_CODE`：TextIn OCR 账号
  - `GEMINI_API_KEY`：Gemini API Key
  - `MODEL`：可选，Gemini 模型名称（默认 `gemini-2.5-flash`）

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

4. 调用 Gemini 评分
   ```bash
   python gemini_client.py --env .env --mds mds --prompt prompts/prompt_v2.txt --output result.jsonl
   ```

5. 导出 CSV
   ```bash
   python export_result.py --input result.jsonl --output result.csv
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
- `gemini_client.py`：
  - 遍历 `mds/` 下所有 `.md` 文件。
  - 拼接提示词 + 规划书内容，并调用 Gemini。
  - 支持从返回文本中提取 JSON，并补充 `filename`、`student_name` 字段。
- `export_result.py`：
  - 解析 JSONL，自动合并列表字段为多行文本。
  - 默认字段：`filename`、`student_name`、`score`、`strengths`、`gaps`、`suggestions`。

备注
----
- OCR 和 Gemini 都是外部服务，请注意 API Key 及配额。
- `clean_md.py` 会移除所有空白字符，如需保留段落结构可修改实现。
