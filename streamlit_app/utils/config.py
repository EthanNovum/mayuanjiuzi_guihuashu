"""
配置管理模块
"""
import os
import streamlit as st
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent


def load_env_file(env_path: str = None) -> dict:
    """加载环境变量文件"""
    if env_path is None:
        env_path = get_project_root() / ".env"

    values = {}
    if not os.path.exists(env_path):
        return values

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def init_config():
    """初始化配置"""
    if "config_loaded" not in st.session_state:
        # 尝试从 .env 文件加载配置
        env_values = load_env_file()

        if "api_config" not in st.session_state:
            st.session_state.api_config = {}

        # 合并环境变量
        for key, value in env_values.items():
            if key not in st.session_state.api_config or not st.session_state.api_config[key]:
                st.session_state.api_config[key] = value

        st.session_state.config_loaded = True


def save_config_to_env(config: dict):
    """保存配置到 .env 文件"""
    env_path = get_project_root() / ".env"

    lines = []
    for key, value in config.items():
        if value:
            lines.append(f'{key}="{value}"')

    with open(env_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def load_css():
    """加载自定义 CSS"""
    css_path = Path(__file__).parent.parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def get_temp_dir() -> Path:
    """获取临时文件目录"""
    temp_dir = get_project_root() / "temp"
    temp_dir.mkdir(exist_ok=True)
    return temp_dir


def get_output_dir() -> Path:
    """获取输出目录"""
    output_dir = get_project_root() / "results"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def get_prompts_dir() -> Path:
    """获取 Prompt 目录"""
    return get_project_root() / "prompts"


def get_mds_dir() -> Path:
    """获取 Markdown 目录"""
    mds_dir = get_project_root() / "mds"
    mds_dir.mkdir(exist_ok=True)
    return mds_dir
