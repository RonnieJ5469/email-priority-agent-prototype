import json
import time

import pandas as pd
import streamlit as st

from core.classifier import classify_email, available_models, MODEL_LABELS

# ── 页面配置 ──────────────────────────────────────────────
st.set_page_config(
    page_title="Email Priority Agent",
    page_icon="📧",
    layout="wide",
)

# ── 加载配置 ──────────────────────────────────────────────
@st.cache_data
def load_context():
    with open("config/user_context.json", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_emails():
    with open("test_cases/emails.json", encoding="utf-8") as f:
        return json.load(f)

ctx = load_context()
test_emails = load_emails()

# ── 分类样式常量 ──────────────────────────────────────────
CATEGORY_CFG = {
    "Needs Your Action":   {"icon": "🔴", "color": "#e53e3e", "label": "Needs Your Action"},
    "Needs Your Response": {"icon": "🟡", "color": "#d69e2e", "label": "Needs Your Response"},
    "FYI":                 {"icon": "🔵", "color": "#3182ce", "label": "FYI"},
    "Low Priority":        {"icon": "⚪", "color": "#718096", "label": "Low Priority"},
}

# ── Header ────────────────────────────────────────────────
st.title("📧 Email Priority Agent")
st.caption(
    f"为 **{ctx['name']}**（{ctx['title']} @ {ctx['company']}）分析邮件优先级"
)
st.divider()

# ── 侧边栏 ────────────────────────────────────────────────

# 模型选择器（只显示已配置 API Key 的模型）
models = available_models()
if not models:
    st.sidebar.error("⚠️ 未检测到任何 API Key，请在 .env 文件中配置至少一个。")
    st.stop()

model_options = [MODEL_LABELS[m] for m in models]
selected_label = st.sidebar.selectbox("🤖 选择模型", model_options)
selected_model = models[model_options.index(selected_label)]

st.sidebar.divider()

# 邮件输入方式
mode = st.sidebar.radio("输入方式", ["📋 选择测试用例", "✏️ 手动输入邮件"])

if mode == "📋 选择测试用例":
    options = [f"#{e['id']} {e['label']}" for e in test_emails]
    chosen = st.sidebar.selectbox("测试邮件", options)
    idx = options.index(chosen)
    email = test_emails[idx]

    exp = email.get("expected", {})
    if exp:
        st.sidebar.divider()
        st.sidebar.markdown("**预期结果**")
        cat = exp.get("category", "-")
        cfg = CATEGORY_CFG.get(cat, {})
        icon = cfg.get("icon", "")
        st.sidebar.markdown(f"分类：{icon} `{cat}`")
        st.sidebar.caption(exp.get("note", ""))
else:
    st.sidebar.markdown("### 填写邮件信息")
    email = {
        "id": 0,
        "label": "自定义邮件",
        "from_name":      st.sidebar.text_input("发件人姓名"),
        "from_email":     st.sidebar.text_input("发件人邮箱"),
        "to":             st.sidebar.text_input("收件人 To", value=f"{ctx['name']} <linyifan@byteflow.ai>"),
        "cc":             st.sidebar.text_input("抄送 CC"),
        "datetime":       st.sidebar.text_input("发送时间", value="2026-04-08 10:00"),
        "subject":        st.sidebar.text_input("主题"),
        "body":           st.sidebar.text_area("正文", height=180),
        "has_attachment": st.sidebar.checkbox("有附件"),
        "is_thread":      st.sidebar.checkbox("转发/回复链"),
    }

# ── 主区域：邮件 + 分析结果 ───────────────────────────────
col_email, col_result = st.columns(2, gap="large")

with col_email:
    st.subheader("📨 邮件内容")
    st.markdown(f"**发件人：** {email.get('from_name')} `{email.get('from_email')}`")
    st.markdown(f"**收件人：** {email.get('to')}")
    if email.get("cc"):
        st.markdown(f"**抄送：** {email.get('cc')}")
    st.markdown(f"**时间：** {email.get('datetime')}")
    st.markdown(f"**主题：** **{email.get('subject')}**")
    flags = []
    if email.get("has_attachment"):
        flags.append("📎 有附件")
    if email.get("is_thread"):
        flags.append("🔄 转发/回复链")
    if flags:
        st.markdown("  ".join(flags))
    st.divider()
    st.markdown(email.get("body", ""))

with col_result:
    st.subheader("🤖 Agent 分析")
    st.caption(f"当前模型：**{selected_label}**")
    run_btn = st.button("▶ 开始分析", type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("分析中…"):
            t0 = time.time()
            result, thinking = classify_email(email, ctx, model=selected_model)
            elapsed = time.time() - t0

        if not result:
            st.error(f"解析失败：{thinking or '请检查 API Key 或重试。'}")
        else:
            category    = result.get("category", "Needs Your Response")
            confidence  = result.get("confidence", "High")
            conf_note   = result.get("confidence_note", "")
            security    = result.get("security_flag", False)

            ccfg = CATEGORY_CFG.get(category, CATEGORY_CFG["Needs Your Response"])

            # 安全警告（最优先展示）
            if security:
                st.error(
                    "🚨 **安全警告：** 检测到可疑指令注入，分类结果仅供参考。"
                    + (f"\n\n{conf_note}" if conf_note else "")
                )

            # 分类 badge
            st.markdown(
                f"""<div style="background:{ccfg['color']}18; border-left:4px solid {ccfg['color']};
                    padding:12px 16px; border-radius:6px; margin-bottom:8px;">
                  <span style="font-size:22px">{ccfg['icon']}</span>
                  <span style="font-size:18px; font-weight:700; margin-left:8px">{ccfg['label']}</span>
                </div>""",
                unsafe_allow_html=True,
            )

            # 置信度警告
            if confidence != "High" and not security:
                st.warning(f"⚠️ 置信度：**{confidence}** — {conf_note}")

            st.divider()

            # 判断理由
            st.markdown("**📋 判断理由**")
            st.info(result.get("reasoning", ""))

            # 关键原文
            if result.get("key_quote"):
                st.markdown("**💬 关键原文**")
                st.markdown(f"> *{result.get('key_quote')}*")

            # 行动项
            items = [a for a in result.get("action_items", []) if a.get("description")]
            if items:
                st.markdown("**✅ 行动项**")
                for item in items:
                    owner = item.get("owner", "")
                    is_user = (owner == "user")
                    owner_label = "**[你]**" if is_user else f"[{owner}]"
                    dl = f" — 截止 `{item['deadline']}`" if item.get("deadline") else ""
                    confirm = " ℹ️ *待确认：你是否需要参与此项？*" if item.get("needs_confirmation") else ""
                    st.markdown(f"- {owner_label} {item.get('description')}{dl}{confirm}")

            st.caption(f"⏱ 处理耗时：{elapsed:.1f}s")

            # 推理过程（折叠）
            if thinking:
                with st.expander("🧠 查看 Agent 推理过程"):
                    st.markdown(thinking)

# ── 批量测试 ──────────────────────────────────────────────
st.divider()
st.subheader("🔄 批量测试 — 运行全部用例")

batch_col1, batch_col2 = st.columns(2)

with batch_col1:
    run_batch = st.button(
        f"运行全部 {len(test_emails)} 个测试用例（{selected_label}）",
        use_container_width=True,
    )

with batch_col2:
    run_compare = st.button(
        "跨模型对比（全部已配置模型）",
        use_container_width=True,
        disabled=len(models) < 2,
    )

# 单模型批量测试
if run_batch:
    rows = []
    progress = st.progress(0, text="准备中…")

    for i, case in enumerate(test_emails):
        progress.progress(i / len(test_emails), text=f"分析 #{case['id']} {case['label']}…")
        result, _ = classify_email(case, ctx, model=selected_model)

        exp = case.get("expected", {})
        actual = result.get("category", "?") if result else "ERROR"
        expected_cat = exp.get("category", "-")
        conf = result.get("confidence", "?") if result else "?"
        sec = "🚨" if (result or {}).get("security_flag") else ""

        ok = "✅" if actual == expected_cat else "❌"
        rows.append({
            "用例":     f"#{case['id']} {case['label']}",
            "预期分类": expected_cat,
            "实际分类": actual,
            "置信度":   conf,
            "安全":     sec,
            "结果":     ok,
        })

    progress.progress(1.0, text="完成！")

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    passed = sum(1 for r in rows if r["结果"] == "✅")
    total  = len(rows)
    c1, c2 = st.columns(2)
    c1.metric("✅ 通过", f"{passed}/{total}")
    c2.metric("通过率", f"{passed/total*100:.0f}%")

# 跨模型对比
if run_compare and len(models) >= 2:
    st.markdown(f"**跨模型对比** — 模型：{', '.join(MODEL_LABELS[m] for m in models)}")
    compare_rows = []
    total_cases = len(test_emails) * len(models)
    progress2 = st.progress(0, text="准备中…")
    counter = 0

    for case in test_emails:
        exp_cat = case.get("expected", {}).get("category", "-")
        row = {"用例": f"#{case['id']} {case['label']}", "预期": exp_cat}
        for m in models:
            progress2.progress(counter / total_cases, text=f"[{MODEL_LABELS[m]}] #{case['id']}…")
            result, _ = classify_email(case, ctx, model=m)
            actual = result.get("category", "?") if result else "ERROR"
            match = "✅" if actual == exp_cat else "❌"
            short = {
                "Needs Your Action":   "🔴 Action",
                "Needs Your Response": "🟡 Response",
                "FYI":                 "🔵 FYI",
                "Low Priority":        "⚪ Low",
            }.get(actual, actual)
            row[MODEL_LABELS[m]] = f"{match} {short}"
            counter += 1
        compare_rows.append(row)

    progress2.progress(1.0, text="完成！")
    df2 = pd.DataFrame(compare_rows)
    st.dataframe(df2, use_container_width=True, hide_index=True)
