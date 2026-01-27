"""
文本管理页面
"""
import streamlit as st
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import init_config, get_mds_dir
from utils.session import init_session_state
from services.text_service import clean_markdown_text, get_text_stats

st.set_page_config(
    page_title="文本管理 - 规划书评分系统",
    page_icon="📝",
    layout="wide",
)

init_session_state()
init_config()

st.title("📝 文本管理")
st.markdown("预览和管理 OCR 转换后的 Markdown 文本。")
st.divider()

# 选项卡
tab1, tab2 = st.tabs(["📂 文件列表", "✏️ 文本编辑"])

with tab1:
    st.subheader("Markdown 文件列表")

    # 从 session 或文件系统加载
    source = st.radio(
        "数据来源",
        ["本次处理结果", "mds 目录文件"],
        horizontal=True
    )

    if source == "本次处理结果":
        items = st.session_state.get("processed_markdowns", [])
        if not items:
            st.info("暂无处理结果，请先在「PDF 处理」页面上传文件。")
        else:
            st.caption(f"共 {len(items)} 个文件")

            for i, item in enumerate(items):
                filename = item.get("filename", f"文件 {i+1}")
                status = item.get("status", "unknown")
                markdown = item.get("markdown", "")

                with st.expander(f"{'✅' if status == 'success' else '❌'} {filename}"):
                    if item.get("error"):
                        st.error(item["error"])
                    elif markdown:
                        stats = get_text_stats(markdown)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("字符数", stats["char_count"])
                        with col2:
                            st.metric("中文字符", stats["chinese_chars"])
                        with col3:
                            st.metric("段落数", stats["paragraph_count"])

                        st.text_area(
                            "内容预览",
                            value=markdown,
                            height=300,
                            key=f"preview_{i}",
                            disabled=True
                        )
                    else:
                        st.warning("无内容")

    else:
        mds_dir = get_mds_dir()

        if not mds_dir.exists():
            st.info(f"目录不存在: {mds_dir}")
        else:
            md_files = sorted([f for f in os.listdir(mds_dir) if f.endswith(".md")])

            if not md_files:
                st.info("目录中暂无 Markdown 文件")
            else:
                st.caption(f"共 {len(md_files)} 个文件")

                for i, filename in enumerate(md_files):
                    filepath = mds_dir / filename

                    with st.expander(f"📄 {filename}"):
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()

                        stats = get_text_stats(content)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("字符数", stats["char_count"])
                        with col2:
                            st.metric("中文字符", stats["chinese_chars"])
                        with col3:
                            st.metric("段落数", stats["paragraph_count"])

                        st.text_area(
                            "内容",
                            value=content,
                            height=300,
                            key=f"file_{i}",
                            disabled=True
                        )

with tab2:
    st.subheader("文本清洗工具")

    input_text = st.text_area(
        "输入文本",
        height=200,
        placeholder="粘贴需要清洗的 Markdown 文本..."
    )

    col1, col2 = st.columns(2)
    with col1:
        preserve_structure = st.checkbox("保留段落结构", value=True)
    with col2:
        if st.button("🧹 清洗文本", type="primary"):
            if input_text:
                cleaned = clean_markdown_text(input_text, preserve_structure)
                st.session_state["cleaned_text"] = cleaned

    if st.session_state.get("cleaned_text"):
        st.divider()
        st.subheader("清洗结果")

        cleaned = st.session_state["cleaned_text"]
        stats = get_text_stats(cleaned)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("字符数", stats["char_count"])
        with col2:
            st.metric("中文字符", stats["chinese_chars"])
        with col3:
            st.metric("段落数", stats["paragraph_count"])

        st.text_area(
            "清洗后文本",
            value=cleaned,
            height=300
        )

        st.download_button(
            "📥 下载清洗后文本",
            data=cleaned,
            file_name="cleaned.md",
            mime="text/markdown"
        )
