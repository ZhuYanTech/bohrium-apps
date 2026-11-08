#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_streamlit.py — PLIP 中文演示界面（Streamlit）

定位：本地演示 + 玻尔 App 的 UI 参考。真正跑任务的是 run_plip.py，
界面本身不做任何计算、不调任何外部 API，只在本机调用 run_plip.py。

启动：
  pip install -r requirements.txt   # streamlit + pandas
  pip install plip==3.0.1           # 本机也要装 PLIP（或改用 Docker，见 README）
  streamlit run app_streamlit.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

BASE = Path(__file__).resolve().parent
RUN_PLIP = BASE / "run_plip.py"

st.set_page_config(page_title="PLIP 结合模式解析", page_icon="🧬", layout="wide")
st.title("🧬 PLIP 蛋白-配体相互作用分析")
st.markdown(
    "上传一个蛋白-配体复合物 PDB，或输入 PDB 编号，几分钟得到相互作用清单和中文报告。"
    "底层是开源 PLIP（GPLv2），不调用任何第三方 API，计算在你自己的机器 / 玻尔节点上跑。"
)

with st.sidebar:
    st.header("使用说明")
    st.markdown(
        "1. 上传 PDB 文件，**或**输入 PDB ID（二选一）\n"
        "2. 点「开始分析」\n"
        "3. 看表格和中文报告，下载 CSV / 报告\n\n"
        "示例：`1VSN`（Cathepsin K + 小分子抑制剂 NFT）\n\n"
        "注意：PLIP 只检测相互作用，**不预测结合亲和力**。"
    )
    model = st.number_input("PDB 模型编号", min_value=1, value=1, step=1)

col1, col2 = st.columns(2)
with col1:
    uploaded = st.file_uploader("上传 PDB 文件", type=["pdb", "ent"])
with col2:
    pdb_id = st.text_input("或输入 PDB ID", value="1VSN", max_chars=4,
                           help="4 位编号，如 1VSN、3MXF，将从 RCSB 下载")

if st.button("开始分析", type="primary"):
    if not uploaded and not pdb_id.strip():
        st.error("请先上传 PDB 文件，或输入一个 PDB ID。")
        st.stop()
    if uploaded and pdb_id.strip() and pdb_id.strip().upper() != "1VSN":
        st.warning("同时给了文件和 PDB ID，将优先使用上传的文件。")

    work = BASE / ".streamlit-work"
    work.mkdir(exist_ok=True)
    out_dir = work / "plip-output"
    cmd = [sys.executable, str(RUN_PLIP), "--out-dir", str(out_dir),
           "--model", str(int(model))]
    if uploaded:
        pdb_path = work / "input.pdb"
        pdb_path.write_bytes(uploaded.getvalue())
        cmd += ["--pdb-file", str(pdb_path)]
    else:
        cmd += ["--pdb-id", pdb_id.strip().upper()]

    with st.spinner("PLIP 分析中，通常不到 1 分钟…"):
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    st.code(proc.stdout[-3000:] if proc.stdout else "(无输出)")
    if proc.returncode != 0:
        st.error("分析失败，原因见上方日志。")
        if proc.stderr:
            st.code(proc.stderr[-3000:])
        st.stop()

    csv_path = out_dir / "interactions.csv"
    report_path = out_dir / "report_zh.md"
    if not csv_path.exists():
        st.error("未生成 interactions.csv，请看日志。")
        st.stop()

    df = pd.read_csv(csv_path)
    st.success(f"完成：共 {len(df)} 个相互作用")
    if not df.empty:
        st.subheader("按类型统计")
        st.bar_chart(df["interaction_type_zh"].value_counts())
        st.subheader("相互作用清单")
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("未检测到相互作用，请检查结构中是否有配体，详见中文报告。")

    if report_path.exists():
        st.subheader("中文报告")
        st.markdown(report_path.read_text(encoding="utf-8"))

    st.subheader("下载")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("下载 interactions.csv", csv_path.read_bytes(),
                           file_name="interactions.csv", mime="text/csv")
    with c2:
        if report_path.exists():
            st.download_button("下载中文报告 (.md)", report_path.read_bytes(),
                               file_name="report_zh.md", mime="text/markdown")
    with c3:
        raw_xml = list((out_dir / "plip_raw").glob("*_report.xml"))
        if raw_xml:
            st.download_button("下载 PLIP 原始 XML", raw_xml[0].read_bytes(),
                               file_name=raw_xml[0].name, mime="application/xml")

st.divider()
st.caption(
    "引用：Salentin et al., Nucleic Acids Res. 2015, doi:10.1093/nar/gkv315；"
    "Schake et al., PLIP 2025, Nucleic Acids Res. 2025, gkaf361。PLIP 许可 GPLv2。"
)
