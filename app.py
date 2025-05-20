import streamlit as st
import time
import os
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

# 페이지 설정 - 기본 스타일링
st.set_page_config(page_title="LittleScienceAI", layout="wide")
load_css()

# 중앙 정렬 강제 적용 (CSS 오버라이드)
st.markdown("""
<style>
/* 중앙 정렬 강제 적용 - 최우선 */
section.main > div.block-container {
    max-width: 800px !important; 
    margin: 0 auto !important;
    padding: 2rem 3rem !important;
    background-color: white !important;
}

/* 오른쪽 구분선 제거 */
.css-18e3th9 {
    padding-right: 0 !important;
    border-right: none !important;
}

/* 모든 요소 중앙 정렬 */
.element-container, .stMarkdown {
    width: 100% !important;
    max-width: 800px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* Claude 스타일 테마 */
body {
    background-color: white !important;
    color: #333 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# 인증 시스템
ACCESS_KEYS = st.secrets["general"]["access_keys"]
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("## LittleScienceAI 로그인")
    user_key = st.text_input("🔑 인증 키를 입력하세요", type="password")
    
    if user_key in ACCESS_KEYS:
        st.session_state.authenticated = True
        st.rerun()
    elif user_key:
        st.warning("🚫 올바른 인증 키를 입력하세요.")
    st.stop()

# 사이드바 - 간단하게 유지
st.sidebar.title("🧭 탐색 단계")
st.sidebar.markdown("""
1. 주제 입력
2. 개념 해설 보기
3. 논문 추천 확인
4. PDF 저장
""")

# 메인 컨텐츠 영역 - 단순하게 유지
st.title("🧪 과학 소논문 주제 탐색 도우미")

# 검색창
topic = st.text_input("🔬 연구하고 싶은 과학 주제를 입력하세요:", 
                     placeholder="예: 양자 컴퓨팅, 유전자 편집, 미생물 연료전지...")

if topic:
    # 주제 해설 파트 - 단순화된 버전
    st.subheader("📘 주제 해설")
    
    with st.spinner("🤖 AI가 주제에 대해 분석 중..."):
        lines = explain_topic(topic)
        
        # 애니메이션 없이 단순하게 텍스트 표시
        full_text = '\n\n'.join(lines)
        st.write(full_text)
    
    # 내부 DB 검색 결과 - 단순화된 버전
    st.subheader("📄 내부 DB 유사 논문")
    
    try:
        internal_results = search_similar_titles(topic)
        if not internal_results:
            st.info("❗ 관련 논문이 없습니다.")
        else:
            for paper in internal_results:
                summary = (
                    paper["요약"]
                    if paper["요약"] != "요약 없음"
                    else explain_topic(paper["제목"])[0]
                )
                
                # Streamlit 컴포넌트 사용
                st.write(f"**📌 {paper['제목']}**")
                st.write(f"*{paper['연도']} · {paper['분야']}*")
                st.write(summary)
                st.write("---")
    except Exception as e:
        st.error(f"❗ 내부 논문 오류: {e}")
    
    # arXiv 논문 검색 - 단순화된 버전
    st.subheader("🌐 arXiv 유사 논문")
    
    try:
        arxiv_results = search_arxiv(topic)
        if not arxiv_results:
            st.info("❗ arXiv 결과가 없습니다.")
        else:
            for paper in arxiv_results:
                st.write(f"**🌐 {paper['title']}**")
                st.write("*출처: arXiv*")
                st.write(paper['summary'])
                st.write(f"[🔗 논문 링크 보기]({paper['link']})")
                st.write("---")
    except Exception as e:
        st.error(f"❗ arXiv 논문 오류: {e}")
    
    # PDF 저장 버튼 - 단순화된 버전
    if st.button("📥 이 내용 PDF로 저장하기"):
        # 마크다운 형식으로 내용 구성
        pdf_content = f"# 📘 {topic} - 주제 해설\n\n{full_text}\n\n"
        
        # 내부 DB 결과 추가
        pdf_content += "## 📄 내부 DB 유사 논문\n\n"
        try:
            if not internal_results:
                pdf_content += "❗ 관련 논문이 없습니다.\n\n"
            else:
                for paper in internal_results:
                    summary = (
                        paper["요약"]
                        if paper["요약"] != "요약 없음"
                        else explain_topic(paper["제목"])[0]
                    )
                    pdf_content += f"**{paper['제목']}**\n{summary}\n_({paper['연도']} · {paper['분야']})_\n\n"
        except:
            pdf_content += "❗ 내부 논문 검색 오류\n\n"
        
        # arXiv 결과 추가
        pdf_content += "## 🌐 arXiv 유사 논문\n\n"
        try:
            if not arxiv_results:
                pdf_content += "❗ arXiv 결과가 없습니다.\n\n"
            else:
                for paper in arxiv_results:
                    pdf_content += f"**{paper['title']}**\n{paper['summary']}\n[링크]({paper['link']})\n\n"
        except:
            pdf_content += "❗ arXiv 검색 오류\n\n"
        
        # PDF 생성 및 다운로드
        path = generate_pdf(pdf_content)
        with open(path, "rb") as f:
            st.download_button(
                "📄 PDF 다운로드", 
                f, 
                file_name="little_science_ai.pdf",
                mime="application/pdf"
            )
