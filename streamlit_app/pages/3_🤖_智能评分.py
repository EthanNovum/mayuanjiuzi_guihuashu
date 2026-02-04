"""
智能评分页面
"""
import streamlit as st
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import init_config, get_prompts_dir, get_mds_dir
from utils.session import init_session_state
from components.progress_tracker import ProgressTracker
from components.result_viewer import display_summary_metrics
from services.scoring_service import (
    SUPPORTED_PROVIDERS,
    get_available_providers,
    list_prompt_files,
    load_prompt_file,
    score_batch
)
from services.storage_service import save_scoring_results, add_history_entry

st.set_page_config(
    page_title="智能评分 - 规划书评分系统",
    page_icon="🤖",
    layout="wide",
)

init_session_state()
init_config()

st.title("🤖 智能评分")
st.markdown("使用 AI 模型对学生规划书进行智能评分。")
st.divider()

api_config = st.session_state.get("api_config", {})

# 检查可用的 LLM
available_providers = get_available_providers(api_config)

if not available_providers:
    st.warning("⚠️ 请先在「系统设置」页面配置至少一个 LLM API 密钥")
    st.stop()

# 选项卡
tab1, tab2 = st.tabs(["🎯 执行评分", "📋 Prompt 管理"])

with tab1:
    # 步骤 1: 选择文件
    st.subheader("1️⃣ 选择待评分文件")

    file_source = st.radio(
        "文件来源",
        ["本次处理结果", "mds 目录文件"],
        horizontal=True,
        key="scoring_source"
    )

    files_to_score = []

    if file_source == "本次处理结果":
        processed = st.session_state.get("processed_markdowns", [])
        success_files = [p for p in processed if p.get("status") == "success" and p.get("markdown")]

        if not success_files:
            st.info("暂无可评分文件，请先在「PDF 处理」页面处理 PDF。")
        else:
            st.caption(f"共 {len(success_files)} 个可评分文件")

            # 全选
            select_all = st.checkbox("全选", value=True, key="score_select_all")

            selected_indices = []
            cols = st.columns(3)
            for i, item in enumerate(success_files):
                with cols[i % 3]:
                    if st.checkbox(item.get("filename", f"文件 {i+1}"), value=select_all, key=f"score_file_{i}"):
                        selected_indices.append(i)

            files_to_score = [success_files[i] for i in selected_indices]
            st.caption(f"已选择 {len(files_to_score)} 个文件")

    else:
        mds_dir = get_mds_dir()
        if mds_dir.exists():
            md_files = sorted([f for f in os.listdir(mds_dir) if f.endswith(".md")])

            if md_files:
                st.caption(f"共 {len(md_files)} 个文件")

                select_all = st.checkbox("全选", value=True, key="score_mds_all")

                selected_files = []
                cols = st.columns(3)
                for i, filename in enumerate(md_files):
                    with cols[i % 3]:
                        if st.checkbox(filename, value=select_all, key=f"score_mds_{i}"):
                            selected_files.append(filename)

                # 加载选中文件内容
                for filename in selected_files:
                    filepath = mds_dir / filename
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    files_to_score.append({
                        "filename": filename,
                        "markdown": content,
                    })

                st.caption(f"已选择 {len(files_to_score)} 个文件")
            else:
                st.info("mds 目录中暂无文件")
        else:
            st.info("mds 目录不存在")

    st.divider()

    # 步骤 2: 选择模型
    st.subheader("2️⃣ 选择评分模型")

    selected_providers = st.multiselect(
        "选择 LLM 提供商",
        options=available_providers,
        default=available_providers[:1] if available_providers else [],
        help="可选择多个模型进行对比评分"
    )

    if selected_providers:
        st.caption(f"已选择: {', '.join(selected_providers)}")

    st.divider()

    # 步骤 3: 选择 Prompt
    st.subheader("3️⃣ 选择评分标准 (Prompt)")

    prompts_dir = get_prompts_dir()
    prompt_files = list_prompt_files(str(prompts_dir))

    prompt_source = st.radio(
        "Prompt 来源",
        ["选择已有模板", "自定义输入"],
        horizontal=True
    )

    selected_prompt = ""
    prompt_name = ""

    if prompt_source == "选择已有模板":
        if prompt_files:
            prompt_options = {p["name"]: p["path"] for p in prompt_files}
            selected_name = st.selectbox(
                "选择 Prompt 模板",
                options=list(prompt_options.keys())
            )

            if selected_name:
                prompt_path = prompt_options[selected_name]
                selected_prompt = load_prompt_file(prompt_path)
                prompt_name = selected_name

                with st.expander("预览 Prompt"):
                    st.text_area(
                        "Prompt 内容",
                        value=selected_prompt,
                        height=300,
                        disabled=True
                    )
        else:
            st.warning(f"prompts 目录中暂无模板文件: {prompts_dir}")

    else:
        prompt_name = st.text_input("Prompt 名称", value="custom")
        selected_prompt = st.text_area(
            "输入 Prompt",
            height=300,
            placeholder="请输入评分标准和要求..."
        )

    st.divider()

    # 步骤 4: 执行评分
    st.subheader("4️⃣ 执行评分")

    # 检查条件
    can_score = (
        len(files_to_score) > 0 and
        len(selected_providers) > 0 and
        len(selected_prompt.strip()) > 0
    )

    if not can_score:
        missing = []
        if len(files_to_score) == 0:
            missing.append("待评分文件")
        if len(selected_providers) == 0:
            missing.append("评分模型")
        if len(selected_prompt.strip()) == 0:
            missing.append("评分 Prompt")

        st.warning(f"请完成以下配置: {', '.join(missing)}")

    else:
        total_tasks = len(files_to_score) * len(selected_providers)
        st.info(f"将执行 {total_tasks} 个评分任务 ({len(files_to_score)} 文件 × {len(selected_providers)} 模型)")

        if st.button("🚀 开始评分", type="primary", use_container_width=True):
            progress = ProgressTracker(total_tasks, "正在评分...")

            def progress_callback(current, total, message):
                progress.update(current, message)

            results = score_batch(
                files=files_to_score,
                providers=selected_providers,
                prompt=selected_prompt,
                api_config=api_config,
                prompt_name=prompt_name,
                progress_callback=progress_callback
            )

            progress.complete("评分完成！")

            # 保存结果到 session
            existing_results = st.session_state.get("scoring_results", [])
            st.session_state.scoring_results = existing_results + results

            # 持久化保存到文件
            save_scoring_results(results, append=True)
            add_history_entry("scoring", {
                "total": len(results),
                "success": len([r for r in results if not r.get("error")]),
                "providers": selected_providers,
                "prompt_name": prompt_name,
                "files": [f.get("filename") for f in files_to_score]
            })

            # 显示结果
            st.divider()
            st.subheader("📊 评分结果")

            display_summary_metrics(results)

            for result in results:
                status = "✅" if not result.get("error") else "❌"
                student = result.get("student_name", "未知")
                score = result.get("score", "-")
                provider = result.get("provider", "-")

                with st.expander(f"{status} {student} - {score}分 ({provider})"):
                    if result.get("error"):
                        st.error(result["error"])
                    else:
                        # 显示详细评分
                        if result.get("strengths"):
                            st.markdown("**✨ 优势:**")
                            for s in (result["strengths"] if isinstance(result["strengths"], list) else [result["strengths"]]):
                                st.markdown(f"- {s}")

                        if result.get("gaps"):
                            st.markdown("**📌 不足:**")
                            for g in (result["gaps"] if isinstance(result["gaps"], list) else [result["gaps"]]):
                                st.markdown(f"- {g}")

                        if result.get("suggestions"):
                            st.markdown("**💡 建议:**")
                            for s in (result["suggestions"] if isinstance(result["suggestions"], list) else [result["suggestions"]]):
                                st.markdown(f"- {s}")

            st.success("评分结果已保存，可在「结果中心」查看和导出。")

with tab2:
    st.subheader("Prompt 模板管理")

    prompt_files = list_prompt_files(str(prompts_dir))

    if prompt_files:
        for p in prompt_files:
            with st.expander(f"📋 {p['name']}"):
                content = load_prompt_file(p["path"])
                st.text_area(
                    "内容",
                    value=content,
                    height=200,
                    key=f"prompt_{p['name']}",
                    disabled=True
                )
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("📋 复制", key=f"copy_{p['name']}"):
                        st.session_state[f"copied_{p['name']}"] = True
                        st.toast(f"已复制 {p['name']} 到剪贴板！")
                with col2:
                    st.caption(f"路径: {p['path']}")

                # 使用 JavaScript 实现复制到剪贴板
                if st.session_state.get(f"copied_{p['name']}", False):
                    st.session_state[f"copied_{p['name']}"] = False
                    escaped_content = content.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
                    st.components.v1.html(
                        f"""
                        <script>
                        navigator.clipboard.writeText(`{escaped_content}`);
                        </script>
                        """,
                        height=0
                    )
    else:
        st.info("暂无 Prompt 模板")

    st.divider()
    st.caption(f"Prompt 目录: {prompts_dir}")
