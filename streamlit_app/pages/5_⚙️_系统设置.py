"""
系统设置页面
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import init_config, save_config_to_env, get_project_root
from utils.session import init_session_state
from utils.validators import validate_api_key

st.set_page_config(
    page_title="系统设置 - 规划书评分系统",
    page_icon="⚙️",
    layout="wide",
)

init_session_state()
init_config()

st.title("⚙️ 系统设置")
st.markdown("配置 API 密钥和系统偏好。")
st.divider()

# 选项卡
tab1, tab2 = st.tabs(["🔑 API 配置", "🎨 偏好设置"])

with tab1:
    st.subheader("API 密钥配置")
    st.caption("配置的密钥仅存储在本地，不会上传到服务器。")

    api_config = st.session_state.get("api_config", {})

    # TextIn OCR
    st.markdown("### 📷 TextIn OCR")
    st.caption("用于将 PDF 转换为文本。[获取密钥](https://www.textin.com/)")

    col1, col2 = st.columns(2)
    with col1:
        textin_app_id = st.text_input(
            "App ID",
            value=api_config.get("TEXTIN_APP_ID", ""),
            type="password",
            key="textin_app_id"
        )
    with col2:
        textin_secret = st.text_input(
            "Secret Code",
            value=api_config.get("TEXTIN_SECRET_CODE", ""),
            type="password",
            key="textin_secret"
        )

    st.divider()

    # LLM 提供商
    st.markdown("### 🤖 LLM 提供商")
    st.caption("配置至少一个 LLM 用于智能评分。")

    # Gemini
    with st.expander("🔷 Google Gemini", expanded=True):
        st.caption("[获取密钥](https://ai.google.dev/)")
        gemini_key = st.text_input(
            "Gemini API Key",
            value=api_config.get("GEMINI_API_KEY", ""),
            type="password",
            key="gemini_key"
        )

    # OpenAI
    with st.expander("🟢 OpenAI"):
        st.caption("[获取密钥](https://platform.openai.com/)")
        openai_key = st.text_input(
            "OpenAI API Key",
            value=api_config.get("OPENAI_API_KEY", ""),
            type="password",
            key="openai_key"
        )

    # Claude
    with st.expander("🟠 Anthropic Claude"):
        st.caption("[获取密钥](https://console.anthropic.com/)")
        claude_key = st.text_input(
            "Claude API Key",
            value=api_config.get("CLAUDE_API_KEY", ""),
            type="password",
            key="claude_key"
        )

    # DeepSeek
    with st.expander("🔵 DeepSeek"):
        st.caption("[获取密钥](https://platform.deepseek.com/)")
        deepseek_key = st.text_input(
            "DeepSeek API Key",
            value=api_config.get("DEEPSEEK_API_KEY", ""),
            type="password",
            key="deepseek_key"
        )

    # Qwen
    with st.expander("🟣 阿里云 Qwen"):
        st.caption("[获取密钥](https://dashscope.aliyun.com/)")
        qwen_key = st.text_input(
            "Qwen API Key",
            value=api_config.get("QWEN_API_KEY", ""),
            type="password",
            key="qwen_key"
        )

    # Doubao
    with st.expander("🔴 字节 Doubao"):
        st.caption("[获取密钥](https://www.volcengine.com/)")
        doubao_key = st.text_input(
            "Doubao API Key",
            value=api_config.get("DOUBAO_API_KEY", ""),
            type="password",
            key="doubao_key"
        )

    # Kimi
    with st.expander("🟡 Kimi (Moonshot)"):
        st.caption("[获取密钥](https://platform.moonshot.cn/)")
        kimi_key = st.text_input(
            "Kimi API Key",
            value=api_config.get("KIMI_API_KEY", ""),
            type="password",
            key="kimi_key"
        )

    st.divider()

    # 保存按钮
    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            # 更新 session state
            new_config = {
                "TEXTIN_APP_ID": textin_app_id,
                "TEXTIN_SECRET_CODE": textin_secret,
                "GEMINI_API_KEY": gemini_key,
                "OPENAI_API_KEY": openai_key,
                "CLAUDE_API_KEY": claude_key,
                "DEEPSEEK_API_KEY": deepseek_key,
                "QWEN_API_KEY": qwen_key,
                "DOUBAO_API_KEY": doubao_key,
                "KIMI_API_KEY": kimi_key,
            }

            st.session_state.api_config = new_config
            st.success("✅ 配置已保存到会话")

    with col2:
        if st.button("📁 保存到 .env 文件", use_container_width=True):
            new_config = {
                "TEXTIN_APP_ID": textin_app_id,
                "TEXTIN_SECRET_CODE": textin_secret,
                "GEMINI_API_KEY": gemini_key,
                "OPENAI_API_KEY": openai_key,
                "CLAUDE_API_KEY": claude_key,
                "DEEPSEEK_API_KEY": deepseek_key,
                "QWEN_API_KEY": qwen_key,
                "DOUBAO_API_KEY": doubao_key,
                "KIMI_API_KEY": kimi_key,
            }

            try:
                save_config_to_env(new_config)
                st.session_state.api_config = new_config
                st.success(f"✅ 配置已保存到 {get_project_root() / '.env'}")
            except Exception as e:
                st.error(f"保存失败: {e}")

with tab2:
    st.subheader("偏好设置")

    settings = st.session_state.get("settings", {})

    st.markdown("### 📄 PDF 处理默认设置")

    col1, col2 = st.columns(2)

    with col1:
        trim_enabled = st.checkbox(
            "默认启用页面裁剪",
            value=settings.get("trim_enabled", True)
        )
        trim_first = st.number_input(
            "默认删除前 N 页",
            min_value=0, max_value=10,
            value=settings.get("trim_first", 1)
        )
        trim_last = st.number_input(
            "默认删除后 N 页",
            min_value=0, max_value=10,
            value=settings.get("trim_last", 2)
        )

    with col2:
        clean_enabled = st.checkbox(
            "默认启用文本清洗",
            value=settings.get("clean_enabled", True)
        )
        dpi = st.selectbox(
            "默认 DPI",
            options=[72, 144, 200, 300],
            index=[72, 144, 200, 300].index(settings.get("dpi", 144))
        )
        parse_mode = st.selectbox(
            "默认解析模式",
            options=["auto", "text", "table"],
            index=["auto", "text", "table"].index(settings.get("parse_mode", "auto"))
        )

    st.divider()

    if st.button("💾 保存偏好设置", type="primary"):
        st.session_state.settings = {
            "trim_enabled": trim_enabled,
            "trim_first": trim_first,
            "trim_last": trim_last,
            "clean_enabled": clean_enabled,
            "dpi": dpi,
            "parse_mode": parse_mode,
        }
        st.success("✅ 偏好设置已保存")

    st.divider()

    # 系统信息
    st.markdown("### ℹ️ 系统信息")

    st.caption(f"项目根目录: {get_project_root()}")
    st.caption(f"Python 版本: {sys.version}")

    # 清除数据
    st.divider()
    st.markdown("### ⚠️ 危险操作")

    if st.button("🗑️ 清除所有会话数据"):
        for key in list(st.session_state.keys()):
            if key not in ["api_config"]:
                del st.session_state[key]
        st.rerun()
