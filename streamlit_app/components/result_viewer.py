"""
结果查看组件
"""
import streamlit as st
import pandas as pd
from typing import Any, Dict, List, Optional


# 字段显示名称映射
FIELD_LABELS = {
    "student_name": "学生姓名",
    "filename": "文件名",
    "final_score": "最终分数",
    "level": "申请层级",
    "profile": "申请形象",
    "provider": "评分模型",
    "model": "模型版本",
    "prompt_name": "Prompt",
    "clearness_and_consistency_score": "清晰一致性",
    "clearness_and_consistency_evaluation": "清晰一致性评价",
    "detail_and_executability_score": "详细可执行性",
    "detail_and_executability_evaluation": "详细可执行性评价",
    "depth_and_intensity_score": "深度强度",
    "depth_and_intensity_evaluation": "深度强度评价",
    "noviceness_score": "新颖度",
    "noviceness__evaluation": "新颖度评价",
    "noviceness_evaluation": "新颖度评价",
    "fitness_score": "适配度",
    "fitness_evaluation": "适配度评价",
    "liberal_values_score": "价值观",
    "liberal_values_evaluation": "价值观评价",
    "suggestions": "改进建议",
    "thinking": "模型思考过程",
    "error": "错误信息",
}

# 分数字段列表
SCORE_FIELDS = [
    "clearness_and_consistency_score",
    "detail_and_executability_score",
    "depth_and_intensity_score",
    "noviceness_score",
    "fitness_score",
    "liberal_values_score",
]

# 评价字段列表
EVALUATION_FIELDS = [
    "clearness_and_consistency_evaluation",
    "detail_and_executability_evaluation",
    "depth_and_intensity_evaluation",
    "noviceness__evaluation",
    "noviceness_evaluation",
    "fitness_evaluation",
    "liberal_values_evaluation",
]


def get_field_label(field: str) -> str:
    """获取字段的显示名称"""
    return FIELD_LABELS.get(field, field.replace("_", " ").title())


def display_score_card(result: Dict) -> None:
    """显示单个评分卡片"""
    with st.container():
        # 标题行
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            student_name = result.get("student_name", "未知")
            st.subheader(f"👤 {student_name}")
        with col2:
            # 使用 final_score
            score = result.get("final_score", result.get("score", "-"))
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

        # 详情展开
        with st.expander("📋 查看详情"):
            display_result_details(result)


def display_result_details(result: Dict) -> None:
    """显示结果的所有详细字段"""

    # 基本信息
    st.markdown("#### 📌 基本信息")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**学生姓名:** {result.get('student_name', '-')}")
    with col2:
        st.markdown(f"**最终分数:** {result.get('final_score', result.get('score', '-'))}")
    with col3:
        st.markdown(f"**申请层级:** {result.get('level', '-')}")

    # 申请形象
    if result.get("profile"):
        st.markdown("#### 🎭 申请形象")
        st.info(result["profile"])

    # 子维度分数
    st.markdown("#### 📊 各维度评分")
    score_cols = st.columns(3)
    score_items = [
        ("clearness_and_consistency_score", "清晰一致性"),
        ("detail_and_executability_score", "详细可执行性"),
        ("depth_and_intensity_score", "深度强度"),
        ("noviceness_score", "新颖度"),
        ("fitness_score", "适配度"),
        ("liberal_values_score", "价值观"),
    ]

    for i, (key, label) in enumerate(score_items):
        if key in result:
            with score_cols[i % 3]:
                score = result[key]
                color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
                st.metric(f"{color} {label}", f"{score}分")

    # 各维度详细评价
    st.markdown("#### 📝 各维度评价")

    eval_items = [
        ("clearness_and_consistency_evaluation", "清晰一致性评价"),
        ("detail_and_executability_evaluation", "详细可执行性评价"),
        ("depth_and_intensity_evaluation", "深度强度评价"),
        ("noviceness__evaluation", "新颖度评价"),
        ("noviceness_evaluation", "新颖度评价"),
        ("fitness_evaluation", "适配度评价"),
        ("liberal_values_evaluation", "价值观评价"),
    ]

    for key, label in eval_items:
        if key in result and result[key]:
            with st.expander(f"📄 {label}"):
                st.write(result[key])

    # 改进建议
    if result.get("suggestions"):
        st.markdown("#### 💡 改进建议")
        suggestions = result["suggestions"]
        if isinstance(suggestions, list):
            for i, s in enumerate(suggestions, 1):
                st.markdown(f"{i}. {s}")
        else:
            st.write(suggestions)

    # 模型思考过程
    if result.get("thinking"):
        with st.expander("🧠 模型思考过程"):
            st.text_area(
                "Thinking",
                value=result["thinking"],
                height=300,
                disabled=True,
                label_visibility="collapsed"
            )

    # 元信息
    st.markdown("#### ⚙️ 评分元信息")
    meta_col1, meta_col2, meta_col3 = st.columns(3)
    with meta_col1:
        st.caption(f"模型: {result.get('provider', '-')}")
    with meta_col2:
        st.caption(f"版本: {result.get('model', '-')}")
    with meta_col3:
        st.caption(f"Prompt: {result.get('prompt_name', '-')}")

    # 显示其他未列出的字段
    displayed_keys = {
        "student_name", "filename", "final_score", "score", "level", "profile",
        "provider", "model", "prompt_name", "suggestions", "thinking", "error",
        *[k for k, _ in score_items],
        *[k for k, _ in eval_items],
    }

    other_fields = {k: v for k, v in result.items() if k not in displayed_keys and v}

    if other_fields:
        st.markdown("#### 📎 其他字段")
        for key, value in other_fields.items():
            label = get_field_label(key)
            if isinstance(value, (str, int, float)):
                st.markdown(f"**{label}:** {value}")
            elif isinstance(value, list):
                st.markdown(f"**{label}:**")
                for item in value:
                    st.markdown(f"  - {item}")


def display_results_table(results: List[Dict], key: str = "results_table") -> Optional[Dict]:
    """
    显示结果表格

    Returns:
        选中的行（如果有）
    """
    if not results:
        st.info("暂无评分结果")
        return None

    # 准备数据 - 使用 final_score
    df_data = []
    for r in results:
        df_data.append({
            "学生姓名": r.get("student_name", "-"),
            "最终分数": r.get("final_score", r.get("score", "-")),
            "申请层级": r.get("level", "-"),
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
            "最终分数": st.column_config.NumberColumn(format="%d"),
        }
    )

    return None


def display_score_distribution(results: List[Dict]) -> None:
    """显示分数分布图"""
    # 使用 final_score
    scores = [r.get("final_score", r.get("score")) for r in results
              if r.get("final_score") is not None or r.get("score") is not None]

    if not scores:
        st.info("暂无有效分数数据")
        return

    df = pd.DataFrame({"分数": scores})
    st.bar_chart(df["分数"].value_counts().sort_index())


def display_summary_metrics(results: List[Dict]) -> None:
    """显示汇总指标"""
    if not results:
        return

    success = [r for r in results if not r.get("error")]
    errors = [r for r in results if r.get("error")]
    # 使用 final_score
    scores = [r.get("final_score", r.get("score")) for r in success
              if r.get("final_score") is not None or r.get("score") is not None]

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
