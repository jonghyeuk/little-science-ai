# app.py

import streamlit as st
import time

st.set_page_config(page_title="LittleScienceAI", layout="wide")  # ✅ 최상단 필수

from utils.layout import render_title, render_paragraph, load_css
from utils.search_db import search_similar_titles
from utils.search_arxiv import search_arxiv
from utils.explain_topic import explain_topic
from utils.pdf_generator import generate_pdf

# 🎨 커스텀 CSS
load_css()

# 🔐 인증
ACCESS_KEYS = st.secrets["general"]["access_keys"]
user_key = st.text_input("🔑 인증 키를 입력하세요", type="password")
if user_key not in ACCESS_KEYS:
    st.warning("🚫 올바른 인증 키를 입력하세요.")
    st.stop()

# ✅ 사이드 메뉴 & 레이아웃 구성
st.sidebar.title("🧭 탐색 단계")
st.sidebar.markdown("""
1️⃣ 주제 입력  
2️⃣ 개념 해설 보기  
3️⃣ 논문 추천 확인  
4️⃣ PDF 저장  
""")

render_title("🧪 과학 소논문 주제 탐색 도우미")

# 🔍 주제 입력
topic = st.text_input("🔬 연구하고 싶은 과학 주제를 입력하세요:")

if topic:
    st.subheader("📘 주제 해설")

    with st.spinner("🤖 AI가 주제에 대해 고민하고 있습니다..."):
        lines = explain_topic(topic)  # 이제 리스트 반환됨
        placeholder = st.empty()
        full_text = ""
        for line in lines:
            full_text += line + "\n"
            placeholder.markdown(f"<div style='font-size:16px;line-height:1.8;'>{full_text}</div>", unsafe_allow_html=True)
            time.sleep(0.15)  # 타이핑 효과 속도

    st.subheader("📄 내부 DB 유사 논문")
    try:
        internal_results = search_similar_titles(topic)
        for paper in internal_results:
            render_paragraph(f"""
- **{paper['제목']}**  
  {paper['요약']}  
  _({paper['연도']} · {paper['분야']})_
""")
    except Exception as e:
        st.error(f"❗ 유사 논문 검색 중 오류가 발생했습니다: {e}")

    st.subheader("🌐 arXiv 유사 논문")
    try:
        arxiv_results = search_arxiv(topic)
        for paper in arxiv_results:
            render_paragraph(f"- [{paper['title']}]({paper['link']})")
    except Exception as e:
        st.error(f"❗ arXiv 논문 검색 중 오류가 발생했습니다: {e}")

    if st.button("📥 이 내용 PDF로 저장하기"):
        path = generate_pdf(full_text)
        with open(path, "rb") as f:
            st.download_button("PDF 다운로드", f, file_name="little_science_ai.pdf")
