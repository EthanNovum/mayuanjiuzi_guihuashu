"""
Session State 管理模块
"""
import streamlit as st
from typing import Any


def init_session_state():
    """初始化 Session State"""
    defaults = {
        # API 配置
        "api_config": {
            "TEXTIN_APP_ID": "",
            "TEXTIN_SECRET_CODE": "",
            "GEMINI_API_KEY": "",
            "OPENAI_API_KEY": "",
            "CLAUDE_API_KEY": "",
            "DEEPSEEK_API_KEY": "",
            "QWEN_API_KEY": "",
            "DOUBAO_API_KEY": "",
            "KIMI_API_KEY": "",
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
        "history": [],

        # 设置
        "settings": {
            "trim_enabled": True,
            "trim_first": 1,
            "trim_last": 2,
            "clean_enabled": True,
            "dpi": 144,
            "parse_mode": "auto",
            "default_providers": ["gemini"],
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_state(key: str, default: Any = None) -> Any:
    """获取 Session State 值"""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any):
    """设置 Session State 值"""
    st.session_state[key] = value


def update_state(key: str, updates: dict):
    """更新 Session State 中的字典"""
    if key in st.session_state and isinstance(st.session_state[key], dict):
        st.session_state[key].update(updates)


def append_to_state(key: str, item: Any):
    """向 Session State 列表追加项"""
    if key in st.session_state and isinstance(st.session_state[key], list):
        st.session_state[key].append(item)


def clear_state(key: str):
    """清空 Session State 值"""
    if key in st.session_state:
        if isinstance(st.session_state[key], list):
            st.session_state[key] = []
        elif isinstance(st.session_state[key], dict):
            st.session_state[key] = {}
        else:
            st.session_state[key] = None
