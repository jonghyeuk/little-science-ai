# app.py 수정본 (정보 설명을 사이드바로 이동 + DB 초기화 추가)
import streamlit as st
import time
import re
from utils.layout import load_css
from utils.search_db import search_similar_titles, initialize_db  # initialize_db 추가
from utils.search_arxiv import search_arxiv
from utils.explain_topic import explain_topic
from utils.pdf_generator import generate_pdf

# 앱 시작 시 DB 초기화 (성능 최적화)
initialize_db()

# DOI 감지 및 링크 변환 함수
def convert_doi_to_links(text):
    """DOI 패턴을 감지하여 클릭 가능한 링크로 변환"""
    # DOI 패턴 정규 표현식: 10.XXXX/YYYY 형식
    doi_pattern = r'(?<!\w)(?:DOI\s*:\s*)?(\b10\.\d{4,}\/[a-zA-Z0-9./_()-]+\b)'
    
    # HTML 링크로 변환
    def replace_doi(match):
        doi = match.group(1)
        return f'<a href="https://doi.org/{doi}" target="_blank" style="color: #0969da; text-decoration: none;">{doi}</a>'
    
    # 텍스트 내 DOI 패턴을 링크로 변환
    linked_text = re.sub(doi_pattern, replace_doi, text)
    
    return linked_text

# 기본 설정
st.set_page_config(page_title="LittleScienceAI", layout="wide")
load_css()

# 중앙 정렬 CSS
st.markdown("""
<style>
section.main > div.block-container {
    max-width: 800px !important; 
    margin: 0 auto !important;
    padding: 2rem 3rem !important;
    background-color: white !important;
}

.sidebar-info-box {
    background-color: #f8f9fa;
    padding: 10px;
    border-radius: 5px;
    margin-bottom: 15px;
    border-left: 3px solid #4a86e8;
    font-size: 0.9em;
}

.sidebar-info-box h4 {
    margin-top: 0;
    color: #2c5aa0;
}

.sidebar-info-box.arxiv {
    border-left-color: #4caf50;
}

.sidebar-info-box.arxiv h4 {
    color: #2e7d32;
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

# 사이드바
st.sidebar.title("🧭 탐색 단계")
st.sidebar.markdown("""
1. 주제 입력
2. 개념 해설 보기
3. 논문 추천 확인
4. PDF 저장
""")

# 사이드바에 학술 자료 설명 추가
st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 학술 자료 정보")

# ISEF 설명 추가
st.sidebar.markdown("""
<div class="sidebar-info-box">
<h4>📊 ISEF</h4>
<p>
세계 최대 규모의 고등학생 과학 경진대회로, 80여 개국에서 1,800명 이상의 학생들이 참가하여 혁신적인 연구 프로젝트를 발표합니다. 1950년부터 시작된 이 대회는 과학, 기술, 공학, 수학(STEM) 분야의 차세대 인재를 발굴합니다.
</p>
</div>
""", unsafe_allow_html=True)

# arXiv 설명 추가
st.sidebar.markdown("""
<div class="sidebar-info-box arxiv">
<h4>📑 arXiv</h4>
<p>
물리학, 수학, 컴퓨터 과학 등의 분야에서 연구자들이 논문을 정식 출판 전에 공유하는 플랫폼입니다. 코넬 대학에서 운영하며, 최신 연구 동향을 빠르게 접할 수 있지만 일부는 아직 peer review를 거치지 않은 상태일 수 있습니다.
</p>
</div>
""", unsafe_allow_html=True)

# 메인 타이틀
st.title("🧪 과학 소논문 주제 탐색 도우미")

# 초기화
if 'full_text' not in st.session_state:
    st.session_state.full_text = ""

# 검색창
topic = st.text_input("🔬 연구하고 싶은 과학 주제를 입력하세요:", 
                     placeholder="예: 양자 컴퓨팅, 유전자 편집, 미생물 연료전지...")

# 주제가 입력된 경우
if topic:
    # 주제 해설 표시
    st.subheader("📘 주제 해설")
    
    # 즉시 해설 생성 및 표시 (DOI 링크 변환 추가)
    with st.spinner("🤖 AI가 주제 분석 중..."):
        try:
            explanation_lines = explain_topic(topic)
            explanation_text = "\n\n".join(explanation_lines)
            
            # DOI 패턴을 링크로 변환 (화면 표시용)
            linked_explanation = convert_doi_to_links(explanation_text)
            
            # 링크가 포함된 설명 표시
            st.markdown(linked_explanation, unsafe_allow_html=True)
            
            # PDF용 텍스트는 원본 형식으로 저장 (마크다운 형식)
            st.session_state.full_text = f"# 📘 {topic} - 주제 해설\n\n{explanation_text}\n\n"
        except Exception as e:
            st.error(f"주제 해설 생성 중 오류: {str(e)}")
            st.session_state.full_text = f"# 📘 {topic} - 주제 해설\n\n생성 중 오류 발생\n\n"
    
    # 내부 DB 검색 결과 (정보 아이콘 제거)
    st.subheader("📄 ISEF (International Science and Engineering Fair) 출품논문")
    
    # 스피너 메시지 수정 (속도 개선 암시)
    with st.spinner("🔍 ISEF 관련 프로젝트를 빠르게 검색 중..."):
        try:
            internal_results = search_similar_titles(topic)
            
            if not internal_results:
                st.info("❗ 관련 프로젝트가 없습니다.")
                st.session_state.full_text += "## 📄 내부 DB 유사 논문\n\n❗ 관련 프로젝트가 없습니다.\n\n"
            else:
                st.session_state.full_text += "## 📄 내부 DB 유사 논문\n\n"
                
                for project in internal_results:
                    title = project.get('제목', '')
                    summary = project.get('요약', '')
                    
                    # 메타 정보
                    meta_parts = []
                    if project.get('연도'):
                        meta_parts.append(f"📅 {project['연도']}")
                    if project.get('분야'):
                        meta_parts.append(f"🔬 {project['분야']}")
                    if project.get('국가'):
                        loc = project['국가']
                        if project.get('지역'):
                            loc += f", {project['지역']}"
                        meta_parts.append(f"🌎 {loc}")
                    if project.get('수상'):
                        meta_parts.append(f"🏆 {project['수상']}")
                    
                    meta_text = " · ".join(meta_parts)
                    
                    # 내부 결과에서도 DOI 변환 적용
                    linked_summary = convert_doi_to_links(summary)
                    
                    # 카드 형태로 표시
                    st.markdown(f"""
                    <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                        <h3 style="color: #333; margin-top: 0;">📌 {title}</h3>
                        <p style="color: #666; font-style: italic; margin-bottom: 12px;">{meta_text}</p>
                        <p>{linked_summary}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.session_state.full_text += f"- **{title}**\n{summary}\n_{meta_text}_\n\n"
        except Exception as e:
            st.error(f"내부 DB 검색 중 오류: {str(e)}")
            st.session_state.full_text += "## 📄 내부 DB 유사 논문\n\n검색 중 오류 발생\n\n"
    
    # arXiv 결과 (정보 아이콘 제거)
    st.subheader("🌐 arXiv 유사 논문")
    
    with st.spinner("🔍 arXiv 논문 검색 중..."):
        try:
            arxiv_results = search_arxiv(topic)
            
            if not arxiv_results:
                st.info("❗ 관련 논문이 없습니다.")
                st.session_state.full_text += "## 🌐 arXiv 유사 논문\n\n❗ 관련 논문이 없습니다.\n\n"
            else:
                st.session_state.full_text += "## 🌐 arXiv 유사 논문\n\n"
                
                for paper in arxiv_results:
                    title = paper.get('title', '')
                    summary = paper.get('summary', '')
                    link = paper.get('link', '')
                    
                    # arXiv 결과에서도 DOI 변환 적용
                    linked_summary = convert_doi_to_links(summary)
                    
                    # 카드 형태로 표시 (프리프린트 표시 추가)
                    st.markdown(f"""
                    <div style="background-color: #f8f9fa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0;">
                        <h3 style="color: #333; margin-top: 0;">🌐 {title}</h3>
                        <p style="color: #666; font-style: italic; margin-bottom: 12px;">출처: arXiv (프리프린트 저장소)</p>
                        <p>{linked_summary}</p>
                        <a href="{link}" target="_blank" style="color: #0969da; text-decoration: none;">🔗 논문 링크 보기</a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.session_state.full_text += f"- **{title}**\n{summary}\n[링크]({link})\n\n"
        except Exception as e:
            st.error(f"arXiv 검색 중 오류: {str(e)}")
            st.session_state.full_text += "## 🌐 arXiv 유사 논문\n\n검색 중 오류 발생\n\n"
    
    # PDF 저장 버튼
    if st.session_state.full_text:
        if st.button("📥 이 내용 PDF로 저장하기"):
            path = generate_pdf(st.session_state.full_text)
            with open(path, "rb") as f:
                st.download_button(
                    "📄 PDF 다운로드", 
                    f, 
                    file_name="little_science_ai.pdf",
                    mime="application/pdf"
                )
