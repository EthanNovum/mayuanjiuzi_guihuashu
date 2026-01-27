"""
结果中心页面
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import init_config, get_output_dir
from utils.session import init_session_state
from components.result_viewer import (
    display_results_table,
    display_summary_metrics,
    display_score_card,
    display_score_distribution
)
from services.export_service import (
    export_to_csv_string,
    export_to_json_string,
    generate_export_filename,
    get_results_summary
)

st.set_page_config(
    page_title="结果中心 - 规划书评分系统",
    page_icon="📊",
    layout="wide",
)

init_session_state()
init_config()

st.title("📊 结果中心")
st.markdown("查看评分结果，分析数据，导出报告。")
st.divider()

# 获取结果
results = st.session_state.get("scoring_results", [])

if not results:
    st.info("暂无评分结果。请先在「智能评分」页面执行评分。")
    st.stop()

# 汇总指标
st.subheader("📈 数据概览")
display_summary_metrics(results)

st.divider()

# 选项卡
tab1, tab2, tab3 = st.tabs(["📋 结果列表", "📊 数据分析", "📥 导出数据"])

with tab1:
    st.subheader("评分结果列表")

    # 筛选器
    col1, col2, col3 = st.columns(3)

    with col1:
        providers = list(set(r.get("provider", "") for r in results if r.get("provider")))
        filter_provider = st.multiselect("筛选模型", options=providers, default=providers)

    with col2:
        prompts = list(set(r.get("prompt_name", "") for r in results if r.get("prompt_name")))
        filter_prompt = st.multiselect("筛选 Prompt", options=prompts, default=prompts)

    with col3:
        filter_status = st.selectbox("筛选状态", options=["全部", "成功", "失败"])

    # 应用筛选
    filtered = results
    if filter_provider:
        filtered = [r for r in filtered if r.get("provider") in filter_provider]
    if filter_prompt:
        filtered = [r for r in filtered if r.get("prompt_name") in filter_prompt]
    if filter_status == "成功":
        filtered = [r for r in filtered if not r.get("error")]
    elif filter_status == "失败":
        filtered = [r for r in filtered if r.get("error")]

    st.caption(f"显示 {len(filtered)} / {len(results)} 条结果")

    # 显示表格
    display_results_table(filtered)

    # 详细卡片视图
    st.divider()
    st.subheader("详细视图")

    for result in filtered:
        display_score_card(result)

with tab2:
    st.subheader("数据分析")

    # 分数分布
    st.markdown("### 分数分布")
    display_score_distribution(results)

    # 按模型统计
    st.markdown("### 按模型统计")

    providers = list(set(r.get("provider", "") for r in results if r.get("provider")))

    for provider in providers:
        provider_results = [r for r in results if r.get("provider") == provider]
        summary = get_results_summary(provider_results)

        with st.expander(f"🤖 {provider}"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("评分数", summary["total"])
            with col2:
                st.metric("成功", summary["success"])
            with col3:
                st.metric("失败", summary["error"])
            with col4:
                if summary["avg_score"]:
                    st.metric("平均分", f"{summary['avg_score']:.1f}")
                else:
                    st.metric("平均分", "-")

    # 按学生统计
    st.markdown("### 按学生统计")

    students = list(set(r.get("student_name", "") for r in results if r.get("student_name")))

    import pandas as pd

    student_data = []
    for student in students:
        student_results = [r for r in results if r.get("student_name") == student and not r.get("error")]
        scores = [r.get("score") for r in student_results if r.get("score") is not None]

        if scores:
            student_data.append({
                "学生姓名": student,
                "评分次数": len(scores),
                "平均分": sum(scores) / len(scores),
                "最高分": max(scores),
                "最低分": min(scores),
            })

    if student_data:
        df = pd.DataFrame(student_data)
        df = df.sort_values("平均分", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("导出数据")

    export_format = st.radio(
        "导出格式",
        ["CSV", "JSON"],
        horizontal=True
    )

    # 选择导出范围
    export_scope = st.radio(
        "导出范围",
        ["全部结果", "筛选后结果"],
        horizontal=True
    )

    if export_scope == "筛选后结果":
        export_data = filtered
    else:
        export_data = results

    st.caption(f"将导出 {len(export_data)} 条结果")

    if export_format == "CSV":
        csv_content = export_to_csv_string(export_data)
        filename = generate_export_filename("result", "csv")

        st.download_button(
            label="📥 下载 CSV",
            data=csv_content,
            file_name=filename,
            mime="text/csv",
            type="primary",
            use_container_width=True
        )

    else:
        json_content = export_to_json_string(export_data)
        filename = generate_export_filename("result", "json")

        st.download_button(
            label="📥 下载 JSON",
            data=json_content,
            file_name=filename,
            mime="application/json",
            type="primary",
            use_container_width=True
        )

    # 清空结果选项
    st.divider()
    st.subheader("⚠️ 危险操作")

    if st.button("🗑️ 清空所有评分结果", type="secondary"):
        st.session_state.scoring_results = []
        st.rerun()
