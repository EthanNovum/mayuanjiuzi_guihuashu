"""
文件上传组件
"""
import streamlit as st
from typing import List, Optional, Tuple
import os


def file_uploader_with_validation(
    label: str = "上传 PDF 文件",
    accept_multiple: bool = True,
    max_files: int = 100,
    max_size_mb: int = 50,
    key: str = "pdf_uploader"
) -> List:
    """
    带验证的文件上传组件

    Returns:
        上传的文件列表
    """
    uploaded_files = st.file_uploader(
        label,
        type=["pdf"],
        accept_multiple_files=accept_multiple,
        key=key,
        help=f"支持 PDF 格式，单文件最大 {max_size_mb}MB，最多 {max_files} 个文件"
    )

    if not uploaded_files:
        return []

    # 转为列表
    if not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    # 验证文件数量
    if len(uploaded_files) > max_files:
        st.warning(f"文件数量超过限制（{max_files}），仅处理前 {max_files} 个文件")
        uploaded_files = uploaded_files[:max_files]

    # 验证文件大小
    valid_files = []
    for file in uploaded_files:
        size_mb = file.size / (1024 * 1024)
        if size_mb > max_size_mb:
            st.error(f"❌ {file.name}: 文件过大 ({size_mb:.1f}MB > {max_size_mb}MB)")
        else:
            valid_files.append(file)

    return valid_files


def display_file_list(files: List, show_size: bool = True) -> None:
    """显示文件列表"""
    if not files:
        st.info("暂无文件")
        return

    for i, file in enumerate(files):
        col1, col2, col3 = st.columns([0.5, 3, 1])
        with col1:
            st.write(f"{i + 1}.")
        with col2:
            st.write(f"📄 {file.name}")
        with col3:
            if show_size:
                size_mb = file.size / (1024 * 1024)
                st.write(f"{size_mb:.2f} MB")


def file_selector(
    files: List,
    key_prefix: str = "select"
) -> List:
    """
    文件选择器（带全选功能）

    Returns:
        选中的文件列表
    """
    if not files:
        return []

    # 全选复选框
    select_all = st.checkbox("全选", value=True, key=f"{key_prefix}_all")

    selected = []
    for i, file in enumerate(files):
        checked = st.checkbox(
            f"📄 {file.name}",
            value=select_all,
            key=f"{key_prefix}_{i}"
        )
        if checked:
            selected.append(file)

    st.caption(f"已选择 {len(selected)} / {len(files)} 个文件")

    return selected
