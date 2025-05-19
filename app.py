import streamlit as st
import time

from utils.layout import (
    render_title,
    render_paragraph,
    render_paper_card,
    load_css
)
from utils.search_db import search_similar_titles
from utils.search_arxiv import search_arxiv
from utils.explain_topic import explain_topic
from utils.pdf_generator import generate_pdf

# ✅ 페이지 설정
st.set_page_config(page_title="LittleScienceAI", layout="wide")
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

# 🧭 사이드 안내
st.sidebar.title("🧭 탐색 단계")
st.sidebar.markdown("""
1️⃣ 주제 입력  
2️⃣ 개념 해설 보기  
3️⃣ 논문 추천 확인  
4️⃣ PDF 저장  
""")

# 🧪 타이틀
render_title("🧪 과학 소논문 주제 탐색 도우미")

# 📝 주제 입력
topic = st.text_input("🔬 연구하고 싶은 과학 주제를 입력하세요:")

# ▶ 실행 흐름
if topic:
    # 📘 개념 해설 출력
    st.subheader("📘 주제 해설")
    with st.spinner("🤖 AI가 주제에 대해 고민하고 있습니다..."):
        lines = explain_topic(topic)
        typed_text = ""
        placeholder = st.empty()

        for line in lines:
            for char in line:
                typed_text += char
                placeholder.markdown(
                    f"<div class='typing-effect'>{typed_text}</div>",
                    unsafe_allow_html=True
                )
                time.sleep(0.012)
            typed_text += "\n\n"

    # 📎 PDF용 텍스트 저장
    full_text = f"# 📘 {topic} - 주제 해설\n\n{typed_text}"

    # 📄 내부 DB 논문
    st.subheader("📄 내부 DB 유사 논문")
    try:
        internal_results = search_similar_titles(topic)
        if not internal_results:
            render_paragraph("❗ 관련 논문이 없습니다.")
            full_text += "\n❗ 관련 논문이 없습니다.\n"
        else:
            for paper in internal_results:
                summary = (
                    paper["요약"]
                    if paper["요약"] != "요약 없음"
                    else explain_topic(paper["제목"])[0]
                )
                render_paper_card(
                    title=f"📌 {paper['제목']}",
                    meta=f"{paper['연도']} · {paper['분야']}",
                    summary=summary,
                    link=None
                )
                full_text += f"\n\n- **{paper['제목']}**\n{summary}\n_({paper['연도']} · {paper['분야']})_"

    except Exception as e:
        st.error(f"❗ 내부 논문 오류: {e}")

    # 🌐 arXiv 논문
    st.subheader("🌐 arXiv 유사 논문")
    try:
        arxiv_results = search_arxiv(topic)
        if not arxiv_results:
            render_paragraph("❗ arXiv 결과가 없습니다.")
            full_text += "\n❗ arXiv 결과가 없습니다.\n"
        else:
            for paper in arxiv_results:
                render_paper_card(
                    title=f"🌐 {paper['title']}",
                    meta="출처: arXiv",
                    summary=paper["summary"],
                    link=paper["link"]
                )
                full_text += f"\n\n- **{paper['title']}**\n{paper['summary']}\n[링크]({paper['link']})"
    except Exception as e:
        st.error(f"❗ arXiv 논문 오류: {e}")

    # 📥 PDF 저장 버튼
    if st.button("📥 이 내용 PDF로 저장하기"):
        path = generate_pdf(full_text)
        with open(path, "rb") as f:
            st.download_button("📄 PDF 다운로드", f, file_name="little_science_ai.pdf")
