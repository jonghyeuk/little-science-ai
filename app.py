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

# 페이지 설정
st.set_page_config(page_title="LittleScienceAI", layout="wide")
load_css()

# JavaScript 타이핑 효과 구현
st.markdown("""
<style>
.js-typing-container {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
    font-size: 16px !important;
    line-height: 1.6 !important;
    color: #333 !important;
    white-space: pre-wrap !important;
}
</style>

<script>
function typeWriter(text, elementId, speed = 8) {
    let container = document.getElementById(elementId);
    if (!container) return;
    
    container.innerHTML = '';
    let i = 0;
    let cursorSpan = document.createElement('span');
    cursorSpan.className = 'typing-cursor';
    cursorSpan.innerHTML = '|';
    cursorSpan.style.animation = 'blink 0.8s step-end infinite';
    container.appendChild(cursorSpan);
    
    function type() {
        if (i < text.length) {
            if (container.childNodes.length > 1) {
                container.removeChild(container.lastChild);
            }
            
            container.insertBefore(document.createTextNode(text.charAt(i)), cursorSpan);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

document.addEventListener('DOMContentLoaded', function() {
    // 실행될 타이핑 효과 함수들
    const typingElements = document.querySelectorAll('.js-typing-target');
    typingElements.forEach(function(element) {
        const text = element.getAttribute('data-text');
        const id = element.id;
        typeWriter(text, id);
    });
});
</script>
""", unsafe_allow_html=True)

# 중앙 정렬 강제 적용
st.markdown("""
<style>
section.main > div.block-container {
    max-width: 800px !important; 
    margin: 0 auto !important;
    padding: 2rem 3rem !important;
    background-color: white !important;
}

.css-18e3th9 {
    padding-right: 0 !important;
    border-right: none !important;
}

.element-container, .stMarkdown {
    width: 100% !important;
    max-width: 800px !important;
    margin-left: auto !important;
    margin-right: auto !important;
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

# 타이틀
st.title("🧪 과학 소논문 주제 탐색 도우미")

# 검색창
topic = st.text_input("🔬 연구하고 싶은 과학 주제를 입력하세요:", 
                     placeholder="예: 양자 컴퓨팅, 유전자 편집, 미생물 연료전지...")

# 새로운 검색 처리 - 실제 입력 감지
if topic and st.session_state.get('_last_topic_', '') != topic:
    # 입력 상태 저장
    st.session_state['_last_topic_'] = topic
    
    # 내용 fetch 상태 초기화
    if 'topic_content' not in st.session_state:
        st.session_state.topic_content = None
    
    if 'db_results' not in st.session_state:
        st.session_state.db_results = None
    
    if 'arxiv_results' not in st.session_state:
        st.session_state.arxiv_results = None
    
    # PDF용 텍스트 초기화
    full_text = f"# 📘 {topic} - 주제 해설\n\n"
    
    # 1. 주제 해설 생성 (처음 한 번만)
    if not st.session_state.topic_content:
        st.subheader("📘 주제 해설")
        
        with st.spinner("🤖 AI가 주제에 대해 분석 중..."):
            lines = explain_topic(topic)
            st.session_state.topic_content = lines
            full_text += "\n\n".join(lines)
    
    # 2. 내부 DB 검색 (처음 한 번만)
    if not st.session_state.db_results:
        st.subheader("📄 내부 DB 유사 논문")
        
        with st.spinner("🔍 ISEF 관련 프로젝트 검색 중..."):
            internal_results = search_similar_titles(topic)
            st.session_state.db_results = internal_results
            
            if not internal_results:
                full_text += "\n\n## 📄 내부 DB 유사 논문\n\n❗ 관련 프로젝트가 없습니다.\n"
            else:
                full_text += "\n\n## 📄 내부 DB 유사 논문\n\n"
                for project in internal_results:
                    title = project.get('제목', '')
                    summary = project.get('요약', '')
                    meta = []
