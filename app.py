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

/* 타이핑 효과용 스타일 */
.typing-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
    font-size: 16px !important;
    line-height: 1.6 !important;
    color: #333 !important;
    white-space: pre-wrap !important;
    margin-bottom: 20px !important;
}

.typing-cursor {
    display: inline-block;
    width: 2px;
    height: 1.2em;
    background-color: #555;
    margin-left: 1px;
    vertical-align: middle;
    animation: blink 0.8s step-end infinite;
}

@keyframes blink {
    from, to { opacity: 0; }
    50% { opacity: 1; }
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
    # 주제 해설 파트
    st.subheader("📘 주제 해설")
    
    with st.spinner("🤖 AI가 주제에 대해 분석 중..."):
        lines = explain_topic(topic)
        
        # 안전한 타이핑 효과 구현 - 텍스트만 처리
        typing_placeholder = st.empty()
        displayed_text = ""
        
        # 모든 줄을 하나의 텍스트로 결합
        all_text = ""
        for i, line in enumerate(lines):
            # 줄이 마크다운 헤더처럼 보이는지 확인
            if line.strip().startswith("#"):
                # 헤더 수준에 따라 스타일 추가
                header_level = min(len(line.strip()) - len(line.strip().lstrip('#')), 6)
                header_text = line.strip().lstrip('#').strip()
                
                # 헤더 스타일을 적용한 텍스트 추가
                all_text += f"\n\n**{header_text}**\n\n"
            else:
                # 일반 텍스트 줄 추가
                all_text += line + "\n\n"
        
        # 글자별 타이핑 효과
        for char in all_text:
            displayed_text += char
            typing_placeholder.markdown(displayed_text, unsafe_allow_html=False)
            time.sleep(0.01)  # 타이핑 속도 - 약간 더 빠르게
        
        # 최종 텍스트 저장
        full_text = all_text
    
    # 내부 DB 검색 결과 부분 수정
st.subheader("📄 내부 DB 유사 논문")

try:
    # 검색 시작 전 상태 표시
    with st.spinner("🔍 내부 DB에서 유사한 논문을 검색 중..."):
        internal_results = search_similar_titles(topic)
    
    # 결과가 없는 경우
    if not internal_results or len(internal_results) == 0:
        st.info("❗ 관련 논문이 없습니다.")
        full_text += "\n❗ 관련 논문이 없습니다.\n"
    else:
        # 안전하게 결과 표시
        for paper in internal_results:
            # 필수 키 확인
            title = paper.get('제목', '제목 없음')
            year = paper.get('연도', '연도 없음')
            category = paper.get('분야', '분야 없음')
            
            # 요약 처리
            if paper.get('요약') and paper['요약'] != "요약 없음":
                summary = paper['요약']
            else:
                # 요약이 없는 경우 기본 텍스트 사용
                summary = "이 논문에 대한 요약 정보가 없습니다."
            
            # Streamlit의 기본 컴포넌트로 표시
            st.markdown(f"### 📌 {title}")
            st.markdown(f"*{year} · {category}*")
            st.markdown(summary)
            st.markdown("---")
            
            # PDF용 텍스트 추가
            full_text += f"\n\n- **{title}**\n{summary}\n_({year} · {category})_"
except Exception as e:
    st.error(f"❗ 내부 논문 검색 오류: {str(e)}")
    import traceback
    st.expander("상세 오류 정보", expanded=False).code(traceback.format_exc())
    full_text += "\n❗ 내부 논문 검색 중 오류가 발생했습니다.\n"
    
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
