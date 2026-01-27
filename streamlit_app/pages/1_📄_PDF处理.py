"""
PDF 处理页面
"""
import streamlit as st
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import init_config, get_temp_dir, get_mds_dir
from utils.session import init_session_state
from components.file_uploader import file_uploader_with_validation, display_file_list
from components.progress_tracker import ProgressTracker
from services.pdf_service import process_pdf_file
from services.text_service import clean_markdown_text
from services.storage_service import save_processed_markdowns, add_history_entry

# 页面配置
st.set_page_config(
    page_title="PDF 处理 - 规划书评分系统",
    page_icon="📄",
    layout="wide",
)

init_session_state()
init_config()

st.title("📄 PDF 处理")
st.markdown("上传学生规划书 PDF，系统将自动进行 OCR 转换。")
st.divider()

# 检查 API 配置
api_config = st.session_state.get("api_config", {})
textin_ok = bool(api_config.get("TEXTIN_APP_ID") and api_config.get("TEXTIN_SECRET_CODE"))

if not textin_ok:
    st.warning("⚠️ 请先在「系统设置」页面配置 TextIn OCR API 密钥")
    st.stop()

# 设置区域
with st.expander("⚙️ 处理设置", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("PDF 裁剪")
        trim_enabled = st.checkbox(
            "启用页面裁剪",
            value=st.session_state.settings.get("trim_enabled", True),
            help="删除规划书的封面和附录页"
        )
        if trim_enabled:
            trim_first = st.number_input(
                "删除前 N 页",
                min_value=0, max_value=10,
                value=st.session_state.settings.get("trim_first", 1)
            )
            trim_last = st.number_input(
                "删除后 N 页",
                min_value=0, max_value=10,
                value=st.session_state.settings.get("trim_last", 2)
            )
        else:
            trim_first = 0
            trim_last = 0

    with col2:
        st.subheader("OCR 设置")
        dpi = st.selectbox(
            "DPI（清晰度）",
            options=[72, 144, 200, 300],
            index=1,
            help="越高越清晰，但处理越慢"
        )
        parse_mode = st.selectbox(
            "解析模式",
            options=["auto", "text", "table"],
            index=0,
            help="auto: 自动识别; text: 纯文本; table: 表格优先"
        )
        clean_enabled = st.checkbox(
            "自动清洗文本",
            value=st.session_state.settings.get("clean_enabled", True),
            help="去除图片和 HTML 标签"
        )

    # 保存设置
    st.session_state.settings.update({
        "trim_enabled": trim_enabled,
        "trim_first": trim_first,
        "trim_last": trim_last,
        "dpi": dpi,
        "parse_mode": parse_mode,
        "clean_enabled": clean_enabled,
    })

st.divider()

# 文件上传
st.subheader("📤 上传文件")

uploaded_files = file_uploader_with_validation(
    label="选择或拖拽 PDF 文件",
    accept_multiple=True,
    max_files=100,
    max_size_mb=50
)

if uploaded_files:
    st.success(f"已上传 {len(uploaded_files)} 个文件")
    display_file_list(uploaded_files)

    st.divider()

    # 处理按钮
    if st.button("🚀 开始处理", type="primary", use_container_width=True):
        progress = ProgressTracker(len(uploaded_files), "正在处理 PDF...")

        results = []

        for i, file in enumerate(uploaded_files):
            progress.update(i, f"处理: {file.name}")

            try:
                # 读取文件内容
                file_bytes = file.read()
                file.seek(0)  # 重置指针

                # 处理 PDF
                result = process_pdf_file(
                    file_bytes=file_bytes,
                    filename=file.name,
                    app_id=api_config.get("TEXTIN_APP_ID"),
                    secret_code=api_config.get("TEXTIN_SECRET_CODE"),
                    trim_enabled=trim_enabled,
                    trim_first=trim_first,
                    trim_last=trim_last,
                    dpi=dpi,
                    parse_mode=parse_mode
                )

                # 清洗文本
                if clean_enabled and result.get("markdown"):
                    result["markdown"] = clean_markdown_text(
                        result["markdown"],
                        preserve_structure=True
                    )

                results.append(result)

            except Exception as e:
                results.append({
                    "filename": file.name,
                    "status": "error",
                    "error": str(e),
                    "markdown": "",
                })

        progress.complete("处理完成！")

        # 保存结果到 session
        st.session_state.processed_markdowns = results

        # 持久化保存到文件
        save_processed_markdowns(results)
        add_history_entry("pdf_processing", {
            "total": len(results),
            "success": len([r for r in results if r.get("status") == "success"]),
            "files": [r.get("filename") for r in results]
        })

        # 显示结果摘要
        st.divider()
        st.subheader("📊 处理结果")

        success_count = len([r for r in results if r.get("status") == "success"])
        error_count = len([r for r in results if r.get("status") == "error"])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总数", len(results))
        with col2:
            st.metric("成功", success_count)
        with col3:
            st.metric("失败", error_count)

        # 详细结果
        for result in results:
            with st.expander(f"{'✅' if result.get('status') == 'success' else '❌'} {result.get('filename', '未知')}"):
                if result.get("error"):
                    st.error(f"错误: {result['error']}")
                else:
                    # 显示裁剪信息
                    if result.get("trim_info"):
                        info = result["trim_info"]
                        st.caption(f"页面: {info.get('original_pages')} → {info.get('final_pages')}")

                    # 显示 Markdown 预览
                    markdown = result.get("markdown", "")
                    if markdown:
                        st.text_area(
                            "Markdown 预览",
                            value=markdown[:2000] + ("..." if len(markdown) > 2000 else ""),
                            height=200,
                            disabled=True
                        )
                        st.caption(f"总字符数: {len(markdown)}")

        # 保存到文件选项
        if success_count > 0:
            st.divider()
            if st.button("💾 保存 Markdown 文件到 mds 目录"):
                mds_dir = get_mds_dir()
                saved_count = 0
                for result in results:
                    if result.get("status") == "success" and result.get("markdown"):
                        filename = result.get("filename", "unknown.pdf")
                        md_filename = filename.rsplit(".", 1)[0] + ".md"
                        md_path = mds_dir / md_filename
                        with open(md_path, "w", encoding="utf-8") as f:
                            f.write(result["markdown"])
                        saved_count += 1
                st.success(f"已保存 {saved_count} 个文件到 {mds_dir}")

# 显示已处理的文件
if st.session_state.get("processed_markdowns"):
    st.divider()
    st.subheader("📂 已处理的文件")
    st.caption(f"共 {len(st.session_state.processed_markdowns)} 个文件")

    for result in st.session_state.processed_markdowns:
        status = "✅" if result.get("status") == "success" else "❌"
        st.write(f"{status} {result.get('filename', '未知')}")
