"""
结果查看组件
"""
import streamlit as st
import pandas as pd
from typing import Any, Dict, List, Optional


def display_score_card(result: Dict) -> None:
    """显示单个评分卡片"""
    with st.container():
        # 标题行
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            student_name = result.get("student_name", "未知")
            st.subheader(f"👤 {student_name}")
        with col2:
            score = result.get("score", "-")
            if isinstance(score, (int, float)):
                color = "green" if score >= 80 else "orange" if score >= 60 else "red"
                st.markdown(f"### :{color}[{score}分]")
            else:
                st.markdown(f"### {score}")
        with col3:
            provider = result.get("provider", "-")
            st.caption(f"🤖 {provider}")

        # 错误信息
        if result.get("error"):
            st.error(f"❌ 错误: {result['error']}")
            return

        # 详细内容
        with st.expander("查看详情"):
            # 子分数
            subscores = ["clearness_and_consistency", "detail_and_executable",
                        "depth_and_intensity", "noviceness", "fitness", "liberal_arts_values"]

            score_cols = st.columns(3)
            for i, key in enumerate(subscores):
                if key in result:
                    with score_cols[i % 3]:
                        label = key.replace("_", " ").title()
                        st.metric(label[:15], result[key])

            st.divider()

            # 优势
            if result.get("strengths"):
                st.markdown("**✨ 优势:**")
                strengths = result["strengths"]
                if isinstance(strengths, list):
                    for s in strengths:
                        st.markdown(f"- {s}")
                else:
                    st.write(strengths)

            # 不足
            if result.get("gaps"):
                st.markdown("**📌 不足:**")
                gaps = result["gaps"]
                if isinstance(gaps, list):
                    for g in gaps:
                        st.markdown(f"- {g}")
                else:
                    st.write(gaps)

            # 建议
            if result.get("suggestions"):
                st.markdown("**💡 建议:**")
                suggestions = result["suggestions"]
                if isinstance(suggestions, list):
                    for s in suggestions:
                        st.markdown(f"- {s}")
                else:
                    st.write(suggestions)


def display_results_table(results: List[Dict], key: str = "results_table") -> Optional[Dict]:
    """
    显示结果表格

    Returns:
        选中的行（如果有）
    """
    if not results:
        st.info("暂无评分结果")
        return None

    # 准备数据
    df_data = []
    for r in results:
        df_data.append({
            "学生姓名": r.get("student_name", "-"),
            "分数": r.get("score", "-"),
            "模型": r.get("provider", "-"),
            "Prompt": r.get("prompt_name", "-"),
            "状态": "✅" if not r.get("error") else "❌",
        })

    df = pd.DataFrame(df_data)

    # 显示表格
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "分数": st.column_config.NumberColumn(format="%d"),
        }
    )

    return None


def display_score_distribution(results: List[Dict]) -> None:
    """显示分数分布图"""
    scores = [r.get("score") for r in results if r.get("score") is not None]

    if not scores:
        st.info("暂无有效分数数据")
        return

    import pandas as pd

    # 分数分布
    df = pd.DataFrame({"分数": scores})

    st.bar_chart(df["分数"].value_counts().sort_index())


def display_summary_metrics(results: List[Dict]) -> None:
    """显示汇总指标"""
    if not results:
        return

    success = [r for r in results if not r.get("error")]
    errors = [r for r in results if r.get("error")]
    scores = [r.get("score") for r in success if r.get("score") is not None]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("总数", len(results))

    with col2:
        st.metric("成功", len(success), delta=None)

    with col3:
        if errors:
            st.metric("失败", len(errors), delta=None)
        else:
            st.metric("失败", 0)

    with col4:
        if scores:
            avg = sum(scores) / len(scores)
            st.metric("平均分", f"{avg:.1f}")
        else:
            st.metric("平均分", "-")
