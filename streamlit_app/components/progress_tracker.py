"""
进度追踪组件
"""
import streamlit as st
from typing import Optional
import time


class ProgressTracker:
    """进度追踪器"""

    def __init__(self, total: int, title: str = "处理中..."):
        self.total = total
        self.current = 0
        self.title = title
        self.start_time = time.time()

        # 创建 UI 元素
        self.status_container = st.empty()
        self.progress_bar = st.progress(0)
        self.message_container = st.empty()

    def update(self, current: int, message: str = ""):
        """更新进度"""
        self.current = current
        progress = current / self.total if self.total > 0 else 0

        # 更新进度条
        self.progress_bar.progress(progress)

        # 计算剩余时间
        elapsed = time.time() - self.start_time
        if current > 0:
            eta = (elapsed / current) * (self.total - current)
            eta_str = f"预计剩余: {int(eta)}秒"
        else:
            eta_str = ""

        # 更新状态
        self.status_container.markdown(
            f"**{self.title}** ({current}/{self.total}) {eta_str}"
        )

        # 更新消息
        if message:
            self.message_container.caption(message)

    def increment(self, message: str = ""):
        """增加进度"""
        self.update(self.current + 1, message)

    def complete(self, message: str = "完成！"):
        """标记完成"""
        self.progress_bar.progress(1.0)
        elapsed = time.time() - self.start_time
        self.status_container.markdown(
            f"✅ **{message}** (共 {self.total} 项，耗时 {elapsed:.1f}秒)"
        )
        self.message_container.empty()

    def error(self, message: str):
        """显示错误"""
        self.status_container.markdown(f"❌ **错误:** {message}")


def show_spinner_with_status(message: str):
    """显示带状态的加载动画"""
    return st.spinner(message)


def show_processing_status(
    current: int,
    total: int,
    item_name: str = "",
    show_eta: bool = True
) -> None:
    """显示处理状态"""
    progress = current / total if total > 0 else 0

    col1, col2 = st.columns([3, 1])
    with col1:
        st.progress(progress)
    with col2:
        st.write(f"{current}/{total}")

    if item_name:
        st.caption(f"正在处理: {item_name}")
