# app.py

import streamlit as st
from utils.search_db import search_similar_titles
from utils.search_arxiv import search_arxiv
from utils.explain_topic import explain_topic
from utils.pdf_generator import generate_pdf
from utils.layout import render_title, render_paragraph

st.set_page_config(page_title="LittleScienceAI", layout="wide")

st.sidebar.title("🔍 탐색 단계")
st.sidebar.markdown("""
1️⃣ 주제 입력  
2️⃣ 개념 해설 보기  
3️⃣ 논문 추천 확인  
4️⃣ PDF 저장  
""")

render_title("과학 소논문 주제 탐색 도우미")

topic = st.text_input("🔬 연구하고 싶은 과학 주제를 입력하세요:")

if topic:
    st.subheader("📘 주제 해설")
    explanation = explain_topic(topic)
    render_paragraph(explanation)

    st.subheader("📄 내부 DB 유사 논문")
    internal_results = search_similar_titles(topic)
    for paper in internal_results:
        render_paragraph(f"- **{paper['제목']}** ({paper['연도']})\n\n{paper['요약']}")

    st.subheader("🌐 arXiv 유사 논문")
    arxiv_results = search_arxiv(topic)
    for paper in arxiv_results:
        render_paragraph(f"- [{paper['title']}]({paper['link']})")

    if st.button("📥 이 내용 PDF로 저장하기"):
        path = generate_pdf(explanation)
        with open(path, "rb") as f:
            st.download_button("PDF 다운로드", f, file_name="little_science_ai.pdf")

