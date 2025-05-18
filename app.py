# app.py

import streamlit as st
import time

# ✅ 페이지 설정 (가장 위에 반드시 위치)
st.set_page_config(page_title="LittleScienceAI", layout="wide")

# ✅ 커스텀 유틸리티 불러오기
from utils.layout import render_title, render_paragraph, load_css
from utils.search_db import search_similar_titles
from utils.search_arxiv import search_arxiv
from utils.explain_topic import explain_topic
from utils.pdf_generator import generate_pdf

# ✅ 커스텀 CSS 스타일 적용
load_css()

# 🔐 인증 처리
ACCESS_KEYS = st.secrets["general"]["access_keys"]
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    user_key = st.text_input("🔑 인증 키를 입력하세요", type="password")
    if user_key in ACCESS_KEYS:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.warning("🚫 올바른 인증 키를 입력하세요.")
        st.stop()

# ✅ 사이드 메뉴 UI
st.sidebar.title("🧭 탐색 단계")
st.sidebar.markdown("""
1️⃣ 주제 입력  
2️⃣ 개념 해설 보기  
3️⃣ 논문 추천 확인  
4️⃣ PDF 저장  
""")

# ✅ 제목 출력
render_title("🧪 과학 소논문 주제 탐색 도우미")

# 🔍 주제 입력창
topic = st.text_input("🔬 연구하고 싶은 과학 주제를 입력하세요:")

# -------------------------------
# ▶ 주제 입력 후 실행 흐름
# -------------------------------
if topic:
    st.subheader("📘 주제 해설")

    with st.spinner("🤖 AI가 주제에 대해 고민하고 있습니다..."):
        lines = explain_topic(topic)  # ✅ 리스트형 텍스트 반환
        placeholder = st.empty()
        typed_text = ""

        # 타이핑 효과 구현
        for line in lines:
            for char in line:
                typed_text += char
                placeholder.markdown(
                    f"<div style='font-size:16px; line-height:1.8; font-family:Nanum Gothic;'>{typed_text}</div>",
                    unsafe_allow_html=True
                )
                time.sleep(0.012)
            typed_text += "\n\n"

    # -------------------------------
    # ▶ 내부 DB 유사 논문
    # -------------------------------
    st.subheader("📄 내부 DB 유사 논문")
    try:
        internal_results = search_similar_titles(topic)
        if not internal_results:
            render_paragraph("❗ 관련 논문이 없습니다.")
        else:
            for paper in internal_results:
                render_paragraph(f"""
- **{paper['제목']}**  
  {paper['요약']}  
  _({paper['연도']} · {paper['분야']})_
""")
    except Exception as e:
        st.error(f"❗ 유사 논문 검색 중 오류가 발생했습니다: {e}")

    # -------------------------------
    # ▶ arXiv 논문 검색
    # -------------------------------
    st.subheader("🌐 arXiv 유사 논문")
    try:
        arxiv_results = search_arxiv(topic)
        if not arxiv_results:
            render_paragraph("❗ arXiv 결과가 없습니다.")
        else:
            for paper in arxiv_results:
                render_paragraph(f"""
- **{paper['title']}**  
{paper['summary']}  
🔗 [논문 링크 바로가기]({paper['link']})
""")
    except Exception as e:
        st.error(f"❗ arXiv 논문 검색 중 오류가 발생했습니다: {e}")

    # -------------------------------
    # ▶ PDF 저장 버튼
    # -------------------------------
    if st.button("📥 이 내용 PDF로 저장하기"):
        path = generate_pdf(typed_text)
        with open(path, "rb") as f:
            st.download_button("📄 PDF 다운로드", f, file_name="little_science_ai.pdf")
