"""
学生规划书智能评分系统 - Streamlit Web 应用
Planbook Scoring System - Main Entry
"""
import streamlit as st
from pathlib import Path
import sys

# 添加父目录到路径，以便导入现有模块
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from utils.config import init_config, load_css
from utils.session import init_session_state

# 页面配置
st.set_page_config(
    page_title="学生规划书智能评分系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 初始化
init_session_state()
init_config()
load_css()

# 侧边栏
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/student-center.png", width=80)
    st.title("规划书评分系统")
    st.divider()

    # API 状态指示
    st.subheader("🔌 服务状态")

    api_config = st.session_state.get("api_config", {})

    # TextIn OCR 状态
    textin_ok = bool(api_config.get("TEXTIN_APP_ID") and api_config.get("TEXTIN_SECRET_CODE"))
    st.markdown(f"{'✅' if textin_ok else '❌'} TextIn OCR")

    # LLM 状态
    llm_providers = ["GEMINI", "OPENAI", "CLAUDE", "DEEPSEEK", "QWEN", "DOUBAO", "KIMI"]
    active_llms = [p for p in llm_providers if api_config.get(f"{p}_API_KEY")]

    if active_llms:
        st.markdown(f"✅ LLM ({len(active_llms)} 个可用)")
        with st.expander("查看详情"):
            for p in active_llms:
                st.markdown(f"  - {p}")
    else:
        st.markdown("❌ LLM (未配置)")

    st.divider()
    st.caption("© 2025 Planbook Scoring System")

# 主页内容
st.title("🏠 学生规划书智能评分系统")
st.markdown("---")

# 统计卡片
col1, col2, col3, col4 = st.columns(4)

with col1:
    processed_count = len(st.session_state.get("processed_markdowns", []))
    st.metric(
        label="📄 已处理文件",
        value=processed_count,
        delta=None
    )

with col2:
    results = st.session_state.get("scoring_results", [])
    if results:
        avg_score = sum(r.get("score", 0) for r in results if r.get("score")) / len(results)
        st.metric(
            label="📊 平均分数",
            value=f"{avg_score:.1f}",
            delta=None
        )
    else:
        st.metric(label="📊 平均分数", value="-")

with col3:
    pending = len(st.session_state.get("uploaded_files", []))
    st.metric(
        label="⏳ 待处理",
        value=pending,
        delta=None
    )

with col4:
    history_count = len(st.session_state.get("history", []))
    st.metric(
        label="📜 历史记录",
        value=history_count,
        delta=None
    )

st.markdown("---")

# 快捷操作
st.subheader("🚀 快捷操作")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📤 上传 PDF", use_container_width=True, type="primary"):
        st.switch_page("pages/1_📄_PDF处理.py")

with col2:
    if st.button("🤖 开始评分", use_container_width=True, type="primary"):
        st.switch_page("pages/3_🤖_智能评分.py")

with col3:
    if st.button("📥 导出结果", use_container_width=True, type="primary"):
        st.switch_page("pages/4_📊_结果中心.py")

st.markdown("---")

# 最近记录
st.subheader("📋 最近评分记录")

results = st.session_state.get("scoring_results", [])
if results:
    import pandas as pd

    # 取最近10条
    recent = results[-10:][::-1]
    df = pd.DataFrame([
        {
            "学生姓名": r.get("student_name", "-"),
            "分数": r.get("score", "-"),
            "模型": r.get("provider", "-"),
            "状态": "✅ 成功" if not r.get("error") else "❌ 失败"
        }
        for r in recent
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("暂无评分记录，请先上传 PDF 并执行评分。")

# 使用指南
with st.expander("📖 使用指南"):
    st.markdown("""
    ### 快速开始

    1. **配置 API**：前往「系统设置」页面，配置 TextIn OCR 和 LLM API 密钥
    2. **上传 PDF**：在「PDF 处理」页面上传学生规划书
    3. **OCR 转换**：系统自动将 PDF 转换为可评分的文本
    4. **执行评分**：在「智能评分」页面选择模型和评分标准
    5. **查看结果**：在「结果中心」查看详细评分并导出 CSV

    ### 支持的 LLM 模型

    - Google Gemini
    - OpenAI GPT-4
    - Anthropic Claude
    - DeepSeek
    - 阿里云 Qwen
    - 字节 Doubao
    - Kimi (Moonshot)
    """)
