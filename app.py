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
    max-width: 720px !important; 
    margin: 0 auto !important;
    padding-left: 40px !important;
    padding-right: 40px !important;
    background-color: white !important;
}

/* 모든 요소 중앙 정렬 */
.element-container, .stMarkdown {
    width: 100% !important;
    max-width: 720px !important;
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
    st.markdown("""
    <div style="display: flex; justify-content: center; margin-top: 100px;">
        <div style="max-width: 450px; width: 100%; background-color: #f8f9fa; padding: 2rem; border-radius: 8px; border: 1px solid #eaecef;">
            <h2 style="text-align: center; margin-bottom: 20px; color: #333;">LittleScienceAI 로그인</h2>
    """, unsafe_allow_html=True)
    
    user_key = st.text_input("🔑 인증 키를 입력하세요", type="password")
    
    if user_key in ACCESS_KEYS:
        st.session_state.authenticated = True
        st.rerun()
    elif user_key:
        st.markdown("""
        <div style="color: #d73a49; background-color: #fff5f5; padding: 10px; border-radius: 4px; margin-top: 10px; text-align: center;">
            🚫 올바른 인증 키를 입력하세요.
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()

# 사이드바 - Claude 스타일로 수정
st.sidebar.markdown("""
<div style="padding: 1rem 0.5rem;">
    <h3 style="font-size: 18px; color: #333; margin-bottom: 15px;">🧭 탐색 단계</h3>
    <ol style="padding-left: 20px; color: #555;">
        <li style="margin-bottom: 10px;">주제 입력</li>
        <li style="margin-bottom: 10px;">개념 해설 보기</li>
        <li style="margin-bottom: 10px;">논문 추천 확인</li>
        <li style="margin-bottom: 10px;">PDF 저장</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# 메인 컨텐츠 영역
# 타이틀 (중앙 정렬 강화)
st.markdown("""
<div style="text-align: center; margin: 2rem auto;">
    <h1 style="font-size: 28px; font-weight: 600; color: #333;">
        🧪 과학 소논문 주제 탐색 도우미
    </h1>
</div>
""", unsafe_allow_html=True)

# 검색창 - Claude 스타일
topic = st.text_input("🔬 연구하고 싶은 과학 주제를 입력하세요:", 
                     placeholder="예: 양자 컴퓨팅, 유전자 편집, 미생물 연료전지...",
                     help="관심 있는 과학 주제나 키워드를 입력하세요")

if topic:
    # 주제 해설 파트
    st.markdown("""
    <h3 style="font-size: 20px; font-weight: 600; color: #333; margin: 1.5rem 0 1rem 0;">
        📘 주제 해설
    </h3>
    """, unsafe_allow_html=True)
    
    with st.spinner("🤖 AI가 주제에 대해 고민하고 있습니다..."):
        lines = explain_topic(topic)
        typed_text = ""
        placeholder = st.empty()
        
        # Claude 스타일 타이핑 효과
        for line in lines:
            # 제목과 중요 키워드 강조
            import re
            # 굵은 글씨 처리
            enhanced_line = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', line)
            
            # 글자별 타이핑 효과
            for char in enhanced_line:
                typed_text += char
                placeholder.markdown(
                    f"<div class='typing-effect'>{typed_text}</div>", 
                    unsafe_allow_html=True
                )
                time.sleep(0.004)  # 더 빠른 타이핑 속도
            typed_text += "\n\n"
    
    # 설명 텍스트 저장
    full_text = f"# 📘 {topic} - 주제 해설\n\n{typed_text}"
    
    # 내부 DB 검색 결과
    st.markdown("""
    <h3 style="font-size: 20px; font-weight: 600; color: #333; margin: 1.5rem 0 1rem 0;">
        📄 내부 DB 유사 논문
    </h3>
    """, unsafe_allow_html=True)
    
    try:
        internal_results = search_similar_titles(topic)
        if not internal_results:
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 12px 16px; border-radius: 6px; border: 1px solid #eaecef; margin: 1rem 0;">
                ❗ 관련 논문이 없습니다.
            </div>
            """, unsafe_allow_html=True)
            full_text += "\n❗ 관련 논문이 없습니다.\n"
        else:
            for paper in internal_results:
                summary = (
                    paper["요약"]
                    if paper["요약"] != "요약 없음"
                    else explain_topic(paper["제목"])[0]
                )
                
                # Claude 스타일 카드 직접 마크업
                st.markdown(f"""
                <div style="background-color: #f8f9fa; border: 1px solid #eaecef; border-radius: 6px; padding: 16px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="font-weight: 600; font-size: 16px; color: #000; margin-bottom: 4px;">
                        📌 {paper['제목']}
                    </div>
                    <div style="font-style: italic; font-size: 14px; color: #666; margin-bottom: 8px;">
                        {paper['연도']} · {paper['분야']}
                    </div>
                    <div style="font-size: 15px; color: #333; margin-bottom: 8px; line-height: 1.5;">
                        {summary}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                full_text += f"\n\n- **{paper['제목']}**\n{summary}\n_({paper['연도']} · {paper['분야']})_"
    except Exception as e:
        st.error(f"❗ 내부 논문 오류: {e}")
    
    # arXiv 논문 검색
    st.markdown("""
    <h3 style="font-size: 20px; font-weight: 600; color: #333; margin: 1.5rem 0 1rem 0;">
        🌐 arXiv 유사 논문
    </h3>
    """, unsafe_allow_html=True)
    
    try:
        arxiv_results = search_arxiv(topic)
        if not arxiv_results:
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 12px 16px; border-radius: 6px; border: 1px solid #eaecef; margin: 1rem 0;">
                ❗ arXiv 결과가 없습니다.
            </div>
            """, unsafe_allow_html=True)
            full_text += "\n❗ arXiv 결과가 없습니다.\n"
        else:
            for paper in arxiv_results:
                # Claude 스타일 arXiv 카드
                st.markdown(f"""
                <div style="background-color: #f8f9fa; border: 1px solid #eaecef; border-radius: 6px; padding: 16px; margin: 16px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                    <div style="font-weight: 600; font-size: 16px; color: #000; margin-bottom: 4px;">
                        🌐 {paper['title']}
                    </div>
                    <div style="font-style: italic; font-size: 14px; color: #666; margin-bottom: 8px;">
                        출처: arXiv
                    </div>
                    <div style="font-size: 15px; color: #333; margin-bottom: 8px; line-height: 1.5;">
                        {paper['summary']}
                    </div>
                    <div style="font-size: 14px;">
                        <a href="{paper['link']}" target="_blank" style="color: #0969da; text-decoration: none;">
                            🔗 논문 링크 보기
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                full_text += f"\n\n- **{paper['title']}**\n{paper['summary']}\n[링크]({paper['link']})"
    except Exception as e:
        st.error(f"❗ arXiv 논문 오류: {e}")
    
    # PDF 저장 버튼 - Claude 스타일
    st.markdown("<div style='margin-top: 2rem;'>", unsafe_allow_html=True)
    if st.button("📥 이 내용 PDF로 저장하기", key="save_pdf", 
                help="현재 검색 결과와 설명을 PDF 파일로 저장합니다"):
        path = generate_pdf(full_text)
        with open(path, "rb") as f:
            st.download_button(
                "📄 PDF 다운로드", 
                f, 
                file_name="little_science_ai.pdf",
                mime="application/pdf",
                help="생성된 PDF 파일을 다운로드합니다"
            )
    st.markdown("</div>", unsafe_allow_html=True)

# 디버깅 모드 추가 (문제 해결 후 제거 가능)
with st.expander("🔧 레이아웃 디버깅", expanded=False):
    st.markdown("""
    <style>
        /* 디버깅용 레이아웃 가시화 */
        .debug-mode section.main > div.block-container {
            border: 2px solid red !important;
        }
        .debug-mode .element-container {
            border: 1px dashed blue !important;
            margin: 5px 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if st.checkbox("레이아웃 경계선 표시", value=False):
        st.markdown("""
        <script>
            document.body.classList.add('debug-mode');
        </script>
        """, unsafe_allow_html=True)
    
    st.write("화면 크기 정보:")
    
    # Streamlit 버전과 환경 정보 확인
    st.code(f"""
    Streamlit 버전: {st.__version__}
    Python 버전: {os.sys.version}
    """)
    
    st.markdown("""
    ### 레이아웃 수동 조정
    
    아래 값을 바꿔서 컨테이너 너비를 조정할 수 있습니다.
    """)
    
    container_width = st.slider("컨테이너 너비 (px)", 500, 1200, 720)
    st.markdown(f"""
    <style>
    section.main > div.block-container {{
        max-width: {container_width}px !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    st.info("💡 디버깅 완료 후 이 expander 섹션은 제거하세요.")

# config.toml 생성 안내
if not os.path.exists(".streamlit/config.toml"):
    with st.expander("⚙️ 설정 파일 생성", expanded=False):
        st.markdown("""
        ### config.toml 파일 생성 필요
        
        Streamlit 테마 설정을 위해 `.streamlit/config.toml` 파일을 생성하세요:
        
        ```toml
        [theme]
        primaryColor="#0969da"
        backgroundColor="#ffffff"
        secondaryBackgroundColor="#f8f9fa"
        textColor="#333333"
        font="sans serif"
        
        [server]
        enableCORS=false
        
        [browser]
        gatherUsageStats=false
        ```
        
        이 파일은 프로젝트 루트 폴더의 `.streamlit` 폴더에 저장하세요.
        """)
