import streamlit as st

def load_css():
    """커스텀 CSS 불러오기"""
    try:
        with open("assets/styles.css", encoding="utf-8") as f:
            css = f"<style>{f.read()}</style>"
            st.markdown(css, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("❗ CSS 파일을 찾을 수 없습니다.")

def render_title(title: str):
    """페이지 제목 영역 (클래스 기반 스타일 적용)"""
    st.markdown(f"""
    <div class="title-section">
        <h2>🔬 {title}</h2>
    </div>
    """, unsafe_allow_html=True)

def render_paragraph(text: str):
    """일반 텍스트 블록 렌더링"""
    st.markdown(f"""
    <div class="text-block">
        {text}
    </div>
    """, unsafe_allow_html=True)

def render_paper_card(title: str, meta: str, summary: str, link: str = None):
    """논문 카드 렌더링 (내부 DB/외부 API 통합용)"""
    link_html = f"<div class='paper-link'>🔗 <a href='{link}' target='_blank'>논문 링크 보기</a></div>" if link else ""
    
    st.markdown(f"""
    <div class="paper-card">
        <div class="paper-title">{title}</div>
        <div class="paper-meta">{meta}</div>
        <div class="paper-summary">{summary}</div>
        {link_html}
    </div>
    """, unsafe_allow_html=True)
